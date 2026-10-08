"""Synthetic only: test public dependency containment in candidate restorer."""
import argparse, gzip, hashlib, io, json, runpy, sys, tarfile, time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True);a=p.parse_args()
root=Path(a.root).resolve();dest=Path(a.out).resolve();assert dest.is_relative_to(root/'results/unified_exact_round108/review');dest.mkdir(exist_ok=False)
source=root/'scripts/round108_public.py';candidate=hashlib.sha256(source.read_bytes()).hexdigest();assert candidate=='62333f124a980e1abe07adda886f389aecc872fde67d89ada5483c0a58be636d'
ns=runpy.run_path(str(source));api=ns['restore'];sha=ns['sha'];tick=time.perf_counter()
public=dest/'public';package=public/ns['ROUND']/'compact_evidence';package.mkdir(parents=True);(public/'reference').mkdir()
reader=b'# synthetic only, never executed\n';archive=package/'evidence.tar.gz'
with archive.open('xb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz,tarfile.open(fileobj=gz,mode='w|') as t:
    info=tarfile.TarInfo('scripts/round108_reader.py');info.size=len(reader);t.addfile(info,io.BytesIO(reader))
outside=dest/'outside.txt';outside.write_bytes(b'exact synthetic public dependency outside the supplied public root\n')
manifest=dict(archive_path='evidence.tar.gz',archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,parts=[],single_blob_limit_bytes=4096,part_bytes=2048,
    files=[dict(path='scripts/round108_reader.py',bytes=len(reader),sha256=hashlib.sha256(reader).hexdigest())],
    public_dependencies=[dict(path='reference/../../outside.txt',bytes=outside.stat().st_size,sha256=sha(outside))])
(package/'manifest.json').write_text(json.dumps(manifest)+'\n',encoding='utf-8')
error=None;rejected=False
try:api(public,dest/'restored',4096,2048)
except Exception as e:rejected=True;error=type(e).__name__+': '+str(e)
result=dict(decision='ACCEPT' if rejected else 'HOLD',case='dependency path may not escape supplied public root',expected='reject',actual='rejected' if rejected else 'accepted',exception=error,
    actual_command=[sys.executable,*sys.argv],explicit_read_root=str(root),source_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),candidate_source_SHA=candidate,
    input_manifest_SHA=sha(package/'manifest.json'),outside_synthetic_path=str(outside),unexpected_success_receipt=(dest/'restored/restore_receipt.json').exists(),
    engineering_seconds=time.perf_counter()-tick,exit_code=0 if rejected else 1,Optimize=0,LP_solve=0,native_environment=0,compiler=0)
with (dest/'receipt.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['decision','actual','candidate_source_SHA','unexpected_success_receipt','exit_code']}))
if not rejected:sys.exit(1)
