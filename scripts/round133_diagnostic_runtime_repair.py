"""Single preregistered runtime repair before the first C-R3 Optimize."""
import importlib.metadata, importlib.util, sys
from pathlib import Path
import round133_common as C
import round133_diagnostic as diagnostic

PLAN=C.OUT/'plans/C_diagnostics_runtime_repair.json'

def check():
    plan=C.read(PLAN);repair=plan['runtime_repair']
    assert C.sha(__file__)==repair['wrapper_SHA256']
    assert C.sha(sys.executable)==repair['python_SHA256']
    assert C.sha(C.ROOT/repair['original_plan'])==repair['original_plan_SHA256']
    failure=C.read(C.OUT/'fees/C_R3_GEOM_matrix_replay_01/receipt.json')
    assert failure['exit_code']==1
    old=C.ROOT/repair['failed_destination']
    assert not (old/'binding.json').exists() and not (old/'native_return.json').exists()
    for name,record in repair['helper_bindings'].items():assert C.sha(C.ROOT/name)==record['SHA256']
    assert importlib.metadata.version('gurobipy')=='13.0.2'
    origin=Path(importlib.util.find_spec('gurobipy').origin)
    assert C.sha(origin)==repair['gurobipy_init_SHA256']
    diagnostic.PLAN=PLAN

if __name__=='__main__':
    check()
    if len(sys.argv)>1 and sys.argv[1]=='analyze':diagnostic.analyze()
    else:sys.exit(diagnostic.run_r3())
