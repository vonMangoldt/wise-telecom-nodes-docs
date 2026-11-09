# Flushing Referral Weeks - UI Integration Guide

Ship a referrer's closed weeks from a vault to the hub so they get priced. Covers the World Mobile vaults `usdc`,
`usdt` and `usdg` on Ethereum, Base, Arbitrum and Robinhood Chain.

`flushReferrals()`, `flushReferralWindow()`, `advanceBook()`, `quoteFlushFee()`, `previewFlushEnvelope()`, `getFlushCursors()`

## Core Concept

Nothing is paid on the vault. Each vault holds a book per referrer and ships it to the hub on Ethereum mainnet as a
flush envelope: a transaction on the vault that settles the referrer's book, plans the closed weeks not yet shipped
and sends them. From Base, Arbitrum and Robinhood the envelope travels over Chainlink CCIP and the caller pays the
CCIP fee in the chain's native token, excess refunded. From a mainnet vault the envelope is delivered to the hub in
the same transaction by a direct call.

```
quoteFlushFee([referrer])        ->  fee (0 on mainnet)
flushReferrals([referrer])       ->  closed weeks above the cursors leave the vault
hub FlushReceived / FlushApplied ->  the weeks are priced, claimable grows
```

A referrer may always flush its own book. For another referrer's book the caller must be an allowlisted flush bot
unless the public flush switch is on, which ships off. Only closed weeks travel; the current week never does.

## 1. Check who may flush

```javascript
const vault = new web3.eth.Contract(VAULT_ABI, vaultAddress);
const [isBot, publicOn] = await Promise.all([
    vault.methods.getAllowedFlushBot(callerAddress).call(),
    vault.methods.getPublicFlushEnabled().call()
]);
const own = callerAddress.toLowerCase() === referrer.toLowerCase();
const mayFlush = own || isBot || publicOn;
```

## 2. See what is pending

```javascript
const week = Math.floor(Date.now() / 1000 / 604800);
const cursors = await vault.methods.getFlushCursors([referrer]).call();
const through = Number(cursors.throughWeeks[0]);
const pendingWeeks = Math.max(0, week - 1 - through);   // closed weeks not yet shipped
```

`previewFlushEnvelope([referrer])` returns the bytes a flush would send, planned on storage before the settle a
real flush performs, so it is a lower bound; a zero length envelope means nothing to ship.

## 3. Quote and flush

```javascript
const fee = await vault.methods.quoteFlushFee([referrer]).call();   // 0 on mainnet
await vault.methods.flushReferrals([referrer]).send({ from: callerAddress, value: fee });
```

Send the quoted fee as value on Base, Arbitrum and Robinhood and nothing on mainnet; excess is refunded.

## 4. Batches and the window form

A batch of more than one referrer takes only books already advanced to the current week; `advanceBook(referrer,
maxBoundaries)` is permissionless and walks a book across week boundaries. On mainnet a batch holds at most six
referrers.

```javascript
await vault.methods.advanceBook(referrer, 60).send({ from: callerAddress });
await vault.methods.flushReferrals([a, b, c]).send({ from: callerAddress, value: await vault.methods.quoteFlushFee([a, b, c]).call() });
```

The window form ships one referrer from a chosen week and gap record onward; a referrer uses it to ship a book
older than two years or a particular span:

```javascript
await vault.methods.flushReferralWindow(referrer, fromWeek, fromGapIndex).send({ from: referrer, value: fee });
```

Only the referrer's own flush writes the vault's cursors; a courier can only ship weeks above them.

### Parameters

| Parameter | Type | Meaning |
|---|---|---|
| `_referrers` | `address[]` | The books to ship; one for a self flush, at most six on mainnet. |
| `_referrer`, `_fromWeek`, `_fromGapIndex` | `address`, `uint256`, `uint256` | The window form: one book from this closed week and gap record onward. |
| `_maxBoundaries` | `uint256` | How many week boundaries `advanceBook` may walk in one call. |
| value | native | The quoted CCIP fee on a spoke chain, nothing on mainnet. |

## Preconditions

```javascript
const [hub, syncEnabled] = await Promise.all([
    vault.methods.getFlushHub().call(),            // (address, chainSelector); zero selector means direct call on mainnet
    vault.methods.getCohortSyncEnabled().call()
]);
const wired = hub[0] !== ZERO && syncEnabled;
```

## Errors

| Error | Cause |
|---|---|
| `NotFlushBot` | The caller is neither the referrer nor an allowlisted bot while public flush is off. |
| `NothingToFlush` | No closed week above the cursors. |
| `FlushBatchTooLarge` | More referrers than a batch may hold. |
| `FlushBookNotAdvanced` | A book in a multi referrer batch was not advanced to the current week; call `advanceBook` first. |
| `InsufficientFlushFee` | The value sent is below `quoteFlushFee`. |
| `FlushWindowInvalid` | The window form's from week or gap index is out of range. |
| `FlushCursorVirgin` | A courier tried to ship a book the referrer has never flushed itself; the referrer's own first flush opens it. |
| `FlushOutageGraceActive` | The weeks to ship overlap a recent pause or disarm of the recorder and the outage grace has not passed yet. |
| `FlushHubNotSet`, `CohortSyncDisabled` | The vault is not wired or not armed yet. |
| `FlushRefundFailed` | The excess fee could not be returned to the caller; use an address that accepts native value. |

## Events

```javascript
// a CCIP flush left a spoke vault; match messageId with the hub's FlushReceived and FlushApplied
vault.events.CohortFlushSent().on('data', (e) => { const { messageId, deliverer, entryCount } = e.returnValues; });

// a mainnet flush was delivered by direct call
vault.events.CohortFlushDelivered().on('data', (e) => { const { flushHub, deliverer, entryCount } = e.returnValues; });

// the referrer's own flush advanced the cursors
vault.events.CohortReferrerFlushed({ filter: { referrer } })
    .on('data', (e) => { const { flushedThroughWeek, flushedGapIndex, gapResumeWeek } = e.returnValues; });

// on the hub (mainnet): the envelope arrived and was priced
hub.events.FlushApplied().on('data', (e) => { const { messageId, source, entryCount } = e.returnValues; });
```

A courier watches `DelivererSharePaid(chainId, deliverer, referrer, messageId, amount)` on the hub for the share
it earned.

## Gotchas

- **Only closed weeks travel.** Nobody gains by flushing at a particular moment inside a week.
- **The referrer's own flush moves the cursors.** A courier can only ship weeks above them; a referrer who wants to
  control what ships first flushes its own book first.
- **The courier share is paid on top.** An allowlisted bot earns 5 percent (the genesis courier share) of the
  commission of the closed weeks it priced first, paid by the protocol, never deducted from the referrer. A self
  flush earns no share.
- **Later delivery costs nothing but time.** A week flushed late is priced at the rate it had when it closed. The
  vaults keep up to 104 weeks of history per book for the first flush, so flush each book at least once every two
  years.
- **Each envelope is bounded.** At most 16 referrers and a bounded amount of work, so every accepted flush fits one
  transaction at the hub.

## Addresses

| Contract | Address | Chain |
|---|---|---|
| Vault `usdc` | `0x7e1EFF4301defc24936470B30bd1c686D2a295dc` | Ethereum, Base, Arbitrum |
| Vault `usdt` | `0x7e1EBE1D25367C6D3bC0aA72A1f00fC5320a05d7` | Ethereum, Base, Arbitrum |
| Vault `usdg` | `0x7E1e77EDE1d3b67ee46d031FC7De9e1379856064` | Ethereum, Arbitrum, Robinhood |
| Referral hub | `0x68D207E22037d1B0764a509C16c08310C539ce94` | Ethereum |

Everything is 6 decimals. The flush functions become live on each vault once its flush round executes.
