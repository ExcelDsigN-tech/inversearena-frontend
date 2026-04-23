import re

with open('staking/src/test.rs', 'r') as f:
    text = f.read()

# Fix for timelock_non_admin_execute_panics
text = text.replace('''
    let contract_id = env.register(StakingContract, (&admin, &token_id));
    env.mock_all_auths();
''', '''
    env.mock_all_auths();
    let contract_id = env.register(StakingContract, (&admin, &token_id));
''')

with open('staking/src/test.rs', 'w') as f:
    f.write(text)

