# Payout Designation - UI Integration Guide

Let a referrer say which mainnet address its commission is paid to, per source chain. Covers the World Mobile
vaults `usdc`, `usdt` and `usdg` on Ethereum, Base, Arbitrum and Robinhood Chain.

`setPayoutAddress()`, `pushPayoutAddress()`, `quotePushPayoutFee()`, `getPayoutDesignation()`, `payoutAddressOf()`

## Core Concept

Commission accrues at the hub on Ethereum mainnet per source chain and referrer, and is always paid in USDC on
mainnet. The mainnet bucket pays the referrer's own address unless the referrer sets another on the hub. A Base,
Arbitrum or Robinhood bucket pays nothing until a designation made on that chain has reached the hub, because the
same address on mainnet may be undeployed or belong to someone else.

```
spoke chain:  registry.setPayoutAddress(payout)   ->  travels with the next flush of the book
              registry.pushPayoutAddress(owner)   ->  or at once, for the quoted CCIP fee
mainnet:      hub.setPayoutAddress(payout)        ->  redirects the mainnet bucket
hub:          payoutAddressOf(chainId, owner)     ->  the address a claim of that bucket pays
```

The newest designation wins at the hub. A designation of the zero address is valid and pays the referrer's own
address on mainnet.

## 1. See which buckets need a designation

```javascript
const reader = new web3.eth.Contract(READER_ABI, READER);          // mainnet
const CHAINS = [1, 8453, 42161, 4663];
const b = await reader.methods.claimablesOf(referrer, CHAINS).call();
const needsDesignation = CHAINS.filter((_, i) => b.amounts[i] !== '0' && b.payouts[i] === ZERO);
```

## 2. Designate on the spoke chain

```javascript
const registry = new web3.eth.Contract(REGISTRY_ABI, REGISTRY_OF_THAT_CHAIN);   // on Base, Arbitrum or Robinhood
await registry.methods.setPayoutAddress(mainnetPayout).send({ from: referrer });
```

The designation is recorded under the caller's address. It travels to the hub with the next flush of the
referrer's book on that chain.

## 3. Push it now

```javascript
const fee = await registry.methods.quotePushPayoutFee(referrer).call();
await registry.methods.pushPayoutAddress(referrer).send({ from: anyAddress, value: fee });
```

Anyone may push any owner's designation for the quoted CCIP fee; excess is refunded.

## 4. Redirect the mainnet bucket

```javascript
const hub = new web3.eth.Contract(HUB_ABI, HUB);   // mainnet
await hub.methods.setPayoutAddress(mainnetPayout).send({ from: referrer });
```

### Reads

| View | Chain | Returns |
|---|---|---|
| `getPayoutDesignation(address _owner)` | spoke registry | `(address payout, uint256 stamp)`, the stamp is `(setAt << 8) \| rank`. |
| `payoutAddressOf(uint256 _chainId, address _owner)` | hub | The address a claim of that bucket pays; zero means not claimable yet. |
| `payoutStamp(uint256 _chainId, address _owner)` | hub | The stamp the hub holds for that bucket; zero means none. |

## Preconditions

```javascript
const payoutHub = await registry.methods.payoutHub().call();   // must be nonzero before a push
```

A designation on the registry needs no precondition beyond a non vault caller; a push needs the registry's payout
route set and the fee.

## Errors

| Error | Cause |
|---|---|
| `InvalidPayoutOwner` | A vault address tried to designate. |
| `PayoutStampNotNewer` | A second designation in the same second; wait one block. |
| `NothingToPush` | No designation to push for that owner. |
| `InsufficientPushFee` | The value sent is below `quotePushPayoutFee`. |
| `PayoutHubNotSet` | The registry's payout route is not set. |
| `PushRefundFailed` | The excess fee could not be returned to the caller. |

## Events

```javascript
// on the spoke registry
registry.events.PayoutAddressSet({ filter: { owner: referrer } })
    .on('data', (e) => { const { payout, stamp } = e.returnValues; });
registry.events.PayoutPushed({ filter: { owner: referrer } })
    .on('data', (e) => { const { payout, stamp, messageId } = e.returnValues; });

// on the hub (mainnet): the designation landed for a bucket
hub.events.PayoutAddressSet({ filter: { owner: referrer } })
    .on('data', (e) => { const { chainId, payout } = e.returnValues; });
```

`DesignationPushReceived` and `FlushDesignationSkipped` on the hub show a push arriving or a stale designation
word being rejected; `PayoutBacklogReleased(chainId, owner, amount)` fires when a bucket becomes claimable and
its backlog joins the amount owed.

## Gotchas

- **A contract wallet on a spoke chain must designate.** Its address on mainnet may be nobody's, or someone
  else's. Designate a nonzero mainnet address it controls.
- **The newest designation wins.** A later stamp replaces an earlier one at the hub; two in the same second revert.
- **Offer the push button when a bucket shows a zero payout with a nonzero amount.** Otherwise the designation
  waits for the next flush of the book.
- **The zero address is a valid designation.** It pays the referrer's own address on mainnet.
- **The hub's own `setPayoutAddress` only moves the mainnet bucket.** Spoke buckets take their designation from
  their own chain.

## Addresses

| Contract | Address | Chain |
|---|---|---|
| Referral registry | `0x15576bCE5a72566EbaeEBaB0D7b560Ef973C5767` | Base (8453) |
| Referral registry | `0x8d2C71eCF741B1A6ca1797Cf6E6B67aC9e234Ad3` | Arbitrum (42161) |
| Referral registry | `0xC97aCd3450e60962E1259e5cFd78Dc99d0D86753` | Robinhood (4663) |
| Referral registry | `0x294713C98E20F2120261201B7B74079bba2E3617` | Ethereum (1) |
| Referral hub | `0x68D207E22037d1B0764a509C16c08310C539ce94` | Ethereum |
| `ReferralHubReader` | `0xd0ec5Cc9A6F4d1289fAdbA648C165027cF57c125` | Ethereum |

The hub pays USDC, 6 decimals.
