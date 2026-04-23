import re

with open('arena/src/lib.rs', 'r') as f:
    text = f.read()

if 'mod invariants;' not in text:
    text = text.replace('mod bounds;', 'mod bounds;\n#[cfg(test)]\nmod invariants;')

with open('arena/src/lib.rs', 'w') as f:
    f.write(text)

