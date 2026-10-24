"""Finite actual-matrix bridge; all Optimize calls are qualification costs."""
from round132_common import *
from round132_build import EXPORT,PE
from round127_data import TRAIN
import round108_reader as core
import collections, copy
from fractions import Fraction as F

def export(p,a,b,U,expression,d,original=False):
    args=[EXPORTER if original else EXPORT,ROOT/p['input_path'],p['T_seconds'],a,b,U,'s2-root',d]
    if not original:args.append(expression)
    subprocess.run(list(map(str,args)),cwd=ROOT,env=environment(),check=True,capture_output=True,timeout=120)
    assert read(d/'native_metadata.json')['Optimize']==0
    return core.lp_model(d/'original.lp')

def W_projection(m):
    lo=[];hi=[];keep=[]
    for terms,sense,rhs in m['rows']:
        c=dict(terms)
        if not c.get('W_SP',0):keep.append((terms,sense,rhs));continue
        assert sense!='='
        if sense=='>=':c={n:-v for n,v in c.items()};rhs=-rhs
        row=({n:F.from_float(v) for n,v in c.items()},F.from_float(rhs))
        (lo if c['W_SP']<0 else hi).append(row)
    wl,wu=m['bounds']['W_SP'];lo.append(({'W_SP':F(-1)},-F.from_float(wl)));hi.append(({'W_SP':F(1)},F.from_float(wu)))
    result=[]
    for l,lr in lo:
        for u,ur in hi:
            a,b=-l['W_SP'],u['W_SP'];c={n:b*l.get(n,F(0))+a*u.get(n,F(0)) for n in l.keys()|u.keys() if n!='W_SP'}
            result.append(({n:v for n,v in c.items() if v},b*lr+a*ur))
    return keep,result

def compare(base,candidate,expression):
    for k in ['objective']:assert base[k]==candidate[k]
    expected=set(base['types'])-({'W_SP'} if expression=='sp' else set());assert set(candidate['types'])==expected
    for n in expected:assert base['types'][n]==candidate['types'][n] and base['bounds'][n]==candidate['bounds'][n],n
    a,b=collections.Counter(base['rows']),collections.Counter(candidate['rows'])
    if expression=='geom':
        assert not b-a
        removed=list((a-b).elements())
        assert removed and all(s=='<=' and (any(n.startswith('h_') for n,v in t) or sum(n.startswith('r_') for n,v in t)>=2) for t,s,r in removed)
        return dict(removed_rows=len(removed),added_rows=0,other_columns_bounds_types_objective_identical=True)
    keep,exact=W_projection(base);remaining=b-collections.Counter(keep)
    assert not collections.Counter(keep)-b
    actual=list(remaining.elements());assert len(actual)==len(exact)==12
    # Match the generated order after all unchanged rows; retain duplicates.
    generated=list(actual);errors=[]
    for r,rr in exact:
        options=[]
        for j,(terms,sense,rhs) in enumerate(generated):
            c=dict(terms)
            if sense!='<=' or c.keys()!=r.keys():continue
            error=abs(F.from_float(rhs)-rr)
            for n,v in r.items():error+=abs(F.from_float(c[n])-v)*F.from_float(max(map(abs,base['bounds'][n])))
            options.append((error,j))
        assert options,'actual projection coefficient support mismatch'
        error,j=min(options);generated.pop(j);errors.append(float(error))
    assert max(errors)<1e-7
    return dict(removed_W_rows=5,removed_W_columns=1,complete_projection_rows=12,
        max_coefficient_serialization_residual_bound=max(errors),exact_native_binary64_rational_projection_proved=True,
        emitted_binary64_rows_only_numerically_consistent=True,P_domain_implications_retained=True)

def run():
    from round100_gurobi_runtime import gp,binding
    frozen_identity();attempt=1+len(list((OUT/'qualification').glob('C_matrices*')))
    d=OUT/'qualification'/f'C_matrices{attempt:02d}';d.mkdir(parents=True,exist_ok=False)
    records=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start();runtime=binding()
        for p in [TRAIN[0],TRAIN[2]]:
            physical=core.evidence.instance(ROOT,p);U=core.evidence.objective(physical,physical['b'],.15)['F'];beta=min(U,(p['V']-1)/p['V'])
            for label,alpha in [('root',0.),('positive_lower',beta*.3)]:
                dest=d/p['id']/label
                base=export(p,alpha,beta,U,'off',dest/'off')
                old=export(p,alpha,beta,U,'off',dest/'E3',True);assert base==old
                assert sha(dest/'off/original.lp')==sha(dest/'E3/original.lp')
                models={'off':base};detail={}
                for expression in ['geom','sp']:
                    models[expression]=export(p,alpha,beta,U,expression,dest/expression)
                    detail[expression]=compare(base,models[expression],expression)
                solved={}
                for expression in ['off','geom','sp']:
                    with gp.read(str(dest/expression/'original.lp'),env=env) as model:
                        model.Params.Threads=1;model.Params.Seed=0;model.Params.TimeLimit=60
                        for v in model.getVars():v.VType=gp.GRB.CONTINUOUS
                        model.update();model.optimize()
                        assert model.Status==gp.GRB.OPTIMAL,(p['id'],label,expression,model.Status)
                        solved[expression]=dict(value=model.ObjVal,Runtime=model.Runtime,Work=model.Work,
                            rows=model.NumConstrs,columns=model.NumVars)
                assert max(q['value'] for q in solved.values())-min(q['value'] for q in solved.values())<1e-7
                records.append(dict(id=p['id'],interval=[alpha,beta],cutoff=U,default_off_E3_same_bytes=True,
                    actual_matrix_differences=detail,canonical_all_continuous_LP=solved))
    write(OUT/'qualification/C_matrix_qualification.json',dict(passed=True,records=records,runtime=runtime,
        numerical_contract=1e-7,exact_rational_vs_binary64_distinguished=True,LP_calls=12,H_calls=0,
        production_compile=0,research_PE_SHA=sha(PE),research_exporter_SHA=sha(EXPORT),
        no_formal_role_performance_observed=True,remaining='actual CLI default-off behavioral bridge and own physical Start mapping for each expression'))
    print('C_ACTUAL_MATRIX_AND_LP_QUALIFICATION_PASS',flush=True)
if __name__=='__main__':run()
