with open("arena/src/lib.rs", "r") as f:
    arena = f.read()

# Add NotWhitelisted
arena = arena.replace("InvalidGracePeriod = 46,\n}", "InvalidGracePeriod = 46,\n    NotWhitelisted = 47,\n}")

# Add is_private definition to struct ArenaConfig
# The end of ArenaConfig is:
#     pub win_fee_bps: u32,
# }
arena = arena.replace("pub win_fee_bps: u32,\n}", "pub win_fee_bps: u32,\n    pub is_private: bool,\n}")

# get_state -> state
arena = arena.replace("get_state(&env)", "state(&env)")

# set_state(&env, ArenaState::Cancelled); -> env.storage().instance().set(&STATE_KEY, &ArenaState::Cancelled);
arena = arena.replace("set_state(&env, ArenaState::Cancelled);", "env.storage().instance().set(&STATE_KEY, &ArenaState::Cancelled);")

with open("arena/src/lib.rs", "w") as f:
    f.write(arena)

with open("factory/src/lib.rs", "r") as f:
    factory = f.read()

# Add TOPIC_ARENA_WL_ADD and TOPIC_ARENA_WL_REM
ins = 'const TOPIC_FEE_CANCELLED: Symbol = symbol_short!("FEE_CAN");\nconst TOPIC_ARENA_WL_ADD: Symbol = symbol_short!("AWL_ADD");\nconst TOPIC_ARENA_WL_REM: Symbol = symbol_short!("AWL_REM");'
factory = factory.replace('const TOPIC_FEE_CANCELLED: Symbol = symbol_short!("FEE_CAN");', ins)

with open("factory/src/lib.rs", "w") as f:
    f.write(factory)
