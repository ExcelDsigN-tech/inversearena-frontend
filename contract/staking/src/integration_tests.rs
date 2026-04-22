#![cfg(test)]

extern crate std;

use super::*;
use soroban_sdk::{
    testutils::Address as _,
    token::{self, StellarAssetClient},
    Address, Env,
};

fn setup() -> (
    Env,
    Address,
    Address,
    Address,
    StakingContractClient<'static>,
    token::TokenClient<'static>,
) {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let staker1 = Address::generate(&env);
    let staker2 = Address::generate(&env);

    let asset = env.register_stellar_asset_contract_v2(admin.clone());
    let token_address = asset.address();
    let token_admin = StellarAssetClient::new(&env, &token_address);
    token_admin.mint(&staker1, &1_000_000_000i128);
    token_admin.mint(&staker2, &1_000_000_000i128);

    let contract_id = env.register(StakingContract, ());
    let client = StakingContractClient::new(&env, &contract_id);
    client.initialize(&admin, &token_address);

    let env_static: &'static Env = unsafe { &*(&env as *const Env) };
    (
        env,
        admin,
        staker1,
        staker2,
        StakingContractClient::new(env_static, &contract_id),
        token::TokenClient::new(env_static, &token_address),
    )
}

#[test]
fn integration_initializes_and_tracks_admin() {
    let (_env, admin, _staker1, _staker2, client, _token_client) = setup();

    assert_eq!(client.admin(), admin);
    assert!(!client.is_paused());
}

#[test]
fn integration_multiple_stakers_keep_independent_balances() {
    let (_env, _admin, staker1, staker2, client, token_client) = setup();
    let contract_address = client.address.clone();

    let stake1 = 250_000_000i128;
    let stake2 = 100_000_000i128;

    client.stake(&staker1, &stake1);
    client.stake(&staker2, &stake2);

    assert_eq!(client.staked_balance(&staker1), stake1);
    assert_eq!(client.staked_balance(&staker2), stake2);
    assert_eq!(token_client.balance(&contract_address), stake1 + stake2);
}

#[test]
fn integration_partial_unstake_only_affects_one_staker() {
    let (_env, _admin, staker1, staker2, client, token_client) = setup();

    client.stake(&staker1, &300_000_000i128);
    client.stake(&staker2, &200_000_000i128);

    let staker2_before = token_client.balance(&staker2);
    let returned = client.unstake(&staker1, &125_000_000i128);

    assert_eq!(returned, 125_000_000i128);
    assert_eq!(client.staked_balance(&staker1), 175_000_000i128);
    assert_eq!(client.staked_balance(&staker2), 200_000_000i128);
    assert_eq!(token_client.balance(&staker2), staker2_before);
}
