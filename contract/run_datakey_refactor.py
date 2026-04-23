import os
import re

def refactor_file(path):
    with open(path, "r") as f:
        content = f.read()

    # Find constants
    const_pattern = re.compile(r'(?:pub\s+)?const\s+([A-Z0-9_]+)_KEY:\s*Symbol\s*=\s*symbol_short!\("([^"]+)"\);')
    constants = const_pattern.findall(content)
    
    if not constants:
        return

    # Prepare DataKey
    variants = []
    reps = []
    
    for const_name, _ in constants:
        parts = const_name.split("_")
        variant_name = "".join(p.capitalize() for p in parts)
        variants.append(f"    {variant_name},")
        
        # Replace `&CONST_KEY` and `CONST_KEY`
        reps.append((f"&{const_name}_KEY", f"&DataKey::{variant_name}"))
        reps.append((f"{const_name}_KEY", f"DataKey::{variant_name}"))

        # remove const
        content = re.sub(r'(?:pub\s+)?const\s+' + const_name + r'_KEY:\s*Symbol\s*=\s*symbol_short!\("([^"]+)"\);\n', '', content)

    # Insert DataKey enum
    if "enum DataKey {" in content:
        # Just inject it before `}` of the FIRST enum DataKey {
        append_str = "\n".join(variants) + "\n"
        content = re.sub(r'enum DataKey \{', 'enum DataKey {\n' + append_str, content, count=1)
    else:
        enum_str = "\n#[contracttype]\n#[derive(Clone, Debug, Eq, PartialEq)]\npub enum DataKey {\n" + "\n".join(variants) + "\n}\n"
        content = content.replace("mod bounds;\n", "mod bounds;\n" + enum_str, 1)
        if "mod bounds;" not in content:
            content = content.replace("pub const TIMELOCK_PERIOD", enum_str + "\npub const TIMELOCK_PERIOD")
            if "pub const TIMELOCK_PERIOD" not in content:
                content = content.replace("const EVENT_VERSION", enum_str + "\nconst EVENT_VERSION")

    for old, new in reps:
        content = content.replace(old, new)

    with open(path, "w") as f:
        f.write(content)


for root, dirs, files in os.walk("contract"):
    if "src" in root and "lib.rs" in files and "proptest" not in root and "tests" not in root:
        refactor_file(os.path.join(root, "lib.rs"))

