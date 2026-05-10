import json
from pathlib import Path

base = Path('.harbor/reports')
files = {
    'checkpoint_basic': base / 'checkpoint-ci.json',
    'checkpoint_off': base / 'checkpoint-ci-no-advice.json',
    'stale_basic': base / 'stale-ci.json',
    'stale_off': base / 'stale-ci-no-advice.json',
    'doctor_basic': base / 'doctor-ci.json',
    'doctor_off': base / 'doctor-ci-no-advice.json',
    'next_json': base / 'next-checkpoint.json',
}

def read_text_auto(path: Path) -> str:
    data = path.read_bytes()
    for enc in ('utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be'):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode('latin-1')

def parse_single(path: Path):
    txt = read_text_auto(path).strip()
    dec = json.JSONDecoder()
    obj, end = dec.raw_decode(txt)
    return obj, (txt[end:].strip() == '')

def has_guidance(x):
    if isinstance(x, dict):
        return ('guidance' in x) or any(has_guidance(v) for v in x.values())
    if isinstance(x, list):
        return any(has_guidance(v) for v in x)
    return False

def count_failures(o):
    arr = o.get('ci_failures') if isinstance(o, dict) else None
    if not isinstance(arr, list):
        return None
    b = sum(1 for i in arr if isinstance(i, dict) and i.get('blocking') is True)
    a = sum(1 for i in arr if isinstance(i, dict) and i.get('blocking') is False)
    return (len(arr), b, a)

parsed = {k: parse_single(p) for k, p in files.items()}
print('single_json_object')
for k, (_, single) in parsed.items():
    print(f'{k}={single}')

print('has_guidance')
for k, (o, _) in parsed.items():
    print(f'{k}={has_guidance(o)}')

print('ci_failure_counts')
for k in ['checkpoint_basic','checkpoint_off','stale_basic','stale_off','doctor_basic','doctor_off']:
    o, _ = parsed[k]
    print(f'{k}={count_failures(o)}')

print('exit_code_fields')
for k in ['checkpoint_basic','checkpoint_off','stale_basic','stale_off','doctor_basic','doctor_off']:
    o, _ = parsed[k]
    print(f"{k}:command={o.get('command')},status={o.get('status')},exit_code={o.get('exit_code')}")

n, _ = parsed['next_json']
print('next_summary')
print(f"command={n.get('command')}")
print(f"status={n.get('status')}")
print(f"writes_files={n.get('writes_files')}")
print(f"llm_used={n.get('llm_used')}")
items = n.get('items') if isinstance(n.get('items'), list) else []
print(f'items_count={len(items)}')
print(f"items_have_blocking={all(isinstance(i, dict) and ('blocking' in i) for i in items)}")
