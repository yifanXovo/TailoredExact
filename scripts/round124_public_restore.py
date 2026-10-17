"""One anonymous, pinned, finite public-file restore and arithmetic rebuild.

This helper downloads only the manifest's small allowlisted text dependencies.
It never downloads campaigns, archives, runtime binaries or literature PDFs.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath
from urllib.parse import quote

PREFIX = "results/unified_exact_round124/"
MANIFEST = PREFIX + "public_manifest.json"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--commit",required=True)
    ap.add_argument("--manifest-sha",required=True)
    ap.add_argument("--destination",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    args=ap.parse_args()
    start=time.perf_counter()
    dest=args.destination.resolve()
    allowed=Path("E:/codes/ExactEBRP-work/restore").resolve()
    assert dest.is_relative_to(allowed) and dest != allowed
    assert not dest.exists(), "Require a genuinely fresh absent restoration root"
    assert len(args.commit)==40 and all(x in "0123456789abcdef" for x in args.commit)
    dest.mkdir(parents=True)
    events=[]
    curl=Path(os.environ["SystemRoot"])/"System32/curl.exe"
    def fetch(rel,expected_sha=None,expected_size=None):
        p=PurePosixPath(rel)
        assert not p.is_absolute() and ".." not in p.parts and "\\" not in rel
        assert rel.startswith(PREFIX) or rel in ["scripts/round124_derive.py","scripts/round124_prepare.py","scripts/round124_public_restore.py"]
        assert p.suffix.lower() in [".md",".json",".csv",".bib",".txt",".py"] or p.name==".gitattributes"
        target=dest/Path(*p.parts)
        assert target.resolve().is_relative_to(dest)
        target.parent.mkdir(parents=True,exist_ok=True)
        url="https://raw.githubusercontent.com/yifanXovo/TailoredExact/"+args.commit+"/"+quote(rel,safe="/")
        t=time.perf_counter()
        run=subprocess.run([str(curl),"-q","--fail","--location","--silent","--show-error",
                            "--proto","=https","--proto-redir","=https","--max-time","60",
                            "--output",str(target),url],capture_output=True,text=True)
        event={"path":rel,"pid_scope":"one observed completed system curl process",
               "exit_code":run.returncode,"elapsed_seconds":time.perf_counter()-t}
        events.append(event)
        assert run.returncode==0,run.stderr[:500]
        data=target.read_bytes()
        assert len(data)<2_000_000
        if expected_sha:assert sha(data)==expected_sha,(rel,"hash")
        if expected_size is not None:assert len(data)==expected_size,(rel,"size")
        event.update(bytes=len(data),sha256=sha(data))
        return data
    manifest=json.loads(fetch(MANIFEST,args.manifest_sha))
    assert manifest["solver_processes_required"]==0 and manifest["optimization_calls_required"]==0
    assert len(manifest["files"])<=80
    for record in manifest["files"]:
        fetch(record["path"],record["sha256"],record["bytes"])
    generated=[PREFIX+"manuscript.md",PREFIX+"tables/complete_results.md"]
    generated += [PREFIX+"tables/"+n for n in ["r122_arms.csv","r122_pairs.csv","r123_arms.csv","r123_pairs.csv","r123_checkpoints.csv"]]
    before={p:(dest/p).read_bytes() for p in generated}
    old=json.loads((dest/PREFIX/"arithmetic_checks.json").read_text(encoding="utf-8"))
    # The reconstructed arithmetic checker is run under a Python audit boundary:
    # no process launches, network sockets, or solver imports from that checker.
    code="""import sys,runpy
def guard(event,args):
    if event.startswith(('subprocess.','socket.','os.system','os.spawn')):
        raise RuntimeError('forbidden arithmetic-check event: '+event)
    if event=='import' and args[0].split('.')[0] in {'gurobipy','cplex','ortools','scipy','pulp'}:
        raise RuntimeError('forbidden solver import')
sys.addaudithook(guard)
sys.argv=[sys.argv[1],'--root',sys.argv[2]]
runpy.run_path(sys.argv[0],run_name='__main__')
"""
    t=time.perf_counter()
    run=subprocess.run([sys.executable,"-X","utf8","-B","-c",code,str(dest/"scripts/round124_derive.py"),str(dest)],
                       capture_output=True,text=True,encoding="utf-8")
    assert run.returncode==0,run.stderr
    rebuild_seconds=time.perf_counter()-t
    assert all((dest/p).read_bytes()==data for p,data in before.items())
    new=json.loads((dest/PREFIX/"arithmetic_checks.json").read_text(encoding="utf-8"))
    for d in [old,new]:d.pop("elapsed_seconds")
    assert old==new,"Typed arithmetic core changed"
    receipt={"science_commit_A":args.commit,"anonymous_public_HTTPS":True,
             "TLS_verification":"system curl default certificate/hostname checks; no credentials/config/insecure flags",
             "manifest_sha256":args.manifest_sha,"fresh_root":str(dest),"transfers":events,
             "downloaded_file_count":len(events),"downloaded_bytes":sum(e["bytes"] for e in events),
             "regenerated_files_byte_equal":generated,"arithmetic_typed_equal_except_measured_elapsed":True,
             "checker_python_audit_guard":"subprocess/network/solver imports prohibited; not an OS sandbox",
             "rebuild_seconds":rebuild_seconds,"elapsed_seconds":time.perf_counter()-start,
             "solver_processes_started":0,"optimization_calls":0,"production_compilations":0,
             "full_prior_raw_or_carrier_opened":False,"checker_stdout":run.stdout.strip()}
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({k:receipt[k] for k in ["downloaded_file_count","downloaded_bytes","rebuild_seconds","elapsed_seconds"]}))

if __name__=="__main__":main()
