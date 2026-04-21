import os, re

ESHOP = 'c:/Users/valen/Documents/GitHub/optivem/academy/eshop-tests/typescript'
SHOP = 'c:/Users/valen/Documents/GitHub/optivem/academy/shop/system-test/typescript'

EXCLUDE_DIR_PARTS = {'node_modules', 'dist', 'test-results', 'playwright-report'}

def collect(root):
    files = []
    for dp, dn, fn in os.walk(root):
        parts = set(dp.replace('\\', '/').split('/'))
        if parts & EXCLUDE_DIR_PARTS:
            continue
        for f in fn:
            if f.endswith('.ts'):
                full = os.path.join(dp, f).replace('\\', '/')
                files.append(full[len(root)+1:])
    return sorted(files)

def pascal_to_kebab(name):
    base, ext = os.path.splitext(name)
    kebab = re.sub(r'(?<!^)(?=[A-Z])', '-', base).lower()
    kebab = re.sub(r'-+', '-', kebab)
    return kebab + ext

def pascal_spec_to_kebab_test(name):
    if name.endswith('.spec.ts'):
        base = name[:-len('.spec.ts')]
        kebab = re.sub(r'(?<!^)(?=[A-Z])', '-', base).lower()
        return f'{kebab}-test.spec.ts'
    return pascal_to_kebab(name)

# Specific contract-test renames: plain "Clock" -> "clock-real"
def contract_spec_real(name):
    if name.endswith('ContractTest.spec.ts'):
        base = name[:-len('ContractTest.spec.ts')]
        kebab = re.sub(r'(?<!^)(?=[A-Z])', '-', base).lower()
        return f'{kebab}-real-contract-test.spec.ts'
    return None

def map_eshop_to_shop_candidates(rel):
    parts = rel.split('/')
    fname = parts[-1]
    dirs = parts[:-1]
    cands = []

    def add(p):
        if p not in cands:
            cands.append(p)

    layer = dirs[0] if dirs else ''

    new_dirs_list = []

    if layer == 'channel':
        new_dirs_list.append(['src', 'testkit', 'channel'] + dirs[1:])
    elif layer == 'common':
        if len(dirs) >= 2 and dirs[1] == 'src':
            new_dirs_list.append(['src', 'testkit', 'common'] + dirs[2:])
        else:
            new_dirs_list.append(['src', 'testkit', 'common'] + dirs[1:])
    elif layer == 'driver-adapter':
        base_new = ['src', 'testkit', 'driver', 'adapter'] + dirs[1:]
        new_dirs_list.append(base_new)
        # Also try dropping 'client' segment (shared/client/http -> shared/http)
        if 'client' in base_new:
            new_dirs_list.append([p for p in base_new if p != 'client'])
    elif layer == 'driver-port':
        new_dirs_list.append(['src', 'testkit', 'driver', 'port'] + dirs[1:])
        # Also try dropping 'error' segment (dtos/error/X -> dtos/X)
        alt = ['src', 'testkit', 'driver', 'port'] + dirs[1:]
        if 'error' in alt:
            new_dirs_list.append([p for p in alt if p != 'error'])
    elif layer == 'dsl-core':
        new_dirs_list.append(['src', 'testkit', 'dsl', 'core'] + dirs[1:])
    elif layer == 'dsl-port':
        sub = dirs[1:]
        new_dirs_list.append(['src', 'testkit', 'dsl', 'port'] + sub)
        # Drop 'scenario' since shop doesn't have it
        if sub and sub[0] == 'scenario':
            new_dirs_list.append(['src', 'testkit', 'dsl', 'port'] + sub[1:])
    elif layer == 'system-test':
        sub = dirs[1:]
        if sub and sub[0] == 'tests':
            new_dirs_list.append(sub)
            # base/fixtures.ts -> fixtures.ts mapping for tests
            if sub and sub[-1] == 'base' and fname == 'fixtures.ts':
                new_dirs_list.append(sub[:-1])
        elif sub and sub[0] == 'src':
            new_dirs_list.append(['src', 'testkit'] + sub[1:])
        else:
            new_dirs_list.append(sub)
    else:
        new_dirs_list.append(dirs[:])

    # Generate filename variants
    fname_variants = [pascal_to_kebab(fname), fname]

    # Spec tests: add -test suffix
    if fname.endswith('.spec.ts'):
        fname_variants.append(pascal_spec_to_kebab_test(fname))
        # Contract-test 'real' variant
        cv = contract_spec_real(fname)
        if cv:
            fname_variants.append(cv)

    # dsl-port port suffix removal (e.g. ScenarioRootPort.ts -> scenario-root.ts)
    if fname.endswith('Port.ts'):
        fname_no_port = fname[:-len('Port.ts')] + '.ts'
        fname_variants.append(pascal_to_kebab(fname_no_port))
        fname_variants.append(fname_no_port)

    for nd in new_dirs_list:
        for fv in fname_variants:
            add('/'.join(nd + [fv]))

    return cands

e_files = collect(ESHOP)
s_files = collect(SHOP)
s_set = set(s_files)

matches = []
eshop_only = []
shop_matched = set()

for er in e_files:
    cands = map_eshop_to_shop_candidates(er)
    found = None
    for c in cands:
        if c in s_set:
            found = c
            break
    if found:
        matches.append((er, found))
        shop_matched.add(found)
    else:
        eshop_only.append(er)

shop_only = [s for s in s_files if s not in shop_matched]

print(f'ESHOP TOTAL: {len(e_files)}')
print(f'SHOP TOTAL: {len(s_files)}')
print(f'MATCHES: {len(matches)}')
print(f'ESHOP-ONLY: {len(eshop_only)}')
print(f'SHOP-ONLY: {len(shop_only)}')

with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/ts_matches.txt', 'w', encoding='utf-8') as f:
    for er, sr in matches:
        f.write(f'{er}\t{sr}\n')
with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/ts_eshop_only.txt', 'w', encoding='utf-8') as f:
    for er in eshop_only:
        f.write(er + '\n')
with open('c:/Users/valen/Documents/GitHub/optivem/academy/claude/.tmp/ts_shop_only.txt', 'w', encoding='utf-8') as f:
    for sr in shop_only:
        f.write(sr + '\n')
