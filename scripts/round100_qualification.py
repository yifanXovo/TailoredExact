"""Finite minimal qualifications, bound to the exact production DLL."""
import collections, json, sys, time
from round100_common import *
from round100_idle import ensure_idle
def exports():
    import subprocess
    for p in read(OUT/'development_inputs.json')['roles']:
        cmd=[BUILD/'Round100ModelExport.exe',ROOT/p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],
             p['diagnostic_gamma_L'],p['diagnostic_gamma_U'],p['diagnostic_cutoff'],OUT/'exports'/p['id']]
        subprocess.run(list(map(str,cmd)),cwd=ROOT,env=env(),check=True,timeout=60)
    print('finite children=3, Optimize=0')
def native(kind,label):
    ensure_idle()
    from round100_gurobi_runtime import gp,binding
    from round98_qualification import physics,residual,check_linkage
    from round98_projection_vector_audit import check
    from gurobipy import GRB
    d=OUT/'diagnostics'/label;d.mkdir(parents=True,exist_ok=False);start=time.monotonic();calls=0
    def optimize(m,name):
        nonlocal calls
        with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='start',name=name))+'\n');f.flush()
        calls+=1;m.Params.TimeLimit=max(.001,280-(time.monotonic()-start));m.optimize()
        with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='return',name=name,status=m.Status,runtime=m.Runtime))+'\n');f.flush()
    def options(m):
        m.Params.Threads=1;m.Params.Seed=0;m.Params.Presolve=-1;m.Params.MIPGap=0;m.Params.MIPGapAbs=0
    def row(c,m):
        r=m.getRow(c);return (c.Sense,c.RHS,tuple(sorted((r.getVar(i).VarName,r.getCoeff(i)) for i in range(r.size()))))
    records=[]
    with gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();assert gp.gurobi.version()==(13,0,2)
        runtime=binding()
        if kind=='micro':
            expected=physics()
            for suffix in ['', '_forced','_empty']:
                path=OUT/'micro_models01'/('ENS-Q'+suffix+'.lp')
                with gp.read(str(path),env=engine) as m:
                    options(m);m.Params.LogFile=str(d/('ENS-Q'+suffix+'.log'))
                    assert all(v.VType=='C' for v in m.getVars() if v.VarName.startswith(('p_','d_')))
                    optimize(m,'ENS-Q'+suffix)
                    if suffix=='_empty':assert m.Status==GRB.INFEASIBLE;obj=None;res=None
                    else:
                        assert m.Status==GRB.OPTIMAL;obj=m.ObjVal;res=residual(m)
                        assert abs(obj-(0 if suffix else expected['optimum']))<=1e-7 and max(res.values())<=1e-5
                        write(d/('ENS-Q'+suffix+'_values.json'),{v.VarName:v.X for v in m.getVars()})
                    records.append(dict(case=suffix,status=m.Status,objective=obj,residual=res,model_sha256=sha(path)))
        elif kind=='matrix':
            p=read(OUT/'development_inputs.json')['roles'][0];models={};numeric={};allrows={};typed={}
            for arm in ['ENS-C','ENS-Q','M-B']:
                path=OUT/'exports'/p['id']/(arm+'.lp');m=gp.read(str(path),env=engine);models[arm]=m;options(m)
                vars=m.getVars();numeric[arm]=[(v.VarName,v.LB,v.UB,v.Obj) for v in vars]
                typed[arm]=[v.VType for v in vars];allrows[arm]=[row(c,m) for c in m.getConstrs()]
                assert all(v.VType==('I' if arm=='ENS-C' else 'C') for v in vars if v.VarName.startswith(('p_','d_')))
                assert all(v.VType=='B' for v in vars if v.VarName.startswith(('mode_','z_')))
                assert all(v.VType=='I' for v in vars if v.VarName.startswith(('Y_','load_')))
                assert all(v.VType=='B' for v in vars if v.VarName.startswith('state_') and not v.VarName.startswith('state_g_'))
                assert not any(v.VarName.startswith('theta_') for v in vars)
                r=m.relax();options(r);r.Params.LogFile=str(d/(arm+'_raw_LP.log'));optimize(r,arm+'_raw_LP')
                assert r.Status==GRB.OPTIMAL;values={v.VarName:v.X for v in r.getVars()};res=check(r,values)
                assert res['maximum_absolute_residual']<=1e-6
                records.append(dict(arm=arm,raw_LP=r.ObjVal,rows=m.NumConstrs,columns=m.NumVars,nonzeros=m.NumNZs,
                    model_sha256=sha(path),all_row_bound_residual=res['maximum_absolute_residual'],raw_LP_runtime=r.Runtime))
                r.dispose()
            assert numeric['ENS-C']==numeric['ENS-Q']==numeric['M-B']
            assert allrows['ENS-C']==allrows['ENS-Q']
            assert abs(records[0]['raw_LP']-records[1]['raw_LP'])<=1e-7
            names=[v.VarName for v in models['ENS-C'].getVars()]
            changed=[n for n,a,b in zip(names,typed['ENS-C'],typed['ENS-Q']) if a!=b]
            assert set(changed)=={n for n in names if n.startswith(('p_','d_'))}
            assert typed['ENS-Q']==typed['M-B']
            removed=collections.Counter(allrows['ENS-Q'])-collections.Counter(allrows['M-B'])
            added=collections.Counter(allrows['M-B'])-collections.Counter(allrows['ENS-Q'])
            assert not removed and sum(added.values())==2*p['V']
            import generate_citibike443_regional_v1 as parser
            check_linkage(models['M-B'],parser.parse_instance_mirror(ROOT/p['input_path'])['initial'],p['M'])
            write(d/'matrix_comparison.json',dict(passed=True,quantity_columns_changed=changed,numeric_rows_equal=True,
                ordered_columns_bounds_objective_equal=True,ENS_Q_AB=False,extra_M_B_rows=sum(added.values()),
                additional_rows=[dict(sense=k[0],rhs=k[1],terms=k[2],multiplicity=v) for k,v in added.items()],
                row_name_number_changes_ignored=True,no_extra_theta_or_link=True))
            for m in models.values():m.dispose()
        else:raise ValueError(kind)
    write(d/'summary.json',dict(passed=True,optimizer_calls=calls,records=records,runtime=runtime,source_bindings=bindings(),
        native_parameters=dict(Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6),
        script_sha256=sha(__file__),outer_seconds=time.monotonic()-start))
    print(json.dumps(dict(passed=True,optimizer_calls=calls,records=records)))
if __name__=='__main__':
    if sys.argv[1]=='exports':exports()
    else:native(sys.argv[1],sys.argv[2])
