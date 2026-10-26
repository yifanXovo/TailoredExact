"""Incremental identity, one old fixture pair of sizes, and zero-Optimize references."""
from round129_common import *
import collections, math
from round127_data import TRAIN
from round127_qualify import row_family
import round108_reader as core

def support_family(row):
    family=row_family(row)
    if family.startswith(('cover_','conditional_')):
        vehicles={n.split('_')[1] for n,_ in row[0] if n.startswith(('p_','z_'))}
        if len(vehicles)!=1:return 'other'
    return family

def difference(base,pair):
    a=core.lp_model(base);b=core.lp_model(pair)
    for k in ['objective','order','types','bounds']:assert a[k]==b[k],k
    ca,cb=collections.Counter(a['rows']),collections.Counter(b['rows'])
    assert not cb-ca,'MS2 adds or changes a row'
    removed=ca-cb;families=collections.Counter()
    for row,count in removed.items():families[support_family(row)]+=count
    assert set(families)<= {'cover_3','conditional_3'},families
    af=collections.Counter(support_family(x) for x in a['rows']);bf=collections.Counter(support_family(x) for x in b['rows'])
    assert af['cover_2']==bf['cover_2'] and af['conditional_2']==bf['conditional_2'] and af['ordered_supply']==bf['ordered_supply']
    assert bf['cover_3']==bf['conditional_3']==0
    assert sum(removed.values())==af['cover_3']+af['conditional_3']
    return dict(removed_rows=sum(removed.values()),removed_columns=[],families=dict(families),
        pair_cover_before=af['cover_2'],pair_conditional_before=af['conditional_2'],
        triple_cover_before=af['cover_3'],triple_conditional_before=af['conditional_3'],
        pair_cover_after=bf['cover_2'],pair_conditional_after=bf['conditional_2'],
        triple_cover_after=bf['cover_3'],triple_conditional_after=bf['conditional_3'],ordered_supply=af['ordered_supply'],
        remaining_objective_columns_order_types_bounds_and_duplicate_preserving_rows_identical=True,
        MB_model_SHA=sha(base),MS2_model_SHA=sha(pair),triple_deletion_exposed=bool(sum(removed.values())))

def export(p,lo,hi,U,mode,d):
    if (d/'build.json').exists():
        assert sha(d/'original.lp')==read(d/'build.json')['canonical_sha256']
        assert read(d/'native_metadata.json')['Optimize']==0
        return
    label='zero_'+d.relative_to(OUT/'qualification').as_posix().replace('/','_')
    assert metered(label,'qualification',[EXPORTER,ROOT/p['input_path'],p['T_seconds'],lo,hi,U,mode,d])==0
    assert read(d/'native_metadata.json')['Optimize']==0
    assert read(d/'native_version.json')==dict(major=13,minor=0,technical=2)

def run():
    identity();records=[]
    for p in [TRAIN[0],TRAIN[2]]:
        a=core.evidence.instance(ROOT,p);U=core.evidence.objective(a,a['b'],.15)['F'];hi=min(U,(p['V']-1)/p['V'])
        d=OUT/'qualification/known_exports'/p['id']
        for mode in ['mb','ms2']:export(p,0,hi,U,mode,d/mode)
        diff=difference(d/'mb/original.lp',d/'ms2/original.lp')
        assert diff['removed_rows']==p['M']*math.comb(p['V'],3)
        mb=core.rows(d/'mb/native_columns.csv');ms=core.rows(d/'ms2/native_columns.csv');assert mb==ms
        records.append(dict(id=p['id'],scope=[0,hi],fixture_U=U,**diff))
    # These are cold structural references required by the inherited P reader,
    # not preliminary performance measurements on evaluation inputs.
    for p in read(OUT/'input_manifest.json')['roles']:
        export(p,0,0,0,'p',OUT/'qualification/references'/p['id'])
    write(OUT/'qualification/incremental_qualification.json',dict(UTC=utc(),assets=identity(),Optimize=0,
        fixture_exports=records,new_input_performance_screening=False,qualification_smoke_native_Optimize=0,
        original_model_Seed_reader_and_full_domain_mask_reused=True,identity_changed=False,
        no_boundary_or_MD_R_repeat=True,no_production_or_exporter_compile=True,
        all_formal_own_H_roots_must_be_rechecked=True,budget=budget()))
    print('INCREMENTAL_QUALIFICATION_COMPLETE Optimize=0; known small/medium exports and five cold structural references')

if __name__=='__main__':run()
