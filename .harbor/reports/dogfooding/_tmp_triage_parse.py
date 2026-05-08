import json, pathlib, collections, re
p=pathlib.Path(r"e:\project\harbor-spec\.harbor\reports\dogfooding\v1.3.0-checkpoint-ci-before-accept.json")
d=json.loads(p.read_text(encoding="utf-16"))
items=d["ci_failures"]

print('SUMMARY status', d.get('status'), 'exit_code', d.get('exit_code'))
print('CONTRACT_IMPACT', d.get('contract_impact'))
print('WRITES_FILES', d.get('writes_files'))

# flags from root fields
ci=d.get('ci',{}) if isinstance(d.get('ci'),dict) else {}
print('CI keys', list(ci.keys()))
print('CI raw', ci)

# category + file
cat=collections.Counter(i.get('category') for i in items)
print('\nCATEGORY COUNTS')
for k,v in cat.items():
    print(k,v)

fp=collections.Counter(i.get('file_path','<none>') for i in items)
print('\nTOP FILE_PATH COUNTS')
for k,v in fp.most_common(20):
    print(v,k)

# module group helper

def module_of(path):
    if not path:
        return '<none>'
    p=path.replace('\\','/')
    parts=p.split('/')
    if len(parts)>=2:
        return '/'.join(parts[:2])
    return parts[0]

mod=collections.Counter(module_of(i.get('file_path','')) for i in items)
print('\nMODULE COUNTS')
for k,v in mod.most_common(20):
    print(v,k)

# missing details
print('\nMISSING_FUNCTION DETAILS')
for i in items:
    if i.get('category')=='missing_function':
        print(json.dumps(i, ensure_ascii=False))

# possible_semantic_drift details
print('\nPOSSIBLE_SEMANTIC_DRIFT DETAILS')
for i in items:
    if i.get('category')=='possible_semantic_drift':
        print(json.dumps(i, ensure_ascii=False))

# untracked grouped targets
print('\nUNTRACKED GROUP COUNTS')
groups={
    'harbor/core/ci.py': lambda p:p=='harbor/core/ci.py',
    'harbor/core/contract_impact.py': lambda p:p=='harbor/core/contract_impact.py',
    'harbor/core/context_integrity.py': lambda p:p=='harbor/core/context_integrity.py',
    'harbor/cli/main.py': lambda p:p=='harbor/cli/main.py',
    'tests/**': lambda p:p.replace('\\','/').startswith('tests/'),
}
counts={k:0 for k in groups}
other=0
for i in items:
    if i.get('category')!='untracked_function':
        continue
    p=i.get('file_path','').replace('\\','/')
    matched=False
    for k,f in groups.items():
        if f(p):
            counts[k]+=1
            matched=True
            break
    if not matched:
        other+=1
for k,v in counts.items():
    print(k,v)
print('other',other)

# collect potential keywords flags
kw = {
    'ddt': re.compile(r'ddt|l3_version|strategy="latest"', re.I),
    'cli_json_write_exit': re.compile(r'\bcli\b|json|write target|writes_files|exit code|exit_code', re.I),
    'path_leak': re.compile(r'path leak|absolute path leak|absolute path|C:\\|[A-Za-z]:\\\\', re.I),
    'unexpected_external_path': re.compile(r'unexpected external path|external path|outside workspace', re.I),
    'missing_function': re.compile(r'missing_function', re.I),
}
texts=[]
for i in items:
    texts.append(' '.join(str(i.get(k,'')) for k in ['category','reason','suggested_action','func_id','file_path']))
alltext='\n'.join(texts)
print('\nKEYWORD FLAGS')
for k,r in kw.items():
    print(k, bool(r.search(alltext)))

# show entries mentioning cli/json/write/exit/path
print('\nMATCHED KEYWORD ENTRIES')
for i in items:
    t=' '.join(str(i.get(k,'')) for k in ['category','reason','suggested_action','func_id','file_path'])
    if re.search(r'\bcli\b|json|write target|writes_files|exit code|exit_code|path leak|absolute path|external path', t, re.I):
        print(json.dumps(i, ensure_ascii=False))
