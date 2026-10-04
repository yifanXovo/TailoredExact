"""Finite current-stack LP qualification on preserved actual ENS-C matrices.
No historical primal/UB enters a formal experiment. Every Optimize is logged.
"""
from round101_common import *
from round100_idle import ensure_idle
import sys,math
def dump_matrix(m,path):
    vars=m.getVars();cols={v.VarName:j for j,v in enumerate(vars)}
    with path.open('x',encoding='utf-8') as f:
        f.write(f'{len(vars)} {m.NumConstrs}\n')
        for v in vars:f.write(f'{v.VarName} {v.VType} {v.LB:.17g} {v.UB:.17g}\n')
        for row in m.getConstrs():
            a=m.getRow(row);f.write(f'{row.Sense} {row.RHS:.17g} {a.size()} ')
            f.write(' '.join(f'{cols[a.getVar(t).VarName]} {a.getCoeff(t):.17g}' for t in range(a.size()))+'\n')
def diagnostic(p,m,point,path,out):
    with point.open('x') as f:f.write('\n'.join(f'{v:.17g}' for v in path)+'\n')
    tick=time.perf_counter()
    cmd=[BUILD/'Round101FleetDiagnostic.exe',ROOT/p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],point.parent/'matrix.txt',point,out]
    proc=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=env(),capture_output=True,text=True,timeout=120)
    assert proc.returncode==0,(proc.returncode,proc.stdout,proc.stderr,read(out) if out.exists() else None)
    result=read(out);result['diagnostic_seconds']=time.perf_counter()-tick;return result
def main(label):
    ensure_idle()
    from round100_gurobi_runtime import gp,binding
    from gurobipy import GRB
    from round98_projection_vector_audit import check
    from round70_affinity import inherited_core
    folder=OUT/'diagnostics'/label;folder.mkdir(parents=True,exist_ok=False);calls=0;records=[]
    locations={
      'F2':'results/unified_exact_round100/exports/F2/ENS-C.lp',
      'R98-C2':'results/unified_exact_round100/exports/R98-C2/ENS-C.lp',
      'R99-N2':'results/unified_exact_round100/certification_N201/raw/03_R99-N2_ENS-C/external/models/L0_epoch_0_generation_1.lp',
      'F5':'results/unified_exact_round100/certification_CF01/raw/04_F5_ENS-C/external/models/L0_epoch_0_generation_1.lp'}
    def optimize(m,name):
        nonlocal calls
        with (folder/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='start',name=name))+'\n');f.flush()
        calls+=1;m.Params.TimeLimit=120;m.optimize()
        with (folder/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='return',name=name,status=m.Status,seconds=m.Runtime))+'\n');f.flush()
        assert m.Status==GRB.OPTIMAL,(name,m.Status)
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();assert gp.gurobi.version()==(13,0,2);runtime=binding()
        for p in read(OUT/'development_inputs.json')['roles']:
            d=folder/p['id'];d.mkdir();source=ROOT/locations[p['id']]
            assert source.exists(),source
            m=gp.read(str(source),env=engine);dump_matrix(m,d/'matrix.txt');vars=m.getVars()
            lp=m.relax();lp.Params.Threads=1;lp.Params.Seed=0;lp.Params.LogFile=str(d/'raw.log')
            optimize(lp,p['id']+'_raw');old=lp.ObjVal;values=[v.X for v in lp.getVars()]
            raw=diagnostic(p,m,d/'raw.point',values,d/'raw.separation.json');assert raw['valid']
            residual=check(lp,{v.VarName:v.X for v in lp.getVars()});assert residual['maximum_absolute_residual']<=1e-6
            rows=raw['rows']
            if not rows:
                # Proof-only search seed; NEVER represented as an old-LP or native point.
                for sign in [-1,1]:
                    seed=[0.0]*len(vars)
                    for states in raw['contract']['states'][1:]:
                        y,j=(min(states) if sign<0 else max(states));seed[j]=1
                    trial=diagnostic(p,m,d/f'proof_seed_{sign}.point',seed,d/f'proof_seed_{sign}.json')
                    rows+=trial['rows'][:1]
            # Save and optimize at most two distinct proven rows for implication.
            bank=[];seen=set();containment=[]
            for row in rows:
                signature=(tuple(row['columns']),row['proof']['rank'])
                if signature in seen:continue
                seen.add(signature);bank.append(row)
                if len(bank)==2:break
            original=lp.getObjective()
            for j,row in enumerate(bank):
                expr=gp.quicksum(lp.getVars()[k] for k in row['columns']);lp.setObjective(expr,GRB.MAXIMIZE)
                optimize(lp,p['id']+f'_implication_{j}');activity=lp.ObjVal
                vals=[v.X for v in lp.getVars()];res=check(lp,{v.VarName:v.X for v in lp.getVars()})
                assert res['maximum_absolute_residual']<=1e-6
                write(d/f'implication_{j}.json',dict(row=row,maximum_activity=activity,rhs=row['proof']['rank'],residual=res,point=vals))
                containment.append(dict(rank=row['proof']['rank'],support=len(row['proof']['events']),method=row['proof']['method'],maximum_violation=activity-row['proof']['rank']))
            lp.setObjective(original,GRB.MINIMIZE)
            for row in bank:lp.addConstr(gp.quicksum(lp.getVars()[k] for k in row['columns'])<=row['proof']['rank'])
            strengthened=None
            if bank:optimize(lp,p['id']+'_original_objective_plus_rows');strengthened=lp.ObjVal
            contract=raw['contract'];Q=max(contract['capacities']);cost=contract['handling_lower'];T=contract['horizon_upper']
            threshold_count={q:sum(1 for i in range(1,p['V']+1) if q<=contract['initial'][i]) for q in [1,Q]}
            records.append(dict(role=p['id'],actual_source=str(source.relative_to(ROOT)),actual_sha256=sha(source),raw_objective=old,
                objective_with_bank=strengthened,raw_residual=residual,raw_selected=len(raw['rows']),raw_reliable=raw['reliable'],raw_separator_seconds=raw['diagnostic_seconds'],
                bank_size=len(bank),containment=containment,processing_only_minimum_conflict={q:(p['M']*math.floor(T/(cost*q))+1 if cost>0 else None) for q in [1,Q]},
                available_pickup_threshold_count=threshold_count,states=sum(len(s) for s in contract['states']),audited_rows=contract['audited_rows']))
            lp.dispose();m.dispose()
    write(folder/'summary.json',dict(records=records,optimizer_calls=calls,runtime=runtime,affinity=affinity,source_hashes=bindings(),passed=True))
    print(json.dumps(dict(records=records,optimizer_calls=calls)),flush=True)
if __name__=='__main__':main(sys.argv[1])
