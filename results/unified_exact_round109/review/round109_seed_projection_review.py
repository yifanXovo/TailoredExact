"""Finite independent audit of seed-metadata compatibility projection only.

Select pure functions from the actual frozen adapter's AST. No production
module is imported, native environment loaded, or algorithm state mutated.
"""
from pathlib import Path
import ast, copy, hashlib, json, sys, time, traceback

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    root=Path(sys.argv[1]).resolve();dest=root/'results/unified_exact_round109/review/seed_projection_finite01';dest.mkdir(exist_ok=False)
    start=time.perf_counter();source=root/'scripts/round109_seed_audit.py';checks=[];error=None
    save(dest/'launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=sha(__file__),adapter_SHA=sha(source),Optimize=0,native_environment=0))
    try:
        tree=ast.parse(source.read_text(encoding='utf-8-sig'));wanted={'expected','checked_projection','parameter_readback'}
        pure=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
        assert {n.name for n in pure}==wanted
        settings=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SETTINGS' for t in n.targets))
        namespace=dict(copy=copy,_active_seed=1)
        def original_parameters(result,require_call,arm):
            assert result['gurobi_seed_requested']==result['gurobi_seed_effective']==0
            return dict(seed=dict(requested=0,effective=0,set_return_code=0,get_return_code=0))
        namespace['_parameters']=original_parameters
        module=ast.fix_missing_locations(ast.Module(body=[settings,*pure],type_ignores=[]));exec(compile(module,str(source),'exec'),namespace)
        actual=namespace['expected'](1);assert actual['Seed']==1 and actual['Threads']==1 and actual['Presolve']==-1
        checks.append('exact Seed1 actual native settings independently read from adapter AST')
        records=[dict(payload=dict(kind='identity',sequence=1)),dict(payload=dict(kind='call',sequence=2,settings=copy.deepcopy(actual))),dict(payload=dict(kind='returned',sequence=3))]
        before=json.dumps(records,sort_keys=True);projected=namespace['checked_projection'](records,1)
        assert json.dumps(records,sort_keys=True)==before and projected[1]['payload']['settings']['Seed']==0 and records[1]['payload']['settings']['Seed']==1
        checks.append('projection uses deepcopy and preserves original committed Seed1 bytes/objects')
        restored=copy.deepcopy(projected);restored[1]['payload']['settings']['Seed']=1
        assert restored==records;checks.append('only Seed metadata changes; every other field identical')
        for key,value in [('Seed',0),('Threads',2),('MIPGap',.01),('FeasibilityTol',1e-5)]:
            bad=copy.deepcopy(records);bad[1]['payload']['settings'][key]=value
            try:namespace['checked_projection'](bad,1)
            except AssertionError:checks.append('incorrect actual '+key+' rejected before legacy projection')
            else:raise AssertionError('incorrect actual native setting accepted: '+key)
        result=dict(gurobi_seed_requested=1,gurobi_seed_effective=1,gurobi_seed_set_return_code=0,gurobi_seed_get_return_code=0)
        old=dict(result);readback=namespace['parameter_readback'](result,require_call=True,arm='P-GRB')
        assert readback['seed']==dict(requested=1,effective=1,set_return_code=0,get_return_code=0) and result==old
        checks.append('actual Seed1 requested/effective/read return codes remain exposed and original result unchanged')
        for key,value in [('gurobi_seed_effective',0),('gurobi_seed_requested',0),('gurobi_seed_get_return_code',1)]:
            bad=dict(result);bad[key]=value
            try:namespace['parameter_readback'](bad,require_call=True,arm='P-GRB')
            except AssertionError:checks.append('incorrect actual '+key+' rejected before old parameter validator')
            else:raise AssertionError('incorrect actual parameter readback accepted: '+key)
        assert all('write' not in getattr(node.func,'attr','').lower() for f in pure for node in ast.walk(f) if isinstance(node,ast.Call))
        checks.append('selected projection/readback functions contain no write API')
    except Exception:error=traceback.format_exc()
    elapsed=time.perf_counter()-start
    value=dict(decision='ACCEPT' if error is None else 'HOLD',checks=checks,error=error,adapter_SHA=sha(source),source_SHA=sha(__file__),elapsed_engineering_seconds=elapsed,
        Optimize=0,LP_solve=0,native_environment=0,production_edits=0,scope='pure metadata projection only; actual CLI Seed settings are separately raw audited')
    save(dest/'audit.json',value);save(dest/'receipt.json',dict(exit_code=int(error is not None),audit_SHA=sha(dest/'audit.json'),elapsed_engineering_seconds=elapsed,source_SHA=sha(__file__)))
    (dest/'source_at_execution.py').write_bytes(Path(__file__).read_bytes());(dest/'adapter_at_execution.py').write_bytes(source.read_bytes())
    print(json.dumps(dict(decision=value['decision'],checks=len(checks),error=error),ensure_ascii=False),flush=True)
    if error:sys.exit(1)
if __name__=='__main__':main()
