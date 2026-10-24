"""Narrow author publication check using the independent existing reader."""
from pathlib import Path
import hashlib, json, sys, time

ROOT=Path.cwd().resolve()
assert (ROOT/'scripts/round132_portable_check.py').is_file()
OUT=ROOT/'results/unified_exact_round132'
sys.path.insert(0,str(ROOT/'scripts'))
from round132_release import idle
import round132_portable_check as checker
assert checker.ROOT==ROOT
receipt_path=OUT/'review/carrier_progress_author_check.json'
assert not receipt_path.exists(),'Preserve the existing author check receipt'

idle()
pack=checker.read(OUT/'delivery_costs/pack01/receipt.json')
assert pack['exit_code']==0 and pack['error'] is None and pack['exit_observed']
assert checker.read(OUT/'review/final_independent_evidence.json')['status']=='PASS'
assert checker.read(OUT/'review/publication_scan.json')['status']=='PASS'
assert len(checker.read(OUT/'raw_archive_manifest.json')['archives'])==34
tick=time.perf_counter()
rows,_=checker.frozen_contract(OUT)
runtime=checker.initialize_standard_runtime()
with checker.readonly_boundary():
    core,*_=checker.reader_imports()
    evidence=checker.progress_and_history(OUT,rows,core)
assert len(evidence['actual_current_native_progress'])==36
assert all(r['corresponding_current_carrier'] for r in evidence['actual_current_native_progress'])
assert len(evidence['historical_fleets'])==2
value=dict(status='PASS',scope='Author publication check of36 actual compact progress files against completed carrier member indexes, plus the existing two small historical fleet dependencies; not another full formal evidence replay.',
    checker_SHA=hashlib.sha256((ROOT/'scripts/round132_portable_check.py').read_bytes()).hexdigest(),
    original_runtime_setup=runtime,seconds=time.perf_counter()-tick,
    Optimize=0,native_starts=0,compilation=0,**evidence)
receipt_path.write_bytes((json.dumps(value,indent=2,allow_nan=False)+'\n').encode())
print(json.dumps(dict(status='PASS',actual_current_progress=36,small_historical_fleets=2,seconds=value['seconds'])))
