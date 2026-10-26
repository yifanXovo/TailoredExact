"""Exact post-audit delivery only. Never launches a solver or reruns math."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import sys
import time
import traceback

SOURCE = Path('E:/codes/ExactEBRP-round111-public-restored01/results/unified_exact_round111/review')
TARGET = Path('E:/codes/ExactEBRP-round111/results/unified_exact_round111/public_validation')


def digest(raw):return hashlib.sha256(raw).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write('\n')


def main():
    begin=time.perf_counter()
    source,target=SOURCE.resolve(),TARGET.resolve()
    assert source.is_dir() and target.is_dir()
    evidence=source/'public_raw01'
    original=json.loads((evidence/'receipt.json').read_text(encoding='utf-8'))
    assert original['exit_code']==0 and original['mode']=='public'
    assert Path(original['cwd']).resolve()==source.parents[2]
    assert original['Optimize']==original['native_environment']==0
    assert digest((evidence/'audit.json').read_bytes())==original['audit_SHA']
    delivery=target/'independent_delivery01';delivery.mkdir(exist_ok=False)
    stdout,stderr=delivery/'stdout.log',delivery/'stderr.log'
    stdout.open('x').close();stderr.open('x').close()
    own=Path(__file__).resolve();raw=own.read_bytes()
    (delivery/own.name).open('xb').write(raw)
    write(delivery/'launch.json',dict(cwd=str(Path.cwd().resolve()),argv=sys.argv,PID=os.getpid(),
        source_root=str(source),target_root=str(target),source_SHA=digest(raw),
        started_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),engineering=True,native_processes=0,Optimize=0))
    records=[];code=1
    try:
        candidates=[(p,target/'public_raw01'/p.relative_to(evidence)) for p in sorted(evidence.rglob('*')) if p.is_file()]
        candidates.append((source/'public_review_provenance.md',target/'public_review_provenance.md'))
        for src,dst in candidates:
            assert src.resolve().is_relative_to(source) and dst.resolve().is_relative_to(target)
            data=src.read_bytes()
            dst.parent.mkdir(parents=True,exist_ok=True)
            with dst.open('xb') as file:file.write(data)
            assert dst.read_bytes()==data
            records.append(dict(source=str(src),destination=str(dst),bytes=len(data),SHA=digest(data)))
        write(delivery/'copied_files.json',records)
        stdout.write_text('exact delivery PASS: '+str(len(records))+' files\n',encoding='utf-8',newline='\n')
        print('exact delivery PASS: '+str(len(records))+' files',flush=True)
        code=0
    except Exception:
        error=traceback.format_exc();stderr.write_text(error,encoding='utf-8',newline='\n');traceback.print_exc()
    write(delivery/'receipt.json',dict(exit_code=code,seconds=time.perf_counter()-begin,
        source_root=str(source),target_root=str(target),public_audit_SHA=original['audit_SHA'],
        source_SHA=digest(raw),copied_files=len(records),copied_bytes=sum(r['bytes'] for r in records),
        stdout_SHA=digest(stdout.read_bytes()),stderr_SHA=digest(stderr.read_bytes()),
        audit_execution_already_completed=True,delivery_only=True,engineering=True,native_processes=0,Optimize=0))
    return code


if __name__=='__main__':raise SystemExit(main())
