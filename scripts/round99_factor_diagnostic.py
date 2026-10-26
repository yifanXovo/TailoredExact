"""4 raw LPs and independent presolve exports on one complete legal root state.
No native MIP optimize here: production logs provide that separate scope.
"""
import sys,json,time,gzip,hashlib,math
import gurobipy as gp
from gurobipy import GRB
from round99_common import *
from round98_projection_vector_audit import check
import generate_citibike443_regional_v1 as parser
MODES=['aggregate','q-integer','m-binary','projected']
def size(m):return dict(rows=m.NumConstrs,columns=m.NumVars,nonzeros=m.NumNZs,binary=m.NumBinVars,integer=m.NumIntVars)
def signature(m,types=False):
    h=hashlib.sha256()
    for v in m.getVars():h.update(repr((v.VarName,v.LB,v.UB,v.Obj,v.VType if types else None)).encode())
    for c in m.getConstrs():
        r=m.getRow(c);h.update(repr((c.ConstrName,c.Sense,c.RHS,[(r.getVar(i).VarName,r.getCoeff(i)) for i in range(r.size())])).encode())
    return h.hexdigest()
def run(role,label):
    p=next(p for p in read(OUT/'development_inputs.json')['roles'] if p['id']==role)
    dest=OUT/'diagnostics'/label;dest.mkdir(parents=True,exist_ok=False)
    write(dest/'plan.json',dict(maximum_optimize=4,process_cap=300,role=p,scope='full initial root; diagnostic replayed cutoff only'))
    start=time.monotonic();records=[];vectors={};calls=0
    ind=parser.parse_instance_mirror(ROOT/p['input_path']);models={}
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start();assert gp.gurobi.version()==(13,0,2)
        for mode in MODES:
            path=OUT/'exports'/role/(mode+'.lp');assert sha(path)==read(path.with_suffix('.json'))['sha256']
            m=gp.read(str(path),env=env);models[mode]=m
            m.Params.Threads=1;m.Params.Seed=0;m.Params.Presolve=-1
            original=size(m);numeric=signature(m);typed=signature(m,True)
            pm=m.presolve();ps=size(pm);pm.write(str(dest/(mode+'_standalone_presolve.lp')))
            families={}
            for v in pm.getVars():
                key=v.VarName.split('_')[0]+':'+v.VType;families[key]=families.get(key,0)+1
            ps['families_by_surviving_name']=families;pm.dispose()
            r=m.relax();r.Params.Threads=1;r.Params.Seed=0;r.Params.LogFile=str(dest/(mode+'_raw_LP.log'))
            r.Params.TimeLimit=max(.001,285-(time.monotonic()-start))
            with (dest/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='start',name=mode+'_raw_LP'))+'\n');f.flush()
            calls+=1;r.optimize()
            with (dest/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='return',name=mode+'_raw_LP',status=r.Status,runtime=r.Runtime))+'\n');f.flush()
            assert r.Status==GRB.OPTIMAL
            vectors[mode]={v.VarName:v.X for v in r.getVars()}
            with gzip.open(dest/(mode+'_values.json.gz'),'wt') as f:json.dump(vectors[mode],f)
            actual=check(r,vectors[mode]);assert actual['maximum_absolute_residual']<=1e-6
            row=dict(mode=mode,model_sha256=sha(path),original=original,numeric_signature=numeric,typed_signature=typed,
                standalone_presolved=ps,standalone_presolved_sha256=sha(dest/(mode+'_standalone_presolve.lp')),
                raw_LP=r.ObjVal,raw_LP_violation=actual['maximum_absolute_residual'],raw_LP_iterations=r.IterCount,
                raw_LP_runtime=r.Runtime,values_sha256=sha(dest/(mode+'_values.json.gz')))
            records.append(row);write(dest/(mode+'_record.json'),row);r.dispose()
        assert records[0]['numeric_signature']==records[2]['numeric_signature'],'R1/M-B changed matrix'
        assert records[1]['numeric_signature']==records[3]['numeric_signature'],'Q-I/R2 changed matrix'
        assert max(r['raw_LP'] for r in records)-min(r['raw_LP'] for r in records)<=1e-7,'raw LP mismatch; identity/numeric failure'
        cross=[]
        for source in MODES:
            for target in MODES:
                values=dict(vectors[source])
                if target in ['q-integer','projected']:
                    values={n:x for n,x in values.items() if not n.startswith('mode_')}
                else:
                    for k,Q in enumerate(p['Q_vector']):
                        for i in range(1,p['V']+1):
                            a=min(ind['initial'][i],Q);values[f'mode_{k}_{i}']=values[f'p_{k}_{i}']/a if a else 0
                audit=check(models[target],values);assert audit['maximum_absolute_residual']<=1e-6
                cross.append(dict(source=source,target=target,maximum_residual=audit['maximum_absolute_residual'],objective=audit['objective']))
        for m in models.values():m.dispose()
    write(dest/'summary.json',dict(passed=True,optimizer_calls=calls,records=records,cross_projection=cross,
        role=p,outer_seconds=time.monotonic()-start,source_bindings=bindings(),script_sha256=sha(__file__),
        presolve_scope='Model.presolve diagnostic only; optimize internal model and uncrush mapping unavailable'))
    print(json.dumps(dict(role=role,passed=True,optimizer_calls=calls,raw_LP=[r['raw_LP'] for r in records],presolved=[r['standalone_presolved'] for r in records])))
if __name__=='__main__':run(sys.argv[1],sys.argv[2])
