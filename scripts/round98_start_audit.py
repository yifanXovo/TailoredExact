"""Read-only actual R68 submitted-column audit, never Optimize."""
import csv,json,math,sys,time,os,subprocess
import gurobipy as gp
from round98_common import *
from round98_projection_vector_audit import check
import round96_external as ext

def run(destination,label):
    # The read-only Python runtime itself resides in an old diagnostic venv;
    # exclude this zero-Optimize audit and its known receipt parent only.
    grandparent=int(subprocess.check_output(['powershell.exe','-NoProfile','-Command',
        f'(Get-CimInstance Win32_Process -Filter "ProcessId = {os.getppid()}").ParentProcessId'],text=True).strip())
    competing=[p for p in ext.r90.foreign_heavy_processes() if p['ProcessId'] not in {os.getpid(),os.getppid(),grandparent}]
    assert not competing,competing
    dest=Path(destination).resolve();tick=time.monotonic();records=[]
    files={sha(p):p for p in (dest/'external/models').glob('*.lp')}
    starts=[(p,read(p)) for p in (dest/'external/native_logs').glob('*.round68.start.json')]
    assert starts,'no complete Start exposure'
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for h in sorted({j['model_sha256'] for p,j in starts if j.get('submitted')}):
            assert h in files
            with gp.read(str(files[h]),env=env) as m:
                assert not any(v.VarName.startswith('mode_') for v in m.getVars()),'R2 retained direction column'
                assert all(v.VType=='C' for v in m.getVars() if v.VarName.startswith(('p_','d_')))
                for path,j in starts:
                    if not j.get('submitted') or j['model_sha256']!=h:continue
                    assert j['mapping_complete'] and j['rows_valid'] and j['objective_valid'] and j['readback_valid']
                    vector=path.with_name(path.name[:-5]+'.values.csv')
                    with vector.open(newline='') as f:table=list(csv.DictReader(f))
                    assert [r['variable'] for r in table]==[v.VarName for v in m.getVars()]
                    values={r['variable']:float(r['value']) for r in table}
                    assert all(math.isfinite(float(r['readback'])) and abs(float(r['value'])-float(r['readback']))<=1e-7 for r in table)
                    for v in m.getVars():
                        x=values[v.VarName]
                        if v.VType in ['B','I'] or v.VarName.startswith(('p_','d_','theta_')):
                            assert abs(x-round(x))<=1e-7,(v.VarName,'physical integer semantics')
                    residual=check(m,values)
                    assert residual['maximum_absolute_residual']<=1e-7
                    assert abs(residual['objective']-j['objective'])<=1e-7
                    records.append(dict(start_path=path.relative_to(ROOT).as_posix(),start_sha256=sha(path),
                        vector_sha256=sha(vector),model_sha256=h,rows=m.NumConstrs,columns=m.NumVars,
                        objective=residual['objective'],maximum_absolute_residual=residual['maximum_absolute_residual']))
    assert records,'no actual native submitted Start'
    write(OUT/'qualification'/(label+'.json'),dict(passed=True,optimizer_calls=0,starts=records,
        wall_seconds=time.monotonic()-tick,scope='every submitted retained R2 Start in this selected completed process; no independent full performance rerun',
        source_sha256=sha(__file__)))
    print(json.dumps(dict(passed=True,starts=len(records),optimizer_calls=0)))
if __name__=='__main__':run(*sys.argv[1:])
