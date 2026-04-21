import os, subprocess, sys, re

ESHOP = 'c:/Users/valen/Documents/GitHub/optivem/academy/eshop-tests/typescript'
SHOP = 'c:/Users/valen/Documents/GitHub/optivem/academy/shop/system-test/typescript'

matches = []
with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/ts_matches.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.rstrip('\n')
        if not line:
            continue
        er, sr = line.split('\t')
        matches.append((er, sr))

IMPORT_RE = re.compile(r'^\s*import\s')
FROM_RE = re.compile(r'\bfrom\s+[\'"]')
EXPORT_FROM_RE = re.compile(r'^\s*export\s+.*\s+from\s+[\'"]')

def is_import_line(line):
    # consider lines that are part of import statements (might be multi-line)
    s = line.strip()
    if s.startswith('import ') or s.startswith('import('):
        return True
    if s.startswith('export ') and ' from ' in s:
        return True
    # multi-line import continuation (contains 'from "' at end, or is inside braces)
    return False

def categorize(eshop_path, shop_path):
    try:
        with open(eshop_path, 'r', encoding='utf-8') as f:
            e_lines = f.read().splitlines()
    except Exception as ex:
        return 'ERROR', f'read eshop failed: {ex}', None
    try:
        with open(shop_path, 'r', encoding='utf-8') as f:
            s_lines = f.read().splitlines()
    except Exception as ex:
        return 'ERROR', f'read shop failed: {ex}', None

    if e_lines == s_lines:
        return 'IDENTICAL', '', None

    # Strip trailing whitespace and blank line diffs
    e_stripped = [l.rstrip() for l in e_lines]
    s_stripped = [l.rstrip() for l in s_lines]
    if e_stripped == s_stripped:
        return 'IDENTICAL', '(whitespace only)', None

    # Compute diff
    import difflib
    diff = list(difflib.unified_diff(e_lines, s_lines, lineterm='', n=1, fromfile=eshop_path, tofile=shop_path))

    # Classify diff lines: collect non-header + or - lines
    added = [l[1:] for l in diff if l.startswith('+') and not l.startswith('+++')]
    removed = [l[1:] for l in diff if l.startswith('-') and not l.startswith('---')]

    # Check if all diff chunks only affect imports
    non_import_removed = [l for l in removed if not (is_import_line(l) or l.strip() == '' or l.strip().startswith('//') )]
    non_import_added = [l for l in added if not (is_import_line(l) or l.strip() == '' or l.strip().startswith('//') )]
    # also filter lines that are just closing brace '}' or opening of import blocks, etc.
    # More lenient: look at multi-line import detection - just check if the surrounding chunks look like imports
    def looks_like_import_fragment(line):
        s = line.strip()
        if not s:
            return True
        if s.startswith('//'):
            return True
        if s.startswith('import') or s.startswith('export'):
            return True
        if s.startswith('}') and 'from' in s:
            return True
        if s.endswith(',') and not ('=' in s):  # listed imports
            # But could also be code - check if it's a bare word-like
            if re.match(r'^[A-Za-z_][A-Za-z0-9_,\s]*,?$', s):
                return True
        if s.startswith("} from '") or s.startswith('} from "'):
            return True
        if re.match(r'^[\'"].*[\'"];?\s*$', s):  # pure string line e.g. ending of multi-line from
            return True
        # bare word followed by optional comma, commonly in import lists
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*,?$', s):
            return True
        return False

    non_import_removed2 = [l for l in removed if not looks_like_import_fragment(l)]
    non_import_added2 = [l for l in added if not looks_like_import_fragment(l)]

    if not non_import_removed2 and not non_import_added2:
        return 'IMPORTS_ONLY', '', '\n'.join(diff)

    return 'LOGIC', '', '\n'.join(diff)

results = []
for er, sr in matches:
    ep = os.path.join(ESHOP, er).replace('\\', '/')
    sp = os.path.join(SHOP, sr).replace('\\', '/')
    cat, note, diff = categorize(ep, sp)
    results.append((er, sr, cat, note, diff))

categorized = {'IDENTICAL': [], 'IMPORTS_ONLY': [], 'LOGIC': [], 'ERROR': []}
for er, sr, cat, note, diff in results:
    categorized[cat].append((er, sr, note, diff))

print(f'IDENTICAL: {len(categorized["IDENTICAL"])}')
print(f'IMPORTS_ONLY: {len(categorized["IMPORTS_ONLY"])}')
print(f'LOGIC: {len(categorized["LOGIC"])}')
print(f'ERROR: {len(categorized["ERROR"])}')

with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/cat_identical.txt', 'w', encoding='utf-8') as f:
    for er, sr, note, diff in categorized['IDENTICAL']:
        f.write(f'{er}\t{sr}\t{note}\n')
with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/cat_imports_only.txt', 'w', encoding='utf-8') as f:
    for er, sr, note, diff in categorized['IMPORTS_ONLY']:
        f.write(f'{er}\t{sr}\n')
with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/cat_logic.txt', 'w', encoding='utf-8') as f:
    for er, sr, note, diff in categorized['LOGIC']:
        f.write(f'=== MATCH: {er} <=> {sr} ===\n')
        f.write(diff + '\n\n')
with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/cat_logic_files.txt', 'w', encoding='utf-8') as f:
    for er, sr, note, diff in categorized['LOGIC']:
        f.write(f'{er}\t{sr}\n')
