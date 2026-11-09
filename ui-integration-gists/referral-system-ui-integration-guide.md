# Referral System - UI Integration Guide

Let a depositor name a referrer with a deposit, show a referrer what it earns, and offer the claim and veto
buttons on the chain each call belongs to. Covers the World Mobile vaults `usdc`, `usdt` and `usdg` on Ethereum,
Base, Arbitrum and Robinhood Chain.

`depositWithReferral()`, `getReferrerOf()`, `claimablesOf()`, `setPayoutAddress()`, `claimAll()`, `cancelCorrectReferrer()`

## Core Concept

A referrer is identified by one thing only: the address written into the referrer field of a deposit. The chain's
referral registry records that address for the depositor once, every vault on the chain reads the same registry,
and the registries of all chains exchange their records over CCIP so the earliest assignment wins everywhere. The
vaults measure, week by week, how much referred stake each referrer had present; the closed weeks are shipped to
the hub on Ethereum mainnet, and the hub prices them against the rate table and credits a claimable USDC bucket per
source chain and referrer.

```
deposit with referrer  ->  registry records the pair (once)
every closed week      ->  vault writes the referrer's record
shipment               ->  closed weeks reach the hub (CCIP from Base, Arbitrum, Robinhood; direct call on mainnet)
hub                    ->  prices the weeks, credits claimable per (source chain, referrer)
claim                  ->  USDC paid on mainnet to the payout address
```

Your front end has four jobs: pass the referrer into the deposit, show a user their referrer, show a referrer its
standing and claimables with the claim buttons, and let a user veto a correction. Everything else is
reading views and listening to events.

Chain ids used by the hub: Ethereum 1, Base 8453, Arbitrum 42161, Robinhood Chain 4663.

## 1. The referral link and the deposit

A referral link carries the referrer's address. Keep that address and write it into the referrer field of the
deposit call you send. Six entrypoints on the vault take a referrer, each the plain deposit variant with the
assignment run first:

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

// 1. the referrer from the link, or the one already recorded for this user
const recorded = await vault.methods.getReferrerOf(userAddress).call();
const referrer = recorded !== ZERO ? recorded : referrerFromLink;

// 2. plain allowance path (Permit2 variants take the four permit arguments before the referrer)
await usd.methods.approve(vaultAddress, amount).send({ from: userAddress });
await vault.methods.depositWithReferral(amount, referrer).send({ from: userAddress });
```

The assignment is written once. A depositor who already has a referrer is kept on it and the deposit still
succeeds with the referrer argument ignored, so read `getReferrerOf` first and show the recorded referrer instead
of the link's address when they differ. The Permit2 variants follow the Permit2 Deposits guide for the signature;
the only difference is the trailing referrer argument.

## 2. Reading a user's referrer

On the vault, `getReferrerOf(address _user)` reads through the registry pointer and returns the zero address while
no referrer is set. On the registry of the same chain you can read more:

```solidity
referrerOf(address _user) returns (address)
getReferrerPair(address _user) returns (address referrer, uint256 assignedAt, uint256 rank)
effectiveReferrerOf(address _user, address _vault) returns (address)
proposedCorrection(address _user) returns (address)
correctionQueuedAt(address _user) returns (uint256)
```

```javascript
const registry = new web3.eth.Contract(REGISTRY_ABI, await vault.methods.getReferralRegistry().call());
const { referrer, assignedAt, rank } = await registry.methods.getReferrerPair(userAddress).call();
```

`assignedAt` is the time of the assignment and `rank` the chain that made it (Ethereum 0, Base 1, Arbitrum 2,
Robinhood 3). An `assignedAt` below 1,700,000,000 marks a pair written by the correction lane; decode it as
3,399,999,999 minus the value. `effectiveReferrerOf` is the referrer a given vault still credits while a cross chain
flip is pending for that vault; it equals `referrerOf` once the flip is delivered.

## 3. The referrer dashboard

All reader calls go to `ReferralHubReader` on Ethereum mainnet; the hub views go to the hub diamond on mainnet.
Weeks are Unix weeks: the current week number is the current timestamp divided by 604,800, and a week is closed
once its end has passed.

```solidity
ladderStandingOf(address _referrer, uint256 _week) returns (LadderStanding standing)
claimablesOf(address _referrer, uint256[] _chainIds) returns (uint256[] amounts, address[] payouts, uint256 total, uint256 claimableNow)
claimableOf(uint256 _chainId, address[] _referrers) returns (uint256[] amounts)
ladderInputsRange(address _referrer, uint256 _fromWeek, uint256 _count) returns (uint256[] referredInputs, uint256[] selfInputs)
weeklyRatesRange(address _referrer, uint256 _fromWeek, uint256 _count) returns (uint256[] y1Bps, uint256[] y2Bps, uint256[] mBps)
```

```javascript
const reader = new web3.eth.Contract(READER_ABI, READER);          // mainnet
const CHAINS = [1, 8453, 42161, 4663];

const week = Math.floor(Date.now() / 1000 / 604800);
const [standing, buckets] = await Promise.all([
    reader.methods.ladderStandingOf(referrer, week - 1).call(),   // last closed week
    reader.methods.claimablesOf(referrer, CHAINS).call()
]);

// buckets.amounts[i] is what chain CHAINS[i] has credited; buckets.payouts[i] is the address a claim pays,
// zero while the spoke chain's payout designation has not reached the hub.
```

`ladderStandingOf` gives the referred and self inputs of a closed week, the tier each reaches, the next threshold of
each (zero at the top tier), the three effective rates in basis points, the latest elevation window and an
`elevated` flag. The current week reads zero until it closes and its records land. `total` sums every bucket and
`claimableNow` only the designated ones, both before the pot's funding is considered.

On each vault, the book views show what the vault has measured for a referrer:

```solidity
getCohortBook(address _referrer) returns (uint256 year1, uint256 year2, uint256 mature, uint256 lastSettleTimestamp)
getCohortWeekCrumbs(address _referrer, uint256 _fromWeek, uint256 _count) returns (uint256[] crumbs)
```

## 4. The payout designation

Commission accrues at the hub per source chain and referrer. On mainnet a bucket pays the referrer's own address
unless the referrer sets another with `setPayoutAddress(address _payout)` on the hub. On Base, Arbitrum and Robinhood
a bucket pays nothing until a designation from that chain has reached the hub.

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
const fee = await registry.methods.quotePushPayoutFee(referrer).call();
await registry.methods.pushPayoutAddress(referrer).send({ from: referrer, value: fee });
```

The designation travels to the hub with the next shipment of the referrer's book on that chain, or at once through
`pushPayoutAddress`, which anyone may send for any owner. The newest designation wins at the hub. Offer the push
button when `claimablesOf` shows a zero payout for a chain with a nonzero amount. A designation of the zero address
is valid and pays the referrer's own address on mainnet. A referrer that is a contract wallet on a spoke chain must
designate a nonzero mainnet address it controls.

## 5. The claim buttons

All on the hub on mainnet.

```solidity
claim(uint256 _chainId, address _referrer)
claimUpTo(uint256 _chainId, address _referrer, uint256 _amount)
claimAll(address _referrer, uint256[] _chainIds) returns (uint256 total)
payoutAddressOf(uint256 _chainId, address _owner) returns (address)
claimable(uint256 _chainId, address _account) returns (uint256)
```

```javascript
const hub = new web3.eth.Contract(HUB_ABI, HUB);                   // mainnet
const usdc = new web3.eth.Contract(ERC20_ABI, await hub.methods.USD_TOKEN().call());

const cover = await usdc.methods.balanceOf(HUB).call();             // what the pot can pay today
const claimableChains = CHAINS.filter((_, i) => buckets.amounts[i] !== '0' && buckets.payouts[i] !== ZERO);
await hub.methods.claimAll(referrer, claimableChains).send({ from: referrer });
```

`claim` pays one bucket in full and reverts `PotDry` when the pot holds less. `claimUpTo` pays up to the given
amount and up to the pot's balance. `claimAll` pays every listed bucket that can pay, in list order against the
pot's cover, and reverts `NothingClaimable` only when nothing was paid. A claim may be sent by the referrer or by
the bucket's payout address and always pays the payout address.

## 6. The correction veto

When the operator proposes a different referrer for a user, the user has three days to refuse. Watch
`ReferralCorrectionProposed(user, oldReferrer, newReferrer, queuedAt)` on the registry of the user's chain and show
a cancel button:

```javascript
registry.events.ReferralCorrectionProposed({ filter: { user: userAddress } })
    .on('data', (e) => {
        const { newReferrer, queuedAt } = e.returnValues;
        const deadline = Number(queuedAt) + 3 * 24 * 3600;
        // show: "proposed referrer newReferrer, you can cancel until deadline"
    });

await registry.methods.cancelCorrectReferrer(userAddress).send({ from: userAddress });
```

The pending proposal is readable with `proposedCorrection(address _user)` and `correctionQueuedAt(address _user)`.
For a user who already has a referrer the proposal appears on the chain whose rank the user's key carries; for a
user without a referrer it may appear on any chain.

## Preconditions

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

For a spoke chain claim check `payoutAddressOf(chainId, referrer)` is nonzero.

## Errors

**From the vault (deposit with referrer):**

| Error | Cause |
|---|---|
| `InvalidValue` | The referrer is the zero address. |
| `SelfReferral` | The referrer is the depositor itself. |
| `ReferralRegistryNotSet` | The vault's registry pointer is not set yet. |
| `InvalidReferrer` (registry) | The referrer is a vault, the registry, the hub, or an address whose own referral chain leads back to the depositor. |

Plus the plain deposit errors (`DepositsDisabled`, `DepositExceedCap`, `Pausable: paused`, and for the combined
variants `GracePeriodNotElapsed` and `NoInterest`).

**From the registry (designation and veto):**

| Error | Cause |
|---|---|
| `InvalidPayoutOwner` | A vault address tried to designate. |
| `PayoutStampNotNewer` | A second designation in the same second; wait one block. |
| `NothingToPush` | No designation to push for that owner. |
| `InsufficientPushFee` | The value sent is below `quotePushPayoutFee`. |
| `NoCorrectionProposed` | No proposal is open against the user. |
| `NotCorrectionParty` | The caller is neither the user nor the operator. |

**From the hub (claims):**

| Error | Cause |
|---|---|
| `PotDry` | `claim` asked for more than the pot holds; use `claimUpTo` or `claimAll`. |
| `NothingClaimable` | `claimAll` paid nothing. |
| `NotPayoutAuthorized` | The caller is neither the referrer nor the bucket's payout address. |
| `PayoutNotDesignated` | A spoke chain bucket has no designation at the hub yet. |

## Events

```javascript
// the assignment, on the registry of the user's chain
registry.events.ReferralAssigned({ filter: { user: userAddress } })
    .on('data', (e) => { const { user, referrer, vault } = e.returnValues; });

// a claim paid, on the hub
hub.events.PayoutClaimed({ filter: { referrer } })
    .on('data', (e) => { const { chainId, payout, amount } = e.returnValues; });
```

Other events worth a dashboard: `CohortContributionCredited(user, referrer, amount)` on the vault for deposit
attribution, `CrumbPriced(source, referrer, week, deliverer, y1Increment, y2Increment, mIncrement, paid)` on the hub
for the commission per week, `PayoutAddressSet(chainId, owner, payout)` on the hub for the designation state,
`ReferralCorrectionProposed`, `ReferralCorrectionCancelled` and `ReferralCorrectionExecuted` on the registry for the
veto, and `ReferrerElevated` and `ReferrerElevationEnded` on the hub for elevation windows.

## Gotchas

- **The referrer is the address in the field, nothing else.** An integrator that wants to be the referrer of every
  deposit it sends writes its own address there, on every chain, in every deposit.
- **The first assignment wins everywhere.** A later deposit with another referrer succeeds as a deposit and the
  argument is ignored; show the recorded referrer, not the link's.
- **Spoke chain buckets need a designation.** Without one the bucket accrues but cannot be claimed; a contract
  wallet on a spoke chain must designate a mainnet address it controls.
- **The current week is never shipped.** Only closed weeks travel, and a week becomes claimable only after its
  envelope is applied at the hub.
- **A closed week keeps its verdict.** Rates can rise when more records arrive, never fall, and nothing already
  credited is clawed back.
- **Joining the exit queue ends the referrer's credit for the queued amount**, like a withdrawal would; leaving the
  queue unfilled restores nothing.

## Addresses

Same vault address on every chain listed. Everything is 6 decimals.

| Contract | Address | Chains |
|---|---|---|
| Vault `usdc` | `0x7e1EFF4301defc24936470B30bd1c686D2a295dc` | Ethereum, Base, Arbitrum |
| Vault `usdt` | `0x7e1EBE1D25367C6D3bC0aA72A1f00fC5320a05d7` | Ethereum, Base, Arbitrum |
| Vault `usdg` | `0x7E1e77EDE1d3b67ee46d031FC7De9e1379856064` | Ethereum, Arbitrum, Robinhood |
| Referral registry | `0x294713C98E20F2120261201B7B74079bba2E3617` | Ethereum (rank 0) |
| Referral registry | `0x15576bCE5a72566EbaeEBaB0D7b560Ef973C5767` | Base (rank 1) |
| Referral registry | `0x8d2C71eCF741B1A6ca1797Cf6E6B67aC9e234Ad3` | Arbitrum (rank 2) |
| Referral registry | `0xC97aCd3450e60962E1259e5cFd78Dc99d0D86753` | Robinhood (rank 3) |
| Referral hub | `0x68D207E22037d1B0764a509C16c08310C539ce94` | Ethereum |
| `ReferralHubReader` | `0xd0ec5Cc9A6F4d1289fAdbA648C165027cF57c125` | Ethereum |

The vault side referral functions become live on each vault once its selector round executes; until then
`getReferralRegistry()` reads the zero address and the referral entrypoints are not routed.
