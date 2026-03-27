# Soroban Contract Data Model

This document describes the current on-chain data model for the Soroban workspace in `contract/`.

It is intended to make storage behavior explicit for:
- contract debugging
- off-chain indexer development
- future schema migrations
- contributor onboarding

## Scope

Contracts in this workspace:
- `arena`
- `factory`
- `payout`
- `staking`

## Workspace Summary

| Contract | Uses storage? | Storage key schema | TTL policy |
| --- | --- | --- | --- |
| `arena` | Yes | `DataKey` enum (persistent) + symbol keys (instance) | Explicit bump on every write |
| `factory` | Yes | Symbol keys (instance) | Instance-managed |
| `payout` | No | None | None |
| `staking` | No | None | None |

## Storage Key Inventory

### Arena Contract

File: `contract/arena/src/lib.rs`

#### Persistent storage (`env.storage().persistent()`)

| `DataKey` variant | Value type | Description |
| --- | --- | --- |
| `DataKey::Config` | `ArenaConfig` | Round speed configuration; written once on `init` |
| `DataKey::Round` | `RoundState` | Active round state (number, ledgers, submission count, flags) |
| `DataKey::Submission(round_number, player)` | `Choice` | A player's Heads/Tails choice for a given round |

#### Instance storage (`env.storage().instance()`)

| Symbol key | Value type | Description |
| --- | --- | --- |
| `ADMIN` | `Address` | Contract admin; set once via `initialize` |
| `P_HASH` | `BytesN<32>` | WASM hash pending upgrade via 48-hour timelock |
| `P_AFTER` | `u64` | Earliest timestamp at which `execute_upgrade` may be called |

### Factory Contract

File: `contract/factory/src/lib.rs`

Instance storage only:

| Symbol key | Value type | Description |
| --- | --- | --- |
| `ADMIN` | `Address` | Contract admin |
| `P_HASH` | `BytesN<32>` | WASM hash pending upgrade |
| `P_AFTER` | `u64` | Upgrade timelock timestamp |

### Payout and Staking Contracts

No custom Soroban storage keys are currently defined or used.

## Access Pattern Matrix

### Arena contract

| Function | Keys read | Keys written | TTL bumped |
| --- | --- | --- | --- |
| `init` | — | `Config`, `Round` | `Config`, `Round` |
| `start_round` | `Config`, `Round` | `Round` | `Round` |
| `submit_choice` | `Round`, `Submission(n, player)` | `Submission(n, player)`, `Round` | `Submission(n, player)`, `Round` |
| `timeout_round` | `Round` | `Round` | `Round` |
| `get_config` | `Config` | — | — |
| `get_round` | `Round` | — | — |
| `get_choice` | `Submission(n, player)` | — | — |
| `get_user_state` | `Round`, `Survivor(player)`, `Submission(n, player)`, `PrizeClaimed(player)` | — | — |
| `get_full_state` | `Config`, `Round`, `PAUSED` (instance) | — | — |
| `initialize` | `ADMIN` (instance) | `ADMIN` (instance) | — |
| `propose_upgrade` | `ADMIN` (instance) | `P_HASH`, `P_AFTER` (instance) | — |
| `execute_upgrade` | `ADMIN`, `P_AFTER`, `P_HASH` (instance) | removes `P_HASH`, `P_AFTER` (instance) | — |
| `cancel_upgrade` | `ADMIN`, `P_HASH` (instance) | removes `P_HASH`, `P_AFTER` (instance) | — |

## View Functions

These read-only functions expose aggregated contract state for frontend clients and indexers. They require no authorization and do not modify state.

### `get_user_state(player: Address) → Result<UserStateView, ArenaError>`

Returns a snapshot of a single player's participation status.

**Return type: `UserStateView`**

| Field | Type | Description |
| --- | --- | --- |
| `is_survivor` | `bool` | `true` if the player has a `Survivor` entry (has joined the arena) |
| `has_submitted` | `bool` | `true` if the player has submitted a choice for the current round |
| `choice` | `Choice` | The player's `Heads`/`Tails` submission (only meaningful when `has_submitted` is `true`) |
| `has_claimed` | `bool` | `true` if the player has already claimed their prize via `claim()` |

**Errors**: `ArenaError::NotInitialized` if `init` has not been called.

### `get_full_state() → Result<FullStateView, ArenaError>`

Returns a combined snapshot of the entire contract state in a single call, reducing the number of RPC round-trips needed by the frontend.

**Return type: `FullStateView`**

| Field | Type | Description |
| --- | --- | --- |
| `config` | `ArenaConfig` | Current round speed configuration (see `ArenaConfig`) |
| `round` | `RoundState` | Current round state (see `RoundState`) |
| `is_paused` | `bool` | Whether the contract is currently paused |

**Errors**: `ArenaError::NotInitialized` if `init` has not been called.

## TTL Policy Baseline

All **persistent** storage entries in the arena contract are explicitly extended on
every write. The policy constants are defined in `contract/arena/src/lib.rs`:

| Constant | Value (ledgers) | Approximate wall-clock duration |
| --- | --- | --- |
| `GAME_TTL_THRESHOLD` | 100,000 | ~5.8 days (at 5 s/ledger) |
| `GAME_TTL_EXTEND_TO` | 535,680 | ~31 days (at 5 s/ledger) |

**Rule**: A `bump(env, key)` helper calls `storage().persistent().extend_ttl(key,
GAME_TTL_THRESHOLD, GAME_TTL_EXTEND_TO)` immediately after every
`storage().persistent().set()`. This ensures the TTL is extended to at least
`GAME_TTL_EXTEND_TO` ledgers from the current ledger whenever it would fall below
`GAME_TTL_THRESHOLD`, covering the maximum possible game duration.

**Instance storage** (admin key, upgrade proposal keys) relies on the automatic
instance TTL managed by the Soroban host and is not explicitly bumped by game logic.

**Factory/payout/staking** contracts do not use persistent storage for game state.

## ER-Style State Diagram

```
ArenaConfig (1)
    │ round_speed_in_ledgers
    │
    └──────────────────────────────────────────────────┐
                                                       │ governs deadline
RoundState (1)                                         │
    │ round_number                                     │
    │ round_start_ledger ──────────────────────────────┘
    │ round_deadline_ledger
    │ active
    │ timed_out
    │ total_submissions
    │
    └─── has many ───► Submission(round_number, player_address)
                           │ Choice { Heads | Tails }
```

Round lifecycle state machine:

```
[not initialised]
    │ init()
    ▼
[Config set, Round { active: false }]
    │ start_round()
    ▼
[Round { active: true }]
    │ submit_choice()  (multiple callers, within deadline)
    │ timeout_round()  (any caller, after deadline)
    ▼
[Round { active: false, timed_out: true }]
    │ start_round()
    ▼
[Round { active: true, round_number + 1 }] ...
```

## Historical baseline note

Prior to the implementation of game state storage and TTL management, the accurate
storage model for this workspace was:

> No custom Soroban storage keys are currently defined or used.
