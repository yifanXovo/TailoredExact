"""Close derived research records; never Optimize or alter sealed raw evidence."""
from round162_common import *
import copy

def metadata():
    changed=[]
    def rename(v):
        if isinstance(v,dict):
            if 'max_stationarity_residual' in v:
                v['max_reduced_cost_box_coefficient']=v.pop('max_stationarity_residual')
            for x in v.values():rename(x)
        elif isinstance(v,list):
            for x in v:rename(x)
    for p in sorted((OUT/'reports').glob('*.json')):
        v=read(p);old=copy.deepcopy(v);rename(v)
        if v!=old:
            before=sha(p);write(p,v);changed.append(dict(path=p.relative_to(ROOT).as_posix(),before_SHA256=before,after_SHA256=sha(p)))
    label_receipt=OUT/'engineering/derived_label_correction.json'
    if changed or not label_receipt.exists():
        write(label_receipt,dict(changed=changed,Optimize=0,arithmetic_recomputed=False,
            reason='A reduced-cost coefficient compensated on finite boxes is not a stationarity error. Rename the old derived label only; all numerical values and sealed raw files remain unchanged.'))
    complete=read(OUT/'reports/complete.json');assert len(complete['samples'])==6 and not complete['full_four_role_confirmation']
    gate=read(OUT/'reports/complete_main_gate_metrics.json');assert all(p['U_gain']< -1e-7 and p['L_gain']==0 for p in gate['pairs'])
    decision=dict(status='CLOSE_CURRENT_CONDITIONING_LAYER_DEFAULT_OFF',branch='primary-positive, permitted stop after six complete arms',
        mathematical_information='Qualified NB35 free full-Q original-J increment beyond OLD+STOCK; one projected row retains about 87.0% in the fixed development scope.',
        RX35='Saved S point cannot complete, but free F remixes to the same objective within inherited precision.',
        Native='Four matched 900s arms complete: NB35 gains physical U with weaker L, RX35 loses U/L. This justified the complete-method test.',
        complete='Six fresh complete arms qualify; PC has worse U than both Eplus and Stock on both primary roles, identical proof L, and no certificate.',
        small_roles='Positions 7--10 were not started, using the predeclared adverse-main-role stop. No four-role confirmation or complete K20/RX20 claim.',
        default_off=True,mechanism_revisions_used=0,new_certificates=0,complete_arms=6,planned_maximum_arms=10,
        stable_GI_TBC_B_changed=False,Eplus_default_changed=False,main_comparison_CSV_changed=False,
        recommendation='Retain the complete-duration conditional-completion finding and the finite numerical projection evidence. Stop this frozen continuous-Q conditioning candidate; do not promote it or open another mechanism/grid. Any later claim of algorithmic value needs independent held-out confirmation against both fresh controls.',
        evidence=['reports/N-B35-S_audit.json','reports/N-B35-S_C_LP_v1_projection_audit.json','reports/native.json','reports/complete.csv','complete_small_role_decision.json'])
    write(OUT/'decision.json',decision)
    q=read(OUT/'qualification/v2/new_interfaces.json');dev=read(OUT/'development_review.json');full=read(OUT/'complete_review.json')
    assert q['PASS'] and dev['PASS'] and full['PASS']
    build=read(OUT/'engineering/cmake_delivery.json');assert build['PASS']
    current=(ROOT/'scripts/round162_complete_read.py').read_bytes()
    start=current.index(b"    for name,digest in manifest['source_hashes'].items():")
    end=current.index(b"    for name,digest in m['helpers'].items():",start)
    actual=current[:start]+b"    for name,digest in manifest['source_hashes'].items():assert sha(ROOT/name)==digest,name\n"+current[end:]
    assert hashlib.sha256(actual).hexdigest()==full['source_SHA256']
    reader_path=OUT/'engineering/review_source_bytes'/(full['source_SHA256']+'.py.txt')
    reader_path.parent.mkdir(parents=True,exist_ok=True);reader_path.write_bytes(actual)
    write(OUT/'final_review.json',dict(PASS=True,UTC=utc(),reviewer='same Codex agent; separate saved-evidence scripts, not independent personnel',
        development_review_SHA256=sha(OUT/'development_review.json'),complete_review_SHA256=sha(OUT/'complete_review.json'),
        qualification_SHA256=sha(OUT/'qualification/v2/new_interfaces.json'),scope_qualification_SHA256=sha(OUT/'qualification/scope/scope_qualification.json'),
        completed_arms=6,actual_full_fleets=sum(x['fleets'] for x in full['checks']),protected_dirty_files=full['protected_dirty_count'],
        all_original_penalty_physical_and_product_contracts_checked=True,source_only_once=True,new_source_scalar_floor=False,
        formal_new_columns=0,formal_NodeLimit_unlimited=True,Optimize=0,
        actual_complete_verifier_bytes=reader_path.relative_to(ROOT).as_posix(),
        clean_default_and_research_build_PASS=True,build_SHA256=sha(OUT/'engineering/cmake_delivery.json'),
        late_default_only_stub_fix_SHA256=sha(OUT/'engineering/default_stub_fix.json'),
        repeated_development_scientific_audit=False,scope='Aggregate the previously passed separate development audit and the one new complete-panel independent-script readback.'))
    write(OUT/'science_identity.json',dict(UTC=utc(),base=BASE,branch='codex/round162-physical-g-completion',
        development_CPP_commit=git('rev-parse','8bbffa3c4').decode().strip(),complete_CPP_commit='e920b92e199e825ec89a2932f701861ff158e0d4',
        frozen_orchestration_commit=git('rev-parse','d6cbfb462').decode().strip(),Native_manifest_SHA256=sha(OUT/'measured_manifest.json'),
        complete_manifest_SHA256=sha(OUT/'complete_candidate_manifest.json'),matrix_SHA256=sha(OUT/'complete_matrix.json'),
        development_PE_SHA256=read(OUT/'candidate_manifest.json')['research_PE_SHA'],
        complete_PE_SHA256=read(OUT/'complete_candidate_manifest.json')['production_PE_SHA'],DLL_SHA256=DLL_SHA,
        late_source_inventory_exception=read(OUT/'engineering/default_stub_fix.json'),
        science_snapshot='The later normal Git science commit fixes these records without trying to contain its own commit SHA.',
        delivery_metadata='A separate later publication record binds the science commit and Draft PR; measured PE is unchanged.'))
    print('PASS final derived metadata, decision and aggregate review; no Optimize',flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
