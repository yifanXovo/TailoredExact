"""Finite zero-Optimize E2/E3 bridge, pair-root and compact contracts."""
from round130_common import *
from round127_data import TRAIN
from round127_qualify import row_family
import round108_reader as core
import collections

def export(p,lo,hi,U,mode,d,layer='E3',fallback=False):
    assert not (d/'build.json').exists()
    args=[E2_EXPORTER if layer=='E2' else EXPORTER,ROOT/p['input_path'],p['T_seconds'],lo,hi,U,mode,d]
    if fallback:args+=['fallback']
    assert metered('zero_'+d.relative_to(OUT/'qualification').as_posix().replace('/','_'),'qualification',args)==0
    assert read(d/'native_metadata.json')['Optimize']==0
    assert read(d/'native_version.json')==dict(major=13,minor=0,technical=2)

def difference(a,b):
    x,y=core.lp_model(a),core.lp_model(b)
    for k in ['objective','order','types','bounds']:assert x[k]==y[k],k
    removed=collections.Counter(x['rows'])-collections.Counter(y['rows'])
    added=collections.Counter(y['rows'])-collections.Counter(x['rows'])
    assert not added and set(removed)<={((),'<=',-1.)}
    families=collections.Counter(row_family(r) for r in y['rows'])
    assert families['cover_3']==families['conditional_3']==0
    return dict(removed_semantic_sentinel_rows=sum(removed.values()),all_other_rows_columns_types_bounds_objective_identical=True,
        pair_cover=families['cover_2'],pair_conditional=families['conditional_2'],ordered_supply=families['ordered_supply'],
        triple_rows=0,other_root_rows_retained=True)

def run():
    assert sha(E2)==E2_SHA and sha(DLL)==DLL_SHA
    records=[]
    for p in [TRAIN[0],TRAIN[2]]:
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        a=core.evidence.instance(ROOT,p);U=core.evidence.objective(a,a['b'],.15)['F'];hi=min(U,(p['V']-1)/p['V'])
        for mode in ['p','ms2']:
            d=OUT/'qualification/bridge'/p['id']/mode
            for layer in ['E2','E3']:export(p,0,hi,U,mode,d/layer,layer)
            assert core.lp_model(d/'E2/original.lp')==core.lp_model(d/'E3/original.lp')
            for n in ['native_columns.csv','native_rows.csv','native_metadata.json']:
                assert (d/'E2'/n).read_bytes()==(d/'E3'/n).read_bytes()
            records.append(dict(id=p['id'],mode=mode,E2_E3_full_semantics_and_actual_columns_equal=True,
                E2_SHA=sha(d/'E2/original.lp'),E3_SHA=sha(d/'E3/original.lp'),different_output_path=True))
        d=OUT/'qualification/pair_root'/p['id']
        for mode in ['ms2','s2-root']:export(p,0,hi,U,mode,d/mode)
        records.append(dict(id=p['id'],emitter='shared',**difference(d/'ms2/original.lp',d/'s2-root/original.lp')))
    # Reuse precisely the old equality fixture, not a formal evaluation role.
    old=WORK/'worktrees/round128/results/unified_exact_round128/qualification/boundaries/zero_S_duration60/input.txt'
    target=OUT/'qualification/equal_cutoff/input.txt';target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old,target)
    p=dict(id='R128_equal_cutoff',input_path=target.relative_to(ROOT).as_posix(),T_seconds=60,V=2,M=1)
    for fallback in [False,True]:
        d=OUT/'qualification/equal_cutoff'/('fallback' if fallback else 'shared')
        for mode in ['ms2','s2-root']:export(p,0,.3,.3,mode,d/mode,fallback=fallback)
        diff=difference(d/'ms2/original.lp',d/'s2-root/original.lp')
        assert diff['removed_semantic_sentinel_rows']==1
        records.append(dict(id=p['id'],emitter='fallback' if fallback else 'shared',**diff))
    # Finite medium fallback check: preserves pair/order/CG/A/B in both emitters.
    p=TRAIN[0];a=core.evidence.instance(ROOT,p);U=core.evidence.objective(a,a['b'],.15)['F'];hi=min(U,(p['V']-1)/p['V'])
    d=OUT/'qualification/pair_root_fallback'/p['id']
    for mode in ['ms2','s2-root']:export(p,0,hi,U,mode,d/mode,fallback=True)
    records.append(dict(id=p['id'],emitter='fallback',**difference(d/'ms2/original.lp',d/'s2-root/original.lp')))
    for p in read(OUT/'input_manifest.json')['roles']:
        export(p,0,0,0,'p',OUT/'qualification/references'/p['id'])
    source=source_bindings();prior=read(ROOT/'results/unified_exact_round129/E2_identity.json')['source_bindings']
    changed=[n for n,h in source.items() if prior[n]!=h]
    assert set(changed)=={'include/Round127Research.hpp','src/GurobiBaseline.cpp'}
    write(OUT/'qualification/zero_qualification.json',dict(UTC=utc(),passed=True,Optimize=0,checks=records,
      E2_PE_SHA=sha(E2),E3_PE_SHA=sha(E3),DLL_SHA=sha(DLL),source_changes=changed,
      H_options_H_implementation_and_native_default_parameter_code_unchanged=True,
      P_PS_full_matrix_and_Start_requirement='pending separate closed native_qualification.json',
      inherited_boundary_contract='R128 equal cutoff, S=0, tiny-positive-U0 and open-return reports retained; only new pair-root combination checked here'))
    print('ZERO_OPTIMIZE_QUALIFICATION_PASS')
def alias():
    p=dict(TRAIN[0]);target=OUT/'qualification/renamed/unchanged_mathematics.txt'
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p['input_path'],target)
    assert sha(target)==p['input_sha256']
    p['input_path']=target.relative_to(ROOT).as_posix()
    a=core.evidence.instance(ROOT,p);U=core.evidence.objective(a,a['b'],.15)['F'];hi=min(U,(p['V']-1)/p['V'])
    d=OUT/'qualification/renamed/export'
    export(p,0,hi,U,'ms2',d)
    prior=OUT/'qualification/bridge/S12/ms2/E2'
    assert core.lp_model(prior/'original.lp')==core.lp_model(d/'original.lp')
    for n in ['native_columns.csv','native_rows.csv','native_metadata.json']:assert (prior/n).read_bytes()==(d/n).read_bytes()
    write(OUT/'qualification/filename_identity_addendum.json',dict(passed=True,Optimize=0,
        original_input=TRAIN[0]['input_path'],renamed_input=p['input_path'],input_SHA=sha(target),
        E2_original_E3_renamed_full_matrix_columns_types_bounds_objective_equal=True,
        native_model_parameters_and_H_source_unchanged=True,performance_screening=False))
    report=read(OUT/'qualification/zero_qualification.json')
    report['P_PS_full_matrix_and_Start_requirement']='separate closed native_qualification.json'
    report['filename_identity_addendum_SHA']=sha(OUT/'qualification/filename_identity_addendum.json')
    write(OUT/'qualification/zero_qualification.json',report)
if __name__=='__main__':(alias if len(sys.argv)>1 and sys.argv[1]=='alias' else run)()
