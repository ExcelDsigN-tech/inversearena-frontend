import re
import subprocess

subprocess.run(["git", "checkout", "arena/src/lib.rs"])
subprocess.run(["git", "checkout", "factory/src/lib.rs"])

with open("arena/src/lib.rs", "r") as f:
    arena = f.read()

# 1. Constants
arena = re.sub(r'const TIMELOCK_PERIOD: u64 = 48 \* 60 \* 60; // 48 hours\n', '', arena)
arena = re.sub(r'const GAME_TTL_THRESHOLD: u32 = 17280; // 1 day\n', '', arena)
arena = re.sub(r'const GAME_TTL_EXTEND_TO: u32 = 120960; // 7 days\n', '', arena)

# 2. Duplicate FullStateView
if arena.count("pub struct FullStateView") > 1:
    fsv_idx1 = arena.find("pub struct FullStateView")
    fsv_idx2 = arena.find("pub struct FullStateView", fsv_idx1 + 10)
    start_cut = arena.rfind("#[contracttype]", 0, fsv_idx2)
    end_cut = arena.find("}", fsv_idx2) + 1
    arena = arena[:start_cut] + arena[end_cut:]

# 3. NotWhitelisted
if "NotWhitelisted" not in arena:
    arena = arena.replace("InvalidGracePeriod = 46,\n}", "InvalidGracePeriod = 46,\n    NotWhitelisted = 47,\n}")

# 4. is_private
if "pub is_private: bool" not in arena:
    arena = arena.replace("pub win_fee_bps: u32,\n}", "pub win_fee_bps: u32,\n    pub is_private: bool,\n}")

# 5. DataKey variations
key_enum = r"""enum DataKey {
    Config,
    Round,
"""
key_enum_new = r"""enum DataKey {
    Config,
    ArenaId,
    FactoryAddress,
    Round,
"""
if "ArenaId," not in arena:
    arena = arena.replace(key_enum, key_enum_new)

# 6. IntoVal
if "IntoVal" not in arena:
    arena = arena.replace("use soroban_sdk::{", "use soroban_sdk::{IntoVal, ")

# Duplicate Methods (exact line by line removal)
# is_cancelled
is_canc = """    pub fn is_cancelled(env: Env) -> bool {
        env.storage().instance().get::<_, bool>(&CANCELLED_KEY).unwrap_or(false)
    }"""
if arena.count(is_canc) > 0:
    arena = arena.replace(is_canc, "", 1)

# leave #1
leave1 = """    pub fn leave(env: Env, player: Address) -> Result<i128, ArenaError> {
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
    }"""
if arena.count("pub fn leave(env: Env, player: Address) -> Result<i128, ArenaError> {") > 0:
    arena = arena.replace(leave1, "")

# set_max_rounds #1
smr1 = """    pub fn set_max_rounds(env: Env, max_rounds: u32) -> Result<(), ArenaError> {
        let admin = Self::admin(env.clone());
        admin.require_auth();

        if max_rounds < bounds::MIN_MAX_ROUNDS || max_rounds > bounds::MAX_MAX_ROUNDS {
            return Err(ArenaError::InvalidMaxRounds);
        }

        let mut config = get_config(&env)?;
        config.max_rounds = max_rounds;
        env.storage().instance().set(&DataKey::Config, &config);
        Ok(())
    }"""
if arena.count("pub fn set_max_rounds") > 1:
    arena = arena.replace(smr1, "", 1)


arena = arena.replace("let arena_id = env.storage().instance().get(&DataKey::ArenaId).unwrap_or(0);", "let arena_id: u64 = env.storage().instance().get(&DataKey::ArenaId).unwrap_or(0);")

with open("arena/src/lib.rs", "w") as f:
    f.write(arena)

with open("factory/src/lib.rs", "r") as f:
    factory = f.read()

hm = "    /// The hash provided to `execute_upgrade` does not match the stored proposal hash.\n    HashMismatch = 17,"
if factory.count("HashMismatch = 17") > 1:
    factory = factory.replace(hm, "", 1)

if "TOPIC_ARENA_WL_ADD" not in factory:
    ins = 'const TOPIC_FEE_CANCELLED: Symbol = symbol_short!("FEE_CAN");\nconst TOPIC_ARENA_WL_ADD: Symbol = symbol_short!("AWL_ADD");\nconst TOPIC_ARENA_WL_REM: Symbol = symbol_short!("AWL_REM");'
    factory = factory.replace('const TOPIC_FEE_CANCELLED: Symbol = symbol_short!("FEE_CAN");', ins)

with open("factory/src/lib.rs", "w") as f:
    f.write(factory)

