"""Conditional same-root transport-budget repair; no scientific-policy change.

This entry cannot run before a real transport-limit failure and a separate
independent admission. It loads the original public bootstrap byte-for-byte,
changes only its finite wall limits, and resumes the same failed owned root.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, sys, time

BOOTSTRAP_SHA='b8062780c069e252df5306d79fc5b1c22038d1adf4f0ec229cdaddc1cbca5aa8'
SCIENCE='e4c6f82316f8697c6dfcf59d3a0807619b7bcae8'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bootstrap',type=Path,required=True)
    parser.add_argument('--admission',type=Path,required=True)
    parser.add_argument('--commit',required=True)
    parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--resume',action='store_true',required=True)
    args=parser.parse_args();tick=time.perf_counter()
    assert args.commit==SCIENCE and args.resume and sha(args.bootstrap)==BOOTSTRAP_SHA
    gate=read(args.admission)
    assert gate['decision']=='ACCEPT_SAME_ROOT_BUDGET_EXTENSION_AFTER_REAL_LIMIT_FAILURE'
    assert gate['science_commit']==SCIENCE and gate['wrapper_SHA']==sha(__file__)
    assert gate['bootstrap_SHA']==BOOTSTRAP_SHA
    assert gate['prior_public_receipt_SHA']==sha(args.receipt)
    assert gate['prior_restore_state_SHA']==sha(args.destination/'restore_state.json')
    prior=read(args.receipt);state=read(args.destination/'restore_state.json')
    assert prior['status']==state['status']=='FAILED_PRESERVE_SAME_ROOT'
    assert 'finite public recovery limit exhausted' in prior['error'] and "'transport'" in prior['error']
    assert prior['science_commit']==state['commit']==SCIENCE
    assert state['initially_empty'] and state['destination']==str(args.destination.resolve())==gate['destination']
    assert state['cumulative_seconds']['transport']>=1799. and state['cumulative_seconds']['semantic']==0.
    assert gate['new_limits_seconds']==dict(total=7200.,transport=6000.,semantic=3600.)
    spec=importlib.util.spec_from_file_location('round133_original_public_bootstrap',args.bootstrap)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.BUDGETS==dict(total=7200.,transport=1800.,semantic=3600.)
    module.BUDGETS=dict(gate['new_limits_seconds'])
    binding=dict(science_commit=SCIENCE,wrapper_SHA=sha(__file__),bootstrap_SHA=BOOTSTRAP_SHA,
        admission_SHA=sha(args.admission),prior_public_receipt_SHA=sha(args.receipt),
        destination=str(args.destination.resolve()),only_wall_limits_changed=True,
        same_failed_owned_root=True,no_scientific_check_removed=True,Optimize=0,compile=0)
    target=args.receipt.parent/'review/public_budget_resume_execution.json'
    target.write_text(json.dumps(binding,indent=2)+'\n',encoding='utf-8')
    sys.argv=[str(args.bootstrap),'--commit',SCIENCE,'--destination',str(args.destination),
        '--receipt',str(args.receipt),'--resume']
    try:module.main()
    finally:
        binding.update(outer_wrapper_seconds=time.perf_counter()-tick,
            resulting_public_receipt_SHA=sha(args.receipt),resulting_status=read(args.receipt)['status'])
        target.write_text(json.dumps(binding,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
