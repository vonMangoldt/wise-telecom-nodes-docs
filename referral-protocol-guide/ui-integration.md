# Vault and Referral UI Integration

Every call, view and event a front end needs, for the vaults and for the referral system.

This chapter is for front end and integration developers. The first part lists the ten vault UI integration guides that exist for the features already live, with the link to each, what your front end does with it and which facet it covers. The second part is the referral system guide in the same shape, written so that it can be published as the next guide beside them, with a reference of every read function and every event at the end.

> Every vault call goes to the vault diamond address of the product on the chain the user is on (the records in `config/vault.<product>.<network>.json`), never to a facet address. Every registry call goes to the registry of the chain the user is on. Every hub and reader call goes to Ethereum mainnet.

## Part One: The Vault UI Integration Guides

Ten guides cover the vault surface as it is live today. Each is one markdown file with worked web3.js examples, preconditions, error handling, events and gotchas, and the live addresses; nine are published as gists and the tenth ships as a gist with the next batch. The vault products are the World Mobile vaults `usdc` (mainnet, Base, Arbitrum), `usdt` (mainnet, Base, Arbitrum) and `usdg` (mainnet, Arbitrum, Robinhood), and the Sovren vault `wsnusdc` on mainnet; every vault has the same address on every chain it runs on and everything is six decimals.

### Permit2 Deposits

**Covers:** `Permit2UserFacet` (`depositWithPermit2`, `depositAndClaimInterestWithPermit2`, `depositAndCompoundInterestWithPermit2`).

Your front end lets a user deposit with a signature instead of a separate approve transaction, which matters for tokens without EIP 2612 such as USDT on mainnet. The user approves the Permit2 contract once, then signs a `PermitTransferFrom` per deposit with the amount, a nonce and a deadline, and the front end passes the signature to the deposit variant the user chose; the combined variants settle pending interest in the same transaction.

Link: [Permit2 Deposits, UI Integration Guide](https://gist.github.com/vonMangoldt/b5874a8588be9ab0dc3182ce9d33b108)

### Compound via Queue

**Covers:** `QueueFulfillFacet` (`compoundInterestViaFulfillBulk`) with the queue views `solveForAmount` and `predictTokensForCost`.

Instead of compounding accrued interest at par, your front end spends it on discounted vault tokens from the exit queue in one transaction, and whatever interest is left over is compounded automatically. The guide covers planning the fill with the solver views and the slippage bounds the call takes.

Link: [Compound via Queue, UI Integration Guide](https://gist.github.com/vonMangoldt/ffda33f1a1cc7106ad98362197575de8)

### Deposit and Compound via Queue in One Transaction

**Covers:** `MulticallFacet` (`multicall`) chaining `compoundInterestViaFulfillBulk` and `depositWithPermit2`.

Your front end replaces `depositAndCompoundInterestWithPermit2` with one `multicall` that deposits fresh stablecoin and puts the user's interest to work on the queue in the same transaction. The order of the two legs matters, and the guide explains why.

Link: [Deposit and Compound via Queue in One Transaction, UI Integration Guide](https://gist.github.com/vonMangoldt/6fffeba6ba4ecf86ace059c70fb888be)

### Switching an Order's Incentive

**Covers:** `QueueJoinLeaveFacet` (`switchQueIncentive`, `switchQueIncentivePartial`) with `getAllOrdersfromAddressWithId`.

Your front end lets a user reprice an active queue order without leaving and rejoining: one transaction, no share movement, whole or in part, with the partial variant peeling part of an order into another tier while the rest keeps its place. Because no shares move, a switch has no effect on referral credit.

Link: [Switching an Order's Incentive, UI Integration Guide](https://gist.github.com/vonMangoldt/e0cd6d7a867e16b1255eba302a371984)

### Move Between Vaults

**Covers:** `MoveFacet` (`moveBetweenVaults`, `getMoveableBalance`, `peerVault`).

Your front end relocates a position to the same chain peer vault, for example from the usdt vault into the usdc vault and back: the source burns the shares and the destination mints them, the deposit cap travels with the shares, and referral attribution follows them with exactly the age it had.

Link: [Move Between Vaults, UI Integration Guide](https://gist.github.com/vonMangoldt/6f79a1422e856f5c4ca39f947fe6139b)

### Cross Chain Bridging

**Covers:** `BridgeFacet` (`bridgeToVault`, `bridgeToVaultWithReferral`, `quoteBridgeFee`, `quoteBridgeFeeWithReferral`, `getBridgeableBalance`).

Your front end quotes the CCIP fee in the native token, sends the bridge with the fee as value and tracks the delivery; the shares burn on the source chain and mint to the same address on the destination chain. While the referral recorder is armed, the vault itself attaches the referral attribution of the bridged shares to the message, so the front end passes no referral data, and the credit travels only when the destination recipient is the sender's own address.

Link: [Cross Chain Bridging, UI Integration Guide](https://gist.github.com/vonMangoldt/cce2fdc186a6f993a4d03fb31c6add01)

### WISE Burn

**Covers:** `BurnWiseFacet` (`burnWise`, `getBurnableWise`, `getNextBurnPercentage`).

Your front end shows the burn state of the Ethereum usdc vault and offers the permissionless `burnWise` button: a rotating slice of the WISE the vault holds is burned, reducing WISE total supply, with a per caller cooldown between burns.

Link: [WISE Burn, UI Integration Guide](https://gist.github.com/vonMangoldt/4bde487f791f074c03e42e938c57db5c)

### Queue Forecast

**Covers:** `QueueForecastFacet` (`solveForAmountAfterFulfill`).

Your front end quotes a queue purchase against the book as it will look after another fill lands, which prices a second fill while a first is still pending and plans the later legs of a `multicall` batch before any of it has executed. The view returns the `fulfillOrderBulk` arrays plus the post fill amounts the chain cannot show yet.

Link: [Queue Forecast, UI Integration Guide](https://gist.github.com/vonMangoldt/8a7fcda79aeef0138a8efe6aeab9c4c6)

### Grace Period Countdown

**Covers:** the grace views compiled into the diamond (`graceThresholdAmount`, `gracePeriodDuration`, `lastLargeDepositAt`, `depositAccumWindow`) and the `GracePeriodNotElapsed` error.

Your front end shows the interest lock timer a large deposit starts: the three views to wire, the exact gate formula, the warning to show before a deposit crosses the threshold, and which functions the lock gates (interest extraction and relocation) and which it does not (deposits and exits). `gracePeriodDuration` reads 0 on every vault since 2026-11-07 (45 days, 3,888,000 seconds, before that, with one day at 0 on 2026-11-05), so no lock is in force today; the master can change it at any time without a timelock, so the countdown reads the view rather than a constant.

Link: [Grace Period Countdown, UI Integration Guide](https://gist.github.com/vonMangoldt/66a8ed87ad6c7d7989ec6ed1e1987a81)

### Exit an Order and Move to the Peer Vault in One Transaction

**Covers:** `MulticallFacet` (`multicall`) chaining `leaveQue` and `moveBetweenVaults`, with `getAllOrdersfromAddressWithId` and `getMoveableBalance`.

Your front end lets a user with an active queue order pull it and relocate the freed shares to the same chain peer vault atomically. For referral credit this is a leave followed by a move: the leave restores nothing and the move carries whatever credit the shares still hold. This guide ships as a gist with the next batch.

## Part Two: Referral UI Integration Guide

Link: [Referral System, UI Integration Guide](https://gist.github.com/vonMangoldt/0965f7a36b0dab6bd775bbaffab4db2d)

The referral system lets a depositor name a referrer with a deposit and pays that referrer a weekly commission at the hub on mainnet. Your front end has four jobs: pass the referrer into the deposit, show a user their referrer, show a referrer their standing and claimables with the claim buttons, and let a user veto a correction. Everything else is reading views and listening to events; the reference tables at the end of this chapter list every one of them.

```
deposit with referrer  ->  the registry records the pair, once
every closed week      ->  the vault writes the referrer's record
shipment               ->  closed weeks reach the hub (CCIP from Base, Arbitrum and Robinhood; a direct call on mainnet)
hub                    ->  prices the weeks, credits a claimable bucket per source chain and referrer
claim                  ->  USDC paid on mainnet to the payout address
```

The chain ids the hub keys its buckets by are Ethereum 1, Base 8453, Arbitrum 42161 and Robinhood Chain 4663. The examples below use web3.js; `ZERO` is the zero address, `CHAINS` is `[1, 8453, 42161, 4663]`, and the contract addresses come from [Addresses](addresses.md).

**Flushing is described, not integrated, for now.** Between the vault's weekly record and the hub's pricing sits the flush: a transaction on the vault that settles a referrer's book and ships its closed weeks to the hub, over CCIP from Base, Arbitrum and Robinhood and by a direct call on mainnet. [Shipping Weeks to the Hub](for-referrers.md#shipping-weeks-to-the-hub) explains it, including who may flush and the courier share. A front end does not need a flush button at the start: the protocol's couriers ship every book on a schedule, so a referrer's weeks reach the hub and become claimable without any action in the user interface. The flush calls and their errors join this chapter once a flush button becomes part of the integration; the two cursor views a front end reads for a book's shipping state are already in the reference table and in [Which Views for Which Screen](ui-integration.md#which-views-for-which-screen).

### The Referral Link:

Link: [Referral Deposits, UI Integration Guide](https://gist.github.com/vonMangoldt/e1bb3959d66e4f3fb717c65dc7f11ddb)

A referral link carries the referrer's address. Keep that address and write it into the referrer field of the deposit call you send; **that exact address is what the chain's registry records for the depositor and what the hub prices**, so a referrer is identified by nothing but the address in that field.

The referral deposit entrypoints on the vault, all on the user's chain, are these.

```solidity
depositWithReferral(uint256 _amount, address _referrer)
depositAndClaimInterestWithReferral(uint256 _amount, address _referrer) returns (uint256)
depositAndCompoundInterestWithReferral(uint256 _amount, address _referrer) returns (uint256)
depositWithPermit2WithReferral(uint256 _amount, uint256 _nonce, uint256 _deadline, bytes _signature, address _referrer)
depositAndClaimInterestWithPermit2WithReferral(uint256 _amount, uint256 _nonce, uint256 _deadline, bytes _signature, address _referrer) returns (uint256)
depositAndCompoundInterestWithPermit2WithReferral(uint256 _amount, uint256 _nonce, uint256 _deadline, bytes _signature, address _referrer) returns (uint256)
```

```javascript
const vault = new web3.eth.Contract(VAULT_ABI, vaultAddress);

// the referrer already recorded for this user wins over the one in the link
const recorded = await vault.methods.getReferrerOf(userAddress).call();
const referrer = recorded !== ZERO ? recorded : referrerFromLink;

// plain allowance path; the Permit2 variants take the four permit arguments before the referrer
await usd.methods.approve(vaultAddress, amount).send({ from: userAddress });
await vault.methods.depositWithReferral(amount, referrer).send({ from: userAddress });
```

Each is the plain deposit variant with the referrer assignment run first. The call reverts when the referrer is the zero address or the depositor itself, when the vault's registry pointer is not set, and when the registry refuses the referrer (a vault, the registry, the hub, or an address whose own referral chain leads back to the depositor). A depositor who already has a referrer is kept on it and the deposit still succeeds, so read the user's referrer first and show it rather than the link's address when they differ. The Permit2 variants follow the Permit2 Deposits guide for the signature; the only difference is the trailing referrer argument.

**Check a contract referrer against mainnet.** The registry accepts any referrer address, and every bucket pays that same address on mainnet unless a designation signed by it on the deposit chain redirects it. An externally owned account owns its address everywhere and is fine. A smart wallet that exists on mainnet alone is fine too: it cannot sign on Base, but its Base bucket pays its own address on mainnet, where it does exist. The case to catch is a contract referrer that has code on the deposit chain but none at the same address on mainnet, or another owner there: its commission on that chain pays an address it may not control until it designates from the deposit chain. Before a deposit on Base, Arbitrum or Robinhood read the referrer's code on both chains, warn the user or refuse the link in that case, and tell referrers to share an address they control on every chain, or to deploy their wallet at the same address on mainnet before they share a link.

```javascript
// an externally owned account has no code and is fine everywhere; a contract referrer is paid at its own address on mainnet
const codeHere = await web3.eth.getCode(referrer);
const codeOnMainnet = await web3Mainnet.eth.getCode(referrer);
if (codeHere !== "0x" && codeOnMainnet === "0x") {
  // a smart wallet that exists on this chain alone is paid at an address on mainnet it may not control: warn, or refuse the link
}
```

### Reading a User's Referrer:

Link: [Reading a User's Referrer, UI Integration Guide](https://gist.github.com/vonMangoldt/1a177aade1303df2aa11155fc9374a2c)

On the vault, `getReferrerOf(address _user) returns (address)` reads through the registry pointer and returns zero while no referrer is set. On the registry of the same chain you can read more.

```solidity
referrerOf(address _user) returns (address)
getReferrerPair(address _user) returns (address referrer, uint256 assignedAt, uint256 rank)
effectiveReferrerOf(address _user, address _vault) returns (address)
```

```javascript
const registry = new web3.eth.Contract(REGISTRY_ABI, await vault.methods.getReferralRegistry().call());
const { referrer, assignedAt, rank } = await registry.methods.getReferrerPair(userAddress).call();
```

`getReferrerPair` returns the assignment time and the rank of the chain that made it (Ethereum 0, Base 1, Arbitrum 2, Robinhood 3); an `assignedAt` below 1,700,000,000 marks a pair written by the correction lane, decoded as 3,399,999,999 minus the value. `effectiveReferrerOf` returns the referrer a given vault still credits while a cross chain flip is pending for that vault; it equals `referrerOf` once the flip is delivered.

### The Referrer Dashboard:

Link: [Referrer Dashboard, UI Integration Guide](https://gist.github.com/vonMangoldt/8cd201ff1fa10861b7d7d6658fdc7970)

All reader calls go to the `ReferralHubReader` contract on mainnet; the hub views named here are on the hub diamond on mainnet. Weeks are Unix weeks: the current week number is the current timestamp divided by 604,800, and a week is closed once its end has passed.

```solidity
ladderStandingOf(address _referrer, uint256 _week) returns (LadderStanding standing)
claimablesOf(address _referrer, uint256[] _chainIds) returns (uint256[] amounts, address[] payouts, uint256 total, uint256 claimableNow)
claimableOf(uint256 _chainId, address[] _referrers) returns (uint256[] amounts)
weeklyRatesRange(address _referrer, uint256 _fromWeek, uint256 _count) returns (uint256[] y1Bps, uint256[] y2Bps, uint256[] mBps)
weeklyRates(address _referrer, uint256 _week) returns (uint256 y1Bps, uint256 y2Bps, uint256 mBps)
```

```javascript
const reader = new web3.eth.Contract(READER_ABI, readerAddress);     // mainnet

const week = Math.floor(Date.now() / 1000 / 604800);
const [standing, buckets] = await Promise.all([
    reader.methods.ladderStandingOf(referrer, week - 1).call(),      // the last closed week
    reader.methods.claimablesOf(referrer, CHAINS).call()
]);

// buckets.amounts[i] is what chain CHAINS[i] has credited; buckets.payouts[i] is the address a
// claim pays, the referrer's own address until a designation from that chain reached the hub.
```

* **`ladderStandingOf`:** the referred and self inputs of a closed week, the tier each reaches, the next threshold of each (zero at the top tier), the three effective rates in basis points, the referrer's latest elevation window and an `elevated` flag. The current week reads zero until it closes and its records land.
* **`claimablesOf`:** one bucket per source chain with the address a claim would pay, the referrer itself until a designation from that chain redirected it. `total` sums every bucket and `claimableNow` equals it, a field kept from the time an undesignated spoke bucket could not pay; both are before the pot's funding.
* **`weeklyRates` and `weeklyRatesRange`:** the three rates of a week in basis points, on the hub itself and batched on the reader.

### The Payout Designation:

Link: [Payout Designation, UI Integration Guide](https://gist.github.com/vonMangoldt/e2b720dace558e8eac0f230ccc3dbba5)

Commission accrues at the hub per source chain and referrer. Every bucket pays the referrer's own address on mainnet unless the referrer designates another: with `setPayoutAddress(address _payout)` on the hub for the mainnet bucket, and on the chain's registry for a Base, Arbitrum or Robinhood bucket, from where the designation has to reach the hub.

On the spoke chain's registry:

```solidity
setPayoutAddress(address _payout)
pushPayoutAddress(address _owner) payable
quotePushPayoutFee(address _owner) returns (uint256)
getPayoutDesignation(address _owner) returns (address payout, uint256 stamp)
```

```javascript
await registry.methods.setPayoutAddress(mainnetPayout).send({ from: referrer });

// optional: push it now instead of waiting for the next shipment of the book
const pushFee = await registry.methods.quotePushPayoutFee(referrer).call();
await registry.methods.pushPayoutAddress(referrer).send({ from: referrer, value: pushFee });
```

`setPayoutAddress` records the designation under the caller's address; a second designation in the same second reverts, so a correction waits one block. The designation travels to the hub with the next shipment of the referrer's book on that chain, or at once through `pushPayoutAddress` with the quoted CCIP fee as value, which anyone may send for any owner. The newest designation wins at the hub. Offer the push button when the registry's stamp for the referrer is above `payoutStamp(chainId, owner)` on the hub, a designation set but not landed.

A designation of the zero address is valid and returns the bucket to the referrer's own address on mainnet, the same as no designation at all. A referrer that is a contract wallet on a spoke chain and does not control its address on mainnet should designate a mainnet address it controls. A vault address can never designate.

The reverse case needs no designation. A contract wallet that exists on mainnet alone cannot designate on a spoke chain, because nobody can sign for that address there, and nothing on the hub or the registry lets us designate on its behalf; but its spoke buckets pay the same address on mainnet by default, where the wallet does exist, so it claims there without any designation. The case that needs care is a contract wallet that exists on a spoke chain but not at the same address on mainnet: its spoke bucket pays an address on mainnet it may not control, and only a designation signed on the spoke redirects it (a Safe or an account factory with the same owners and salt lands on the same address on mainnet, which is the other way out). The check in [The Referral Link](#the-referral-link) keeps a front end from creating that case.

### The Claim Buttons:

Link: [Claiming Commission, UI Integration Guide](https://gist.github.com/vonMangoldt/89bee1f46a5ab0440aa70797ee674f5b)

All on the hub on mainnet.

```solidity
claim(uint256 _chainId, address _referrer)
claimUpTo(uint256 _chainId, address _referrer, uint256 _amount)
claimAll(address _referrer, uint256[] _chainIds) returns (uint256 total)
payoutAddressOf(uint256 _chainId, address _owner) returns (address)
claimable(uint256 _chainId, address _account) returns (uint256)
```

```javascript
const hub = new web3.eth.Contract(HUB_ABI, hubAddress);               // mainnet
const usdc = new web3.eth.Contract(ERC20_ABI, await hub.methods.USD_TOKEN().call());

const cover = await usdc.methods.balanceOf(hubAddress).call();        // what the pot can pay today
const claimableChains = CHAINS.filter((_, i) => buckets.amounts[i] !== '0' && buckets.payouts[i] !== ZERO);
await hub.methods.claimAll(referrer, claimableChains).send({ from: referrer });
```

* **`claim`:** pays one bucket in full and reverts `PotDry` when the pot holds less.
* **`claimUpTo`:** pays up to the given amount and up to the pot's balance.
* **`claimAll`:** pays every listed bucket that can pay, in list order against the pot's cover, and reverts `NothingClaimable` only when nothing was paid.

A claim may be sent by the referrer or by the bucket's payout address and always pays the payout address. Show `claimable` per chain, the hub's USDC balance as the cover, and offer `claimAll` with the chains that have a nonzero amount and a nonzero `payoutAddressOf`.

### The Correction Veto:

Link: [Correction Veto, UI Integration Guide](https://gist.github.com/vonMangoldt/0e0bdb5d5c0c60d890867c7f6d9f6c2e)

When we propose a different referrer for a user, the user has three days to refuse. Watch `ReferralCorrectionProposed(user, oldReferrer, newReferrer, queuedAt)` on the registry of the user's chain and show a cancel button that calls, on that registry:

```solidity
cancelCorrectReferrer(address _user)
```

```javascript
registry.events.ReferralCorrectionProposed({ filter: { user: userAddress } })
    .on('data', (e) => {
        const { newReferrer, queuedAt } = e.returnValues;
        const deadline = Number(queuedAt) + 3 * 24 * 3600;
        // show: proposed referrer newReferrer, you can cancel until deadline
    });

await registry.methods.cancelCorrectReferrer(userAddress).send({ from: userAddress });
```

The pending proposal is readable with `proposedCorrection(address _user) returns (address)` and `correctionQueuedAt(address _user) returns (uint256)`. For a user who already has a referrer the proposal appears on the chain whose rank the user's key carries; for a user without a referrer it may appear on any chain.

### Preconditions:

```javascript
const [registryAddress, syncEnabled, paused, depositsDisabled] = await Promise.all([
    vault.methods.getReferralRegistry().call(),
    vault.methods.getCohortSyncEnabled().call(),
    vault.methods.paused().call(),
    vault.methods.depositsDisabled().call()
]);

// the referral entrypoints need the registry pointer set; the plain deposit gates still apply
const canDepositWithReferral = registryAddress !== ZERO && !paused && !depositsDisabled;
// nothing is measured for commission while the recorder is off
const earning = syncEnabled;
```

For a spoke chain claim check that `payoutAddressOf(chainId, referrer)` is nonzero. The vault side referral functions become live on each vault once its selector round executes; until then `getReferralRegistry()` reads the zero address and the referral entrypoints are not routed.

### Errors:

**From the vault, deposit with referrer:**

| Error | Cause |
|---|---|
| `InvalidValue` | The referrer is the zero address. |
| `SelfReferral` | The referrer is the depositor itself. |
| `ReferralRegistryNotSet` | The vault's registry pointer is not set yet. |
| `InvalidReferrer` (from the registry) | The referrer is a vault, the registry, the hub, or an address whose own referral chain leads back to the depositor. |

The plain deposit errors apply as well: `DepositsDisabled`, `DepositExceedCap`, the pause, and for the combined variants `GracePeriodNotElapsed` and `NoInterest`.

**From the registry, designation and veto:**

| Error | Cause |
|---|---|
| `InvalidPayoutOwner` | A vault address tried to designate. |
| `PayoutStampNotNewer` | A second designation in the same second; wait one block. |
| `NothingToPush` | No designation to push for that owner. |
| `InsufficientPushFee` | The value sent is below `quotePushPayoutFee`. |
| `NoCorrectionProposed` | No proposal is open against the user. |
| `NotCorrectionParty` | The caller is neither the user nor the operator. |

**From the hub, claims:**

| Error | Cause |
|---|---|
| `PotDry` | `claim` asked for more than the pot holds; use `claimUpTo` or `claimAll`. |
| `NothingClaimable` | `claimAll` paid nothing. |
| `NotPayoutAuthorized` | The caller is neither the referrer nor the bucket's payout address. |

### Gotchas:

* **The referrer is the address in the field, nothing else:** an integrator that wants to be the referrer of every deposit it sends writes its own address there, on every chain, in every deposit.
* **The first assignment wins everywhere:** a later deposit with another referrer succeeds as a deposit and the argument is ignored; show the recorded referrer, not the link's.
* **The referral variant is needed once:** pass the referrer only while `getReferrerOf` reads zero for the user. Once a referrer is recorded, the plain deposit, compound, move and bridge calls credit it by themselves, so a front end can switch back to the plain variants.
* **A designation is optional:** every bucket pays the referrer's own address on mainnet until the referrer designates another, and a contract wallet on a spoke chain that does not control its address on mainnet should designate one it controls before its first commission accrues.
* **A contract referrer's address must be its own on mainnet:** a spoke bucket pays the same address on mainnet by default and only a designation that address signs on the deposit chain can redirect it, so a smart wallet that exists on Base, Arbitrum or Robinhood but not at the same address on mainnet earns into a bucket paid to an address it may not control; read the referrer's code on both chains and warn or refuse a link whose contract address has no code on mainnet.
* **The current week is never shipped:** only closed weeks travel, and a week becomes claimable only after its envelope is applied at the hub.
* **A closed week keeps its verdict:** rates can rise when more records arrive, never fall, and nothing already credited is clawed back.
* **Joining the exit queue ends the referrer's credit for the queued amount**, like a withdrawal would; leaving the queue unfilled restores nothing.

### Reference: Every Read Function

The tables below list every read function a front end or an indexer can use, with its signature, the chain it is called on and the statistic it feeds. Vault calls go to the vault diamond of the product on the user's chain, registry calls to that chain's registry, hub and reader calls to mainnet. A week argument is a Unix week number.

#### Vault: Referral and Recorder Views

| Function | Chain | Feeds |
|---|---|---|
| `getReferrerOf(address _user) returns (address)` | vault chain | A user's referrer as the vault reads it from the registry, zero while unset or while the pointer is unset. |
| `getReferralRegistry() returns (address)`, `getProposedReferralRegistry() returns (address)`, `getReferralRegistryChangeQueuedAt() returns (uint256)` | vault chain | Which registry the vault consults and whether a pointer change is pending. |
| `getCohortSyncEnabled() returns (bool)` | vault chain | Whether the recorder is armed; nothing is measured while it is off. |
| `getTrackedContribution(address _user) returns (uint256)` | vault chain | A user's stake as the recorder tracks it, the user's own stake input to the ladder. |
| `getAttributedContribution(address _user) returns (uint256)` | vault chain | The part of a user's tracked stake credited to a referrer's book, the amount a referrer earns on for this user. |
| `getCohortSelfCrumb(address _user) returns (uint256 settledAt, uint256 currentWeekSeconds, uint256 previousWeekSeconds)` | vault chain | A referrer's own presence in the current and the previous week in token seconds, the self input before it is shipped. |
| `getCohortBook(address _referrer) returns (uint256 year1, uint256 year2, uint256 mature, uint256 lastSettleTimestamp)` | vault chain | The referred stake credited to a referrer in this vault by age lane, and when the book was last settled. |
| `getCohortScore(address _referrer) returns (uint256)` | vault chain | The three lanes summed, the referred amount a referrer currently holds in this vault. |
| `getCohortRings(address _referrer) returns (uint64[52] year1, uint64[52] year2)` | vault chain | Per week slot, how much of the referrer's credit graduates at each coming week boundary. |
| `getCohortWeekCrumb(address _referrer, uint256 _week) returns (uint256)` | vault chain | One closed week's referred token seconds (three 80 bit lanes plus the written bit), the record the hub prices. |
| `getCohortWeekCrumbs(address _referrer, uint256 _fromWeek, uint256 _count) returns (uint256[] crumbs)` | vault chain | A range of closed weeks' records, for a per week chart of referred stake. |
| `getCohortGapLogLength(address _referrer) returns (uint256)`, `getCohortGapLogEntry(address _referrer, uint256 _index) returns (uint256)` | vault chain | Dormant spans recorded as one gap record each (from week, to week, mature principal). |
| `getFlushedThroughWeek(address _referrer) returns (uint256)` | vault chain | The last closed week shipped from this vault by a flush that wrote the cursors, the referrer's own flush or the courier batch that opened the book; zero until the book has been shipped here once. |
| `getFlushCursors(address[] _referrers) returns (uint256[] throughWeeks, uint256[] gapIndexes, uint256[] gapResumeWeeks)` | vault chain | The two send cursors of many referrers at once: the through week, the index of the next gap record to ship and the week at which to resume inside it, for the shipping state of a dashboard. |

#### Registry: Every Getter

| Function | Chain | Feeds |
|---|---|---|
| `referrerOf(address _user) returns (address)` | registry chain | A user's referrer. |
| `referrerKey(address _user) returns (uint256)` | registry chain | The packed key `(assignedAt << 8) or rank`; the time since when the user has this referrer and the chain that recorded it. |
| `getReferrerPair(address _user) returns (address referrer, uint256 assignedAt, uint256 rank)` | registry chain | The same, unpacked; an `assignedAt` below 1,700,000,000 marks a pair written by the correction lane (decode it as 3,399,999,999 minus the value). |
| `effectiveReferrerOf(address _user, address _vault) returns (address)` | registry chain | The referrer a vault still credits while a flip is pending there. |
| `pendingFlip(address _vault, address _user) returns (address)` | registry chain | The old referrer a vault has not yet migrated away from, zero when no flip is pending. |
| `LOCAL_CHAIN_RANK() returns (uint256)`, `maxSyncRank() returns (uint256)` | registry chain | This chain's rank and the highest rank the merge accepts. |
| `allowedVault(address _vault) returns (bool)`, `everAllowedVault(address _vault) returns (bool)`, `allowedVaultQueuedAt(address _vault) returns (uint256)`, `trackedVaultCount() returns (uint256)` | registry chain | Which vaults may write, which ever could, and pending allow proposals. |
| `payoutAddress(address _owner) returns (address)`, `payoutStamp(address _owner) returns (uint256)`, `getPayoutDesignation(address _owner) returns (address payout, uint256 stamp)` | registry chain | A referrer's payout designation on this chain and when it was set (the stamp is `(setAt << 8) or rank`). |
| `payoutHub() returns (address)`, `payoutHubChainSelector() returns (uint64)`, `proposedPayoutHub()`, `proposedPayoutHubChainSelector()`, `payoutHubChangeQueuedAt()` | registry chain | The hub a designation push goes to and any pending change. |
| `quotePushPayoutFee(address _owner) returns (uint256)`, `quoteSyncFee(address _user, uint64[] _selectors) returns (uint256)` | registry chain | The native fee of a designation push or a referrer broadcast. |
| `proposedCorrection(address _user) returns (address)`, `correctionQueuedAt(address _user) returns (uint256)`, `proposedCorrectionKey(address _user) returns (uint256)` | registry chain | The correction proposal open against a user: the proposed referrer, when the three days started, and the key it is bound to. |
| `correctionsLatched() returns (bool)`, `seedsLatched() returns (bool)` | registry chain | Whether the correction lane and the retroactive seed are closed on this chain. |
| `ccipRouter() returns (address)`, `syncInitialized() returns (bool)`, `syncGasLimit() returns (uint64)`, `proposedCcipRouter()`, `ccipRouterChangeQueuedAt()` | registry chain | The registry's CCIP wiring and any pending router change. |
| `syncPeer(uint64 _chainSelector) returns (address)`, `syncPeerEnabled(uint64) returns (bool)`, `proposedSyncPeer(uint64)`, `syncPeerChangeQueuedAt(uint64)`, `syncPeerQuarantined(uint64) returns (bool)` | registry chain | The peer registries this chain syncs with, pending peer changes and braked lanes. |
| `processedSyncMessageId(bytes32 _messageId) returns (bool)` | registry chain | Whether a CCIP sync message was already applied. |
| `getCarry(address _srcVault, address _dstVault, address _user) returns (uint256 stagedAt, uint256[] payload)` | registry chain | A same chain move carry staged and not yet consumed (normally empty). |
| `master() returns (address)`, `proposedMaster() returns (address)` | registry chain | The registry's master and a pending handover. |

#### Hub: Every View of `IReferralHub`

| Function | Chain | Feeds |
|---|---|---|
| `claimable(uint256 _chainId, address _account) returns (uint256)` | mainnet | Commission (or courier share) accrued and not yet claimed, per source chain and address. |
| `payoutAddressOf(uint256 _chainId, address _owner) returns (address)` | mainnet | The address a claim of that bucket pays: the owner itself until a designation from that chain redirected it. |
| `payoutStamp(uint256 _chainId, address _owner) returns (uint256)` | mainnet | The stamp of the designation the hub holds for that bucket; zero means none. |
| `totalAccrued() returns (uint256)`, `totalClaimed() returns (uint256)`, `totalPayable() returns (uint256)` | mainnet | Protocol totals: everything priced (commission and courier share), everything paid out, and the amount owed to buckets that can claim; `totalPayable - totalClaimed` is what the pot should hold. |
| `USD_TOKEN() returns (IERC20)` | mainnet | The pot's token; its `balanceOf(hub)` is the cover for claims. |
| `weeklyRates(address _referrer, uint256 _week) returns (uint256 y1Bps, uint256 y2Bps, uint256 mBps)` | mainnet | The three rates of a closed week in basis points, elevation included. |
| `ladderInputsAt(address _referrer, uint256 _week) returns (uint256 referredInput, uint256 selfInput)` | mainnet | A referrer's referred and own average stake of a week, summed over every source. |
| `weekReportOf(bytes32 _source, address _referrer, uint256 _week) returns (uint256 referredAverage, uint256 paidUnits)` | mainnet | One source's reported referred average for a week and the commission units already paid for it. |
| `weekSelfOf(bytes32 _source, address _referrer, uint256 _week) returns (uint256)` | mainnet | One source's reported self average for a week. |
| `paidCursorAtSource(bytes32 _source, address _referrer, uint256 _week) returns (uint256 y1Cursor, uint256 y2Cursor, uint256 mCursor)` | mainnet | How much of a week's referred token seconds a source has had priced, per lane; compare with the vault's crumb to see what is still pending. |
| `sourceKeyOf(uint256 _chainId, address _vault) returns (bytes32)` | mainnet | The source key of a vault on a chain, the argument of the per source views. |
| `sourceCountOf(address _referrer) returns (uint256)`, `sourceOfAt(address _referrer, uint256 _index) returns (bytes32)` | mainnet | The sources (vaults on chains) that ever reported for a referrer. |
| `sourceChainIdOf(bytes32 _source) returns (uint256)`, `sourceSystemOf(bytes32 _source) returns (uint256)`, `MAX_SYSTEMS() returns (uint256)` | mainnet | The chain a source credits and the vault system it belongs to. |
| `elevatedFromWeek(address _referrer) returns (uint256)`, `elevatedUntilWeek(address _referrer) returns (uint256)` | mainnet | The latest elevation window of a referrer (until week zero means open; from week zero means never elevated). |
| `rateTableCount() returns (uint256)`, `rateTableAt(uint256 _index) returns (RateTable)` | mainnet | The published rate tables: effective week, cap, year two and mature rates, courier share, tiers and thresholds. |
| `allowedReporter(address _reporter) returns (bool)` | mainnet | Whether a mainnet vault may report directly. |
| `ccipRouter() returns (address)`, `designationSourceChainId(uint64 _chainSelector, address _sender) returns (uint256)` | mainnet | The hub's CCIP wiring: which registries on which chains it accepts designations from. |
| `leverChangeQueuedAt(bytes32 _changeHash) returns (uint256)`, `selectorToFacet(bytes4)`, `proposedSelectorFacet(bytes4)`, `selectorChangeQueuedAt(bytes4)`, `initialized() returns (bool)` | mainnet | Pending grants and selector changes behind the three day timelock. |
| `master() returns (address)`, `proposedMaster() returns (address)` | mainnet | The hub's master and a pending handover. |

#### Reader: Every View of `ReferralHubReader`

| Function | Chain | Feeds |
|---|---|---|
| `HUB() returns (IReferralHub)` | mainnet | The hub this reader reads. |
| `ladderStandingOf(address _referrer, uint256 _week) returns (LadderStanding)` | mainnet | A referrer's standing in a closed week: both inputs, the tier each reaches, the next threshold of each, the three effective rates, the latest elevation window and the `elevated` flag. |
| `ladderInputsRange(address _referrer, uint256 _fromWeek, uint256 _count) returns (uint256[] referredInputs, uint256[] selfInputs)` | mainnet | Referred and own amounts per week for a chart. |
| `weeklyRatesRange(address _referrer, uint256 _fromWeek, uint256 _count) returns (uint256[] y1Bps, uint256[] y2Bps, uint256[] mBps)` | mainnet | Rates per week for a chart. |
| `weekReportsAtSource(bytes32 _source, address _referrer, uint256 _fromWeek, uint256 _count) returns (uint256[] referredAverages, uint256[] paidUnits)` | mainnet | One vault's reported averages and paid units per week, the settled weeks of a source. |
| `paidCursorAt(address _reporter, address _referrer, uint256 _week) returns (uint256 y1Cursor, uint256 y2Cursor, uint256 mCursor)` | mainnet | The paid cursor of a mainnet vault by address. |
| `paidCursorsAtSource(bytes32 _source, address _referrer, uint256 _fromWeek, uint256 _count) returns (uint256[] cursorWords)` | mainnet | Paid cursors per week as packed lane words, the pending versus settled picture of a source. |
| `claimableOf(uint256 _chainId, address[] _referrers) returns (uint256[] amounts)` | mainnet | Claimable amounts of many referrers on one chain, for leaderboards. |
| `claimablesOf(address _referrer, uint256[] _chainIds) returns (uint256[] amounts, address[] payouts, uint256 total, uint256 claimableNow)` | mainnet | One referrer's buckets across chains with the payout address each pays, the owner itself until designated, and the total; `claimableNow` equals `total`. |

### Reference: Every Event

The tables list every event with its indexed fields marked and what a dashboard derives from it. With them an indexer can build complete per user and per referrer statistics: deposit attribution, weeks priced, claims paid, designations, corrections, elevations and rate tables.

#### Vault Cohort Facets (Emitted by the Vault Diamond on Its Chain)

| Event | Derived statistic |
|---|---|
| `CohortContributionCredited(address indexed user, address indexed referrer, uint256 amount)` | A deposit, compound, seed or relocation credited this amount of the user's stake to the referrer: deposit attribution per user and per referrer. |
| `CohortContributionSeeded(address indexed user, uint256 amount)` | Master credited a user's existing balance from this instant on. |
| `CohortContributionSynced(address indexed user, address indexed referrer, uint256 oldContribution, uint256 newContribution)` | The user's tracked stake was clamped to the balance held; the difference left the referrer's reach. |
| `CohortAttributionCharged(address indexed user, address indexed referrer, uint256 charged, uint256 uncharged)` | How much of a clamp was taken from the referrer's book and how much was never attributed. |
| `CohortDivestParked(address indexed user)`, `CohortDivestDrained(address indexed user)`, `CohortDivestParkSkipped(address indexed user, address indexed parked)` | A share sender awaiting its clamp, the clamp catching up, and a second sender that had to wait. |
| `CohortBookSettled(address indexed referrer, uint256 fromTimestamp, uint256 toTimestamp, uint256 boundariesWalked)` | The referrer's book was brought up to date across this many week boundaries. |
| `CohortBookReduced(address indexed referrer, uint256 amount, uint256 fromYear1, uint256 fromYear2, uint256 fromMature)` | Referred credit left the book, by age lane, through a sale, a queue join, a burn or a relocation. |
| `CohortGapRecorded(address indexed referrer, uint256 fromWeek, uint256 toWeekExclusive, uint256 maturePrincipal)` | A dormant span was compressed into one record. |
| `CohortLaneSaturated(address indexed referrer, uint256 laneKind, uint256 index, uint256 clippedAmount)` | A lane hit its ceiling; an anomaly signal. |
| `CohortReferrerLookupFailed(address indexed user)` | The registry read failed and the mutation was skipped; an anomaly signal. |
| `CohortSyncEnabledSet(bool enabled)`, `CohortDisarmSpanSet(uint256 disarmedAt, uint256 rearmedAt)` | The recorder was armed or disarmed; weeks inside a disarm span count no presence. |
| `CohortCarryStaged(address indexed user, address indexed dstVault, address indexed referrer, uint256 trackedDelta, uint256 year1, uint256 year2, uint256 mature, uint256 pairCount)` | A same chain move captured this much credit for the destination vault. |
| `CohortCarryApplied(address indexed user, address indexed srcVault, address indexed referrer, address carriedReferrer, uint256 trackedDelta, uint256 year1, uint256 year2, uint256 mature, uint256 pairCount)` | The destination landed the carried credit under the referrer it credits. |
| `CohortCarrySkipped(address indexed user, address indexed dstVault)`, `CohortCarryDiscarded(address indexed user, address indexed srcVault, uint256 stagedAt)`, `CohortCarryBookDropped(address indexed user, address indexed srcVault, address carriedReferrer, uint256 trackedDelta, uint256 mature, uint256 pairCount)` | A move whose carry did not land or landed without a book; attribution lost for that move. |
| `CohortReferrerFlipApplied(address indexed user, address indexed oldReferrer, address indexed newReferrer, uint256 year1, uint256 year2, uint256 mature, uint256 pairCount)` | A user's credit moved from the old referrer's book to the new one after a sync flip or a correction. |
| `CohortBridgeCarrySent(address indexed user, uint64 indexed dstChainSelector, address indexed referrer, uint256 trackedDelta, uint256 year1, uint256 year2, uint256 mature, address bookReferrer)` | A bridge took this much credit out of the source book. |
| `CohortBridgeCarryApplied(address indexed user, uint64 indexed srcChainSelector, address indexed effectiveReferrer, address carriedReferrer, uint256 trackedDelta, uint256 year1, uint256 year2, uint256 mature)` | The destination landed the bridged credit. |
| `CohortBridgeCarryDiscarded(address indexed user, uint64 indexed srcChainSelector)`, `CohortBridgeCarryBookDropped(address indexed user, uint64 indexed srcChainSelector, address carriedReferrer, uint256 year1, uint256 year2, uint256 mature)`, `CohortBridgeCarrySkipped(address indexed user, uint64 indexed dstChainSelector)`, `CohortBridgeHookFailed(address indexed user, uint64 indexed srcChainSelector)`, `CohortQuarantineReadFailed(address indexed user, uint64 indexed srcChainSelector)` | Bridges whose attribution did not travel; the shares always arrive. |
| `CohortSelfCrumbSettled(address indexed user, uint256 settledAt, uint256 currentWeekSeconds, uint256 previousWeekSeconds)`, `CohortSelfLogged(address indexed user, uint256 fromWeek, uint256 completedSeconds, uint256 stake)` | A referrer's own presence per week, the self input as it is written. |
| `ReferralRegistrySet(address referralRegistry)`, `ReferralRegistryProposed(address indexed proposedReferralRegistry, uint256 executableAt)`, `ReferralRegistryProposalCancelled(address indexed cancelledReferralRegistry)` | The registry pointer and its timelock. |

#### Registry (Emitted by the Registry on Its Chain)

| Event | Derived statistic |
|---|---|
| `ReferralAssigned(address indexed user, address indexed referrer, address indexed vault)` | A depositor's first referrer and the vault whose deposit recorded it: the referral count per referrer. |
| `ReferralSyncAdopted(address indexed user, address indexed referrer, uint256 syncKey)` | A pair arrived from another chain for a user with none here. |
| `ReferralSyncKeyLowered(address indexed user, address indexed referrer, uint256 oldKey, uint256 newKey)` | The same referrer with an earlier key; the since when of the pair moved earlier. |
| `ReferralSyncFlipped(address indexed user, address indexed oldReferrer, address indexed newReferrer, uint256 syncKey)` | An earlier assignment elsewhere replaced the local referrer. |
| `SyncKeyCollision(address indexed user, address indexed localReferrer, address indexed incomingReferrer, uint256 syncKey)` | Two different referrers with an equal key; the local one stands. |
| `ReferralMutualDissolved(address indexed user, address indexed oldReferrer, uint256 winnerKey)` | A mutual pair was resolved; this user's edge was dropped. |
| `FlipMarked(address indexed vault, address indexed user, address indexed oldReferrer)`, `FlipCleared(...)`, `FlipMigrated(address indexed vault, address indexed user, address oldReferrer, address newReferrer)`, `FlipMigrationDeferred(...)` | The delivery of a flip to each vault: pending, cleared, migrated or deferred until the vault is armed. |
| `SyncBroadcast(address indexed user, uint64 indexed destChainSelector, address indexed referrer, uint256 syncKey, bytes32 messageId)`, `SyncReceived(uint64 indexed srcChainSelector, bytes32 indexed messageId, address indexed user)` | Referrer pairs sent to and received from peer chains. |
| `ReferralCorrectionProposed(address indexed user, address indexed oldReferrer, address indexed newReferrer, uint256 queuedAt)` | A correction or a master assignment opened against the user; the three day veto window starts at `queuedAt`. |
| `ReferralCorrectionCancelled(address indexed user, address indexed newReferrer, address indexed cancelledBy)` | Who cancelled it: the user, master, or the registry itself on a mutual dissolve. |
| `ReferralCorrectionExecuted(address indexed user, address indexed oldReferrer, address indexed newReferrer, uint256 syncKey)` | The correction took effect; a zero `oldReferrer` is an assignment of a user who had none. |
| `CorrectionsLatched()`, `SeedsLatched()` | The lane or the seed was closed for good on this chain. |
| `PayoutAddressSet(address indexed owner, address indexed payout, uint256 stamp)` | A referrer designated a payout address on this chain. |
| `PayoutPushed(address indexed owner, uint64 indexed destChainSelector, address payout, uint256 stamp, bytes32 messageId)` | The designation was pushed to the hub. |
| `CarryStaged(address indexed srcVault, address indexed dstVault, address indexed user, uint256 words)`, `CarryConsumed(address indexed srcVault, address indexed dstVault, address indexed user, uint256 stagedAt)` | A same chain move staged and consumed its carry. |
| `VaultAllowedSet(address indexed vault, bool allowed)`, `VaultAllowProposed(address indexed vault, uint256 queuedAt)`, `VaultAllowProposalCancelled(address indexed vault)` | The vault allowlist and its timelock. |
| `SyncPeerProposed(uint64 indexed chainSelector, address indexed peer, uint256 queuedAt)`, `SyncPeerSet(uint64 indexed chainSelector, address indexed peer)`, `SyncPeerProposalCancelled(...)`, `SyncPeerRemoved(uint64 indexed chainSelector, address indexed peer)`, `SyncPeerQuarantined(uint64 indexed chainSelector)`, `SyncPeerQuarantineLifted(uint64 indexed chainSelector)` | The peer table, its timelock and braked lanes. |
| `CcipRouterSet(address indexed router)`, `CcipRouterProposed(address indexed router, uint256 queuedAt)`, `CcipRouterProposalCancelled(address indexed router)`, `SyncGasLimitSet(uint64 gasLimit)`, `SyncSetupFinalized()`, `MaxSyncRankRaised(uint256 rank)` | The CCIP wiring and the rank bound. |
| `PayoutHubProposed(address indexed hub, uint64 chainSelector, uint256 queuedAt)`, `PayoutHubSet(address indexed hub, uint64 chainSelector)`, `PayoutHubProposalCancelled(address indexed hub)` | The designation route to the hub. |

#### Hub (Emitted by the Hub Diamond on Mainnet)

| Event | Derived statistic |
|---|---|
| `SourceListed(address indexed referrer, bytes32 indexed source, uint256 chainId)` | A vault on a chain reported for a referrer for the first time. |
| `WeekReferredReported(bytes32 indexed source, address indexed referrer, uint256 indexed week, uint256 referredAverage)`, `WeekSelfReported(bytes32 indexed source, address indexed referrer, uint256 indexed week, uint256 selfAverage)` | A source's referred and self averages for a week: the referred and self amounts per week per referrer, summed over sources. |
| `WeekRatesRaised(address indexed referrer, uint256 indexed week)` | A later report raised the week's rates; top ups follow. |
| `WeekToppedUp(bytes32 indexed source, address indexed referrer, uint256 indexed week, uint256 amount)` | A source's cell was paid the difference after a rate rise. |
| `CrumbPriced(bytes32 indexed source, address indexed referrer, uint256 indexed week, address deliverer, uint256 y1Increment, uint256 y2Increment, uint256 mIncrement, uint256 paid)` | A week's referred token seconds were priced for a source: the commission per week per referrer and who delivered it. |
| `GapPriced(bytes32 indexed source, address indexed referrer, address deliverer, uint256 fromWeek, uint256 toWeekExclusive, uint256 paid)` | A dormant span was priced across several weeks at once. |
| `CrumbLaneRegression(bytes32 indexed source, address indexed referrer, uint256 indexed week, uint256 laneKind, uint256 incoming, uint256 cursor)` | A delivery below the paid cursor; nothing paid, an anomaly signal. |
| `PayoutAddressSet(uint256 indexed chainId, address indexed owner, address indexed payout)` | A designation reached the hub for a bucket; the state of the payout designation per chain. |
| `DesignationPushReceived(uint64 indexed srcChainSelector, uint256 indexed chainId, address indexed owner)` | A pushed designation arrived. |
| `PayoutClaimed(uint256 indexed chainId, address indexed referrer, address indexed payout, uint256 amount)` | A claim was paid: claimed per chain, per referrer and per payout address. |
| `ReferrerElevated(address indexed referrer, uint256 fromWeek)`, `ReferrerElevationEnded(address indexed referrer, uint256 untilWeek)` | Elevation windows per referrer; replayed in order they give the whole history. |
| `RateTableScheduled(uint256 indexed index, uint256 effectiveFromWeek)` | A rate table was published for a future week; read it with `rateTableAt(index)`. |
| `DelivererShareCapSet(uint256 cap)`, `ReporterAllowedSet(address indexed reporter, bool allowed)`, `SourceSystemSet(bytes32 indexed source, uint256 systemId)` | Policy changes on the courier cap, the reporters and the system tags. |
| `CcipRouterSet(address indexed router)`, `DesignationSourceSet(uint64 indexed chainSelector, address indexed registry, uint256 chainId)` | The hub's CCIP wiring. |
| `LeverChangeProposed(bytes32 indexed changeHash, bytes call, uint256 executableAt)`, `LeverChangeCancelled(bytes32 indexed changeHash)` | A grant was queued or dropped; `call` is the exact setter call, so a dashboard can show pending grants in plain words. |
| `SelectorProposed(bytes4 indexed selector, address indexed facet, uint256 executableAt)`, `SelectorsProposed(bytes4[] selectors, address indexed facet, uint256 executableAt)`, `SelectorUpdated(bytes4 indexed selector, address indexed facet)`, `SelectorProposalCancelled(bytes4 indexed selector)`, `SetupFinalized()` | The hub's own upgrade timelock. |

### Which Views for Which Screen

* **A depositor's profile:** read `getReferrerPair` on the user's chain for the referrer and the time since when, `proposedCorrection` and `correctionQueuedAt` for an open proposal to veto, and `getAttributedContribution` on each vault for how much of the user's stake is credited.
* **A referrer's overview:** read `claimablesOf` on the reader for accrued and claimable per chain, `ladderStandingOf` for the current tier and rates, `ladderInputsRange` and `weeklyRatesRange` for the week charts, and `getPayoutDesignation` on each spoke registry beside `payoutAddressOf` on the hub for the designation state.
* **A referrer's shipping and payout state:** nothing here needs the referrer's action. A vault whose `getFlushedThroughWeek` reads zero while the fourth value of `getCohortBook`, the last settle timestamp, is nonzero holds a book that has not been shipped yet; the next courier batch opens it. A spoke chain whose registry `getPayoutDesignation` returns a stamp of zero pays the referrer's own address on mainnet, and `claimablesOf` shows that address for the bucket. A designation is set but not landed when the registry's stamp is above `payoutStamp(chainId, owner)` on the hub for that chain; the bucket pays its previous address until the designation reaches the hub with the next flush of the book or a push. A front end that helps a contract wallet referrer shows the designation step on every spoke chain where the wallet does not control its address on mainnet.
* **A per vault detail:** read `getCohortBook` and `getCohortWeekCrumbs` for the measured weeks and `weekReportsAtSource` with `paidCursorsAtSource` on the reader for shipped versus settled weeks.
* **An indexer:** build the history from `ReferralAssigned`, `CohortContributionCredited`, `CrumbPriced`, `GapPriced`, `WeekToppedUp`, `PayoutAddressSet`, `PayoutClaimed`, the correction events and the elevation events.

**Batching a designation with an own flush.** A referrer who wants both in one go cannot use the vault's `MulticallFacet`: `multicall` batches calls into the same diamond only and is not payable, so it can neither reach the registry nor carry the CCIP fee of the flush. It is a wallet level batch, EIP 5792 calls from a smart wallet or an externally owned account under EIP 7702, with the registry designation first, so that the flush carries it, and the vault flush with its fee second, or two transactions in that order. The flush refunds the excess fee to the sender, so a contract wallet that sends it must be able to receive the native token.

### Conclusion

Pass the referrer address into the deposit, read the registry for the user's referrer, read the reader for the referrer's standing and claimables, and offer the designation, claim and veto buttons on the chain each call belongs to. The reference tables give you every view and every event with its signature, so a dashboard and an indexer can show the whole picture without guessing at anything.
