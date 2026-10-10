"""Finite delivery/goal analysis of already completed evidence; no solver."""
import csv, hashlib, json, math, subprocess, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'results/unified_exact_round111'
SCIENCE = 'b92b27c895043af669e64ae32ef0b232262c3244'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024*1024):
            h.update(block)
    return h.hexdigest()

def rows(path):
    with path.open(newline='',encoding='utf-8') as stream:
        return list(csv.DictReader(stream))

def main():
    decision = read(OUT/'selection_decision.json')
    assert decision == read(OUT/'reports_final/selection_decision.json')
    assert decision['stage'] == 'CONFIRMATION_SUPPORT'
    assert decision['evidence_layer'] == 'R110_MAIN_36_PLUS_R111_SEED_6'
    assert decision['main_denominator'] == 12
    assert decision['main_counts'] == {'WIN':11,'TIE':1}
    assert decision['current_qualified_formal_arms'] == 6
    assert decision['current_six_complete'] and decision['current_three_seed_pairs_evaluable']
    assert not decision['blocking_reasons'] and not decision['reason_codes']
    assert decision['main_severe_P_regressions'] == decision['seed_severe_P_regressions'] == 0
    assert all(values for group in decision['stratum_WIN_roles'].values() for values in group.values())
    assert not decision['Seed0_WIN_to_current_Seed1_LOSS']
    assert decision['evaluable_seed_nonLOSS'] == 3 and decision['no_hidden_ENS_veto']
    expected = {'G20-C2':'TIE','G50-R1':'WIN','G100-R2':'WIN'}
    arithmetic = {}
    for role, pair in decision['seed_primary_pairs'].items():
        assert pair['classification'] == expected[role] and pair['evaluable']
        assert pair['severe_regression'] is False
        assert all(math.isfinite(pair[key]) for key in ('candidate_U','candidate_L','control_U','control_L'))
        if role == 'G20-C2':
            assert pair['candidate_certified'] and pair['control_certified']
            assert pair['candidate_U'] == pair['control_U'] == 0
            difference = pair['control_seconds']-pair['candidate_seconds']
            threshold = max(30,.10*pair['control_seconds'])
            assert abs(difference) < threshold
            arithmetic[role] = dict(both_own_zero_certificates=True,time_difference=difference,time_materiality=threshold)
        else:
            assert not pair['candidate_certified'] and not pair['control_certified']
            u_gain = pair['control_U']-pair['candidate_U']
            gap_gain = pair['control_gap']-pair['candidate_gap']
            u_threshold = max(.001,.01*abs(pair['control_U']))
            gap_threshold = max(.001,.10*abs(pair['control_gap']))
            assert u_gain > u_threshold and gap_gain > gap_threshold
            arithmetic[role] = dict(own_U_improvement=u_gain,own_gap_improvement=gap_gain,U_materiality=u_threshold,gap_materiality=gap_threshold)
    assert Counter(p['classification'] for p in decision['main_MB_ENS_pairs'].values()) == {'WIN':5,'TIE':3,'LOSS':4}
    assert {r for r,p in decision['main_MB_ENS_pairs'].items() if p['severe_regression']} == {'G50-C1','G100-R2'}
    old = rows(OUT/'reports_final/inherited_old_seed6.csv')
    invalid = next(p for p in old if p['id']=='G100-R2' and p['arm']=='M-B')
    assert float(invalid['complete_seconds']) == 3600.7215734999627
    assert invalid['formal_protocol_qualified'] == 'False'
    assert float(invalid['complete_seconds']) > float(invalid['cap_seconds'])
    assert decision['old_round110_stage']=='BLOCKED' and not decision['old_all42_valid_formal']
    assert not decision['all42_measured_under_new_wrapper'] and not decision['cross_wrapper_exact_speedup']
    assert decision['new_independent_samples_added']==0 and not decision['default_ENS_changed']
    assert not decision['statistical_guarantee'] and not decision['full_paper_benchmark_completed']
    candidate = read(OUT/'candidate_identity.json')
    assert len(candidate['source_bindings']) == 205
    for mapping in (candidate['source_bindings'],candidate['helpers']):
        assert all(sha(ROOT/name)==digest for name,digest in mapping.items())
    assert sha(ROOT/'build/research/round111-inherited/ExactEBRP.exe') == candidate['production_PE_SHA']
    assert sha(Path('D:/gurobi1302/win64/bin/gurobi130.dll')) == candidate['DLL_SHA']
    campaign = read(OUT/'campaign/identity.json')
    assert [p['old_R110_number'] for p in campaign['launches']] == list(range(37,43))
    assert [p['command'] for p in campaign['launches']] == candidate['full_argv']
    clocks = []
    for launch in campaign['launches']:
        raw = Path(launch['destination'])
        native = read(raw/'native_end_receipt.json')['complete_seconds_until_native_end']
        audit = read(raw/'postexit_audit_receipt.json')['complete_seconds_until_audit_end']
        whole = read(raw/'whole_arm_receipt.json')
        assert native <= audit <= whole['complete_seconds'] <= launch['cap_seconds']
        assert whole['includes_admission_identity_checks_startup_native_calls_callbacks_raw_writes_postexit_audit_crosscheck']
        clocks.append(dict(number=launch['number'],native_end=native,audit_end=audit,whole=whole['complete_seconds'],cap=launch['cap_seconds']))
    local = read(OUT/'review/final_raw01/audit.json')
    public = read(OUT/'public_validation/public_raw01/audit.json')
    assert local['stage'] == public['stage'] == decision['stage']
    assert public['no_original_root_fallback']
    narratives = {}
    for name in ('final_report.md','contribution_evidence_map.md','paper_candidate_spec.md','repair_scope.md'):
        path = OUT/name
        frozen = subprocess.check_output(['git','show',SCIENCE+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
        assert frozen == path.read_bytes()
        narratives[name] = sha(path)
    report = (OUT/'final_report.md').read_text(encoding='utf-8')
    assert 'no established zero-optimum proof' in report
    assert 'Only two falsifiable future questions' in report
    manifest = read(OUT/'compact_evidence/manifest.json')
    assert manifest['old_main_raw_copied'] is False and manifest['no_PE_DLL_license_or_credentials']
    assert not any(Path(p['path']).suffix.lower() in {'.exe','.dll','.lic','.key','.pem'} for p in manifest['files'])
    remote = read(OUT/'remote_validation/remote_identity01.json')
    assert remote['passed'] and remote['actual_PR']['state']=='OPEN' and remote['actual_PR']['isDraft']
    assert remote['verified_scientific_commit']==SCIENCE and remote['production_205_paths_unchanged_from_R110']
    resources = read(OUT/'post_science_resource_accounting.json')['research']
    assert resources['paid_starts']==15 and resources['paid_outer_seconds']==11299.309934754972
    assert resources['qualification_starts']==6 and resources['qualification_seconds']==583.7201481292723
    assert not resources['unclosed']
    value = dict(passed=True,stage=decision['stage'],evidence_layer=decision['evidence_layer'],analysis_unix=time.time(),
        source_SHA=sha(Path(__file__)),cwd=str(Path.cwd()),scientific_payload_commit=SCIENCE,
        observed_PR_head=remote['actual_fetched_head'],seed_materiality_analysis=arithmetic,exact_current_clocks=clocks,
        frozen_narrative_SHA=narratives,old_arm42_invalid_preserved=True,all_ENS_costs_disclosed=True,
        no_old_new_cherry_pick_or_cross_wrapper_exact_speedup=True,no_unproved_zero_or_unconditional_AM_or_causal_claim=True,
        necessary_validation_in_complete_clock=True,audit_improvement_is_engineering=True,no_new_solver_mechanism_or_task=True,
        actual_restored_root_primary_and_independent_reviews_pass=True,unresolved_goal_conditions=[],research=resources,
        manual_time='unknown',Optimize=0,native_processes=0)
    with (OUT/'final_goal_review.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(passed=True,stage=value['stage'],observed_PR_head=value['observed_PR_head'],Optimize=0)))

if __name__ == '__main__':
    main()
