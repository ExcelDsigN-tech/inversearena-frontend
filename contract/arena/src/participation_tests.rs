#![cfg(test)]
//! Integration tests for player participation rate limiting.
//!
//! Tests verify that the factory correctly enforces per-address participation limits,
//! preventing sybil attacks where one player fills multiple arena slots.

extern crate std;
use std::vec::Vec;

use crate::ArenaContractClient;
use soroban_sdk::{
    Address, Env,
    testutils::{Address as _, Ledger as _, LedgerInfo},
    token::StellarAssetClient,
};

const TEST_REQUIRED_STAKE: i128 = 100i128;

/// Helper: Create a test environment with mock auth
fn make_env() -> Env {
    let env = Env::default();
    env.mock_all_auths();
    let ledger = env.ledger().get();
    env.ledger().set(LedgerInfo {
        timestamp: 1_700_000_000,
        protocol_version: 22,
        sequence_number: ledger.sequence_number,
        network_id: ledger.network_id,
        base_reserve: ledger.base_reserve,
        min_temp_entry_ttl: u32::MAX / 4,
        min_persistent_entry_ttl: u32::MAX / 4,
        max_entry_ttl: u32::MAX / 4,
    });
    env
}

/// Helper: Register and initialize arena contract
fn setup_arena(env: &Env) -> (ArenaContractClient<'_>, Address) {
    let contract_id = env.register(crate::ArenaContract, ());
    let client = ArenaContractClient::new(env, &contract_id);
    let admin = Address::generate(env);
    client.initialize(&admin);
    (client, admin)
}

/// Helper: Create token and configure arena
fn configure_arena(
    env: &Env,
    client: &ArenaContractClient<'_>,
    admin: &Address,
    round_speed: u32,
) -> Address {
    let token_id = env
        .register_stellar_asset_contract_v2(admin.clone())
        .address();
    let _asset = StellarAssetClient::new(env, &token_id);
    
    client.set_token(&token_id);
    client.init(&round_speed, &TEST_REQUIRED_STAKE);
    
    token_id
}

/// Helper: Create multiple arenas for testing
fn create_multiple_arenas(env: &Env, count: u32) -> Vec<(ArenaContractClient<'_>, Address, Address)> {
    let mut arenas = Vec::new();
    let admin = Address::generate(env);
    
    for _ in 0..count {
        let (client, _) = setup_arena(env);
        let token_id = configure_arena(env, &client, &admin, 5);
        let contract_id = client.contract_id.clone();
        arenas.push((client, contract_id, token_id));
    }
    
    arenas
}

/// Test 1: Player can join 3 arenas successfully (default limit)
#[test]
fn test_join_3_arenas_success() {
    let env = make_env();
    let arenas = create_multiple_arenas(&env, 3);
    let player = Address::generate(&env);
    
    // Mint tokens for the player across all arenas
    let total_stake = TEST_REQUIRED_STAKE * 3;
    let _asset = StellarAssetClient::new(&env, &arenas[0].2);
    _asset.mint(&player, &total_stake);
    
    // Join arena 1
    arenas[0].0.join(&player, &TEST_REQUIRED_STAKE);
    
    // Join arena 2
    arenas[1].0.join(&player, &TEST_REQUIRED_STAKE);
    
    // Join arena 3 - should succeed
    arenas[2].0.join(&player, &TEST_REQUIRED_STAKE);
    
    // Verify player is in all 3 arenas (would need get_survivor or similar)
    // For now, the test passes if no error was thrown during joins
}

/// Test 2: Player cannot join 4th arena (exceeds default limit of 3)
#[test]
#[should_panic(expected = "ParticipationLimitReached")]
fn test_4th_arena_join_fails() {
    let env = make_env();
    let arenas = create_multiple_arenas(&env, 4);
    let player = Address::generate(&env);
    
    // Mint tokens for the player
    let total_stake = TEST_REQUIRED_STAKE * 4;
    let _asset = StellarAssetClient::new(&env, &arenas[0].2);
    _asset.mint(&player, &total_stake);
    
    // Join arenas 1, 2, 3
    for i in 0..3 {
        arenas[i].0.join(&player, &TEST_REQUIRED_STAKE);
    }
    
    // Attempt to join 4th arena - should panic with ParticipationLimitReached
    arenas[3].0.join(&player, &TEST_REQUIRED_STAKE);
}

/// Test 3: Multiple players have independent participation limits
#[test]
fn test_multiple_players_independent_limits() {
    let env = make_env();
    let arenas = create_multiple_arenas(&env, 4);
    
    let player_a = Address::generate(&env);
    let player_b = Address::generate(&env);
    
    // Mint tokens for both players
    let total_stake = TEST_REQUIRED_STAKE * 4;
    let _asset = StellarAssetClient::new(&env, &arenas[0].2);
    _asset.mint(&player_a, &total_stake);
    _asset.mint(&player_b, &total_stake);
    
    // Player A joins arenas 0, 1, 2 (hits limit)
    for i in 0..3 {
        arenas[i].0.join(&player_a, &TEST_REQUIRED_STAKE);
    }
    
    // Player B joins arenas 0, 1, 2 (hits limit) - should succeed independently
    for i in 0..3 {
        arenas[i].0.join(&player_b, &TEST_REQUIRED_STAKE);
    }
    
    // Both players trying to join arena 3:
    // Player A should fail
    let result_a = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        arenas[3].0.join(&player_a, &TEST_REQUIRED_STAKE);
    }));
    assert!(result_a.is_err(), "Player A should not be able to join 4th arena");
    
    // Player B should also fail (independent limit)
    let result_b = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        arenas[3].0.join(&player_b, &TEST_REQUIRED_STAKE);
    }));
    assert!(result_b.is_err(), "Player B should not be able to join 4th arena");
}

/// Test 4: Counter is properly incremented (verify via multiple joins)
#[test]
fn test_participation_counter_increment() {
    let env = make_env();
    let arenas = create_multiple_arenas(&env, 5);
    let player = Address::generate(&env);
    
    // Mint sufficient tokens
    let total_stake = TEST_REQUIRED_STAKE * 5;
    let _asset = StellarAssetClient::new(&env, &arenas[0].2);
    _asset.mint(&player, &total_stake);
    
    // Join arenas one by one
    for i in 0..3 {
        arenas[i].0.join(&player, &TEST_REQUIRED_STAKE);
        // After each join, counter should be incremented
        // (Verification would need accessor function)
    }
    
    // 4th join should fail
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        arenas[3].0.join(&player, &TEST_REQUIRED_STAKE);
    }));
    assert!(result.is_err(), "4th join should fail due to limit");
}

/// Test 5: Participation counter is decremented after game completion
/// (This test would require completing a full game cycle, which is complex.
///  For now, it serves as a placeholder for full lifecycle testing.)
#[test]
fn test_participation_counter_decrement_after_game() {
    // TODO: Implement full game lifecycle test that:
    // 1. Creates an arena and factory
    // 2. Player joins 3 arenas
    // 3. Completes a game in one arena (winner claims prize)
    // 4. Verifies participation count decreased
    // 5. Player can now join a 4th arena
    
    // This requires:
    // - Factory contract deployment and integration
    // - Full game simulation (rounds, submissions, resolution)
    // - Access to factory state or event inspection
}
