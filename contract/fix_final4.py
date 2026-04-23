with open("arena/src/lib.rs", "r") as f:
    arena = f.read()

# Fix ArenaConfig init missing is_private
# Find win_fee_bps, inside init_with_fee
arena_init_target = """                join_deadline,
                win_fee_bps,
            },"""
arena_init_replacement = """                join_deadline,
                win_fee_bps,
                is_private: false,
            },"""
arena = arena.replace(arena_init_target, arena_init_replacement)

# Fix player moved 
# players.push_back(player); -> players.push_back(player.clone());
arena = arena.replace("players.push_back(player);", "players.push_back(player.clone());")

with open("arena/src/lib.rs", "w") as f:
    f.write(arena)
