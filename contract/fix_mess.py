import subprocess

def fix():
    subprocess.run(["git", "checkout", "arena/src/lib.rs"])
    subprocess.run(["git", "checkout", "factory/src/lib.rs"])
    
    with open("arena/src/lib.rs", "r") as f:
        arena = f.read()
    
    # 1. Dup constants
    arena = arena.replace("const TIMELOCK_PERIOD: u64 = 48 * 60 * 60; // 48 hours\n\nconst GAME_TTL_THRESHOLD: u32 = 17280; // 1 day\nconst GAME_TTL_EXTEND_TO: u32 = 120960; // 7 days", "")
    
    # 2. Dup FullStateView
    full_sv = """#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FullStateView {
    pub survivors_count: u32,
    pub max_capacity: u32,
    pub round_number: u32,
    pub current_stake: i128,
    pub potential_payout: i128,
    pub is_active: bool,
    pub has_won: bool,
}"""
    if arena.count(full_sv) > 1:
        arena = arena.replace(full_sv, "", 1)
        
    # 3. NotWhitelisted
    if "NotWhitelisted = 47" not in arena:
        arena = arena.replace("InvalidGracePeriod = 46,\n}", "InvalidGracePeriod = 46,\n    NotWhitelisted = 47,\n}")
        
    # 4. is_private
    if "pub is_private: bool," not in arena:
        arena = arena.replace("pub win_fee_bps: u32,\n}", "pub win_fee_bps: u32,\n    pub is_private: bool,\n}")
        
    # 5. DataKey Enum Items
    # Need to be very precise
    key_rep = "enum DataKey {\n    Config,\n    ArenaId,\n    FactoryAddress,"
    if "ArenaId" not in arena:
        arena = arena.replace("enum DataKey {\n    Config,", key_rep)
        
    # 6. IntoVal
    if "use soroban_sdk::{IntoVal" not in arena and "use soroban_sdk::IntoVal;" not in arena:
        arena = arena.replace("use soroban_sdk::{", "use soroban_sdk::{IntoVal, ")
        
    # 7. is_cancelled / leave / set_max_rounds
    # remove the FIRST occurrence block of each duplicate method
    def remove_method(start_sig):
        nonlocal arena
        if arena.count(start_sig) > 1:
            idx1 = arena.find(start_sig)
            # Find the end of this method which is before the next pub fn
            idx2 = arena.find("pub fn ", idx1 + 10)
            if idx2 != -1:
                # also include the space before the pub fn
                last_brace = arena.rfind("}\n", idx1, idx2)
                if last_brace != -1:
                    arena = arena[:idx1] + arena[last_brace+2:]
            
    remove_method("pub fn is_cancelled(env: Env) -> bool {")
    remove_method("pub fn leave(env: Env, player: Address) -> Result<i128, ArenaError> {")
    remove_method("pub fn set_max_rounds(env: Env, max_rounds: u32) -> Result<(), ArenaError> {")
    
    # Also fix some minor bugs in arena:
    arena = arena.replace("get_state(&env)", "state(&env)")
    arena = arena.replace("set_state(&env, ArenaState::Cancelled);", "env.storage().instance().set(&STATE_KEY, &ArenaState::Cancelled);")
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
fix()
