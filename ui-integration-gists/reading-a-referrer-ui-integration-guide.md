# Reading a User's Referrer - UI Integration Guide

Show a user who their referrer is, since when, and which chain recorded it. Covers the World Mobile vaults `usdc`,
`usdt` and `usdg` on Ethereum, Base, Arbitrum and Robinhood Chain.

`getReferrerOf()`, `referrerOf()`, `getReferrerPair()`, `effectiveReferrerOf()`, `pendingFlip()`

## Core Concept

A user's referrer is one fact across the whole mesh. Each chain's registry records the pair with a key made of the
time of the assignment and the rank of the chain that made it, the registries exchange these keys over CCIP, and
when two registries disagree the lower key wins, which means the earlier assignment wins. The vault reads the
registry through its pointer; the registry answers for every vault on the chain.

```
vault.getReferrerOf(user)         ->  the referrer, zero while unset
registry.getReferrerPair(user)    ->  referrer, assignedAt, rank
registry.effectiveReferrerOf(u,v) ->  the referrer a given vault still credits during a pending flip
```

Chain ranks: Ethereum 0, Base 1, Arbitrum 2, Robinhood 3.

## 1. The quick read

```javascript
const ZERO = '0x0000000000000000000000000000000000000000';
const vault = new web3.eth.Contract(VAULT_ABI, vaultAddress);

const referrer = await vault.methods.getReferrerOf(userAddress).call();
const hasReferrer = referrer !== ZERO;
```

`getReferrerOf` returns zero while no referrer is set and while the vault's registry pointer is unset.

## 2. The full pair

```javascript
const registry = new web3.eth.Contract(REGISTRY_ABI, await vault.methods.getReferralRegistry().call());
const { referrer, assignedAt, rank } = await registry.methods.getReferrerPair(userAddress).call();

const RANKS = { 0: 'Ethereum', 1: 'Base', 2: 'Arbitrum', 3: 'Robinhood' };
const byCorrection = Number(assignedAt) < 1_700_000_000;
const since = byCorrection ? 3_399_999_999 - Number(assignedAt) : Number(assignedAt);
// "referrer since <since> as recorded on <RANKS[rank]>", with "set by a correction" when byCorrection
```

An `assignedAt` below 1,700,000,000 marks a pair written by the correction lane; decode it as 3,399,999,999 minus
the value. The raw packed key is `referrerKey(user)`, which is `(assignedAt << 8) | rank`.

## 3. A pending flip

When an earlier assignment arrives from another chain, the registry switches the user to it and marks each vault
where the user holds stake for relocation from the old referrer's book to the new one. Until a vault has migrated,
it still credits the old referrer.

```javascript
const effective = await registry.methods.effectiveReferrerOf(userAddress, vaultAddress).call();
const oldReferrer = await registry.methods.pendingFlip(vaultAddress, userAddress).call();
const flipPending = oldReferrer !== ZERO;
// show "credit moving from oldReferrer to referrer" while flipPending
```

### Returns

| View | Returns |
|---|---|
| `getReferrerOf(address _user)` | `address`, zero while unset. |
| `referrerOf(address _user)` | `address`, the registry's own answer. |
| `getReferrerPair(address _user)` | `(address referrer, uint256 assignedAt, uint256 rank)`. |
| `referrerKey(address _user)` | `uint256`, the packed key. |
| `effectiveReferrerOf(address _user, address _vault)` | `address`, equals `referrerOf` once the flip is delivered. |
| `pendingFlip(address _vault, address _user)` | `address`, the old referrer not yet migrated away from, zero when none. |

## Preconditions

Reads only; nothing to gate. `getReferrerOf` on the vault needs the registry pointer set (`getReferralRegistry()`
nonzero), which is the case once the vault's selector round has executed; the registry views answer regardless.

## Errors

The views do not revert. A zero answer means unset, never an error.

## Events

```javascript
// the first assignment
registry.events.ReferralAssigned({ filter: { user: userAddress } })
    .on('data', (e) => { const { referrer, vault } = e.returnValues; });

// an earlier assignment from another chain replaced the local one
registry.events.ReferralSyncFlipped({ filter: { user: userAddress } })
    .on('data', (e) => { const { oldReferrer, newReferrer, syncKey } = e.returnValues; });

// the same referrer with an earlier key arrived; the since when moved earlier
registry.events.ReferralSyncKeyLowered({ filter: { user: userAddress } })
    .on('data', (e) => { const { oldKey, newKey } = e.returnValues; });
```

`FlipMarked`, `FlipMigrated`, `FlipCleared` and `FlipMigrationDeferred` on the registry follow a flip through each
vault.

## Gotchas

- **One referrer per user, not per chain.** Read any chain's registry and you get the same answer once the
  registries have synced; a difference between chains is a sync in flight, not two referrers.
- **The earlier assignment wins.** A user who named A on Base on Monday and B on Arbitrum on Tuesday ends up with
  A everywhere once the Base pair reaches Arbitrum.
- **Decode the correction encoding.** A small `assignedAt` is not a 1970 timestamp.
- **Show `effectiveReferrerOf` on a per vault screen.** During a flip the vault's book still belongs to the old
  referrer until the migration lands.
- **Read, do not wait for events.** A repeat deposit emits no `ReferralAssigned`.

## Addresses

| Contract | Address | Chains |
|---|---|---|
| Vault `usdc` | `0x7e1EFF4301defc24936470B30bd1c686D2a295dc` | Ethereum, Base, Arbitrum |
| Vault `usdt` | `0x7e1EBE1D25367C6D3bC0aA72A1f00fC5320a05d7` | Ethereum, Base, Arbitrum |
| Vault `usdg` | `0x7E1e77EDE1d3b67ee46d031FC7De9e1379856064` | Ethereum, Arbitrum, Robinhood |
| Referral registry | `0x294713C98E20F2120261201B7B74079bba2E3617` | Ethereum (rank 0) |
| Referral registry | `0x15576bCE5a72566EbaeEBaB0D7b560Ef973C5767` | Base (rank 1) |
| Referral registry | `0x8d2C71eCF741B1A6ca1797Cf6E6B67aC9e234Ad3` | Arbitrum (rank 2) |
| Referral registry | `0xC97aCd3450e60962E1259e5cFd78Dc99d0D86753` | Robinhood (rank 3) |

Read the registry from the vault with `getReferralRegistry()` rather than hardcoding it.
