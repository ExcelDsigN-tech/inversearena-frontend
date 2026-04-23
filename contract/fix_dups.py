import re

with open('arena/src/lib.rs', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.strip() == 'pub fn leave(env: Env, player: Address) -> Result<(), ArenaError> {':
        skip = True
    if skip and 'pub fn set_max_rounds(env: Env, max_rounds: u32) -> Result<(), ArenaError> {' in line:
        pass
    if skip and line.strip() == '}' and ('max_rounds' in lines[i-1] or 'Config' in lines[i-1] or 'SURVIVOR_COUNT_KEY' in lines[i-1]):
        pass
    # we just skip from leave() all the way to after set_max_rounds
    # wait it's just simpler to look for the duplicate lines

with open('arena/src/lib.rs', 'r') as f:
    text = f.read()

# Let's cleanly cut out the three functions at the end of the file
# 982-1011 or so
bad_leave = r'    pub fn leave\(env: Env, player: Address\) -> Result<\(\), ArenaError> \{\n        player\.require_auth\(\);\n        if !env\n            \.storage\(\)\n            \.persistent\(\)\n            \.has\(&DataKey::Survivor\(player\.clone\(\)\)\)\n        \{\n            return Err\(ArenaError::NotASurvivor\);\n        \}\n        env\.storage\(\)\n            \.persistent\(\)\n            \.remove\(&DataKey::Survivor\(player\)\);\n        let count: u32 = env\n            \.storage\(\)\n            \.instance\(\)\n            \.get\(&SURVIVOR_COUNT_KEY\)\n            \.unwrap_or\(0\);\n        env\.storage\(\)\n            \.instance\(\)\n            \.set\(&SURVIVOR_COUNT_KEY, &count\.saturating_sub\(1\)\);\n        Ok\(\(\)\)\n    \}\n\n'

text = re.sub(bad_leave, '', text)

bad_smr = r'    pub fn set_max_rounds\(env: Env, max_rounds: u32\) -> Result<\(\), ArenaError> \{\n        let admin = Self::admin\(env\.clone\(\)\);\n        admin\.require_auth\(\);\n        if max_rounds < bounds::MIN_MAX_ROUNDS \|\| max_rounds > bounds::MAX_MAX_ROUNDS \{\n            return Err\(ArenaError::InvalidMaxRounds\);\n        \}\n        let mut config = get_config\(&env\)\?;\n        config\.max_rounds = max_rounds;\n        env\.storage\(\)\.instance\(\)\.set\(&DataKey::Config, &config\);\n        Ok\(\(\)\)\n    \}\n\n'

text = re.sub(bad_smr, '', text)

with open('arena/src/lib.rs', 'w') as f:
    f.write(text)

