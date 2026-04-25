# Soroban Contract Data Model

This document describes the storage layout and TTL policy for the contracts in
`contract/`.

It is intended to answer two questions quickly:

1. Which keys does each contract persist on-chain?
2. How long do those keys stay durable without operator intervention?

## Scope

Contracts in this workspace:

- `arena`
- `factory`
- `payout`
- `staking`

## Workspace Summary

| Contract | Storage model | Persistent TTL policy | Instance TTL policy |
| --- | --- | --- | --- |
| `arena` | Persistent `DataKey` entries plus symbol-based instance config | Explicitly bumped on every persistent write to a 31-day target | Host-managed instance TTL; no manual bump |
| `factory` | Persistent `DataKey` records plus symbol-based instance config | No explicit bump; entries rely on Soroban's normal persistent TTL lifecycle | Host-managed instance TTL; no manual bump |
| `payout` | Mixed persistent receipt data plus instance config and idempotency guards | `Payout(...)` and `SplitPayout(...)` are explicitly bumped; `PayoutHistory(...)` and `ArenaPayout(...)` are not | `execute_payout` and `distribute_split_payout` extend instance TTL to the same 31-day target |
| `staking` | Persistent per-staker/per-host records plus symbol-based instance config | No explicit bump; entries rely on Soroban's normal persistent TTL lifecycle | Host-managed instance TTL; no manual bump |

## Arena

Primary source: `contract/arena/src/lib.rs`

### Storage layout

Persistent keys:

- `Config`: arena configuration, including round speed, stake amount, join deadline, and yield-share settings
- `Round`: current round state
- `Submission(round, player)`: player choice for a round
- `Survivor(player)`: membership marker for joined players
- `Eliminated(player)`: elimination marker
- `PrizeClaimed(winner)`: prize-claim guard
- `Metadata(arena_id)`, `Refunded(player)`, and other game-state entries in the same `DataKey` enum

Instance keys:

- `ADMIN`, `TOKEN`, `CAPACITY`, `POOL`, `YIELD`, `WY_BPS`, `S_COUNT`
- `P_HASH`, `P_AFTER` for upgrade timelock
- `P_ADMIN`, `A_EXP` for admin transfer
- `PAUSED`, `STATE`, `WINNER`, `FACTORY`, `CREATOR`, vault-related keys

### TTL policy

| Storage class | Keys | Explicit bump? | Policy |
| --- | --- | --- | --- |
| Persistent | All arena `DataKey` entries written through the game flow | Yes | `bump(env, key)` calls `persistent().extend_ttl(key, 100_000, 535_680)` after every persistent write |
| Instance | Admin/config/governance symbols | No | Relies on Soroban instance TTL management |

### Rationale

Arena state can remain live for days while rounds advance or while a winner delays
claiming. The contract therefore actively extends persistent TTL on write so the
game state stays durable without requiring an operator to manually restore it.

## Factory

Primary source: `contract/factory/src/lib.rs`

### Storage layout

Persistent keys:

- `SupportedToken(address)`: allowed pool currencies
- `Pool(pool_id)`: immutable arena metadata snapshot
- `ArenaRef(arena_id)`: address, status, and host for cursor-based discovery
- `ArenaWhitelist(arena_id, address)`: allowlist entries for private arenas

Instance keys:

- `ADMIN`, `P_ADMIN`, `A_EXP`
- `P_HASH`, `P_AFTER` for upgrade timelock
- `MIN_STK`, `AR_WASM`, `P_CNT`, `S_VER`, `PAUSED`
- `TOK_CNT`, `MAX_PLR`, `STAKING`, `HST_MIN`
- `FEE_BPS`, `P_FEE`, `F_AFTER`
- `CR_FEE`, `CR_TOK`, `CR_ACC`, `WIN_ACC`

### TTL policy

| Storage class | Keys | Explicit bump? | Policy |
| --- | --- | --- | --- |
| Persistent | `SupportedToken`, `Pool`, `ArenaRef`, `ArenaWhitelist` | No | All entries rely on Soroban's default persistent TTL behavior |
| Instance | Governance/config counters and fee settings | No | Relies on Soroban instance TTL management |

### Rationale

Factory state is mostly registry/config data rather than rapidly mutating
round-by-round state. Operators should treat factory persistent entries as
durable only while their Soroban TTL remains active, because the contract does
not currently refresh those keys on writes or reads.

## Payout

Primary source: `contract/payout/src/lib.rs`

### Storage layout

Persistent keys:

- `Payout(ctx, pool_id, round_id, winner)`: idempotent payout receipts
- `SplitPayout(arena_id, winner)`: per-winner split payout receipts
- `PayoutHistory(index)`: append-only payout history
- `ArenaPayout(arena_id)`: latest payout receipt keyed by arena

Instance keys:

- `ADMIN`, `P_ADMIN`, `A_EXP`, `TREAS`, `FACTORY`, `PAUSED`
- `P_HASH`, `P_AFTER` for upgrade timelock
- `P_COUNT`: payout-history cursor
- `CurrencyToken(symbol)`: symbol-to-token-address registry
- `PrizePayout(game_id)`, `SplitPayoutBatch(arena_id)`: idempotency guards

### TTL policy

| Storage class | Keys | Explicit bump? | Policy |
| --- | --- | --- | --- |
| Persistent | `Payout(...)`, `SplitPayout(...)` | Yes | Extended with `persistent().extend_ttl(key, 100_000, 535_680)` when written |
| Persistent | `PayoutHistory(...)`, `ArenaPayout(...)` | No | Written without a follow-up TTL extension |
| Instance | Whole contract instance during payout execution paths | Yes, selectively | `execute_payout` and `distribute_split_payout` call `instance().extend_ttl(100_000, 535_680)` |
| Instance | Governance/config/idempotency keys outside those flows | No direct per-key bump | Relies on the contract instance still being alive |

### Rationale

Payout keeps the receipt families that are queried most often alive explicitly,
but its history index and arena lookup records are only as durable as their base
persistent TTL. If long-term payout history matters operationally, index it
off-chain instead of assuming the on-chain history keys will live forever.

## Staking

Primary source: `contract/staking/src/lib.rs`

### Storage layout

Persistent keys:

- `Stake(address)` and `Position(address)`: staker balances and share positions
- `HostLock(host, arena_id)` and `HostLockedTotal(host)`: host collateral locks
- `RewardDebt(address)`, `PendingRewards(address)`, `StakedAt(address)`
- `TotalClaimedRewards(address)`

Instance keys:

- `ADMIN`, `P_ADMIN`, `A_EXP`, `PAUSED`
- `TOKEN`, `FACTRY`, `TSTAKE`, `TSHARES`
- `P_HASH`, `P_AFTER` for upgrade timelock
- `LOCK_SEC`, `MIN_STK`, `MAX_STK`
- `RWD_EN`, `RWD_PSH`, `RWD_POOL`, `RWD_UNA`

### TTL policy

| Storage class | Keys | Explicit bump? | Policy |
| --- | --- | --- | --- |
| Persistent | All staking `DataKey` entries | No | Relies on Soroban's default persistent TTL behavior |
| Instance | Config, totals, reward settings, governance state | No | Relies on Soroban instance TTL management |

### Rationale

Staking stores long-lived balances and reward accounting, but today it does not
refresh TTL explicitly. Operators should plan around Soroban TTL restoration for
staking state if positions are expected to remain untouched for long periods.

## Shared Upgrade Timelock Flow

The four contracts now share the same reusable helper module in
`contract/shared/upgrade.rs`.

Common flow:

1. `propose_upgrade(new_hash)` stores `P_HASH` and `P_AFTER`, then emits
   `UP_PROP`.
2. `execute_upgrade(expected_hash)` checks the stored proposal, clears it,
   emits `UP_EXEC`, and then upgrades the current contract WASM.
3. `cancel_upgrade()` clears the pending proposal and emits `UP_CANC`.
4. `pending_upgrade()` returns `(hash, execute_after)` only when both keys are
   present.

Factory keeps its additional malformed-state guard; arena keeps its stricter
"strictly after" execution boundary to preserve existing behavior.
