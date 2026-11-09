# Claiming Commission - UI Integration Guide

Pay a referrer its accrued commission from the hub, per source chain, in USDC on Ethereum mainnet. Covers the
World Mobile vaults `usdc`, `usdt` and `usdg` on Ethereum, Base, Arbitrum and Robinhood Chain.

`claim()`, `claimUpTo()`, `claimAll()`, `claimable()`, `payoutAddressOf()`

## Core Concept

Commission accrues at the hub in USDC into a claimable bucket per source chain and referrer: what was earned on
Base is a different bucket from what was earned on mainnet. The hub is its own pot, funded by plain USDC transfers
from the protocol, and pays claims from it. A claim may be sent by the referrer or by the bucket's payout address
and always pays the payout address.

```
claimable(chainId, referrer)        ->  the bucket
USD_TOKEN().balanceOf(hub)          ->  the cover the pot holds today
claimAll(referrer, chainIds)        ->  pays every listed bucket that can pay, in list order
```

All calls go to the hub on Ethereum mainnet. Chain ids: Ethereum 1, Base 8453, Arbitrum 42161, Robinhood Chain 4663.

## 1. Read the buckets and the cover

```javascript
const hub = new web3.eth.Contract(HUB_ABI, HUB);                               // mainnet
const usdc = new web3.eth.Contract(ERC20_ABI, await hub.methods.USD_TOKEN().call());
const CHAINS = [1, 8453, 42161, 4663];

const [amounts, payouts, cover] = await Promise.all([
    Promise.all(CHAINS.map((c) => hub.methods.claimable(c, referrer).call())),
    Promise.all(CHAINS.map((c) => hub.methods.payoutAddressOf(c, referrer).call())),
    usdc.methods.balanceOf(HUB).call()
]);
const claimableChains = CHAINS.filter((_, i) => amounts[i] !== '0' && payouts[i] !== ZERO);
```

The reader's `claimablesOf(referrer, chainIds)` returns the same amounts and payout addresses in one call, with
`total` and `claimableNow`.

## 2. Claim everything that can pay

```javascript
await hub.methods.claimAll(referrer, claimableChains).send({ from: referrer });
```

`claimAll` pays every listed bucket that can pay, each up to the cover left after the buckets before it, and
reverts only when it paid nothing at all.

## 3. Claim one bucket

```javascript
await hub.methods.claim(8453, referrer).send({ from: referrer });                 // full bucket, reverts if the pot is short
await hub.methods.claimUpTo(8453, referrer, amount).send({ from: referrer });     // up to amount and up to the cover
```

### Parameters

| Parameter | Type | Meaning |
|---|---|---|
| `_chainId` | `uint256` | The source chain of the bucket. |
| `_referrer` | `address` | The bucket's owner. |
| `_amount` | `uint256` | `claimUpTo` only: the most to pay, in USDC base units. |
| `_chainIds` | `uint256[]` | `claimAll` only: the buckets to pay, in the order to pay them. |

### Returns

`claimAll` returns the total paid. `claim` and `claimUpTo` return nothing.

## Preconditions

```javascript
const canClaim = (i) => amounts[i] !== '0' && payouts[i] !== ZERO && BigInt(cover) > 0n;
const isParty = [referrer, ...payouts].some((a) => a.toLowerCase() === callerAddress.toLowerCase());
```

A spoke chain bucket needs a payout designation from that chain at the hub before it can pay; see the Payout
Designation guide.

## Errors

| Error | Cause |
|---|---|
| `PotDry` | `claim` asked for more than the pot holds; use `claimUpTo` or `claimAll`. |
| `NothingClaimable` | `claimAll` paid nothing, or the bucket is empty. |
| `NotPayoutAuthorized` | The caller is neither the referrer nor the bucket's payout address. |
| `PayoutNotDesignated` | A spoke chain bucket has no designation at the hub yet. |

## Events

```javascript
hub.events.PayoutClaimed({ filter: { referrer } })
    .on('data', (e) => { const { chainId, payout, amount } = e.returnValues; });
```

For the protocol view read `totalAccrued()`, `totalClaimed()` and `totalPayable()`: `totalPayable - totalClaimed`
is what the pot should hold.

## Gotchas

- **Nothing is lost when the pot is short.** `claim` reverts, `claimUpTo` and `claimAll` pay what is covered and the
  remainder stays claimable until the pot is topped up.
- **The USDC goes to the payout address, never to the caller.** A payout address may send the claim itself.
- **List order matters in `claimAll`.** Each bucket takes from the cover left after the ones before it.
- **A closed week keeps its verdict.** Nothing already credited is clawed back, not even after a correction of the
  referrer.
- **Courier shares live in the same buckets.** A flush bot claims its share with the same calls, keyed by its own
  address.

## Addresses

| Contract | Address | Chain |
|---|---|---|
| Referral hub | `0x68D207E22037d1B0764a509C16c08310C539ce94` | Ethereum |
| `ReferralHubReader` | `0xd0ec5Cc9A6F4d1289fAdbA648C165027cF57c125` | Ethereum |
| USDC (the pot's token) | `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` | Ethereum |

Read the pot's token from the hub with `USD_TOKEN()` rather than hardcoding it. 6 decimals.
