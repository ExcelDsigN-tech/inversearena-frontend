import re

with open('contract/payout/src/test.rs', 'r') as f:
    content = f.read()

# find a place to insert our tests. 
# let's just append to the end
test_str = """

#[test]
fn test_distribute_winnings_authorized() {
    let (env, admin, client, factory_id, factory_client, token_client, token_admin) = setup_with_token();
    let winner = Address::generate(&env);
    let ctx = symbol_short!("TEST");
    let pool_id = 1;
    let round_id = 1;
    let amount = 1000;
    let currency_sym = symbol_short!("USDC");

    // register token
    client.set_currency_token(&currency_sym, &token_client.address);
    // mint tokens to contract (so it has funds to pay out)
    token_admin.mint(&client.address, &100_000);

    let arena_contract = Address::generate(&env);
    // mock factory sets arena 
    env.as_contract(&factory_id, || {
        let r = ArenaRef {
            contract: arena_contract.clone(),
            status: ArenaStatus::Active,
            host: Address::generate(&env),
        };
        env.storage().instance().set(&(pool_id as u64), &r);
    });

    let balance_before = token_client.balance(&winner);
    // call from arena contract
    env.mock_auths(&[soroban_sdk::testutils::MockAuth {
        address: &arena_contract,
        invoke: &soroban_sdk::testutils::MockAuthInvoke {
            contract: &client.address,
            fn_name: "distribute_winnings",
            args: (arena_contract.clone(), ctx.clone(), pool_id, round_id, winner.clone(), amount, currency_sym.clone()).into_val(&env),
            sub_invokes: &[],
        },
    }]);

    client.distribute_winnings(&arena_contract, &ctx, &pool_id, &round_id, &winner, &amount, &currency_sym);

    let balance_after = token_client.balance(&winner);
    assert_eq!(balance_after, balance_before + amount);
}

#[test]
#[should_panic(expected = "1")]
fn test_distribute_winnings_unauthorized() {
    let (env, _, client, _, _, _, _) = setup_with_token();
    let caller = Address::generate(&env);
    let winner = Address::generate(&env);
    client.distribute_winnings(&caller, &symbol_short!("CTX"), &1, &1, &winner, &1000, &symbol_short!("DAI"));
}

#[test]
#[should_panic(expected = "2")]
fn test_distribute_winnings_zero_amount() {
    let (env, admin, client, factory_id, factory_client, token_client, token_admin) = setup_with_token();
    let winner = Address::generate(&env);
    let ctx = symbol_short!("TEST");
    let pool_id = 1;
    let round_id = 1;
    let amount = 0;
    let currency_sym = symbol_short!("USDC");

    let arena_contract = Address::generate(&env);
    env.as_contract(&factory_id, || {
        let r = ArenaRef {
            contract: arena_contract.clone(),
            status: ArenaStatus::Active,
            host: Address::generate(&env),
        };
        env.storage().instance().set(&(pool_id as u64), &r);
    });

    client.distribute_winnings(&arena_contract, &ctx, &pool_id, &round_id, &winner, &amount, &currency_sym);
}

#[test]
#[should_panic(expected = "3")]
fn test_distribute_winnings_double_payout() {
    let (env, admin, client, factory_id, factory_client, token_client, token_admin) = setup_with_token();
    let winner = Address::generate(&env);
    let ctx = symbol_short!("TEST");
    let pool_id = 1;
    let round_id = 1;
    let amount = 1000;
    let currency_sym = symbol_short!("USDC");

    let arena_contract = Address::generate(&env);
    env.as_contract(&factory_id, || {
        let r = ArenaRef {
            contract: arena_contract.clone(),
            status: ArenaStatus::Active,
            host: Address::generate(&env),
        };
        env.storage().instance().set(&(pool_id as u64), &r);
    });

    // first pay
    client.distribute_winnings(&arena_contract, &ctx, &pool_id, &round_id, &winner, &amount, &currency_sym);
    // double pay
    client.distribute_winnings(&arena_contract, &ctx, &pool_id, &round_id, &winner, &amount, &currency_sym);
}
"""

with open('contract/payout/src/test.rs', 'a') as f:
    f.write(test_str)

