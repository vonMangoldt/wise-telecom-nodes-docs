# Referrer Dashboard - UI Integration Guide

Show a referrer its standing: the tier and rates of each week, the referred and own stake behind them, what each
vault has shipped, and what is claimable per chain. Covers the World Mobile vaults `usdc`, `usdt` and `usdg` on
Ethereum, Base, Arbitrum and Robinhood Chain.

`ladderStandingOf()`, `claimablesOf()`, `ladderInputsRange()`, `weeklyRatesRange()`, `getCohortBook()`, `getFlushCursors()`

## Core Concept

The vaults measure and the hub prices. For every referrer and every closed week each vault writes a record of the
referred stake present during that week, in token seconds and by age lane, and a record of the referrer's own
stake. A flush ships those records to the hub on Ethereum mainnet, which sums them per referrer and week across
every vault of every chain, places the two inputs on the ladder, prices the week and credits a claimable bucket
per source chain.

```
vault (any chain)   records per closed week   ->  flush  ->  hub (mainnet) prices the week
reader (mainnet)    ladderStandingOf, claimablesOf, the per week ranges
```

All reader and hub calls go to Ethereum mainnet. Weeks are Unix weeks: the current week number is the current
timestamp divided by 604,800, and a week is closed once its end has passed. Chain ids: Ethereum 1, Base 8453,
Arbitrum 42161, Robinhood Chain 4663.

## 1. The standing of a closed week

```javascript
const reader = new web3.eth.Contract(READER_ABI, READER);          // mainnet
const week = Math.floor(Date.now() / 1000 / 604800);
const standing = await reader.methods.ladderStandingOf(referrer, week - 1).call();   // last closed week
```

`ladderStandingOf` returns the referred and self inputs of the week, the tier each reaches, the next threshold of
each (zero at the top tier), the three effective rates in basis points (year one, year two, mature), the latest
elevation window and an `elevated` flag. The current week reads zero until it closes and its records land.

## 2. The claimables per chain

```javascript
const CHAINS = [1, 8453, 42161, 4663];
const buckets = await reader.methods.claimablesOf(referrer, CHAINS).call();
// buckets.amounts[i]: credited by chain CHAINS[i]; buckets.payouts[i]: the address a claim pays, zero while the
// spoke chain's designation has not reached the hub; buckets.total; buckets.claimableNow (designated buckets only)
```

Both totals are before the pot's funding. The cover is the hub's USDC balance, `USD_TOKEN().balanceOf(hub)`.

## 3. The week charts

```javascript
const count = 12;
const [inputs, rates] = await Promise.all([
    reader.methods.ladderInputsRange(referrer, week - count, count).call(),
    reader.methods.weeklyRatesRange(referrer, week - count, count).call()
]);
// inputs.referredInputs[i], inputs.selfInputs[i]; rates.y1Bps[i], rates.y2Bps[i], rates.mBps[i]
```

A week's commission is its referred average times its year one rate times 7 over 364, plus the year two and
mature lanes at their rates in weeks where the uncapped ladder sum reaches the cap.

## 4. What each vault holds and has shipped

```javascript
const vault = new web3.eth.Contract(VAULT_ABI, vaultAddress);   // on that vault's chain
const [book, cursors, crumbs] = await Promise.all([
    vault.methods.getCohortBook(referrer).call(),
    vault.methods.getFlushCursors([referrer]).call(),
    vault.methods.getCohortWeekCrumbs(referrer, week - count, count).call()
]);
// book.year1, book.year2, book.mature: referred stake credited in this vault by age lane
// cursors.throughWeeks[0]: the last closed week shipped; closed weeks above it are pending
```

For a leaderboard on one chain use `claimableOf(chainId, referrers[])` on the reader.

### Returns

| View | Chain | Returns |
|---|---|---|
| `ladderStandingOf(address _referrer, uint256 _week)` | mainnet | `LadderStanding`: inputs, tiers, next thresholds, three rates, elevation window, `elevated`. |
| `claimablesOf(address _referrer, uint256[] _chainIds)` | mainnet | `(uint256[] amounts, address[] payouts, uint256 total, uint256 claimableNow)`. |
| `claimableOf(uint256 _chainId, address[] _referrers)` | mainnet | `uint256[] amounts`. |
| `ladderInputsRange(address, uint256 _fromWeek, uint256 _count)` | mainnet | `(uint256[] referredInputs, uint256[] selfInputs)`. |
| `weeklyRatesRange(address, uint256 _fromWeek, uint256 _count)` | mainnet | `(uint256[] y1Bps, uint256[] y2Bps, uint256[] mBps)`. |
| `getCohortBook(address _referrer)` | vault chain | `(uint256 year1, uint256 year2, uint256 mature, uint256 lastSettleTimestamp)`. |
| `getFlushCursors(address[] _referrers)` | vault chain | `(uint256[] throughWeeks, uint256[] gapIndexes, uint256[] gapResumeWeeks)`. |
| `getCohortWeekCrumbs(address, uint256 _fromWeek, uint256 _count)` | vault chain | `uint256[] crumbs`, one closed week's referred token seconds each. |
| `getTrackedContribution(address _user)`, `getAttributedContribution(address _user)` | vault chain | A user's stake as tracked, and the part credited to a referrer's book. |

## Preconditions

Reads only. A vault answers its cohort views once its selector round has executed and the recorder is armed
(`getCohortSyncEnabled()`); before that every book reads zero. The reader needs the hub to have received at least
one flush for the referrer before a standing is nonzero.

## Errors

The views do not revert for an unknown referrer; they return zeros. A week in the future reads zero.

## Events

```javascript
const hub = new web3.eth.Contract(HUB_ABI, HUB);   // mainnet

// a source's referred average for a week landed; the dashboard input per week
hub.events.WeekReferredReported({ filter: { referrer } })
    .on('data', (e) => { const { source, week, referredAverage } = e.returnValues; });

// a week was priced for a source: the commission per week and who delivered it
hub.events.CrumbPriced({ filter: { referrer } })
    .on('data', (e) => { const { source, week, deliverer, paid } = e.returnValues; });

// a later report raised the week's rates; a top up follows
hub.events.WeekRatesRaised({ filter: { referrer } })
    .on('data', (e) => { const { week } = e.returnValues; });
```

## Gotchas

- **The current week is never priced.** Read `week - 1` for the latest standing; the current week reads zero.
- **Inputs sum across every vault of every chain.** Referred stake in one vault and own stake in another add up on
  the same ladder in the same week.
- **A week's rate never falls.** A later record for the same week can raise it and the hub tops up what it paid.
  Until `settleWeeks` runs, a claimable may read low, never high.
- **A zero payout address means not claimable yet**, not zero earnings. Point the referrer at the payout
  designation.
- **Pending versus settled.** A closed week above a vault's through week has not reached the hub; compare the
  vault's crumbs with the reader's `weekReportsAtSource` and `paidCursorsAtSource` for a per source picture.

## Addresses

| Contract | Address | Chain |
|---|---|---|
| Referral hub | `0x68D207E22037d1B0764a509C16c08310C539ce94` | Ethereum |
| `ReferralHubReader` | `0xd0ec5Cc9A6F4d1289fAdbA648C165027cF57c125` | Ethereum |
| Vault `usdc` | `0x7e1EFF4301defc24936470B30bd1c686D2a295dc` | Ethereum, Base, Arbitrum |
| Vault `usdt` | `0x7e1EBE1D25367C6D3bC0aA72A1f00fC5320a05d7` | Ethereum, Base, Arbitrum |
| Vault `usdg` | `0x7E1e77EDE1d3b67ee46d031FC7De9e1379856064` | Ethereum, Arbitrum, Robinhood |

Everything is 6 decimals; rates are basis points per 52 week year.
