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
    StakingContractClient<'static>,
    token::TokenClient<'static>,
) {
    let env = Env::default();
    env.mock_all_auths();

    let admin = Address::generate(&env);
    let staker = Address::generate(&env);

    let asset = env.register_stellar_asset_contract_v2(admin.clone());
    let token_address = asset.address();
    let token_admin = StellarAssetClient::new(&env, &token_address);
    token_admin.mint(&staker, &1_000_000_000i128);

    let contract_id = env.register(StakingContract, ());
    let client = StakingContractClient::new(&env, &contract_id);
    client.initialize(&admin, &token_address);

    let env_static: &'static Env = unsafe { &*(&env as *const Env) };
    (
        env,
        admin,
        staker,
        StakingContractClient::new(env_static, &contract_id),
        token::TokenClient::new(env_static, &token_address),
    )
}

#[test]
fn hello_returns_liveness_value() {
    let env = Env::default();
    let contract_id = env.register(StakingContract, ());
    let client = StakingContractClient::new(&env, &contract_id);

    assert_eq!(client.hello(), 101112);
}

#[test]
fn initialize_sets_admin_and_unpaused() {
    let (_env, admin, _staker, client, _token_client) = setup();

    assert_eq!(client.admin(), admin);
    assert!(!client.is_paused());
}

#[test]
fn stake_transfers_tokens_and_updates_balance() {
    let (_env, _admin, staker, client, token_client) = setup();
    let contract_address = client.address.clone();

    let staker_before = token_client.balance(&staker);
    let contract_before = token_client.balance(&contract_address);

    let minted = client.stake(&staker, &250_000_000i128);

    assert_eq!(minted, 250_000_000i128);
    assert_eq!(client.staked_balance(&staker), 250_000_000i128);
    assert_eq!(token_client.balance(&staker), staker_before - 250_000_000i128);
    assert_eq!(
        token_client.balance(&contract_address),
        contract_before + 250_000_000i128
    );
}

#[test]
fn stake_rejects_non_positive_amounts() {
    let (_env, _admin, staker, client, _token_client) = setup();

    assert_eq!(
        client.try_stake(&staker, &0i128),
        Err(Ok(StakingError::InvalidAmount))
    );
    assert_eq!(
        client.try_stake(&staker, &-1i128),
        Err(Ok(StakingError::InvalidAmount))
    );
}

#[test]
fn unstake_returns_tokens_and_reduces_balance() {
    let (_env, _admin, staker, client, token_client) = setup();

    let balance_before = token_client.balance(&staker);
    client.stake(&staker, &400_000_000i128);

    let returned = client.unstake(&staker, &150_000_000i128);

    assert_eq!(returned, 150_000_000i128);
    assert_eq!(client.staked_balance(&staker), 250_000_000i128);
    assert_eq!(token_client.balance(&staker), balance_before - 250_000_000i128);
}

#[test]
fn unstake_rejects_invalid_or_excessive_amounts() {
    let (_env, _admin, staker, client, _token_client) = setup();

    client.stake(&staker, &100_000_000i128);

    assert_eq!(
        client.try_unstake(&staker, &0i128),
        Err(Ok(StakingError::InvalidAmount))
    );
    assert_eq!(
        client.try_unstake(&staker, &101_000_000i128),
        Err(Ok(StakingError::InsufficientStake))
    );
}

#[test]
fn pause_blocks_stake_and_unstake_until_unpaused() {
    let (_env, _admin, staker, client, _token_client) = setup();

    client.stake(&staker, &200_000_000i128);
    client.pause();

    assert!(client.is_paused());
    assert_eq!(
        client.try_stake(&staker, &10i128),
        Err(Ok(StakingError::Paused))
    );
    assert_eq!(
        client.try_unstake(&staker, &10i128),
        Err(Ok(StakingError::Paused))
    );

    client.unpause();

    assert!(!client.is_paused());
    assert_eq!(client.unstake(&staker, &50i128), 50i128);
    assert_eq!(client.staked_balance(&staker), 199_999_950i128);
}
