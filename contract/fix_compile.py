import re

with open("arena/src/lib.rs", "r") as f:
    content = f.read()

# 1. Remove duplicate constants:
# const TIMELOCK_PERIOD: u64 = 48 * 60 * 60; // 48 hours
# const GAME_TTL_THRESHOLD: u32 = 17280; // 1 day
# const GAME_TTL_EXTEND_TO: u32 = 120960; // 7 days
content = re.sub(r'const TIMELOCK_PERIOD: u64 = 48 \* 60 \* 60; // 48 hours\n', '', content)
content = re.sub(r'const GAME_TTL_THRESHOLD: u32 = 17280; // 1 day\n', '', content)
content = re.sub(r'const GAME_TTL_EXTEND_TO: u32 = 120960; // 7 days\n', '', content)

# 2. Remove second FullStateView
# Note: we need to find the second occurrence.
# First, let's find the exact string that is duplicated:
full_state_view_regex = r'#\[contracttype\]\n#\[derive\(Clone, Debug, Eq, PartialEq\)\]\npub struct FullStateView \{\n    pub survivors_count: u32,\n    pub max_capacity: u32,\n    pub round_number: u32,\n    pub current_stake: i128,\n    pub potential_payout: i128,\n    pub is_active: bool,\n    pub has_won: bool,\n\}'
# Find all occurrences
parts = re.split(full_state_view_regex, content)
if len(parts) >= 3:
    # It appeared at least twice, so keep the first one
    content = parts[0] + '\n#[contracttype]\n#[derive(Clone, Debug, Eq, PartialEq)]\npub struct FullStateView {\n    pub survivors_count: u32,\n    pub max_capacity: u32,\n    pub round_number: u32,\n    pub current_stake: i128,\n    pub potential_payout: i128,\n    pub is_active: bool,\n    pub has_won: bool,\n}' + parts[1] + parts[2]

# 3. Remove duplicate assert_state in case it is duplicated
assert_state_def = r'macro_rules! assert_state ! \{\n    \(\$current:expr, \$expected:pat\) => \{\n        match \$current \{\n            \$expected => \{\},\n            _ => panic\!\("Invalid state transition: current state \{:\?\} is not allowed for this operation", \$current\),\n        \}\n    \};\n\}'
# Wait, actually let's just delete the block we know is bad for duplicates
