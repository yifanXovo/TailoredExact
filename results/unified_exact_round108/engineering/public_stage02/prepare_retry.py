"""Preserve the ignored-log stage failure and prepare the exact allowlist retry."""
import hashlib,json,sys,time
from pathlib import Path

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
here=Path(__file__).resolve().parent;root=here.parents[3];out=root/'results/unified_exact_round108'
start=time.perf_counter();old=out/'engineering/public_stage01/stage.py'
source=old.read_bytes();needle=b"command=['git','add','--pathspec-from-file=-','--pathspec-file-nul']"
assert source.count(needle)==1
new=here/'stage.py'
with new.open('xb') as stream:stream.write(source.replace(needle,b"command=['git','add','--force','--pathspec-from-file=-','--pathspec-file-nul']"))
with (here/'failed_stage01_source.py').open('xb') as stream:stream.write(source)
assert sha(old)==sha(here/'failed_stage01_source.py')
failure=dict(actual_command=[sys.executable,'results/unified_exact_round108/engineering/public_stage01/stage.py','--root',str(root)],
    exit_code=1,observed_exec_command_seconds=5.4598399,seconds_scope='Enclosing exec_command observation; no exact script-only failure timer was captured',
    source_SHA=sha(old),proposed_path_manifest_SHA=sha(out/'engineering/public_stage01/proposed_public_paths.json'),
    reason='git add rejected explicitly selected engineering stdout/stderr logs under existing ignore rules',
    partial_index_possible=True,repair='Force-add only the same explicitly selected public allowlist; no ignore/config changes',
    engineering=True,Optimize=0,IIS=0,conservative_solver_starts=0)
with (here/'failed_stage01_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(failure,stream,indent=2);stream.write('\n')
value=dict(command=[sys.executable,str(Path(__file__).resolve())],exit_code=0,seconds=time.perf_counter()-start,
    source_SHA=sha(__file__),new_stage_source_SHA=sha(new),original_stage_source_preserved=True,engineering=True,Optimize=0,IIS=0)
with (here/'prepare_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
print(json.dumps(dict(exit_code=0,original_source_SHA=sha(old),retry_source_SHA=sha(new))))
