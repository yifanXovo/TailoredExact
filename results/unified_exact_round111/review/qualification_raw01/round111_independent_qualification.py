"""One actual small CLI raw review, separate from final wrapper admission."""
from pathlib import Path
import argparse
import datetime
import json
import os
import sys
import time
import traceback
from round111_import_main import Tee,write,digest
from round111_independent_core import Audit,ROUND,PE,DLL


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--label',required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    destination = root/ROUND/'review'/args.label
    destination.mkdir(parents=True,exist_ok=False)
    stdout = (destination/'stdout.log').open('x',encoding='utf-8',newline='\n')
    stderr = (destination/'stderr.log').open('x',encoding='utf-8',newline='\n')
    sys.stdout,sys.stderr = Tee(sys.stdout,stdout),Tee(sys.stderr,stderr)
    start = time.perf_counter()
    sources = {}
    for path in (Path(__file__),Path(__file__).with_name('round111_independent_core.py'),Path(__file__).with_name('round111_import_main.py')):
        sources[path.name] = digest(path.read_bytes())
        (destination/path.name).open('xb').write(path.read_bytes())
    launch = dict(cwd=str(Path.cwd().resolve()),argv=sys.argv,PID=os.getpid(),root=str(root),source_bindings=sources,
                  start_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),Optimize=0,native_environment=0)
    write(destination/'launch.json',launch)
    code = 1
    try:
        a = Audit(root,destination)
        identity = a.obj(a.out/'qualification/cli01/identity.json')
        fee = a.out/'fees/qualification_cli02'
        fee_launch,fee_receipt = a.obj(fee/'launch.json'),a.obj(fee/'receipt.json')
        a.require(fee_receipt['exit_code'] == 0 and fee_receipt['actual_native_children_with_launch'] == 2 and
                  fee_launch['helpers'] == identity['helpers'],'actual two native qualified source process graph')
        for path,expected in identity['helpers'].items():
            a.require(a.sha(fee/'source_snapshot'/path) == expected,'actual qualified helper execution snapshot '+path)
        a.require(identity['candidate_binary_sha256'] == PE and identity['dll_sha256'] == DLL and
                  [(v['id'],v['arm'],v['seed']) for v in identity['launches']] == [('H100','P-GRB',1),('H100','M-B',1)],
                  'exact original PE DLL and fixed two H100 Seed1 CLI identities')
        records = []
        for entry in identity['launches']:
            record,models,q = a.arm(entry,identity)
            a.require(record['formal_protocol_qualified'] and entry['cap_seconds'] <= 120,'actual full qualification arm clock fits original cap')
            records.append(record)
        a.require(any(v['solve_kind'] == 'LP' for v in records[1]['native_records']) and
                  any(v['solve_kind'] == 'MIP' for v in records[1]['native_records']) and records[1]['starts'],
                  'actual M-B LP/MIP/type/own full-column Start paths reached')
        audit = dict(decision='ACCEPT_ACTUAL_H100_TWO_CLI_RAW_QUALIFICATION',qualification_identity_SHA=a.sha(a.out/'qualification/cli01/identity.json'),
                     actually_qualified_helper_bindings=identity['helpers'],own_actual_qualification_arms=records,production_PE_SHA=PE,DLL_SHA=DLL,
                     formal_performance_admission_signed=False,final_metadata_wrapper_closure_still_separate=True,
                     completed_checks=a.checks,read_bindings=a.reads,explicit_read_root=str(root),reviewer_source_bindings=sources,Optimize=0,native_environment=0)
        write(destination/'audit.json',audit)
        print(json.dumps(dict(decision=audit['decision'],checks=a.checks,whole_clocks=[v['whole_seconds'] for v in records])),flush=True)
        code = 0
    except Exception:
        traceback.print_exc()
        write(destination/'hold.json',dict(decision='HOLD',error=traceback.format_exc(),Optimize=0,native_environment=0))
    sys.stdout.flush();sys.stderr.flush()
    receipt = dict(exit_code=code,cwd=launch['cwd'],explicit_read_root=str(root),engineering_elapsed_seconds=time.perf_counter()-start,
                   source_bindings=sources,stdout_SHA=digest((destination/'stdout.log').read_bytes()),stderr_SHA=digest((destination/'stderr.log').read_bytes()),
                   Optimize=0,native_environment=0)
    if (destination/'audit.json').exists():
        receipt['audit_SHA'] = digest((destination/'audit.json').read_bytes())
    write(destination/'receipt.json',receipt)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
