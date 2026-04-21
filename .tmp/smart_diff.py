import os, re, difflib

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

def strip_imports(lines):
    """Remove lines that are part of import/export-from statements, handling multi-line cases."""
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if (s.startswith('import ') or s.startswith('import(') or s.startswith('import{')
            or (s.startswith('export ') and ' from ' in s)
            or s.startswith('export {')
            or s.startswith('export *')
           ):
            # Could be single or multi-line. Consume until we see "from ... ;" or line ends with ";"
            # For simple single-line imports, s ends with ';' or has 'from'
            # Multi-line: { ... } from '...';
            # Accumulate lines until terminator
            full = s
            # Advance if current line ends the statement
            if (';' in s or s.endswith(';') or (('from ' in s) and s.endswith("';") or s.endswith('";'))):
                # ends
                i += 1
                continue
            # multi-line
            i += 1
            while i < len(lines):
                ln2 = lines[i].strip()
                i += 1
                if ln2.endswith(';') or re.search(r"from\s+['\"].+['\"]\s*;?\s*$", ln2):
                    break
            continue
        out.append(ln)
        i += 1
    return out

def normalize_content(lines):
    """Apply normalizations: strip trailing whitespace, drop fully blank lines from comparison."""
    norm = []
    for l in lines:
        l = l.rstrip()
        norm.append(l)
    # Drop leading/trailing blank lines
    while norm and norm[0] == '':
        norm.pop(0)
    while norm and norm[-1] == '':
        norm.pop()
    return norm

def read_file(p):
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return f.read().splitlines()
    except Exception:
        try:
            with open(p, 'r', encoding='utf-8', errors='replace') as f:
                return f.read().splitlines()
        except Exception as e:
            return None

results = []
for er, sr in matches:
    ep = os.path.join(ESHOP, er).replace('\\', '/')
    sp = os.path.join(SHOP, sr).replace('\\', '/')
    e_raw = read_file(ep)
    s_raw = read_file(sp)
    if e_raw is None or s_raw is None:
        results.append((er, sr, 'ERROR', 'read error', ''))
        continue

    # Quick check
    if e_raw == s_raw:
        results.append((er, sr, 'IDENTICAL', '', ''))
        continue

    e_norm = normalize_content(e_raw)
    s_norm = normalize_content(s_raw)
    if e_norm == s_norm:
        results.append((er, sr, 'IDENTICAL', 'whitespace only', ''))
        continue

    # Strip imports and re-compare
    e_noimp = normalize_content(strip_imports(e_raw))
    s_noimp = normalize_content(strip_imports(s_raw))
    if e_noimp == s_noimp:
        results.append((er, sr, 'IMPORTS_ONLY', '', ''))
        continue

    # Compute non-import unified diff
    diff = '\n'.join(difflib.unified_diff(e_noimp, s_noimp, lineterm='', fromfile=f'[eshop-tests] {er}', tofile=f'[shop] {sr}', n=2))
    results.append((er, sr, 'LOGIC', '', diff))

categorized = {'IDENTICAL': [], 'IMPORTS_ONLY': [], 'LOGIC': [], 'ERROR': []}
for r in results:
    categorized[r[2]].append(r)

print(f'IDENTICAL: {len(categorized["IDENTICAL"])}')
print(f'IMPORTS_ONLY: {len(categorized["IMPORTS_ONLY"])}')
print(f'LOGIC: {len(categorized["LOGIC"])}')
print(f'ERROR: {len(categorized["ERROR"])}')

with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/smart_identical.txt', 'w', encoding='utf-8') as f:
    for er, sr, cat, note, diff in categorized['IDENTICAL']:
        f.write(f'{er}\t{sr}\t{note}\n')
with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/smart_imports_only.txt', 'w', encoding='utf-8') as f:
    for er, sr, cat, note, diff in categorized['IMPORTS_ONLY']:
        f.write(f'{er}\t{sr}\n')
with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/smart_logic.txt', 'w', encoding='utf-8') as f:
    for er, sr, cat, note, diff in categorized['LOGIC']:
        f.write(f'=== MATCH: {er} <=> {sr} ===\n')
        f.write(diff + '\n\n')
with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/smart_logic_files.txt', 'w', encoding='utf-8') as f:
    for er, sr, cat, note, diff in categorized['LOGIC']:
        f.write(f'{er}\t{sr}\n')
