"""One finite R3 qualification: exactly seven Optimize calls plus paid exports.

Three micro MIPs, one micro LP, one real root LP, two fixed-coordinate
completion LPs. Fresh plain reference is generated inside this paid batch;
its subsequent reuse must not charge the same process twice.
"""
import gzip,json,math,subprocess,time,sys
import gurobipy as gp
from gurobipy import GRB
from round98_common import *
from round98_qualification import physics,residual,rows
from round98_projection_vector_audit import check
import generate_citibike443_regional_v1 as parser

def theta_rows(model,initial,Q):
    actual=rows(model);names={v.VarName for v in model.getVars()};expected_names=set()
    for i,b in enumerate(initial[1:],1):
        states=sorted(int(n.split('_')[2]) for n in names if n.startswith(f'state_{i}_'))
        for y in states:
            if y==b:continue
            eq={f'state_{i}_{y}':-1.0}
            for k,q in enumerate(Q):
                if abs(y-b)<=q:
                    name=f'theta_{k}_{i}_{y}';eq[name]=1.;expected_names.add(name)
            assert ('=',0.,eq) in actual,(i,y,'state_mass')
        for k,q in enumerate(Q):
            pool=[y for y in states if y!=b and abs(y-b)<=q]
            for prefix,cost in [('z',lambda y:1),('p',lambda y:max(b-y,0)),('d',lambda y:max(y-b,0))]:
                eq={f'{prefix}_{k}_{i}':1.}
                eq.update({f'theta_{k}_{i}_{y}':-float(cost(y)) for y in pool if cost(y)})
                assert ('=',0.,eq) in actual,(k,i,prefix,'reconstruction')
    assert {n for n in names if n.startswith('theta_')}==expected_names
    assert not any(n.startswith('mode_') for n in names)
    assert all(v.VType=='C' for v in model.getVars() if v.VarName.startswith(('theta_','p_','d_')))
    assert all(v.VType=='B' for v in model.getVars() if v.VarName.startswith(('z_','state_')) and not v.VarName.startswith('state_g_'))
    return len(expected_names)

def size(m):return dict(rows=m.NumConstrs,columns=m.NumVars,nonzeros=m.NumNZs,binary=m.NumBinVars,integer=m.NumIntVars)

def main():
    dest=OUT/'diagnostics/vehicle01';dest.mkdir(parents=True,exist_ok=False)
    tick=time.monotonic();role=next(p for p in read(OUT/'development_inputs.json')['roles'] if p['id']=='R97-C3')
    assert sha(ROOT/role['input_path'])==role['input_sha256'];calls=[]
    def child(label,command,cap):
        d=dest/label;d.mkdir(exist_ok=False);write(d/'launch.json',dict(command=list(map(str,command)),optimizer_calls=0,
            bindings={str(p):sha(p) for p in map(Path,map(str,command)) if p.is_file()}))
        start=time.monotonic()
        with (d/'stdout.log').open('x') as so,(d/'stderr.log').open('x') as se:
            r=subprocess.run(list(map(str,command)),cwd=ROOT,env=env(),stdout=so,stderr=se,timeout=cap)
        write(d/'completion.json',dict(returncode=r.returncode,outer_seconds=time.monotonic()-start,
            optimizer_calls=0,already_billed_parent='qualification/vehicle01'))
        assert r.returncode==0,label
    child('real_export',[BUILD/'Round98ModelExport.exe',role['input_path'],role['T_seconds'],60,60,.15,
        role['diagnostic_gamma_L'],role['diagnostic_gamma_U'],role['diagnostic_cutoff'],dest/'real_models'],60)
    for mode in ['off','aggregate','projected']:
        assert sha(dest/'real_models'/(mode+'.lp'))==sha(OUT/'exports/R97-C3'/(mode+'.lp')),'old matrix changed'
    child('plain_reference',[BUILD/'Round65ReferenceBuild.exe',role['input_path'],role['T_seconds'],60,60,.15,dest/'plain_reference'],60)
    assert read(dest/'plain_reference/build.json')==role['reference']
    def optimize(m,label):
        m.Params.Threads=1;m.Params.Seed=0;m.Params.Presolve=-1;m.Params.MIPGap=0;m.Params.MIPGapAbs=0
        m.Params.TimeLimit=max(.001,285-(time.monotonic()-tick));m.Params.LogFile=str(dest/(label+'.log'))
        with (dest/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='start',label=label,seconds=time.monotonic()-tick))+'\n')
        m.optimize();record=dict(kind='complete',label=label,status=m.Status,seconds=time.monotonic()-tick)
        calls.append(record)
        with (dest/'calls.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
    expected=physics();write(dest/'enumeration.json',expected);micro=[]
    with gp.Env(empty=True) as native_env:
        native_env.setParam('OutputFlag',0);native_env.start();assert gp.gurobi.version()==(13,0,2)
        for suffix in ['', '_forced','_empty']:
            path=BUILD/'round98_ctest_models'/('vehicle-state'+suffix+'.lp')
            with gp.read(str(path),env=native_env) as m:
                if suffix!='_empty':theta_rows(m,[0,0,3,4] if not suffix else [0,0,3],[2,3] if not suffix else [3])
                optimize(m,'micro'+(suffix or '_base'))
                if suffix=='_empty':assert m.Status==GRB.INFEASIBLE
                else:
                    assert m.Status==GRB.OPTIMAL and abs(m.ObjVal-(0 if suffix else expected['optimum']))<=1e-7
                    res=residual(m);assert max(res.values())<=1e-5
                    write(dest/('micro'+(suffix or '_base')+'_values.json'),{v.VarName:v.X for v in m.getVars()})
                micro.append(dict(case=suffix or 'base',status=m.Status,model_sha256=sha(path),objective=m.ObjVal if m.SolCount else None))
                if not suffix:
                    relaxed=m.relax();optimize(relaxed,'micro_raw_LP');assert relaxed.Status==GRB.OPTIMAL
                    micro[-1]['raw_lp']=relaxed.ObjVal;relaxed.dispose()
        saved=OUT/'diagnostics/lp_strict_R97-C3';saved_record=read(saved/'projected_record.json')
        with gzip.open(saved/'projected_values.json.gz','rt') as f:values=json.load(f)
        assert sha(saved/'projected_values.json.gz')==saved_record['values_sha256']
        with gp.read(str(dest/'real_models/projected.lp'),env=native_env) as old:
            assert sha(dest/'real_models/projected.lp')==saved_record['model_sha256']
            original_vector=check(old,values);assert original_vector['maximum_absolute_residual']<=1e-7
        with gp.read(str(dest/'real_models/vehicle-state.lp'),env=native_env) as integer:
            integer.Params.Threads=1;integer.Params.Seed=0;integer.Params.Presolve=-1
            theta_count=theta_rows(integer,parser.parse_instance_mirror(ROOT/role['input_path'])['initial'],role['Q_vector'])
            before=size(integer);presolved=integer.presolve();after=size(presolved);presolved.dispose()
            m=integer.relax();m.Params.FeasibilityTol=1e-8;m.Params.OptimalityTol=1e-9
            optimize(m,'real_raw_LP');assert m.Status==GRB.OPTIMAL
            assert m.ObjVal+1e-7>=saved_record['objective']
            root=dict(objective=m.ObjVal,status=m.Status,primal_violation=m.ConstrVio,dual_violation=m.DualVio,
                R2_objective=saved_record['objective'],original=before,presolved=after,theta_columns=theta_count,
                model_sha256=sha(dest/'real_models/vehicle-state.lp'))
            with gzip.open(dest/'real_R3_values.json.gz','wt') as f:json.dump({v.VarName:v.X for v in m.getVars()},f)
            root['values_sha256']=sha(dest/'real_R3_values.json.gz');m.dispose()
            completions=[]
            for label,free_states in [('fixed_R2_state_assignment',False),('fixed_original_physical_coordinates',True)]:
                m=integer.relax();m.Params.FeasibilityTol=1e-8;m.Params.OptimalityTol=1e-9
                fixed=[]
                for v in m.getVars():
                    if v.VarName.startswith('theta_') or (free_states and v.VarName.startswith('state_')):continue
                    assert v.VarName in values;v.LB=v.UB=values[v.VarName];fixed.append(v.VarName)
                m.setObjective(0);optimize(m,label)
                completions.append(dict(label=label,status=m.Status,fixed_columns=len(fixed),
                    feasible=m.Status==GRB.OPTIMAL,proved_no_extension=m.Status==GRB.INFEASIBLE,
                    scope='Known R3 interval feasible. Fix saved R2 coordinates, solve extension only; not interval infeasibility.'))
                m.dispose()
    assert len(calls)==7
    write(dest/'summary.json',dict(passed=True,optimizer_calls=7,maximum_optimizer_calls=7,role=role,micro=micro,
        original_R2_vector_audit=original_vector,root=root,completions=completions,source_sha256=sha(__file__),
        exporter_sha256=sha(BUILD/'Round98ModelExport.exe'),reference_binary_sha256=sha(BUILD/'Round65ReferenceBuild.exe'),
        production_binary_sha256=sha(BUILD/'ExactEBRP.exe'),source_bindings=bindings(),outer_seconds=time.monotonic()-tick,
        diagnostic_only_tolerances='FeasibilityTol=1e-8, OptimalityTol=1e-9 on real raw/completion LP only',
        prepaid_plain_reference='plain_reference; one zero-Optimize child, included in parent fee'))
    print(json.dumps(dict(passed=True,calls=len(calls),root=root,completions=completions)),flush=True)
if __name__=='__main__':main()
