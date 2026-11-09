# Correction Veto - UI Integration Guide

Let a user refuse a change of referrer that the protocol operator proposed. Covers the World Mobile vaults `usdc`,
`usdt` and `usdg` on Ethereum, Base, Arbitrum and Robinhood Chain.

`cancelCorrectReferrer()`, `proposedCorrection()`, `correctionQueuedAt()`, `ReferralCorrectionProposed`

## Core Concept

A user's referrer can only be changed with the user's consent. The operator (master in the code) may propose a
different referrer with `proposeCorrectReferrer`, which opens a three day window. During the window the user can
cancel it unilaterally, and so can the operator. Only after the three days may the operator execute it. The same
lane attaches a referrer to a user who never named one.

```
ReferralCorrectionProposed(user, oldReferrer, newReferrer, queuedAt)   ->  show a cancel button until queuedAt + 3 days
cancelCorrectReferrer(user)                                            ->  the proposal is gone
ReferralCorrectionExecuted                                             ->  the change took effect, for the future only
```

A correction takes effect for the future only: everything already priced at the hub stays with the old referrer.

## 1. Listen for a proposal

```javascript
const registry = new web3.eth.Contract(REGISTRY_ABI, REGISTRY);   // the registry of the user's chain

registry.events.ReferralCorrectionProposed({ filter: { user: userAddress } })
    .on('data', (e) => {
        const { oldReferrer, newReferrer, queuedAt } = e.returnValues;
        const deadline = Number(queuedAt) + 3 * 24 * 3600;
        // show: "a change of referrer to newReferrer is proposed; you can cancel it until deadline"
    });
```

For a user who already has a referrer the proposal appears on the chain whose rank the user's key carries, which
is the chain of the user's earliest referral deposit or of the last correction. For a user without a referrer it
may appear on any chain.

## 2. Read a pending proposal

```javascript
const ZERO = '0x0000000000000000000000000000000000000000';
const [proposed, queuedAt] = await Promise.all([
    registry.methods.proposedCorrection(userAddress).call(),
    registry.methods.correctionQueuedAt(userAddress).call()
]);
const pending = proposed !== ZERO;
const secondsLeft = pending ? Number(queuedAt) + 3 * 24 * 3600 - Math.floor(Date.now() / 1000) : 0;
```

## 3. Cancel

```javascript
await registry.methods.cancelCorrectReferrer(userAddress).send({ from: userAddress });
```

### Parameters

| Parameter | Type | Meaning |
|---|---|---|
| `_user` | `address` | The user the proposal is open against. The caller must be that user or the operator. |

## Preconditions

```javascript
const latched = await registry.methods.correctionsLatched().call();   // true once the lane is closed for good on this chain
```

A proposal can only exist while the lane is open; once `correctionsLatched` reads true no new proposal can appear.

## Errors

| Error | Cause |
|---|---|
| `NoCorrectionProposed` | No proposal is open against the user. |
| `NotCorrectionParty` | The caller is neither the user nor the operator. |

## Events

```javascript
registry.events.ReferralCorrectionCancelled({ filter: { user: userAddress } })
    .on('data', (e) => { const { newReferrer, cancelledBy } = e.returnValues; });   // the user, the operator, or the registry itself

registry.events.ReferralCorrectionExecuted({ filter: { user: userAddress } })
    .on('data', (e) => { const { oldReferrer, newReferrer, syncKey } = e.returnValues; });   // zero oldReferrer: an assignment of a user who had none
```

`CorrectionsLatched()` fires once when the lane is closed on a chain.

## Gotchas

- **Three days, on chain time.** Compute the deadline from `queuedAt`, not from when the front end saw the event.
- **A referral deposit during the window kills the proposal.** The proposal is bound to the exact key the user held
  when it was made, so a new assignment drops it.
- **Watch the right chain.** The proposal for a user with a referrer is made on the chain of the user's key; read
  `getReferrerPair(user).rank` to know which registry to watch.
- **Nothing already paid changes.** Weeks priced under the old referrer stay with the old referrer.
- **The registry can cancel too.** A mutual pair resolved by the registry drops the proposal and emits
  `ReferralCorrectionCancelled` with the registry as `cancelledBy`.

## Addresses

| Contract | Address | Chain |
|---|---|---|
| Referral registry | `0x294713C98E20F2120261201B7B74079bba2E3617` | Ethereum (rank 0) |
| Referral registry | `0x15576bCE5a72566EbaeEBaB0D7b560Ef973C5767` | Base (rank 1) |
| Referral registry | `0x8d2C71eCF741B1A6ca1797Cf6E6B67aC9e234Ad3` | Arbitrum (rank 2) |
| Referral registry | `0xC97aCd3450e60962E1259e5cFd78Dc99d0D86753` | Robinhood (rank 3) |

Read the registry from the vault with `getReferralRegistry()` rather than hardcoding it.
