"""Zero-Optimize all-row checks of actual mode-specific submitted Starts."""
import csv,json,sys,time,math
import gurobipy as gp
from round99_common import *
from round98_projection_vector_audit import check
from round99_factor_diagnostic import MODES
def run(destination,label,mode):
    assert mode in MODES or mode=='off'
    dest=Path(destination).resolve();models={sha(p):p for p in (dest/'external/models').glob('*.lp')}
    starts=[(p,read(p)) for p in (dest/'external/native_logs').glob('*.round68.start.json')]
    assert starts;records=[];tick=time.monotonic()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for h in sorted({j['model_sha256'] for p,j in starts if j.get('submitted')}):
            assert h in models
            with gp.read(str(models[h]),env=env) as m:
                modes=[v for v in m.getVars() if v.VarName.startswith('mode_')]
                assert (not modes) if mode in ['projected','q-integer'] else (modes and all(v.VType=='B' for v in modes))
                qt='C' if mode in ['projected','m-binary'] else 'I'
                assert all(v.VType==qt for v in m.getVars() if v.VarName.startswith(('p_','d_')))
                for path,j in starts:
                    if not j.get('submitted') or j['model_sha256']!=h:continue
                    assert all(j[k] for k in ['mapping_complete','rows_valid','objective_valid','readback_valid'])
                    vector=path.with_name(path.name[:-5]+'.values.csv')
                    with vector.open(newline='') as f:table=list(csv.DictReader(f))
                    assert [r['variable'] for r in table]==[v.VarName for v in m.getVars()]
                    values={r['variable']:float(r['value']) for r in table}
                    assert all(math.isfinite(float(r['readback'])) and abs(float(r['value'])-float(r['readback']))<=1e-7 for r in table)
                    for v in m.getVars():
                        if v.VType in ['B','I'] or v.VarName.startswith(('p_','d_')):assert abs(values[v.VarName]-round(values[v.VarName]))<=1e-7
                    audited=check(m,values);assert audited['maximum_absolute_residual']<=1e-7
                    assert abs(audited['objective']-j['objective'])<=1e-7
                    records.append(dict(start_path=path.relative_to(ROOT).as_posix(),start_sha256=sha(path),vector_sha256=sha(vector),
                        model_sha256=h,mode=mode,rows=m.NumConstrs,columns=m.NumVars,objective=audited['objective'],
                        max_residual=audited['maximum_absolute_residual'],actual_quantity_type=qt,direction_columns=len(modes)))
    assert records
    write(OUT/'qualification'/(label+'.json'),dict(passed=True,optimizer_calls=0,starts=records,
        wall_seconds=time.monotonic()-tick,scope='all retained submitted Starts of this completed process',script_sha256=sha(__file__)))
    print(json.dumps(dict(passed=True,mode=mode,starts=len(records),optimizer_calls=0)))
if __name__=='__main__':run(*sys.argv[1:])
