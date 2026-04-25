# Contract Workspace

This directory contains the Soroban contract workspace for:

- `arena`
- `factory`
- `payout`
- `staking`

## TTL Policy Overview

Detailed storage and TTL documentation lives in `DATA_MODEL.md`. The short
version is:

| Contract | Persistent TTL approach | Instance TTL approach |
| --- | --- | --- |
| `arena` | Explicit bump on every persistent write | Host-managed |
| `factory` | No explicit bump | Host-managed |
| `payout` | Mixed: payout receipt families are bumped, history keys are not | Selective instance bump during payout execution paths |
| `staking` | No explicit bump | Host-managed |

Operationally, this means `arena` is the only contract that treats on-chain game
state as actively refreshed by default. `factory`, `payout`, and `staking`
should still be indexed and monitored with Soroban TTL limits in mind.

## Shared Upgrade Timelock Helper

The upgrade proposal / execute / cancel flow is centralized in
`shared/upgrade.rs` and reused by all four contracts. Each contract still owns
its own auth checks and error mapping, but event payloads and storage-key
handling now follow one shared path.

## ABI Snapshots

ABI snapshots live at:

- `arena/abi_snapshot.json`
- `factory/abi_snapshot.json`
- `payout/abi_snapshot.json`
- `staking/abi_snapshot.json`

To update snapshots after an intentional contract API change:

```bash
cd contract
./scripts/generate_abi_snapshots.sh
```

CI runs the same script with `--check` after building the WASM artifacts. If any
snapshot differs from the committed version, the check fails and the ABI change
must be reviewed and committed intentionally.

The script uses `stellar contract inspect --wasm ... --output xdr-base64-array`
when `stellar` is installed, or falls back to `soroban contract inspect`.
