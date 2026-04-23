import re

with open('payout/src/test.rs', 'r') as f:
    text = f.read()

# Replace `let (env, _admin, client, token_id, _treasury) = setup_with_token();`
# with `let (env, _admin, client, token_id, _treasury, _, _) = setup_with_token();`
text = re.sub(
    r'let \((env, _admin, client, token_id, _treasury)\)\s*=\s*setup_with_token\(\);',
    r'let (\1, _, _) = setup_with_token();',
    text
)

with open('payout/src/test.rs', 'w') as f:
    f.write(text)

