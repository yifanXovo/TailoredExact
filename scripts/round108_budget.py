"""Supplemental corrected prelaunch budget check; no solver or helper mutation."""
import argparse, json, time
from pathlib import Path

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def check(root,label,additional_starts,required_seconds):
    root=Path(root).resolve();out=root/'results/unified_exact_round108'
    launches=list((out/'fees').glob('*/launch.json'));receipts=list((out/'fees').glob('*/receipt.json'))
    corrections=[read(p) for p in sorted((out/'fee_corrections').glob('*.json'))]
    originals=sum(read(p)['conservative_process_starts'] for p in launches)
    additional=sum(r['additional_conservative_starts'] for r in corrections)
    seconds=sum(read(p)['outer_seconds'] for p in receipts)
    unclosed=[p.parent.name for p in launches if not (p.parent/'receipt.json').exists()]
    assert not unclosed and originals+additional+additional_starts<=48 and seconds+required_seconds<=80000
    directory=out/'engineering'/label;directory.mkdir(parents=True,exist_ok=False)
    value=dict(corrected_conservative_starts=originals+additional,original_declared_starts=originals,
        retained_additional_driver_correction=additional,requested_additional_starts=additional_starts,
        outer_solver_fee_seconds=seconds,required_reserved_seconds=required_seconds,
        remaining_starts=48-originals-additional,remaining_outer_seconds=80000-seconds,
        unclosed=unclosed,passed=True,engineering=True,Optimize=0,IIS=0,new_solver_starts=0,
        checked_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        supersedes_frozen_wrapper_declaration_only_budget_arithmetic=True,frozen_performance_helpers_changed=False)
    with (directory/'corrected_budget.json').open('x',encoding='utf-8',newline='\n') as file:
        json.dump(value,file,indent=2,allow_nan=False);file.write('\n')
    print(json.dumps(value,allow_nan=False));return value

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--label',required=True)
    p.add_argument('--additional-starts',required=True,type=int);p.add_argument('--required-seconds',required=True,type=float)
    a=p.parse_args();check(a.root,a.label,a.additional_starts,a.required_seconds)
