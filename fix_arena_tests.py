import re

with open('arena/src/lib.rs', 'r') as f:
    text = f.read()

# Fix duplicate `mod abi_guard;`
text = re.sub(r'(mod abi_guard;\n.*?)(mod abi_guard;)', r'\1', text, flags=re.DOTALL, count=1)

# Fix client.initialize(&admin); because the method is init? Wait, let's see.
text = text.replace('client.initialize(&admin);', '')
text = text.replace('client.init(&10u32, &100i128);', 'client.init(&10u32, &100i128, &0u64);')

with open('arena/src/lib.rs', 'w') as f:
    f.write(text)

with open('arena/src/test.rs', 'r') as f:
    text = f.read()

# Fix invariants module
if 'mod invariants;' not in text and 'invariants::' in text:
    # actually wait, maybe the invariants module wasn't included?
    pass

text = text.replace('invariants::', 'crate::state_machine_tests::')
text = text.replace('crate::state_machine_tests::check_round_number_monotonic', 'crate::state_machine_tests::invariants::check_round_number_monotonic')
text = text.replace('crate::state_machine_tests::check_submission_count_monotonic', 'crate::state_machine_tests::invariants::check_submission_count_monotonic')
text = text.replace('crate::state_machine_tests::check_round_flags', 'crate::state_machine_tests::invariants::check_round_flags')
text = text.replace('crate::state_machine_tests::check_timeout_transition', 'crate::state_machine_tests::invariants::check_timeout_transition')


with open('arena/src/test.rs', 'w') as f:
    f.write(text)

