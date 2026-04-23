with open("factory/src/lib.rs", "r") as f:
    content = f.read()

dupe_hash_mismatch = r'''    /// The hash provided to `execute_upgrade` does not match the stored proposal hash.
    HashMismatch = 17,'''

if content.count(dupe_hash_mismatch) > 0:
    content = content.replace(dupe_hash_mismatch, "", 1)

# just in case it was a different capitalization or spacing:
# let's regex out the second HashMismatch
import re
hm_regex = r'HashMismatch\s*=\s*17,'
matches = re.finditer(hm_regex, content)
lines = list(matches)
if len(lines) > 1:
    idx2 = lines[1].start()
    # Find the line start of the duplicate
    line_start = content.rfind("\n", 0, idx2)
    # Remove the whole line
    line_end = content.find("\n", idx2)
    content = content[:content.rfind("\n", 0, line_start)] + content[line_end:]

with open("factory/src/lib.rs", "w") as f:
    f.write(content)
