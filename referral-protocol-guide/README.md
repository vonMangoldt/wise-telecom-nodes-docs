# Referral Protocol Guide

Earn on the deposits you bring to the Wise Telecom Nodes vaults.

The Wise Telecom Nodes vaults pay their depositors a fixed interest rate. The referral system adds a second income on top: when you bring a depositor to a vault, you earn a commission on that depositor's principal for as long as it stays, paid in USDC on Ethereum mainnet and priced week by week against a published rate table. Nothing is taken from the depositor; the commission is paid by the protocol.

This guide is cut by the question you bring to it. Depositors, referrers, integrators, front end developers, protocol developers and reviewers each have their own chapter, and a thing is explained in one place and linked from the others.

## What the Referral System Is

The system adds three parts to the running vault diamonds.

**A registry per chain.** The registry records which referrer a depositor named, once, and keeps every chain in agreement about it. Every vault on a chain reads and writes the same registry, the registries exchange their records over Chainlink CCIP, and the earliest assignment wins everywhere. A consent gated correction lane lets the operator propose a different referrer, which the user can veto for three days.

**Cohort facets on every vault.** New facets on each vault diamond record, week by week, how much referred stake and how much own stake each referrer had present in that vault, in token seconds and by age. They ship those weekly records to the hub as flush envelopes, over CCIP from Base, Arbitrum and Robinhood and by direct call on mainnet. Nothing already deployed is edited; the facets are added through the vaults' three day timelocks.

**A hub on Ethereum mainnet.** The hub receives the weekly records from every vault on every chain, sums them per referrer and week, prices each closed week against the rate table in force for that week and credits a claimable bucket per source chain and referrer. It is its own pot, funded by plain USDC transfers from the protocol, and pays claims from it.

> Every number in this guide is read from the code. Where a figure is a genesis value that we can later change through a timelocked lever, the guide says so.

## Weeks and Years

**A week** is the Unix timestamp divided by one week, so every week starts at the same instant on every chain, and a week is closed once that instant has passed. Every quantity in the system is counted in whole weeks: the records a vault writes, the cursors a flush advances, the envelopes the hub receives, the rate tables and the elevation windows.

**A year** is 52 weeks, 364 days. Referred credit ages in a ring of 52 weekly slots from year one into year two and then into mature credit, and every rate in the rate table is a rate per 52 week year. Read against a calendar year of 365.25 days a stated rate pays about 0.34 percent more; the referrer chapter explains why in [The 52 Week Year](for-referrers.md#the-52-week-year).

**A source** is one vault on one chain as the hub sees it. The hub keys everything it receives by source, because the same vault product has the same address on every chain it runs on.

## Several Vault Systems Under One Referral Umbrella

The referral system is one umbrella over several **vault systems**. The nine World Mobile vaults are system 0. The Sovren vault, product `wsnusdc` on Ethereum mainnet, a USDC vault whose deposits finance Sovren infrastructure nodes, is system 1. Later node systems built on the same code can join as further systems. Every system runs under the same settings: one rate table, one cap, one ladder, one courier share and one payout pot at the hub.

A referrer's ladder inputs sum over every vault of every system, so 500,000 referred in a World Mobile vault plus 500,000 in the Sovren vault counts as 1,000,000 on the ladder. The hub tags every source vault with its system number for reporting only; pricing never reads the tag. **Money never moves between systems:** no move peer and no bridge peer is ever registered between a Sovren vault and a World Mobile vault, on any chain.

The Sovren vault joins the referral system alongside the World Mobile rollout, through its own upgrade rounds and the registry's allow lane. Its referral facets are the same code under the Sovren contract names, built and rehearsed in its own repository, so a referrer sees one behaviour in every system; the fourteen facets of its registry round are routed since 2026-10-28 and its flush round since 2026-11-02, listed in [Addresses](addresses.md#ethereum-mainnet-chain-id-1); its registry pointer is wired, its recorder armed and the hub accepts it as a reporter since 2026-11-02, so it measures from that day. Its record is allowlisted on the mainnet registry since 2026-10-25, its flush hub pointer is wired since 2026-11-05 and its books ship to the hub since that day, so the join is complete. Adding a system is an operator procedure, a configuration record, the registry allow lane and the hub source tag, never a redeploy of anything shared.

## The Sovren Vault

The Sovren vault is Wise Sovren Nodes, a USDC vault on Ethereum mainnet whose deposits finance Sovren infrastructure nodes. Its share token is `wsnUSDC`, its diamond address is listed in [Addresses](addresses.md#ethereum-mainnet-chain-id-1), it runs on mainnet only, and it is built on the same vault code as the World Mobile vaults with its own exit queue incentive ladder. Its source is public at [wise-sovren-nodes-v1](https://github.com/vonMangoldt/wise-sovren-nodes-v1).

For a depositor nothing differs. The referral deposit entrypoints, the write once referrer, the three day correction veto and the queue rules of [For Depositors](for-depositors.md) are the same functions on the Sovren diamond, and the referrer named there is recorded in the mainnet registry that the three World Mobile mainnet vaults share. For a referrer the Sovren vault is one more source: its weekly records reach the hub by direct call in the flush transaction itself, because the vault and the hub share a chain, and the commission lands in the mainnet bucket beside the World Mobile mainnet commission. The ladder sums Sovren stake with every other stake, as the section above describes, and the Sovren queue treats a join exactly as a World Mobile queue does. Shares never move or bridge between the Sovren vault and a World Mobile vault.

The join runs in the same order as a World Mobile vault's rollout. The mainnet registry admits the vault through its three day allow lane, the hub tags its source as system 1, the Sovren diamond routes the registry round and then the flush round through its own three day selector timelock, and the hub grants it the reporter role through the lever timelock. The referral facets are the same code under the Sovren contract names, built and rehearsed in the Sovren repository; the two queue facets additionally carry the Sovren incentive ladder and let a standing order leave a lane that was closed to new joins. Their addresses are added to [Addresses](addresses.md) as each round lands.

## How to Read This Guide

* **[For Depositors](for-depositors.md):** naming a referrer, the referral link, what changes for you, and what the exit queue does to your referrer's commission.
* **[For Referrers](for-referrers.md):** the tiers and rates with worked examples, elevated status, how weeks are priced, flushing, claiming, the payout designation per chain, and what to expect.
* **[For Integrators and Partners](for-integrators.md):** the functions reference, the elevated referrer address rule, the admin functions and what the upgrade changes, and the pre audit notes.
* **[UI Integration](ui-integration.md):** the ten vault UI guides with their links, the referral UI guide, every view and event in reference tables, and which views for which screen.
* **[Architecture for Developers](architecture.md):** components, the data flow from a deposit to a claim, registry keys and the merge rule, flush cursors and work caps, hub buckets, timelocks and levers, storage rules and events.
* **[Safety and Known Findings](safety-and-known-findings.md):** the trust model and timelocks first, then every accepted review finding grouped by the question a reader would ask.
* **[Addresses](addresses.md):** the vault diamonds, USD tokens and CCIP routers per chain, the four live registries, the hub with its facets and the reader, all from the configuration and broadcast records, and the vault facet rows that fill once the selector rounds execute.
* **[Frequently Asked Questions](faq.md):** short answers for depositors, referrers, integrators and reviewers, each linked to the chapter that explains it in full.

### Conclusion

The vaults measure what was present, the hub prices it at the rate of the week and pays you in USDC, and the registry makes sure the referrer is one fact across every chain. Start with the chapter written for you; every other chapter is one link away where it matters.
