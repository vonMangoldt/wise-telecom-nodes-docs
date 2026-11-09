# Referral Deposits - UI Integration Guide

Let a depositor name a referrer with a deposit. The referrer is written once into the chain's referral registry and
earns a weekly commission on the depositor's principal from then on. Covers the World Mobile vaults `usdc`, `usdt`
and `usdg` on Ethereum, Base, Arbitrum and Robinhood Chain.

`depositWithReferral()`, `depositAndClaimInterestWithReferral()`, `depositAndCompoundInterestWithReferral()` and their three Permit2 twins

## Core Concept

A referrer is identified by one thing only: the address written into the referrer field of a deposit. That exact
address is what the chain's registry records for the depositor and what the hub prices, so a referral link carries
nothing but that address and your front end writes it into the deposit call it sends.

```
referral link  ->  referrer address  ->  depositWithReferral(amount, referrer)
                                         registry records (depositor, referrer) once
                                         the deposit runs as a plain deposit
```

The assignment is written once. The first referrer a depositor names is recorded in the chain's registry and shared
by every vault on that chain, and the registries of all chains exchange their records so the earliest assignment
wins everywhere. A later deposit that names a different referrer is accepted as a deposit and the referrer argument
is ignored. Nothing is taken from the depositor; the commission is paid by the protocol.

## The Six Functions

| Function | What it does after recording the referrer |
|---|---|
| `depositWithReferral` | Nothing. Plain deposit. |
| `depositAndClaimInterestWithReferral` | Pays out the user's whole interest balance in stablecoin. |
| `depositAndCompoundInterestWithReferral` | Converts the user's whole interest balance into vault tokens. |
| `depositWithPermit2WithReferral` | Plain deposit, token pulled through Permit2 with a signature. |
| `depositAndClaimInterestWithPermit2WithReferral` | As above plus the interest payout. |
| `depositAndCompoundInterestWithPermit2WithReferral` | As above plus the compound. |

```solidity
depositWithReferral(uint256 _amount, address _referrer)
depositAndClaimInterestWithReferral(uint256 _amount, address _referrer) returns (uint256)
depositAndCompoundInterestWithReferral(uint256 _amount, address _referrer) returns (uint256)
depositWithPermit2WithReferral(uint256 _amount, uint256 _nonce, uint256 _deadline, bytes _signature, address _referrer)
depositAndClaimInterestWithPermit2WithReferral(uint256 _amount, uint256 _nonce, uint256 _deadline, bytes _signature, address _referrer) returns (uint256)
depositAndCompoundInterestWithPermit2WithReferral(uint256 _amount, uint256 _nonce, uint256 _deadline, bytes _signature, address _referrer) returns (uint256)
```

Each is the plain deposit variant with the referrer assignment run first. The Permit2 variants take the four
permit arguments of the Permit2 Deposits guide and the referrer last.

## 1. Read the recorded referrer first

A depositor who already has a referrer is kept on it, so show the recorded referrer instead of the link's address
when they differ.

```javascript
const ZERO = '0x0000000000000000000000000000000000000000';
const vault = new web3.eth.Contract(VAULT_ABI, vaultAddress);

const recorded = await vault.methods.getReferrerOf(userAddress).call();
const referrer = recorded !== ZERO ? recorded : referrerFromLink;
const linkIgnored = recorded !== ZERO && recorded.toLowerCase() !== referrerFromLink.toLowerCase();
```

## 2. Validate the referrer before sending

The call reverts on a zero referrer, on the depositor's own address, and on an address the registry refuses: a
vault, the registry, the hub, or an address whose own referral chain leads back to the depositor. Check the cheap
cases in the front end.

```javascript
const registry = new web3.eth.Contract(REGISTRY_ABI, await vault.methods.getReferralRegistry().call());

const selfReferral = referrer.toLowerCase() === userAddress.toLowerCase();
const isVault = VAULTS.some((v) => v.toLowerCase() === referrer.toLowerCase());
const referrersReferrer = await registry.methods.referrerOf(referrer).call();
const loop = referrersReferrer.toLowerCase() === userAddress.toLowerCase();

const canName = referrer !== ZERO && !selfReferral && !isVault && !loop;
```

## 3. Deposit

```javascript
await usd.methods.approve(vaultAddress, amount).send({ from: userAddress });
await vault.methods.depositWithReferral(amount, referrer).send({ from: userAddress });
```

### Parameters

| Parameter | Type | Meaning |
|---|---|---|
| `_amount` | `uint256` | Deposit size in the underlying's base units. 6 decimals. |
| `_referrer` | `address` | The referrer to record. Ignored when the depositor already has one. |

## Preconditions

```javascript
const [registryAddress, paused, depositsDisabled, totalSupply, cap] = await Promise.all([
    vault.methods.getReferralRegistry().call(),
    vault.methods.paused().call(),
    vault.methods.depositsDisabled().call(),
    vault.methods.totalSupply().call(),
    vault.methods.totalDepositCap().call()
]);

const hasRoom = BigInt(totalSupply) + BigInt(amount) <= BigInt(cap);
const canDeposit = registryAddress !== ZERO && !paused && !depositsDisabled && hasRoom;
```

The referral entrypoints need the vault's registry pointer set; until a vault's selector round has executed the
pointer reads zero and the entrypoints are not routed. The combined variants add the grace period check of the
Permit2 Deposits guide.

## Errors

| Error | Cause |
|---|---|
| `InvalidValue` | The referrer is the zero address. |
| `SelfReferral` | The referrer is the depositor itself. |
| `ReferralRegistryNotSet` | The vault's registry pointer is not set yet. |
| `InvalidReferrer` | The registry refused the referrer: a vault, the registry, the hub, or a referral chain that leads back to the depositor. |
| `NotAllowedVault` | The vault is not on the registry's allowlist; it never is for a live vault, a sign of a wrong address. |

Plus the plain deposit errors: `DepositsDisabled`, `DepositExceedCap`, `Pausable: paused`, and for the combined
variants `GracePeriodNotElapsed` and `NoInterest`.

## Events

```javascript
// the assignment, on the registry of the user's chain; only the first referral deposit emits it
registry.events.ReferralAssigned({ filter: { user: userAddress } })
    .on('data', (e) => { const { user, referrer, vault } = e.returnValues; });

// the stake credited to the referrer's book, on the vault
vault.events.CohortContributionCredited({ filter: { user: userAddress } })
    .on('data', (e) => { const { referrer, amount } = e.returnValues; });
```

You will also see the plain deposit events, `Deposited` and the ERC20 `Transfer(0x0, user, amount)`.

## Gotchas

- **The referrer is the address in the field, nothing else.** An integrator that wants to be the referrer of every
  deposit it sends writes its own address there, on every chain, in every deposit.
- **The first assignment wins everywhere.** A later deposit with another referrer succeeds as a deposit and the
  argument is ignored; show the recorded referrer, not the link's.
- **No `ReferralAssigned` on a repeat deposit.** Only the first referral deposit of a user emits it; a dashboard
  reads `referrerOf` rather than waiting for the event.
- **A referral deposit during a pending correction kills the proposal.** The proposal is bound to the exact key the
  user held when it was made.
- **The plain deposit gates still apply.** `depositsDisabled()` and the cap cover the referral entrypoints too.

## Addresses

Same vault address on every chain listed. Everything is 6 decimals.

| Contract | Address | Chains |
|---|---|---|
| Vault `usdc` | `0x7e1EFF4301defc24936470B30bd1c686D2a295dc` | Ethereum, Base, Arbitrum |
| Vault `usdt` | `0x7e1EBE1D25367C6D3bC0aA72A1f00fC5320a05d7` | Ethereum, Base, Arbitrum |
| Vault `usdg` | `0x7E1e77EDE1d3b67ee46d031FC7De9e1379856064` | Ethereum, Arbitrum, Robinhood |
| Referral registry | `0x294713C98E20F2120261201B7B74079bba2E3617` | Ethereum |
| Referral registry | `0x15576bCE5a72566EbaeEBaB0D7b560Ef973C5767` | Base |
| Referral registry | `0x8d2C71eCF741B1A6ca1797Cf6E6B67aC9e234Ad3` | Arbitrum |
| Referral registry | `0xC97aCd3450e60962E1259e5cFd78Dc99d0D86753` | Robinhood |

Read the registry from the vault with `getReferralRegistry()` rather than hardcoding it.
