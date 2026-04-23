import re

with open("arena/src/lib.rs", "r") as f:
    arena = f.read()

# 1. Remove Duplicate Constants
dup_consts = """const TIMELOCK_PERIOD: u64 = 48 * 60 * 60; // 48 hours

const GAME_TTL_THRESHOLD: u32 = 17280; // 1 day
const GAME_TTL_EXTEND_TO: u32 = 120960; // 7 days"""
arena = arena.replace(dup_consts, "")

# 1.1 Remove double empty lines left behind optionally (not strictly necessary)

# 2. Remove second FullStateView
# we find all indices of `pub struct FullStateView`
fsv_start = arena.find("pub struct FullStateView")
if fsv_start != -1:
    fsv_second = arena.find("pub struct FullStateView", fsv_start + 10)
    if fsv_second != -1:
        # find the preceding #[contracttype] for it
        start_to_remove = arena.rfind("#[contracttype]", 0, fsv_second)
        # find the end of the struct '}
        end_to_remove = arena.find("}", fsv_second) + 1
        arena = arena[:start_to_remove] + arena[end_to_remove:]

# 3. Add NotWhitelisted
if "NotWhitelisted = 47," not in arena:
    arena = arena.replace("InvalidGracePeriod = 46,", "InvalidGracePeriod = 46,\n    NotWhitelisted = 47,")

# 4. Add is_private
if "pub is_private: bool," not in arena:
    arena = arena.replace("pub win_fee_bps: u32,", "pub win_fee_bps: u32,\n    pub is_private: bool,")

# 5. Missing Enum Variants in DataKey
# specifically replace 'enum DataKey {\n    Config,'
# with 'enum DataKey {\n    Config,\n    ArenaId,\n    FactoryAddress,'
if "ArenaId," not in arena:
    arena = re.sub(r'enum DataKey \{\n\s*Config,', 'enum DataKey {\n    Config,\n    ArenaId,\n    FactoryAddress,', arena)

# 6. IntoVal import
if "use soroban_sdk::{IntoVal," not in arena and "use soroban_sdk::IntoVal;" not in arena:
    arena = arena.replace("use soroban_sdk::{", "use soroban_sdk::{IntoVal, ")

# 7. get_state -> state
arena = arena.replace("get_state(&env)", "state(&env)")

# 8. set_state -> STATE_KEY set
arena = arena.replace("set_state(&env, ArenaState::Cancelled);", "env.storage().instance().set(&STATE_KEY, &ArenaState::Cancelled);")

# 9. let arena_id: u64
arena = arena.replace("let arena_id = env.storage().instance().get(&DataKey::ArenaId).unwrap_or(0);", 
                      "let arena_id: u64 = env.storage().instance().get(&DataKey::ArenaId).unwrap_or(0);")

# 10. Remove duplicate methods in ArenaContract
# is_cancelled
bad_is_cancelled = r'''    pub fn is_cancelled(env: Env) -> bool {
        env.storage().instance().get::<_, bool>(&CANCELLED_KEY).unwrap_or(false)
    }'''
if arena.count("pub fn is_cancelled") > 1:
    arena = arena.replace(bad_is_cancelled, "", 1)

# leave
bad_leave = r'''    pub fn leave(env: Env, player: Address) -> Result<i128, ArenaError> {
        player.require_auth();
        require_not_paused(&env)?;
        let current_state = state(&env);
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
if arena.count("pub fn leave") > 1:
    # note: get_state(&env) became state(&env) on line 42, so updated bad_leave
    # to find it perfectly we might just use regex to strip it
    pass

# let's just do an aggressive string search block stripping:
def strip_block(start, text, count_check):
    if text.count(start) > 1:
        idx = text.find(start)
        # we know it goes until the end of the method: `    }\n` or `    }\n\n`
        # assuming next method starts with `    pub fn`
        next_fn = text.find("    pub fn", idx + 10)
        return text[:idx] + text[next_fn:]
    return text

arena = strip_block("    pub fn leave(env: Env, player: Address) -> Result<i128, ArenaError> {", arena, True)
arena = strip_block("    pub fn set_max_rounds(env: Env, max_rounds: u32) -> Result<(), ArenaError> {", arena, True)

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
