"""Pure engineering: exact-byte package/freeze checks, no numerical replay."""
import ast,gzip,hashlib,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round103'
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def main(package,label):
    manifest=OUT/package/'manifest.json';m=read(manifest);checked={}
    for c in m['copies']:
        source,target=ROOT/c['source'],ROOT/c['target']
        assert sha(source)==c['source_sha256'],source
        if c['target'] not in checked:
            assert sha(target)==c['sha256'],target
            h=hashlib.sha256()
            opener=gzip.open if c['compression'] else open
            with opener(target,'rb') as f:
                for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
            checked[c['target']]=h.hexdigest()
        assert checked[c['target']]==c['source_sha256'],target
    freeze=read(OUT/'production_freeze.json')
    for field in ['source_bindings','runners']:
        for p,digest in freeze[field].items():assert sha(ROOT/p)==digest,(field,p)
    for name,field in [('ExactEBRP.exe','PE_sha256'),('Round103HullOracle.exe','oracle_PE_sha256'),('Round65ReferenceBuild.exe','reference_PE_sha256')]:
        assert sha(ROOT/'build/research/round103-hull-v1'/name)==freeze[field],name
    assert sha('D:/gurobi1302/win64/bin/gurobi130.dll')==freeze['DLL_sha256']
    for p,digest in read(OUT/'baseline.json')['protected_files'].items():assert sha(ROOT/p)==digest,p
    for p in (ROOT/'scripts').glob('round103*.py'):ast.parse(p.read_text(encoding='utf-8'))
    for field,file in [('production_freeze_sha256','production_freeze.json'),('confirmation_freeze_sha256','confirmation_freeze.json'),('stage_decision_sha256','stage_decision.json')]:
        assert read(OUT/'final_decision.json')[field]==sha(OUT/file),file
    result=dict(passed=True,manifest_sha256=sha(manifest),source_records=len(m['copies']),
        unique_files=len(checked),byte_exact=True,source_and_explicit_frozen_runners_unchanged=True,
        protected_user_files_unchanged=True,Optimize_calls=0,DP_calls=0,model_reads=0,
        scope='Byte packaging/freeze preservation and Python syntax only; no mathematical certificate audit or experimental reader')
    with (OUT/(label+'.json')).open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
