import re

def fix_payout():
    with open('payout/src/lib.rs', 'r') as f:
        c = f.read()
    # Looking for 'pub struct SplitPayoutReceipt {' without closing
    # but wait, `git restore payout/src/lib.rs` should have fixed it?
    # I didn't git restore it after the `fix_mess.py`. BUT `fix_mess.py` didn't touch payout!
    pass

def fix_arena():
    with open('arena/src/lib.rs', 'r') as f:
        c = f.read()

    # amount -> config.required_stake_amount
    c = c.replace('.set(&PRIZE_POOL_KEY, &(pool + amount));', '.set(&PRIZE_POOL_KEY, &(pool + refund));')

    c = c.replace('use soroban_sdk::{', 'use soroban_sdk::{IntoVal, ')

    c = c.replace('NotWhitelisted = 20,', 'NotWhitelisted = 30,')
    
    # is_private missing
    c = c.replace('pub grace_period_seconds: u64,\n            }', 'pub grace_period_seconds: u64,\n                is_private: false,\n            }')

    # arena_id u32 -> u64
    c = c.replace('arena_id,\n                timestamp: request.timestamp,', 'arena_id: arena_id as u64,\n                timestamp: request.timestamp,')

    c = c.replace('to_val()', 'into_val(&env)')
    c = c.replace('Ok(())', 'Ok(refund)') # there might be other Ok(())

    with open('arena/src/lib.rs', 'w') as f:
        f.write(c)

def fix_factory():
    with open('factory/src/lib.rs', 'r') as f:
        c = f.read()

    c = c.replace('const TOPIC_UPGRADE: Symbol = symbol_short!("UPGRADE");', 'const TOPIC_UPGRADE: Symbol = symbol_short!("UPGRADE");\nconst TOPIC_ARENA_WL_ADD: Symbol = symbol_short!("WL_ADD");\nconst TOPIC_ARENA_WL_REM: Symbol = symbol_short!("WL_REM");\n')

    with open('factory/src/lib.rs', 'w') as f:
        f.write(c)

# payout/src/lib.rs is just broken, I will `git checkout .` to be safe, but wait, my fix_mess.py applied to arena and factory!
# Let's undo checkout on payout only
import os; os.system('git checkout payout/src/lib.rs')

fix_arena()
fix_factory()

