import os
import re

def refactor_datakey(path):
    with open(path, "r") as f:
        content = f.read()

    # Skip if DataKey is already present
    if "#[contracttype]" in content and "enum DataKey {" in content and "Admin" in content:
        return

    # Collect all const *_KEY
    const_pattern = re.compile(r'const\s+([A-Z0-9_]+)_KEY:\s*Symbol\s*=\s*symbol_short!\("([^"]+)"\);')
    constants = const_pattern.findall(content)
    
    if not constants:
        return

    # Special handling for already existing DataKey (e.g. in payout)
    if "enum DataKey {" in content:
        # Payout has its own DataKey, let's just append to it instead of creating a new one
        # Or rather, let's leave it alone if it's already using DataKey and has its own enums
        if path.endswith('payout/src/lib.rs'):
             # actually I'll just rewrite everything if we want
             pass

    # Create DataKey enum
    enum_variants = []
    for const_name, const_val in constants:
        # Convert CONST_NAME to ConstName
        parts = const_name.split("_")
        variant_name = "".join([p.capitalize() for p in parts])
        enum_variants.append(f"    {variant_name},")
        
    enum_str = "\n#[contracttype]\n#[derive(Clone, Debug, Eq, PartialEq)]\npub enum DataKey {\n" + "\n".join(enum_variants) + "\n}\n"

    # Since Payout already has one, let's just replace all usages first, except we need to handle Payout properly
    # If the file already has pub enum DataKey, we should inject into it
    has_datakey = "pub enum DataKey {" in content
    
    if not has_datakey:
        content = re.sub(r'(const\s+[A-Z0-9_]+_KEY:\s*Symbol\s*=\s*symbol_short!\("[^"]+"\);\n+)+', enum_str + "\n", content, count=1)
        # remove the rest 
        content = re.sub(r'const\s+[A-Z0-9_]+_KEY:\s*Symbol\s*=\s*symbol_short!\("[^"]+"\);\n', "", content)
    else:
        # Append to existing DataKey
        # Actually it's complex, I will just manual-replace usages
        pass
        
    if not has_datakey:
        for const_name, const_val in constants:
            parts = const_name.split("_")
            variant_name = "".join([p.capitalize() for p in parts])
            content = content.replace(f"&{const_name}_KEY", f"&DataKey::{variant_name}")
            content = content.replace(f"{const_name}_KEY", f"DataKey::{variant_name}")

    with open(path, "w") as f:
        f.write(content)
        
    print(f"Refactored {path}")

for root, dirs, files in os.walk("."):
    if "src" in root and "lib.rs" in files:
        if "proptest" not in root and "tests" not in root and "payout" not in root:
            refactor_datakey(os.path.join(root, "lib.rs"))
