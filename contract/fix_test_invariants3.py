with open('arena/src/lib.rs', 'r') as f:
    text = f.read()

text = text.replace('mod invariants;', 'pub mod invariants;')

with open('arena/src/lib.rs', 'w') as f:
    f.write(text)

