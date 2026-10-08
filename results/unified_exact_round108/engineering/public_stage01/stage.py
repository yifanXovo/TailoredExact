"""Stage an explicit public result set, never the oversized local archives."""
import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path

ROUND='results/unified_exact_round108'
LIMIT=95*1024*1024
FORBIDDEN={'.exe','.dll','.lic','.pfx','.pem','.key','.pyc','.obj','.o'}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def run(root):
    start=time.perf_counter();root=Path(root).resolve();out=root/ROUND;here=Path(__file__).resolve().parent
    manifest=read(out/'compact_evidence/manifest.json');comparison=read(out/'public_comparison_receipt.json')
    assert comparison['comparison']['passed'] is True
    assert read(out/'review/public_isolated_review01.json')['decision']=='ACCEPT'
    assert read(out/'selection_decision.json')['stage']=='SELECT_MB_FOR_BROAD_EVALUATION'
    assert (out/'final_report.md').is_file() and (out/'engineering/public_pr_body01/receipt.json').is_file()
    files=set(root.glob('scripts/round108*.py'))
    files.update(p for p in out.iterdir() if p.is_file() and p.suffix in {'.md','.json'})
    files.update(p for p in (out/'reports_final').iterdir() if p.is_file())
    files.update(p for p in (out/'review').iterdir() if p.is_file() and p.suffix in {'.py','.md','.json','.diff'})
    for directory in (out/'review').glob('public_*'):
        if directory.is_dir():files.update(p for p in directory.rglob('*') if p.is_file())
    for directory in (out/'engineering').glob('public_*'):
        if directory.is_dir():files.update(p for p in directory.rglob('*') if p.is_file())
    files.update(p for p in (out/'engineering/final_report01').rglob('*') if p.is_file())
    files.add(out/'compact_evidence/manifest.json')
    files.update(out/'compact_evidence'/p['path'] for p in manifest['parts'])
    if not manifest['parts']:files.add(out/'compact_evidence'/manifest['archive_path'])
    files.update(p for p in (root/'reference/round108_confirmation').rglob('*') if p.is_file())
    files={p for p in files if '__pycache__' not in p.parts}
    records=[]
    for path in sorted(files):
        assert path.is_relative_to(root) and path.is_file() and not path.is_symlink()
        assert path.suffix.lower() not in FORBIDDEN and path.stat().st_size<LIMIT
        assert 'compact_evidence_failed01' not in path.parts
        assert path!=out/'compact_evidence/evidence.tar.gz' or not manifest['parts']
        records.append(dict(path=path.relative_to(root).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))
    write(here/'proposed_public_paths.json',records)
    selected=[r['path'] for r in records]+[(here/'proposed_public_paths.json').relative_to(root).as_posix()]
    command=['git','add','--pathspec-from-file=-','--pathspec-file-nul']
    process=subprocess.run(command,cwd=root,input=b''.join(p.encode('utf-8')+b'\0' for p in selected),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert process.returncode==0,process.stderr.decode(errors='replace')
    diff=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=root)
    changed=[p.decode('utf-8') for p in diff.split(b'\0') if p]
    assert all(p.startswith(('scripts/round108','results/unified_exact_round108/','reference/round108_confirmation/')) for p in changed)
    receipt=dict(command=[sys.executable,str(Path(__file__).resolve()),'--root',str(root)],
        exit_code=0,seconds=time.perf_counter()-start,source_SHA=sha(__file__),git_add_command=command,
        selected_paths=len(selected),new_or_changed_index_paths=len(changed),selected_bytes=sum(r['bytes'] for r in records),
        staged_paths=changed,public_path_manifest_SHA=sha(here/'proposed_public_paths.json'),
        public_path_manifest_exact_SHA256=True,large_combined_and_failed_archives_not_staged=True,
        engineering=True,Optimize=0,IIS=0,conservative_solver_starts=0)
    write(here/'receipt.json',receipt)
    subprocess.run(['git','add','--',(here/'receipt.json').relative_to(root).as_posix()],cwd=root,check=True)
    print(json.dumps({k:receipt[k] for k in ['exit_code','seconds','selected_paths','new_or_changed_index_paths','selected_bytes']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);args=parser.parse_args();run(args.root)
