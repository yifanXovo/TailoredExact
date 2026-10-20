"""One post-seal verification attempt; this entry point never executes a solver."""
from pathlib import Path
import datetime,hashlib,json,shutil,sys,traceback

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from round127_evidence import verify

OUT=ROOT/'results/unified_exact_round127'
GROUP=OUT/'tiny/07_SM-B10-B_S0_R1'
D=GROUP/'raw/01_SM-B10-B_S0_R1_MB'

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')

attempt=OUT/'review/tiny07_readonly_verification_attempts'/sys.argv[1]
attempt.mkdir(parents=True,exist_ok=False)
preserved=read(OUT/'review/tiny07_failure_snapshot/preservation.json')
assert sha(D/'producer_receipt.json')==preserved['producer_receipt_SHA']
assert sha(D/'producer_seal.json')==preserved['producer_seal_SHA']
assert not (D/'arm_total_receipt.json').exists(),'a closed original arm must not be verified a second time'
seal=read(D/'producer_seal.json')
assert seal['required_SHA']==preserved['original_producer_required_SHA']
fixed={name:sha(D/name) for name in seal['required_SHA']}
assert fixed==seal['required_SHA']
fixed.update({name:sha(D/name) for name in ['producer_receipt.json','producer_seal.json',
    'hga.csv.exchange/initial.json','hga.csv.exchange/final.json']})
identity=read(GROUP/'identity.json');launch=identity['launches'][0]
assert launch['method']=='MB' and launch['seed']==0 and Path(launch['destination'])==D
derived_names=['audit.json','round120_model_contracts.json','call_log_views.json',
    'round120_extended_verification.json','round127_empty_route_handoff.json',
    'independent_evidence.json','native_claims.json','claim_rejections.json',
    'audit_execution_metrics.json','postexit_audit_receipt.json',
    'verification_closeout.json','arm_total_receipt.json']
prior={};prior_dir=attempt/'preexisting_derived';prior_dir.mkdir()
# The inherited final audit intentionally uses exclusive writes. Preserve each
# prior derived file under this attempt before asking it to create fresh files.
# No sealed producer, native model, witness, H exchange or parameter file moves.
for name in derived_names:
    source=D/name;target=prior_dir/name
    if source.exists():
        assert source.resolve().is_relative_to(D.resolve())
        assert target.resolve().is_relative_to(attempt.resolve())
        digest=sha(source);source.rename(target);assert sha(target)==digest
        prior[name]=digest
write(attempt/'preexisting_derived_SHA256.json',prior)
status='FAILED';error=None
try:
    result=verify(launch,identity)
    assert result['passed'] is True
    assert read(D/'verification_closeout.json')['necessary_verification_complete'] is True
    assert read(D/'arm_total_receipt.json')['necessary_verification_complete'] is True
    status='PASS'
except BaseException:
    error=traceback.format_exc()
    (attempt/'exception.txt').write_text(error,encoding='utf-8')
    raise
finally:
    unchanged={name:sha(D/name)==digest for name,digest in fixed.items()}
    copied={}
    for name in derived_names:
        if (D/name).exists():
            shutil.copyfile(D/name,attempt/name);copied[name]=sha(attempt/name)
    write(attempt/'receipt.json',dict(status=status,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        original_producer_bytes_unchanged=unchanged,derived_files_SHA256=copied,
        prior_derived_files_preserved_SHA256=prior,
        original_T_produce=read(D/'producer_receipt.json')['T_produce'],
        recovery_wait_retained_in_T_verify_and_T_total=True,Optimize=0,
        verifier_source_SHA256=sha(ROOT/'scripts/round127_evidence.py'),error_recorded=error is not None))
    assert all(unchanged.values()),'post-seal producer mutation'
    print(json.dumps(dict(status=status,Optimize=0,original_bytes_unchanged=all(unchanged.values()),
        derived_files=list(copied))),flush=True)
