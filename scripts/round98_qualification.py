"""Independent micro physics enumeration and actual exported LP/MIP audit.

Exactly 9 integer Optimize and 3 raw-LP Optimize; no search on import.
Each call shares a finite diagnostic-only process cap and is recorded.
"""
import itertools,json,math,sys,time
from pathlib import Path
import gurobipy as gp
from gurobipy import GRB
from round98_common import ROOT,OUT,sha,write,read

def physics():
    best=math.inf;best_witness=None;count=0
    # Enumerate final integer inventory and station assignment/orders independently
    # of the LP writer. Empty station1 has zero capacity and cannot be served.
    for y2 in range(6):
        for y3 in range(5):
            final=[0,0,y2,y3];initial=[0,0,3,4]
            active=[i for i in [2,3] if final[i]!=initial[i]]
            for owners in itertools.product(range(2),repeat=len(active)):
                choices=[list(itertools.permutations([i for i,k in zip(active,owners) if k==v])) for v in range(2)]
                for orders in itertools.product(*choices):
                    valid=True;routes=[]
                    for k,order in enumerate(orders):
                        load=0;ops=[]
                        for i in order:
                            delta=initial[i]-final[i];p=max(0,delta);d=max(0,-delta);load+=delta
                            valid &= 0<=load<=[2,3][k]
                            ops.append([i,p,d])
                        # Travel is unit metric, handling zero, T100. Loaded return allowed.
                        valid &= not order or len(order)+1<=100
                        routes.append(dict(vehicle=k,nodes=[0,*order,0],operations=ops))
                    if not valid:continue
                    count+=1;r=[0,y2/2,y3/3];S=sum(r)
                    G=sum(abs(a-b) for a,b in itertools.combinations(r,2))/(3*S) if S else 0
                    F=G+.15*sum(abs(a-1) for a in r)
                    if F<best:best,best_witness=F,dict(routes=routes,final=final,G=G,F=F)
    return dict(feasible_enumerated=count,optimum=best,witness=best_witness)

def residual(model):
    bound=max((max(v.LB-v.X,v.X-v.UB,0) for v in model.getVars()),default=0)
    row=0
    for c in model.getConstrs():
        lhs=model.getRow(c).getValue()
        violation=abs(lhs-c.RHS) if c.Sense=='=' else max(0,lhs-c.RHS) if c.Sense=='<' else max(0,c.RHS-lhs)
        row=max(row,violation)
    op=max((abs(v.X-round(v.X)) for v in model.getVars() if v.VarName.startswith(('p_','d_'))),default=0)
    return dict(max_bound=bound,max_row=row,max_physical_operation_integrality=op)

def rows(model):
    out=[]
    for c in model.getConstrs():
        r=model.getRow(c)
        out.append((c.Sense,c.RHS,{r.getVar(j).VarName:r.getCoeff(j) for j in range(r.size())}))
    return out

def check_linkage(model,initial,M):
    actual=rows(model);names={v.VarName for v in model.getVars()}
    for i,b in enumerate(initial[1:],1):
        movement={f'{prefix}_{k}_{i}':1.0 for k in range(M) for prefix in ['p','d']}
        for n in names:
            if n.startswith(f'state_{i}_'):
                y=int(n.split('_')[2]);coef=-abs(b-y)
                if coef:movement[n]=coef
        visit={f'z_{k}_{i}':1.0 for k in range(M)}
        if f'state_{i}_{b}' in names:visit[f'state_{i}_{b}']=1.0
        assert ('=',0.0,movement) in actual,(i,'A')
        assert ('=',1.0,visit) in actual,(i,'B')

def main():
    assert gp.gurobi.version()==(13,0,2)
    dest=Path(sys.argv[1]);dest.mkdir(parents=True,exist_ok=False)
    inputs=Path(sys.argv[2]);expected=physics();records=[]
    write(dest/'enumeration.json',expected)
    started=time.monotonic()
    def optimize(model,label):
        with (dest/'calls.jsonl').open('a') as f:
            f.write(json.dumps(dict(label=label,kind='start',seconds=time.monotonic()-started))+'\n')
        model.optimize()
        with (dest/'calls.jsonl').open('a') as f:
            f.write(json.dumps(dict(label=label,kind='complete',status=model.Status,seconds=time.monotonic()-started))+'\n')
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for mode in ['off','aggregate','projected']:
            path=inputs/(mode+'.lp')
            with gp.read(str(path),env=env) as model:
                model.Params.Threads=1;model.Params.Seed=0;model.Params.Presolve=-1
                model.Params.MIPGap=0;model.Params.MIPGapAbs=0
                model.Params.TimeLimit=max(.001,110-(time.monotonic()-started))
                model.Params.LogFile=str(dest/(mode+'.log'))
                before=dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs,
                    binary=model.NumBinVars,integer=model.NumIntVars)
                if mode!='off':check_linkage(model,[0,0,3,4],2)
                optimize(model,mode+'_MIP');assert model.Status==GRB.OPTIMAL
                assert abs(model.ObjVal-expected['optimum'])<=1e-7,(mode,model.ObjVal,expected)
                check=residual(model);assert max(check.values())<=1e-5,check
                values={v.VarName:v.X for v in model.getVars()}
                if mode=='projected':
                    assert not any(n.startswith('mode_') for n in values)
                    assert all(v.VType=='C' for v in model.getVars() if v.VarName.startswith(('p_','d_')))
                write(dest/(mode+'_integer_values.json'),values)
                mip=dict(objective=model.ObjVal,bound=model.ObjBound,status=model.Status,residual=check)
                relaxed=model.relax();relaxed.Params.TimeLimit=max(.001,110-(time.monotonic()-started))
                optimize(relaxed,mode+'_LP');assert relaxed.Status==GRB.OPTIMAL
                records.append(dict(mode=mode,model_sha256=sha(path),original=before,mip=mip,
                    raw_lp=relaxed.ObjVal,lp_status=relaxed.Status,optimizer_calls=2))
                relaxed.dispose()
        boundaries=[]
        for suffix in ['forced','empty']:
            for mode in ['off','aggregate','projected']:
                path=inputs/(mode+'_'+suffix+'.lp')
                with gp.read(str(path),env=env) as model:
                    model.Params.Threads=1;model.Params.Seed=0;model.Params.Presolve=-1
                    model.Params.MIPGap=0;model.Params.MIPGapAbs=0
                    model.Params.TimeLimit=max(.001,110-(time.monotonic()-started))
                    optimize(model,mode+'_'+suffix)
                    if suffix=='forced':
                        assert model.Status==GRB.OPTIMAL and abs(model.ObjVal)<=1e-7
                        assert model.getVarByName('state_1_0') is None
                        assert model.getVarByName('state_2_3') is None
                        if mode!='off':check_linkage(model,[0,0,3],1)
                        check=residual(model);assert max(check.values())<=1e-5
                    else:assert model.Status==GRB.INFEASIBLE
                    boundaries.append(dict(mode=mode,case=suffix,status=model.Status,model_sha256=sha(path)))
    assert abs(records[1]['raw_lp']-records[2]['raw_lp'])<=1e-7
    assert records[1]['raw_lp']+1e-7>=records[0]['raw_lp']
    write(dest/'summary.json',dict(passed=True,optimizer_calls=12,records=records,boundaries=boundaries,
        outer_seconds=time.monotonic()-started,scope='micro correctness only; no performance claim'))
    print(json.dumps(dict(passed=True,optimum=expected['optimum'],records=records)),flush=True)
if __name__=='__main__':main()
