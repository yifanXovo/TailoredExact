"""Targeted exact-SHA history scan and exact old-input-byte comparison.

This pre-admission scan reads only explicitly declared retained history roots.
It never solves, decompresses historical campaigns or infers performance.
It discloses unread historical archives instead of claiming a private history.
"""
from pathlib import Path
import argparse, csv, hashlib, json, re, subprocess, sys, time, traceback

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def obj(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--history-root',action='append',required=True);p.add_argument('--rg',default='rg')
    args=p.parse_args();root=Path(args.root).resolve();review=root/'results/unified_exact_round109/review';dest=review/'eligibility_scan01';dest.mkdir(exist_ok=False)
    start=time.perf_counter();roles=obj(root/'results/unified_exact_round109/input_manifest.json')['roles'];needles=dest/'exact_input_SHA.txt'
    needles.write_text('\n'.join(r['input_sha256'] for r in roles)+'\n',encoding='ascii')
    histories=[Path(x).resolve() for x in args.history_root];reads=[];matches=[];inputmatches=[];scans=[];error=None
    save(dest/'launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=sha(__file__),input_manifest_SHA=sha(root/'results/unified_exact_round109/input_manifest.json'),history_roots=list(map(str,histories)),Optimize=0,native_environment=0,started_unix=time.time()))
    try:
        bysha={r['input_sha256']:r for r in roles};assert len(bysha)==len(roles)==12
        for i,history in enumerate(histories,1):
            assert history.is_dir() and history!=root
            paths=[history/x for x in ('results','reference') if (history/x).is_dir()]
            command=[args.rg,'-l','--fixed-strings','--file',str(needles),'--glob','*.json','--glob','*.jsonl','--glob','*.csv','--glob','*.md',*map(str,paths)]
            proc=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=600)
            stdout=dest/f'history{i:02d}_stdout.txt';stderr=dest/f'history{i:02d}_stderr.txt';stdout.write_bytes(proc.stdout);stderr.write_bytes(proc.stderr)
            assert proc.returncode in (0,1),(command,proc.returncode,proc.stderr.decode('utf-8',errors='replace'))
            scans.append(dict(root=str(history),command=command,exit_code=proc.returncode,stdout_SHA=sha(stdout),stderr_SHA=sha(stderr),matched_paths=proc.stdout.decode('utf-8-sig').splitlines(),scope='retained JSON/JSONL/CSV/Markdown under results and reference; compressed historical archives not decompressed'))
            for retained in proc.stdout.decode('utf-8-sig').splitlines():
                path=Path(retained).resolve();assert path.is_relative_to(history);raw=path.read_bytes();reads.append(dict(path=str(path),SHA=hashlib.sha256(raw).hexdigest()))
                text=raw.decode('utf-8-sig',errors='replace')
                for digest,role in bysha.items():
                    if digest in text:matches.append(dict(id=role['id'],input_SHA=digest,path=str(path),T_seconds=role['T_seconds'],**{'lambda':role['lambda']},pickup_seconds=60,drop_seconds=60))
            # Reference inputs use a strict station-count/vehicle header. Hash
            # only syntactically plausible exact-size input files; JSON files
            # and unrelated engineering prose are not candidate input bytes.
            plausible=0
            for path in (history/'reference').rglob('*.txt'):
                with path.open('rb') as f:header=f.readline(256)
                if not re.fullmatch(rb'(?:20|50|100)\s+\d+\s+\[.*\]\s*',header):continue
                plausible+=1;digest=sha(path)
                if digest in bysha:inputmatches.append(dict(id=bysha[digest]['id'],path=str(path),SHA=digest))
            scans[-1]['independently_hashed_plausible_reference_inputs']=plausible
        # A new generated source snapshot of a would-be role is not a measured
        # arm by itself. All actual matches must be inspected, never dismissed.
        assert not matches and not inputmatches,('retained exact candidate history requires manual scope/tuple review',matches,inputmatches)
        initial=obj(root/'results/unified_exact_round109/baseline.json')
        assert initial['active_solver_processes_before_start']==0
        assert not (root/'results/unified_exact_round109/campaign/summary.jsonl').exists()
        value=dict(decision='ACCEPT',eligible={r['id']:True for r in roles},exact_main_denominator=12,
            frozen_identity_tuples=[dict(id=r['id'],input_SHA=r['input_sha256'],T_seconds=r['T_seconds'],**{'lambda':r['lambda']},pickup_seconds=60,drop_seconds=60) for r in roles],
            scans=scans,exact_SHA_matches=matches,exact_reference_byte_matches=inputmatches,read_bindings=reads,
            at_initial_freeze_only=True,new_formal_measurements_do_not_revoke_initial_eligibility=True,
            scope_limitation='Retained explicit local uncompressed history and original reference inputs; unopened private bytes and historical compressed archives are not claimed reread.',
            current_source_commit=initial['base_head'],input_manifest_SHA=sha(root/'results/unified_exact_round109/input_manifest.json'),source_SHA=sha(__file__),
            Optimize=0,LP_solve=0,native_environment=0,production_edits=0,elapsed_engineering_seconds=time.perf_counter()-start)
        save(review/'input_eligibility.json',value);save(dest/'audit.json',value)
    except Exception:
        error=traceback.format_exc();save(dest/'audit.json',dict(decision='HOLD',error=error,scans=scans,matches=matches,inputmatches=inputmatches,Optimize=0))
    save(dest/'receipt.json',dict(exit_code=int(error is not None),error=error,source_SHA=sha(__file__),audit_SHA=sha(dest/'audit.json'),elapsed_engineering_seconds=time.perf_counter()-start,cwd=str(Path.cwd())))
    print(json.dumps(dict(decision='ACCEPT' if error is None else 'HOLD',error=error,scanned_roots=len(scans),matches=len(matches),inputmatches=len(inputmatches)),ensure_ascii=False),flush=True)
    if error:sys.exit(1)
if __name__=='__main__':main()
