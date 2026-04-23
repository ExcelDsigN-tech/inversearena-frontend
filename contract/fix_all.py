import re

with open("arena/src/lib.rs", "r") as f:
    arena = f.read()

# 1. Remove duplicate constants (TIMELOCK_PERIOD, GAME_TTL_...)
arena = re.sub(r'const TIMELOCK_PERIOD: u64 = 48 \* 60 \* 60; // 48 hours\n', '', arena)
arena = re.sub(r'const GAME_TTL_THRESHOLD: u32 = 17280; // 1 day\n', '', arena)
arena = re.sub(r'const GAME_TTL_EXTEND_TO: u32 = 120960; // 7 days\n', '', arena)

# 2. Add NotWhitelisted
if "NotWhitelisted =" not in arena:
    arena = arena.replace("InvalidGracePeriod = 46,\n}", "InvalidGracePeriod = 46,\n    NotWhitelisted = 47,\n}")

# 3. Add is_private to ArenaConfig
if "pub is_private: bool" not in arena:
    arena = arena.replace("pub win_fee_bps: u32,\n}", "pub win_fee_bps: u32,\n    pub is_private: bool,\n}")

# 4. ArenaId and FactoryAddress in DataKey
if "ArenaId," not in arena:
    arena = arena.replace("Config,", "Config,\n    ArenaId,\n    FactoryAddress,")

# 5. Fix IntoVal trait
if "use soroban_sdk::{IntoVal," not in arena and "use soroban_sdk::IntoVal;" not in arena:
    arena = arena.replace("use soroban_sdk::{", "use soroban_sdk::{IntoVal, ")

# 6. Fix `get_state` -> `state`
arena = arena.replace("get_state(&env)", "state(&env)")

# 7. Fix `set_state`
arena = arena.replace("set_state(&env, ArenaState::Cancelled);", "env.storage().instance().set(&STATE_KEY, &ArenaState::Cancelled);")

# 8. Fix int type for arena_id 
arena = arena.replace("let arena_id = env.storage().instance().get(&DataKey::ArenaId).unwrap_or(0);", "let arena_id: u64 = env.storage().instance().get(&DataKey::ArenaId).unwrap_or(0);")

with open("arena/src/lib.rs", "w") as f:
    f.write(arena)

with open("factory/src/lib.rs", "r") as f:
    factory = f.read()

# Add Missing Topics
if "TOPIC_ARENA_WL_ADD" not in factory:
    factory = factory.replace("const TOPIC_FEE_CANCELLED: Symbol = symbol_short!(\"FEE_CAN\");", "const TOPIC_FEE_CANCELLED: Symbol = symbol_short!(\"FEE_CAN\");\nconst TOPIC_ARENA_WL_ADD: Symbol = symbol_short!(\"AWL_ADD\");\nconst TOPIC_ARENA_WL_REM: Symbol = symbol_short!(\"AWL_REM\");")

with open("factory/src/lib.rs", "w") as f:
    f.write(factory)
