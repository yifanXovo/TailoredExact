"""One finite batch: 6 new-mode MIPs + 4 all-continuous LPs, durable calls."""
import sys,time,json
import gurobipy as gp
from gurobipy import GRB
from round99_common import *
from round98_qualification import physics,residual,check_linkage
def run(label,inputs):
    dest=OUT/'diagnostics'/label;dest.mkdir(parents=True,exist_ok=False)
    write(dest/'plan.json',dict(maximum_optimize=10,outer_cap=120,models=str(inputs)))
    started=time.monotonic();calls=0;records=[];expected=physics()
    def optimize(m,name):
        nonlocal calls
        assert calls<10
        with (dest/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='start',name=name))+'\n');f.flush()
        calls+=1;m.Params.TimeLimit=max(.001,110-(time.monotonic()-started));m.optimize()
        with (dest/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='return',name=name,status=m.Status,runtime=m.Runtime))+'\n');f.flush()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start();assert gp.gurobi.version()==(13,0,2)
        for mode in ['q-integer','m-binary']:
            for suffix in ['', '_forced','_empty']:
                path=Path(inputs)/(mode+suffix+'.lp')
                with gp.read(str(path),env=env) as m:
                    m.Params.Threads=1;m.Params.Seed=0;m.Params.MIPGap=0;m.Params.MIPGapAbs=0
                    m.Params.LogFile=str(dest/(mode+suffix+'.log'))
                    assert all(v.VType==('I' if mode=='q-integer' else 'C') for v in m.getVars() if v.VarName.startswith(('p_','d_')))
                    modes=[v for v in m.getVars() if v.VarName.startswith('mode_')]
                    assert (not modes) if mode=='q-integer' else (modes and all(v.VType=='B' for v in modes))
                    assert all(v.VType=='B' for v in m.getVars() if v.VarName.startswith(('state_','z_')) and not v.VarName.startswith('state_g_'))
                    if suffix!='_empty':check_linkage(m,[0,0,3] if suffix else [0,0,3,4],1 if suffix else 2)
                    optimize(m,mode+suffix)
                    if suffix=='_empty':assert m.Status==GRB.INFEASIBLE;check=None
                    else:
                        assert m.Status==GRB.OPTIMAL
                        assert abs(m.ObjVal-(0 if suffix else expected['optimum']))<=1e-7
                        check=residual(m);assert max(check.values())<=1e-5
                        write(dest/(mode+suffix+'_values.json'),{v.VarName:v.X for v in m.getVars()})
                    records.append(dict(mode=mode,case=suffix,status=m.Status,sha256=sha(path),residual=check))
        lp=[]
        for mode in ['aggregate','q-integer','m-binary','projected']:
            with gp.read(str(Path(inputs)/(mode+'.lp')),env=env) as m:
                r=m.relax();r.Params.Threads=1;optimize(r,mode+'_raw_LP')
                assert r.Status==GRB.OPTIMAL;lp.append(r.ObjVal);r.dispose()
        assert max(lp)-min(lp)<=1e-7
    write(dest/'summary.json',dict(passed=True,optimizer_calls=calls,records=records,raw_LP=lp,
        expected=expected,outer_seconds=time.monotonic()-started,script_sha256=sha(__file__)))
    print(json.dumps(dict(passed=True,optimizer_calls=calls,raw_LP=lp)))
if __name__=='__main__':run(sys.argv[1],sys.argv[2])
