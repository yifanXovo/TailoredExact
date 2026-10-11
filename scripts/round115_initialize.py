"""Directed offline preparation; no native run, compilation or new reference."""
from round115_common import *
import shutil,subprocess

def initialize():
    tick=time.perf_counter();oldroot=Path('E:/codes/ExactEBRP-round114');old=oldroot/'results/unified_exact_round114'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=oldroot,text=True).strip()==BASE
    assert not (OUT/'protocol.json').exists()
    shutil.copyfile('C:/Users/Administrator/.codex/attachments/d3dad822-fa10-45c1-9f88-029ecff543c3/已粘贴的文本.txt',OUT/'goal.md')
    peold=oldroot/'build/research/round114-inherited/ExactEBRP.exe';assert sha(peold)==PE_SHA and sha(DLL)==DLL_SHA
    PE.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(peold,PE)
    production=read(old/'production_identity.json');assert production['source_bindings']==bindings()
    write(OUT/'production_identity.json',dict(production,round115_inherited_PE_origin=str(peold),round114_head=BASE,production_recompiled=False))
    manifest=read(old/'input_manifest.json');h=manifest['qualification_roles'][0]
    h['method_order']=['P-GRB','P-S','ENS-C','M-B']
    for p in manifest['roles']+[h]:
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        dst=OUT/'qualification/reference'/p['id'];dst.mkdir(parents=True)
        for n in ['original.lp','build.json']:shutil.copyfile(old/'qualification/reference'/p['id']/n,dst/n)
        assert sha(dst/'original.lp')==read(dst/'build.json')['canonical_sha256']
    write(OUT/'input_manifest.json',manifest)
    graph=dict(schema='round115-producer-dependencies-v2',edges=[
        ['t0/admission_identity','original_PE_input_H_models_Start_callbacks_controller'],
        ['original_PE_input_H_models_Start_callbacks_controller','native_return_cleanup_serialization_close'],
        ['native_return_cleanup_serialization_close','observer_drain_completion_observations_light_fleet_return_checks'],
        ['observer_drain_completion_observations_light_fleet_return_checks','producer_seal_closed_then_t_produce'],
        ['producer_seal_closed_then_t_produce','producer_receipt_and_complete_R114_offline_verification'],
        ['producer_receipt_and_complete_R114_offline_verification','verification_closeout_closed_then_t_verified'],
        ['verification_closeout_closed_then_t_verified','next_fixed_method'],
        ['all_four_verified','cohort_revocation_pairs_export_restore_review']],
        production_decision_modules=['src/PhysicalWitnessValidation.cpp','src/NativeEvidenceJournal.cpp','src/MipStartMapping.cpp','src/Round112CompactStart.inc',
            'src/ProcessPhaseLedger.cpp','src/GurobiBaseline.cpp','src/PaperExternalGiniTree.cpp','src/Evaluator.cpp'],
        retained_supervisor='original R90 run_one through observations; full final fleet/normal return check before seal',
        moved_independent_functions=['round114_audit.journal','round114_audit.return_chain','round114_audit.independent',
            'round114_audit.claims_for','round114_audit.rejected_mandatory','round113_audit.adapter','round114_ps.adapter'],
        no_verifier_to_producer_edge=True,no_cohort_to_online_edge=True)
    write(OUT/'producer_dependency_graph.json',graph)
    protocol=read(old/'protocol.json');protocol.update(round=115,base=BASE,roles=manifest['roles'],total_start_limit=24,total_outer_seconds_limit=20000,
        qualification_start_limit=10,qualification_outer_seconds_limit=600,evidence_layer=LAYER,main_clock='T_produce',
        measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md'),full_goal_SHA=sha(OUT/'goal.md'),
        qualification_driver_outer_cap=30,qualification_CLI_wrapper_and_native_children=5,qualification_CLI_outer_cap=540,
        qualification_post_driver_outer_cap=30,qualification_planned_conservative_starts=7,qualification_planned_outer_cap_total=600,
        claim_policy_SHA=sha(old/'claim_policy.md'),prospective_only=True,heterogeneous_measurement_policy=True,
        prior_round114_state='BLOCKED',old_R114_ENS_overcap_not_requalified=True,
        repairs=['prospective producer/verification boundary only'],comparison_policy='unchanged materiality/severity, signed gaps; current main T_produce')
    write(OUT/'protocol.json',protocol);shutil.copyfile(old/'claim_policy.md',OUT/'inherited_claim_policy_r114.md')
    # Only the signed small historical authority; no old carrier or LP matrix.
    shutil.copytree(old/'inherited_r113',OUT/'inherited_r113')
    hist=OUT/'historical_r114';hist.mkdir()
    for n in ['final_report.md','blocking_incident.md','physical_completion.json','numerical_evidence.md']:
        shutil.copyfile(old/n,hist/n)
    for name in ['new_arms.csv','new_pairs.csv','fees.csv']:shutil.copyfile(old/'reports_final'/name,hist/name)
    signed=OUT/'signed_fixture';signed.mkdir()
    for p in [old/'review/performance_admission.json',old/'review/whole_goal01/signed_review.json',old/'qualification/finite02/counterexample/receipt.json']:
        if p.is_file():shutil.copyfile(p,signed/p.parent.name+'_'+p.name)
    for n in ['cold_claim_bindings.json','api_binary64_verification.json','api_binary64_second_arithmetic_check.json',
              'printed_decimal_verification.json','printed_decimal_second_arithmetic_check.json','matrix_equivalence.json']:
        shutil.copyfile(old/'qualification/finite02/counterexample'/n,signed/n)
    fixture=old/'management_counterexample/source/campaign/raw'
    for arm,names in [('04_G50-C1_S0_P-GRB',['observations.json','result.json']),('02_G50-C1_S0_ENS-C',['result.json'])]:
        for name in names:
            src=fixture/arm/name
            if src.is_file():dst=signed/arm/name;dst.parent.mkdir(exist_ok=True);shutil.copyfile(src,dst)
    write(OUT/'engineering/initialization01/receipt.json',dict(seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
        managed_full_checkout_failed_disk_C_and_auto_cleaned=True,sparse_E_checkout=True,remote_base_verified=BASE,
        historical_small_authority_files=297,historical_small_authority_bytes=10464392,
        preexisting_primary_tracked_modifications=['results/gf_compact_bc_round/handling_convention_test/handling_convention.json',
          'results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv',
          'results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json'],user_files_preserved=True,
        no_applicable_AGENTS_found=True))
    (OUT/'RESUME.md').write_text('# Round115 resume\n\nVerified PR176/head '+BASE+' / R113 base ea9410163aafd3877cdcde80e01ccd34d893f11b.\n'
        'E:/codes/ExactEBRP-round115 isolated sparse checkout; no applicable AGENTS.md. Exact PE/DLL/source206 unchanged.\n'
        'No paid qualification or formal starts. Freeze adapters/reader/arithmetic before qualification. Never repeat an existing formal destination.\n'
        'Qualification H100 order P/P-S/ENS/M-B cap120. Formal G100 P/ENS/P-S/M-B cap3600 once.\n'
        'Main T_produce; serial post-verification T_verify/T_total. Old R112/R113/R114 qualifications unchanged.\n',encoding='utf-8')

if __name__=='__main__':initialize()
