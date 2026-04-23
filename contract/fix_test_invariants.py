with open('arena/src/test.rs', 'r') as f:
    text = f.read()

text = text.replace('crate::state_machine_tests::invariants::', 'crate::invariants::')

with open('arena/src/test.rs', 'w') as f:
    f.write(text)

