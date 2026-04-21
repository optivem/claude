import os, difflib

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

sizes = []
for er, sr in matches:
    ep = os.path.join(ESHOP, er)
    sp = os.path.join(SHOP, sr)
    try:
        with open(ep, 'r', encoding='utf-8') as f:
            e = f.read().splitlines()
        with open(sp, 'r', encoding='utf-8') as f:
            s = f.read().splitlines()
    except Exception as ex:
        sizes.append((99999, er, sr, f'read err: {ex}'))
        continue
    sm = difflib.SequenceMatcher(a=e, b=s)
    ratio = sm.ratio()
    # count changed lines
    changed = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            changed += (i2-i1) + (j2-j1)
    sizes.append((changed, ratio, er, sr, len(e), len(s)))

sizes.sort(key=lambda x: x[0])
with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/diff_sizes.txt', 'w', encoding='utf-8') as f:
    for entry in sizes:
        f.write(f'{entry[0]:5d}  ratio={entry[1]:.2f}  e={entry[4]:4d} s={entry[5]:4d}  {entry[2]}  <=>  {entry[3]}\n')
print('Written diff_sizes.txt')
print(f'Total: {len(sizes)}')
print(f'<=5 changed lines: {sum(1 for s in sizes if s[0] <= 5)}')
print(f'<=15 changed lines: {sum(1 for s in sizes if s[0] <= 15)}')
print(f'<=50 changed lines: {sum(1 for s in sizes if s[0] <= 50)}')
