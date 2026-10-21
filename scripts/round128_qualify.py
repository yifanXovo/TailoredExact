"""Finite E1/E2 bridge, semantic sentinel differences and boundary witnesses."""
from round128_common import *
import collections,copy,math,types
import round108_reader as core
import round127_boundaries as boundary
from round127_qualify import compare

def export(p,lo,hi,U,mode,d,layer='E2',fallback=False):
    if (d/'build.json').exists():
        assert sha(d/'original.lp')==read(d/'build.json')['canonical_sha256'];return
    exe=BUILD/'Round128ExportE2.exe' if layer=='E2' else WORK/'build-cache/round127/Round127ExportE1.exe'
    label='zero_'+d.relative_to(OUT/'qualification').as_posix().replace('/','_')
    args=[exe,ROOT/p['input_path'],p['T_seconds'],lo,hi,U,mode,d]
    if fallback:args+=['fallback']
    assert metered(label,'qualification',args)==0

def root_diff(a,b):
    x=core.lp_model(a);y=core.lp_model(b)
    assert x['objective']==y['objective'] and x['types']==y['types'] and x['bounds']==y['bounds'] and x['order']==y['order']
    removed=collections.Counter(x['rows'])-collections.Counter(y['rows']);added=collections.Counter(y['rows'])-collections.Counter(x['rows'])
    assert not added and set(removed)<= {((),'<=',-1.0)}
    return dict(removed_semantic_sentinel_rows=sum(removed.values()),all_other_duplicate_preserving_rows_columns_types_bounds_objective_identical=True)

def point(p,w,path):
    # The inherited mapper fails on an unknown actual column and checks every
    # row and bound. Actual types/objective are checked separately below.
    r=boundary.physical_point(p,w,core.lp_model(path));physical=core.full_fleet(ROOT,p,w)
    assert abs(physical['F']-r['objective']['F'])<=1e-12
    return r

def zero():
    case=types.FunctionType(boundary.case.__code__,dict(vars(boundary),ROOT=ROOT,OUT=OUT),'case')
    p=case('zero_S_duration60',[0,0],[1,1],[1],60)
    cases=[('La_equal_c',p,0.,.3,.3),('La_less_c',p,0.,.31,.31),('La_greater_c_illegal_Start',p,0.,.29,.29),
        ('within_1e9_from_below',p,0.,.3000000005,.3000000005)]
    p2=case('zero_S_duration3600',[0,0],[1,1],[1],3600);cases.append(('T3600_no_old_sentinel',p2,0.,.3,.3))
    p3=case('inventory_loaded_return',[4,0],[2,2],[1],3600)
    a=core.evidence.instance(ROOT,p3);u=core.evidence.objective(a,a['b'],.15)['F'];mid=min(u,.5)/2
    cases += [('inventory_root',p3,0.,min(u,.5),u),('shared_left',p3,0.,mid,u),('shared_right',p3,mid,min(u,.5),u)]
    records=[]
    for label,p,lo,hi,U in cases:
        for fallback in [False,True] if label in ['La_equal_c','T3600_no_old_sentinel'] else [False]:
            d=OUT/'qualification/boundaries'/label/('fallback' if fallback else 'shared')
            for mode in ['mb','md-r']:export(p,lo,hi,U,mode,d/mode,fallback=fallback)
            diff=root_diff(d/'mb/original.lp',d/'md-r/original.lp')
            witnesses=[dict(label='empty',routes=[])]
            if p['id']=='inventory_loaded_return':
                witnesses += [dict(label='loaded_return',routes=[dict(vehicle=0,nodes=[0,1,0],operations=[dict(station=1,pickup=1,drop=0)])]),
                    dict(label='shared_endpoint',routes=[dict(vehicle=0,nodes=[0,1,2,0],operations=[dict(station=1,pickup=1,drop=0),dict(station=2,pickup=0,drop=1)])])]
            for w in witnesses:
                Y=list(core.evidence.instance(ROOT,p)['b'])
                for route in w['routes']:
                    for op in route['operations']:Y[op['station']]+=op['drop']-op['pickup']
                w['F']=core.evidence.objective(core.evidence.instance(ROOT,p),Y,.15)['F']
                ph=core.full_fleet(ROOT,p,w);in_scope=lo<=ph['G']<=hi and ph['F']<=U
                b=point(p,w,d/'mb/original.lp');r=point(p,w,d/'md-r/original.lp')
                if in_scope:assert not r['violations'],(label,w,r)
                else:assert r['violations'],('incompatible Start must be rejected',label,w)
                records.append(dict(case=label,fallback=fallback,witness=w['label'],physical=ph,scope=[lo,hi],cutoff=U,
                    expected_Start_accepted=in_scope,old=b,new=r,**diff,model_SHA=sha(d/'md-r/original.lp')))
    eq=next(r for r in records if r['case']=='La_equal_c' and not r['fallback'])
    assert len(eq['old']['violations'])==1 and eq['removed_semantic_sentinel_rows']==1
    assert eq['new']['objective']['G']==0 and eq['new']['objective']['P']==2
    write(OUT/'qualification/boundary_vectors.json',dict(UTC=utc(),Optimize=0,records=records,
        decimal_boundary='3/10 exact in the physical toy; binary64 U and lambda*2 are represented by the same 0.29999999999999999 value',
        theory='B_I=min(a+lambda*P_lower,c) by actual-domain/cutoff-complement coverage; equality rules out strict improvement, not inclusive feasibility',
        near_equality='For c-1e-9<=La<c the supported raw lower bound is La; no new exact-c certificate is inferred',
        no_rational_global_error_bound=True,no_analytic_bound_injected=True))
    # One small and one medium full original model and actual native VTypes,
    # bounds/objective bridge; no Optimize and no Fingerprint shortcut.
    from round127_data import TRAIN
    bridges=[]
    for p in [TRAIN[0],TRAIN[2]]:
        path=ROOT/p['input_path']
        if sha(path)!=p['input_sha256']:path.write_bytes(git('show',BASE+':'+p['input_path']))
        assert sha(path)==p['input_sha256']
        a=core.evidence.instance(ROOT,p);U=core.evidence.objective(a,a['b'],.15)['F'];hi=min(U,(p['V']-1)/p['V'])
        for mode in ['mb','p','ms2']:
            d=OUT/'qualification/bridge'/p['id']/mode
            for layer in ['E1','E2']:export(p,0,hi,U,mode,d/layer,layer)
            assert core.lp_model(d/'E1/original.lp')==core.lp_model(d/'E2/original.lp')
            for n in ['native_columns.csv','native_rows.csv','native_metadata.json']:assert (d/'E1'/n).read_bytes()==(d/'E2'/n).read_bytes()
            bridges.append(dict(id=p['id'],mode=mode,full_semantics_and_native_types_bounds_objective_identical=True,Optimize=0))
    write(OUT/'qualification/E1_E2_zero_bridge.json',dict(UTC=utc(),comparisons=bridges,Optimize=0))
    print(json.dumps(dict(boundary_checks=len(records),bridges=len(bridges),Optimize=0)))

def historical():
    import csv
    records=[]
    for row in csv.DictReader((PREVIOUS/'results/unified_exact_round127/core_arms.csv').open(encoding='utf-8')):
        if row['method']!='MB':continue
        d=Path(row['destination']);obs=read(d/'observations.json');calls=[r['payload'] for r in obs if r['payload']['kind']=='call']
        models={c['model_sha256']:Path(c['model_path']) for c in calls};facts=[]
        for h,path in models.items():
            assert sha(path)==h
            m=core.lp_model(path);sentinels=sum(1 for terms,sense,rhs in m['rows'] if terms==() and sense=='<=' and rhs==-1.)
            facts.append(dict(path=str(path),SHA=h,sentinel_rows=sentinels,rows=len(m['rows'])))
        records.append(dict(id=row['id'],PE_SHA=row['PE_SHA'],input_SHA=row['input_SHA'],certificate=row['certificate'],
            observations_SHA=sha(d/'observations.json'),calls=len(calls),unique_models=facts,
            saved_call_depends_on_sentinel=any(m['sentinel_rows'] for m in facts)))
    assert len(records)==3
    write(OUT/'qualification/R127_finite_impact.json',dict(UTC=utc(),roles=records,Optimize=0,
        scope='Only the three saved R127 core MB call matrices; no global historical revalidation or blanket revocation',
        real_certificate_sentinel_dependence_observed=any(r['saved_call_depends_on_sentinel'] and r['certificate']=='True' for r in records)))
    print(json.dumps(records))

def roles():
    import csv
    records=[]
    # Saved same-H root scopes are qualification fixtures only. Formal arms
    # still compute their own H and are compared again after their actual runs.
    for r in csv.DictReader((PREVIOUS/'results/unified_exact_round127/core_arms.csv').open(encoding='utf-8')):
        if r['method']!='MB':continue
        old=Path(r['destination']);i=read(old.parents[1]/'identity.json')
        p=next(l['panel'] for l in i['launches'] if l['method']=='MB')
        c=next(x['payload'] for x in read(old/'observations.json') if x['payload']['kind']=='call')
        assert c['leaf']=='L0' and c['lower_g']==0
        d=OUT/'qualification/formal_role_roots'/p['id']
        for mode in ['mb','md-r','ms2']:export(p,c['lower_g'],c['upper_g'],c['cutoff'],mode,d/mode)
        m=core.lp_model(d/'mb/original.lp');assert m==core.lp_model(Path(c['model_path']))
        records.append(dict(id=p['id'],archived_H_scope_only_not_a_formal_UB=True,initial_U=c['cutoff'],scope=[c['lower_g'],c['upper_g']],
            MB_sentinel_rows=sum(1 for t,s,b in m['rows'] if not t and s=='<=' and b==-1),
            MD_R=root_diff(d/'mb/original.lp',d/'md-r/original.lp'),MS2=compare(d/'mb/original.lp',d/'ms2/original.lp','ms2',p['V'],p['M'])))
    from round127_data import TRAIN
    for p in [TRAIN[0],TRAIN[2]]:
        a=core.evidence.instance(ROOT,p);U=core.evidence.objective(a,a['b'],.15)['F'];hi=min(U,(p['V']-1)/p['V'])
        for mode in ['mb','p','ms2']:
            d=OUT/'qualification/final_bridge'/p['id']/mode
            export(p,0,hi,U,mode,d)
            earlier=OUT/'qualification/bridge'/p['id']/mode/'E1'
            assert core.lp_model(earlier/'original.lp')==core.lp_model(d/'original.lp')
            for n in ['native_columns.csv','native_rows.csv','native_metadata.json']:assert (earlier/n).read_bytes()==(d/n).read_bytes()
            assert read(d/'native_version.json')==dict(major=13,minor=0,technical=2)
    write(OUT/'qualification/formal_role_root_differences.json',dict(UTC=utc(),Optimize=0,records=records,
        final_E2_PE_SHA=sha(E2),final_exporter_SHA=sha(BUILD/'Round128ExportE2.exe'),
        E1_final_E2_MB_P_MS2_full_native_bridge=['S12','R98-C2'],actual_Gurobi_version='13.0.2',
        formal_same_H_scope_checked_again_after_execution=True))
    print(json.dumps(dict(roles=3,final_bridge=6,Optimize=0)))

if __name__=='__main__':{'zero':zero,'historical':historical,'roles':roles}[sys.argv[1]]()
