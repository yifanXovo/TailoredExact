"""Archive completed stage-2 evidence and exact development source, no Optimize."""
import hashlib
import json
import subprocess
import time
import zipfile
from pathlib import Path
from round96_prepare import ROOT,OUT,read,write,sha

def main():
    started=time.perf_counter();dest=OUT/'stage2_evidence.zip';assert not dest.exists()
    folders=['route_order','route_order_audit','reorder_qualification','reorder_F5_final','route_order_cli',
             'external/raw/01_H1_P-GRB','external_report_h1_p']
    files=[]
    for folder in folders:files.extend(p for p in (OUT/folder).rglob('*') if p.is_file())
    files += [p for p in OUT.iterdir() if p.is_file() and (
        p.name.startswith(('route_order_','reorder_','external_run_01')))]
    files += [OUT/'external/summary.jsonl',OUT/'external/processes.jsonl',OUT/'external/cross_arm_H1_1.json']
    gate=read(OUT/'route_order_build_gate.json');members=[];sources=[]
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(set(files)):
            data=path.read_bytes();name=path.relative_to(ROOT).as_posix();archive.writestr(name,data)
            members.append(dict(name=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        for path,expected in gate['source_hashes'].items():
            data=(ROOT/path).read_bytes();source='current_bytes'
            if hashlib.sha256(data).hexdigest()!=expected:
                data=subprocess.check_output(['git','show','d42c96f18:'+path],cwd=ROOT);source='git:d42c96f18'
            assert hashlib.sha256(data).hexdigest()==expected,path
            name='development_source/'+path;archive.writestr(name,data)
            members.append(dict(name=name,bytes=len(data),sha256=expected));sources.append(dict(path=path,source=source,sha256=expected))
    with zipfile.ZipFile(dest) as archive:
        assert set(archive.namelist())=={r['name'] for r in members}
        for r in members:assert hashlib.sha256(archive.read(r['name'])).hexdigest()==r['sha256']
    write(OUT/'stage2_archive.json',dict(path=dest.relative_to(ROOT).as_posix(),sha256=sha(dest),
        bytes=dest.stat().st_size,members=members,development_sources=sources,verified=True,
        optimizer_calls=0,elapsed_before_index=time.perf_counter()-started))
    print(json.dumps(dict(bytes=dest.stat().st_size,members=len(members),verified=True)))

if __name__=='__main__':main()
