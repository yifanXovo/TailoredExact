"""Supply exact completed-run metadata to the fresh isolated review root."""
import argparse, hashlib, json, sys, time
from pathlib import Path

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def run(root,recovered):
    start=time.perf_counter();root=Path(root).resolve();recovered=Path(recovered).resolve()
    out=root/'results/unified_exact_round108';here=Path(__file__).resolve().parent
    target=recovered/'results/unified_exact_round108/review/public_primary_comparison_metadata01'
    target.mkdir(exist_ok=False);records=[]
    paths={'public_comparison_receipt.json':out/'public_comparison_receipt.json',
        'public_restore_receipt.json':out/'public_restore_receipt.json',
        'public_rebuild_wrapper_receipt.json':out/'engineering/public_rebuild01/receipt.json',
        'public_rebuild_launch.json':out/'engineering/public_rebuild01/launch.json',
        'public_rebuild_stdout.log':out/'engineering/public_rebuild01/stdout.log',
        'public_rebuild_stderr.log':out/'engineering/public_rebuild01/stderr.log'}
    for name,source in paths.items():
        data=source.read_bytes();destination=target/name
        with destination.open('xb') as stream:stream.write(data)
        assert sha(source)==sha(destination)
        records.append(dict(source=str(source),destination=str(destination),bytes=len(data),SHA256=sha(destination)))
    receipt=dict(command=[sys.executable,str(Path(__file__).resolve()),'--root',str(root),'--recovered-root',str(recovered)],
        exit_code=0,seconds=time.perf_counter()-start,source_SHA=sha(__file__),files=records,
        scope='Exact completed public reconstruction metadata; no raw carrier or rebuilt output mutation',
        raw_evidence_read=False,summary_reconstruction=False,engineering=True,Optimize=0,IIS=0,conservative_solver_starts=0)
    write(here/'receipt.json',receipt);write(target/'metadata_copy_receipt.json',receipt)
    print(json.dumps(dict(exit_code=0,copied_files=len(records),target=str(target),rebuilt=str(recovered/'rebuilt'))))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--recovered-root',required=True)
    args=parser.parse_args();run(args.root,args.recovered_root)
