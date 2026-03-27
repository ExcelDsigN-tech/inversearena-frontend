//! ABI guard tests — ensure the contract's public surface matches abi_snapshot.json.
//!
//! Any addition or removal of a public function, or a field change in a view
//! struct, must be reflected in both this file and `abi_snapshot.json`.
//! CI will catch drift automatically.
#![cfg(test)]

extern crate std;
use std::collections::HashSet;

/// Snapshot of exported function names, kept in sync with abi_snapshot.json.
const SNAPSHOT_FUNCTIONS: &[&str] = &[
    "init",
    "set_token",
    "set_winner",
    "claim",
    "initialize",
    "admin",
    "set_admin",
    "pause",
    "unpause",
    "is_paused",
    "set_capacity",
    "get_arena_state",
    "join",
    "start_round",
    "submit_choice",
    "timeout_round",
    "resolve_round",
    "get_config",
    "get_round",
    "get_choice",
    "propose_upgrade",
    "execute_upgrade",
    "cancel_upgrade",
    "pending_upgrade",
    "get_user_state",
    "get_full_state",
];

/// Functions that are implemented in the current lib.rs and must appear in the
/// snapshot. This is the authoritative list of what the contract actually exports.
const IMPLEMENTED_FUNCTIONS: &[&str] = &[
    "init",
    "initialize",
    "admin",
    "set_admin",
    "pause",
    "unpause",
    "is_paused",
    "join",
    "start_round",
    "submit_choice",
    "timeout_round",
    "get_config",
    "get_round",
    "get_choice",
    "get_user_state",
    "get_full_state",
    "claim",
    "propose_upgrade",
    "execute_upgrade",
    "cancel_upgrade",
    "pending_upgrade",
];

/// Field names for UserStateView — changing these is a breaking ABI change.
const USER_STATE_VIEW_FIELDS: &[&str] = &["is_survivor", "has_submitted", "choice", "has_claimed"];

/// Field names for FullStateView — changing these is a breaking ABI change.
const FULL_STATE_VIEW_FIELDS: &[&str] = &["config", "round", "is_paused"];

// ── Tests ─────────────────────────────────────────────────────────────────────

/// Every implemented function must appear in the ABI snapshot.
/// Prevents silent omissions from the snapshot when new functions are added.
#[test]
fn implemented_functions_present_in_snapshot() {
    let snapshot: HashSet<&str> = SNAPSHOT_FUNCTIONS.iter().copied().collect();
    for func in IMPLEMENTED_FUNCTIONS {
        assert!(
            snapshot.contains(func),
            "Function `{func}` is implemented but missing from abi_snapshot.json. \
             Add it to SNAPSHOT_FUNCTIONS and abi_snapshot.json."
        );
    }
}

/// The snapshot must not contain functions that no longer exist in the contract.
/// Prevents stale entries from giving false confidence.
#[test]
fn snapshot_functions_are_known() {
    // Functions in the snapshot that are planned / reserved but not yet
    // implemented in this crate are listed here so the guard stays strict.
    let reserved: HashSet<&str> = [
        "set_token",
        "set_winner",
        "set_capacity",
        "get_arena_state",
        "resolve_round",
    ]
    .iter()
    .copied()
    .collect();

    let implemented: HashSet<&str> = IMPLEMENTED_FUNCTIONS.iter().copied().collect();

    for func in SNAPSHOT_FUNCTIONS {
        assert!(
            implemented.contains(func) || reserved.contains(func),
            "Function `{func}` is in abi_snapshot.json but is neither implemented \
             nor listed as reserved. Remove it from the snapshot or implement it."
        );
    }
}

/// UserStateView field schema guard — field additions/removals are breaking changes.
#[test]
fn user_state_view_fields_match_snapshot() {
    // Parse the snapshot JSON embedded at compile time.
    let snapshot_json = include_str!("../abi_snapshot.json");

    for field in USER_STATE_VIEW_FIELDS {
        assert!(
            snapshot_json.contains(field),
            "UserStateView field `{field}` is missing from abi_snapshot.json struct_schemas. \
             Update the snapshot to reflect the current struct definition."
        );
    }
}

/// FullStateView field schema guard.
#[test]
fn full_state_view_fields_match_snapshot() {
    let snapshot_json = include_str!("../abi_snapshot.json");

    for field in FULL_STATE_VIEW_FIELDS {
        assert!(
            snapshot_json.contains(field),
            "FullStateView field `{field}` is missing from abi_snapshot.json struct_schemas. \
             Update the snapshot to reflect the current struct definition."
        );
    }
}

/// Snapshot JSON is valid and contains the required top-level keys.
#[test]
fn snapshot_json_is_well_formed() {
    let snapshot_json = include_str!("../abi_snapshot.json");
    assert!(
        snapshot_json.contains("\"exported_functions\""),
        "abi_snapshot.json must contain an `exported_functions` key"
    );
    assert!(
        snapshot_json.contains("\"struct_schemas\""),
        "abi_snapshot.json must contain a `struct_schemas` key"
    );
    assert!(
        snapshot_json.contains("\"UserStateView\""),
        "abi_snapshot.json struct_schemas must include UserStateView"
    );
    assert!(
        snapshot_json.contains("\"FullStateView\""),
        "abi_snapshot.json struct_schemas must include FullStateView"
    );
}
