"""Preserve the failed post-seal audit before a read-only serialization repair."""
from pathlib import Path
import json,hashlib,shutil,datetime

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round127'
D=OUT/'tiny/07_SM-B10-B_S0_R1/raw/01_SM-B10-B_S0_R1_MB'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

target=OUT/'review/tiny07_failure_snapshot'
target.mkdir(exist_ok=False)
copied={}
for name in ['audit.json','round120_model_contracts.json','call_log_views.json','round120_extended_verification.json']:
    source=D/name
    if source.exists():
        shutil.copyfile(source,target/name)
        assert sha(source)==sha(target/name)
        copied[name]=sha(source)
seal=read(D/'producer_seal.json')
assert seal['native_stopped_no_reentry'] and seal['required_outputs_closed']
for name,h in seal['required_SHA'].items():assert sha(D/name)==h
producer=read(D/'producer_receipt.json')
assert producer['producer_seal_SHA']==sha(D/'producer_seal.json')
fee=OUT/'fees/tiny_07_SM-B10-B_S0_R1'
evidence=dict(status='FAILURE_EVIDENCE_PRESERVED',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    original_producer_receipt=producer,producer_receipt_SHA=sha(D/'producer_receipt.json'),
    producer_seal_SHA=sha(D/'producer_seal.json'),original_producer_required_SHA=seal['required_SHA'],
    copied_failed_verification_files=copied,
    original_native_creation=read(D/'child_process_origin.json'),
    H_initial_SHA=sha(D/'hga.csv.exchange/initial.json'),H_final_SHA=sha(D/'hga.csv.exchange/final.json'),
    failed_fee_receipt=read(fee/'receipt.json'),failed_stderr_SHA=sha(fee/'stderr.log'),
    raw_outputs_changed=False,Optimize=0,production_or_parameter_changes=False,
    scope='Only preserves the failed verification state; physical equivalence and complete proof admission still require review.')
(target/'preservation.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=evidence['status'],copied_files=list(copied),T_produce=producer['T_produce'],Optimize=0)))
