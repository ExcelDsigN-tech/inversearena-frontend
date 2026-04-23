with open("arena/src/lib.rs", "r") as f:
    content = f.read()

bad_is_cancelled = r'''    pub fn is_cancelled(env: Env) -> bool {
        env.storage().instance().get::<_, bool>(&CANCELLED_KEY).unwrap_or(false)
    }'''

if bad_is_cancelled in content:
    content = content.replace(bad_is_cancelled, "", 1)

bad_leave = r'''    pub fn leave(env: Env, player: Address) -> Result<i128, ArenaError> {
        player.require_auth();
        require_not_paused(&env)?;
        let current_state = get_state(&env);
        assert_state!(current_state, ArenaState::Pending);

        let round = get_round(&env)?;
        if round.round_number != 0 {
            return Err(ArenaError::RoundAlreadyActive);
        }

        let survivor_key = DataKey::Survivor(player.clone());
        if !env.storage().persistent().has(&survivor_key) {
            return Err(ArenaError::NotASurvivor);
        }

        let config = get_config(&env)?;
        let refund = config.required_stake_amount;
        let token: Address = env.storage().instance().get(&TOKEN_KEY).ok_or(ArenaError::TokenNotSet)?;

        env.storage().persistent().remove(&survivor_key);
        let count: u32 = env.storage().instance().get(&SURVIVOR_COUNT_KEY).unwrap_or(0);
        env.storage().instance().set(&SURVIVOR_COUNT_KEY, &count.saturating_sub(1));
            
        let mut all_players: Vec<Address> = env.storage().persistent().get(&DataKey::AllPlayers).unwrap_or(Vec::new(&env));
        if let Some(i) = all_players.first_index_of(&player) {
            all_players.remove(i);
        }
        env.storage().persistent().set(&DataKey::AllPlayers, &all_players);
        bump(&env, &DataKey::AllPlayers);

        let pool: i128 = env.storage().instance().get(&PRIZE_POOL_KEY).unwrap_or(0);
        env.storage()
            .instance()
            .set(&PRIZE_POOL_KEY, &(pool + amount));
        Ok(())
    }'''
if bad_leave in content:
    content = content.replace(bad_leave, "", 1)

bad_max_rounds = r'''    pub fn set_max_rounds(env: Env, max_rounds: u32) -> Result<(), ArenaError> {
        let admin = Self::admin(env.clone());
        admin.require_auth();

        if max_rounds < bounds::MIN_MAX_ROUNDS || max_rounds > bounds::MAX_MAX_ROUNDS {
            return Err(ArenaError::InvalidMaxRounds);
        }

        let mut config = get_config(&env)?;
        config.max_rounds = max_rounds;
        env.storage().instance().set(&DataKey::Config, &config);
        Ok(())
    }'''

if bad_max_rounds in content:
    content = content.replace(bad_max_rounds, "", 1)

with open("arena/src/lib.rs", "w") as f:
    f.write(content)
