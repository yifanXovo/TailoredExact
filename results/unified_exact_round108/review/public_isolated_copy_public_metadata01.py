"""Copy only explicitly proposed public distribution metadata for final seal."""
import argparse, hashlib, json, sys, time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root).resolve();review=root/'results/unified_exact_round108/review'
dest=review/'public_isolated_copy_public_metadata01';dest.mkdir(exist_ok=False);tick=time.perf_counter()
rr=json.loads((root/'restore_receipt.json').read_text());public=Path(rr['public_root']).resolve()
assert public!=root and rr['public_files_only'] and not rr['original_workspace_reads']
targets=review/'public_primary_comparison_metadata01';records=[]
for rel,name in [('results/unified_exact_round108/compact_evidence/manifest.json','public_manifest.json'),('public_export_receipt.json','public_export_receipt.json')]:
    src=public/rel;dst=targets/name
    assert src.absolute()==src.resolve() and src.resolve().is_relative_to(public) and src.is_file() and not src.is_symlink()
    assert dst.resolve().is_relative_to(review) and not dst.exists()
    b=src.read_bytes();digest=hashlib.sha256(b).hexdigest()
    if name=='public_manifest.json':assert digest==rr['manifest_SHA']
    with dst.open('xb') as f:f.write(b)
    assert hashlib.sha256(dst.read_bytes()).hexdigest()==digest
    records.append(dict(source_proposed_public_path=str(src),destination=str(dst),bytes=len(b),SHA=digest,exact=True))
value=dict(actual_command=[sys.executable,*sys.argv],read_root=str(root),public_distribution_root=str(public),original_workspace_reads=False,public_metadata_only=True,source_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),files=records,exit_code=0,seconds=time.perf_counter()-tick,Optimize=0,LP_solve=0,native_environment=0,compiler=0)
with (dest/'receipt.json').open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n')
print(json.dumps(dict(exit_code=0,metadata_files=len(records),original_workspace_reads=False)))
