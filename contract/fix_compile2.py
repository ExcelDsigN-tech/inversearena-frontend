import re

with open("arena/src/lib.rs", "r") as f:
    content = f.read()

# Remove the second duplicate macro assert_state
assert_state = r'''macro_rules! assert_state {
    (\$current:expr, \$expected:pat) => {
        match \$current {
            \$expected => {},
            _ => panic!("Invalid state transition: current state {:?} is not allowed for this operation", \$current),
        }
    };
}'''
if content.count(assert_state) > 1:
    idx = content.find(assert_state)
    next_idx = content.find(assert_state, idx + 10)
    content = content[:next_idx] + content[next_idx + len(assert_state):]

# Remove the duplicated FullStateView block after line 200
full_state_view = r'''#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FullStateView {
    pub survivors_count: u32,
    pub max_capacity: u32,
    pub round_number: u32,
    pub current_stake: i128,
    pub potential_payout: i128,
    pub is_active: bool,
    pub has_won: bool,
}'''
# Find second occurrence and remove
first_idx = content.find(full_state_view)
if first_idx != -1:
    next_idx = content.find(full_state_view, first_idx + 10)
    if next_idx != -1:
        content = content[:next_idx] + content[next_idx + len(full_state_view):]

# Same for ArenaError -> add NotWhitelisted
if "NotWhitelisted = 47," not in content:
    content = content.replace("InvalidGracePeriod = 46,", "InvalidGracePeriod = 46,\n    NotWhitelisted = 47,")

# Same for ArenaConfig -> add is_private
if "pub is_private: bool," not in content:
    content = content.replace("pub win_fee_bps: u32,\n}", "pub win_fee_bps: u32,\n    pub is_private: bool,\n}")

with open("arena/src/lib.rs", "w") as f:
    f.write(content)
