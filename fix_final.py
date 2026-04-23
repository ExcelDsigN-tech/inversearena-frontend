import re

def refactor(file, enums, replacements):
    with open(file, 'r') as f:
        content = f.read()

    enum_str = "#[contracttype]\n#[derive(Clone, Copy, Debug, Eq, PartialEq)]\npub enum DataKey {\n" + "".join([f"    {e},\n" for e in enums]) + "}\n"
    
    # insert enum after imports
    content = content.replace("mod bounds;\n", "mod bounds;\n\n" + enum_str + "\n")
    content = content.replace("use soroban_sdk::{", "use soroban_sdk::{\n    ")

    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(file, 'w') as f:
        f.write(content)

# Arena DataKey refactor
arena_enums = [
    "Admin",
    "Paused",
    "Config",
    "State",
    "Players",
    "Survivors",
    "Eliminated",
    "RoundTimer",
    "Choices",
    "Winner",
    "Token",
    "Capacity",
    "PrizePool",
    "Yield",
    "WinnerShare",
    "SurvivorCount",
    "Cancelled",
    "GameFinished",
    "PendingHash",
    "ExecuteAfter",
    "WinnerAddr",
    "Factory",
    "Creator"
]
arena_replacements = [
    ('const ADMIN_KEY: Symbol = symbol_short!("ADMIN");\n', ''),
    ('const TOKEN_KEY: Symbol = symbol_short!("TOKEN");\n', ''),
    ('const CAPACITY_KEY: Symbol = symbol_short!("CAPACITY");\n', ''),
    ('const PRIZE_POOL_KEY: Symbol = symbol_short!("POOL");\n', ''),
    ('const YIELD_KEY: Symbol = symbol_short!("YIELD");\n', ''),
    ('const WINNER_SHARE_KEY: Symbol = symbol_short!("WY_BPS");\n', ''),
    ('const SURVIVOR_COUNT_KEY: Symbol = symbol_short!("S_COUNT");\n', ''),
    ('const CANCELLED_KEY: Symbol = symbol_short!("CANCEL");\n', ''),
    ('const GAME_FINISHED_KEY: Symbol = symbol_short!("FINISHED");\n', ''),
    ('const PAUSED_KEY: Symbol = symbol_short!("PAUSED");\n', ''),
    ('const PENDING_HASH_KEY: Symbol = symbol_short!("P_HASH");\n', ''),
    ('const EXECUTE_AFTER_KEY: Symbol = symbol_short!("P_AFTER");\n', ''),
    ('const STATE_KEY: Symbol = symbol_short!("STATE");\n', ''),
    ('const WINNER_ADDR_KEY: Symbol = symbol_short!("WINNER");\n', ''),
    ('const FACTORY_KEY: Symbol = symbol_short!("FACTORY");\n', ''),
    ('const CREATOR_KEY: Symbol = symbol_short!("CREATOR");\n', ''),

    ('ADMIN_KEY', 'DataKey::Admin'),
    ('TOKEN_KEY', 'DataKey::Token'),
    ('CAPACITY_KEY', 'DataKey::Capacity'),
    ('PRIZE_POOL_KEY', 'DataKey::PrizePool'),
    ('YIELD_KEY', 'DataKey::Yield'),
    ('WINNER_SHARE_KEY', 'DataKey::WinnerShare'),
    ('SURVIVOR_COUNT_KEY', 'DataKey::SurvivorCount'),
    ('CANCELLED_KEY', 'DataKey::Cancelled'),
    ('GAME_FINISHED_KEY', 'DataKey::GameFinished'),
    ('PAUSED_KEY', 'DataKey::Paused'),
    ('PENDING_HASH_KEY', 'DataKey::PendingHash'),
    ('EXECUTE_AFTER_KEY', 'DataKey::ExecuteAfter'),
    ('STATE_KEY', 'DataKey::State'),
    ('WINNER_ADDR_KEY', 'DataKey::WinnerAddr'),
    ('FACTORY_KEY', 'DataKey::Factory'),
    ('CREATOR_KEY', 'DataKey::Creator')
]
refactor('arena/src/lib.rs', arena_enums, arena_replacements)

# Wait we have enum DataKey { Config(u64), etc } in the PR description explicitly:
# "Example for ArenaContract:
# #[contracttype]
# pub enum DataKey {
#   Admin,
#   Paused,
#   ...
#   Config(u64),
#   State(u64),
#   Players(u64),
#   Survivors(u64),
#   Eliminated(u64),
#   RoundTimer(u64, u32),
#   Choices(u64, u32, Address),
#   Winner(u64),
# }"
# This is completely different from just removing _KEY globals!
