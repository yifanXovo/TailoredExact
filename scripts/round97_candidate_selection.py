"""Apply the pre-attribution operator rule, then freeze one confirmation candidate.

No confirmation result is an input. Both actions require an idle machine and
complete, audited development. Frozen files are exclusively created, never edited.
"""
import argparse
import csv
import json
from pathlib import Path
import round97_operator_attribution as attribution
import round97_confirmation as confirmation
from round97_campaign_v2 import ROOT,OUT,BUILD,read,write,sha,ext

VIEW=OUT/'analysis_views/development_with_attribution_analysis'
DECISION=OUT/'operator_selection.json'


def rows(path):
    with path.open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))


def material_gain(candidate,baseline,relative):
    return baseline-candidate>=1e-5 and baseline-candidate>=relative*abs(baseline)


def calculate():
    ext.ensure_idle()
    assert not confirmation.CAMP.exists() and not confirmation.FREEZE.exists()
    identity=read(attribution.CAMP/'identity.json');attribution.check(identity);attribution.prefix(identity,3)
    assert read(attribution.CAMP/'queue/status.json')['phase']=='block_complete_requires_candidate_selection'
    confirmation.development.qualified()
    arms=rows(VIEW/'arms.csv');pairs=rows(VIEW/'pairs.csv');assert len(arms)==16 and len(pairs)==24
    by={(r['id'],r['arm']):r for r in arms}
    # Restrict the interrupted quality comparison to a jointly recorded horizon.
    paths=[OUT/'trajectories/development02_v1/09_FEEDBACK.csv',
           OUT/'trajectories/attribution01_v1/02_OLD-FEEDBACK.csv']
    traces=[rows(p) for p in paths]
    horizon=min(max(float(r['process_seconds']) for r in trace) for trace in traces)
    common=[]
    for trace in traces:
        eligible=[r for r in trace if float(r['process_seconds'])<=horizon]
        last=eligible[-1]
        common.append(dict(process_seconds=float(last['process_seconds']),
            U=float(last['available_physical_U']),L=float(last['available_global_native_L']),
            gap=float(last['available_gap'])))
    comparisons=[];favorable=[]
    for role in ('F5','D7','V1','F2'):
        pair=next(r for r in pairs if (r['id'],r['candidate'],r['baseline'])==(role,'FEEDBACK','OLD-FEEDBACK'))
        if role=='V1':
            new,old=common
            gain=material_gain(new['U'],old['U'],.01) or material_gain(new['gap'],old['gap'],.1)
            basis='Independently recovered, jointly recorded quality only; certificate order unknown.'
        elif role=='F2':
            assert by[role,'FEEDBACK']['certificate']=='True' and by[role,'OLD-FEEDBACK']['certificate']=='True'
            gain=pair['classification']=='material_time_gain'
            basis='Both normally certified; full process completion cost, no invented first-certificate time.'
        else:
            gain=(float(pair['candidate_minus_baseline_U'])<0 and pair['material_UB_difference']=='True') or (
                float(pair['candidate_minus_baseline_absolute_gap'])<0 and pair['material_gap_difference']=='True')
            basis='Common registered cap, normal uncertified endpoints; final certificate order unknown.'
        if gain:favorable.append(role)
        comparisons.append(dict(role=role,combined_material_favorable=bool(gain),basis=basis,paired_result=pair))
    # These assertions make the actual observed decision explicit, not a fallback.
    assert favorable==['V1']
    selected='r83'
    assert all(by[role,'OLD-FEEDBACK']['normal_return']=='True' for role in ('F5','D7','V1','F2'))
    assert not any(r['classification']=='one_sided_certificate_loss' for r in pairs
                   if r['candidate']=='OLD-FEEDBACK' and r['baseline']=='P-GRB')
    costs=read(OUT/'costs/attribution_complete/identity.json')
    assert costs['solver_process_seconds']+18900<=80000
    evidence=[VIEW/'identity.json',VIEW/'arms.csv',VIEW/'pairs.csv',attribution.PLAN,
        attribution.CAMP/'identity.json',attribution.CAMP/'summary.jsonl',attribution.CAMP/'queue/status.json',
        OUT/'costs/attribution_complete/identity.json',OUT/'production_v2_identity.json',
        OUT/'development02/hard_stop09_recovery.json',Path(__file__).resolve(),*paths]
    return dict(schema='round97-preconfirmation-operator-selection-v1',selected_operator=selected,
        both_operators_preserve_F2_certificate=True,combined_material_favorable_roles=favorable,
        minimum_favorable_roles_for_combined=2,comparisons=comparisons,
        V1_jointly_recorded_horizon_seconds=horizon,V1_common_window=dict(combined=common[0],old=common[1]),
        operator_rule='Both preserve F2; prefer simpler old closure unless combined has material favorable comparisons on at least two roles. No per-instance choice.',
        qualification='Research confirmation eligible; no default adoption. V1 old-vs-OFF material U regression retained; interrupted certificate comparisons stay unknown.',
        solver_process_seconds_before_confirmation=costs['solver_process_seconds'],
        maximum_with_reserved_confirmation=costs['solver_process_seconds']+18900,
        experimental_starts_before_confirmation=costs['experimental_starts_including_micro_and_diagnostics'],
        projected_experimental_starts=costs['experimental_starts_including_micro_and_diagnostics']+9,
        optimizer_calls=0,source_bindings={p.relative_to(ROOT).as_posix():sha(p) for p in evidence})


def freeze():
    decision=calculate();assert read(DECISION)==decision
    review=OUT/'review_operator_selection.md';report=OUT/'attribution_report.md'
    assert review.is_file() and report.is_file()
    assert read(OUT/'engineering/confirmation_guard_checks02/receipt.json')['exit_code']==0
    evidence=[DECISION,review,report,VIEW/'identity.json',VIEW/'arms.csv',VIEW/'pairs.csv',attribution.PLAN,
        OUT/'engineering/confirmation_guard_checks02/receipt.json',
        ROOT/'tests/round97_confirmation_guard_test.py',Path(__file__).resolve()]
    write(confirmation.FREEZE,dict(schema='round97-one-candidate-confirmation-freeze-v1',
        development_complete=True,allow_confirmation=True,selected_operator=decision['selected_operator'],mode='feedback',
        source_hashes=confirmation.campaign.bindings(),candidate_binary_sha256=sha(BUILD/'ExactEBRP.exe'),
        input_manifest_sha256=sha(confirmation.INPUTS),recipe_sha256=sha(confirmation.RECIPE),
        confirmation_runner_sha256=sha(confirmation.__file__),
        decision_evidence_bindings={p.relative_to(ROOT).as_posix():sha(p) for p in evidence},
        prohibited_changes=['startup','physics','objective','numerical_tolerances','native_parameters',
            'reserved_inputs','role_windows','operator_after_confirmation_starts'],
        algorithm=dict(event_rule='Full verified MIPSOL state; exclude immutable initial seed and current actual Start matches. No time, Work or node gate.',
            operator='Existing R83/R76 physical closure; fixed for the entire session and every confirmation role.',
            cache='Full physical-state hash within fixed instance/session/operator. Exhausted output cache only; remap every current model. Per-call submitted hash deduplication.',
            mapping='G=true Gini, complete actual-model variables, bounds/types/rows/objective; strict physical improvement relative to input and original native/cutoff admission.',
            archive='Only predeadline independently verified physical candidates. Handoff only on original safe native return; never force restart.',
            startup_and_parameters='Unchanged protected ENS-C 24+1 startup and startup closure; R96 startup reordering off. Same v2 build, original tolerances, Threads1 Seed0 PresolveAuto and registered caps.'),
        optimizer_calls=0,default_adoption=False,
        caveats=['Single-run research candidate, not established stable final speedup over P.',
            'V1 old closure has material U regression against OFF; combined interrupted certificate ordering unknown.',
            'No post-confirmation tuning or input replacement. All three reserved roles and outcomes retained.']))
    confirmation.candidate()
    print(json.dumps(dict(frozen=True,selected_operator=decision['selected_operator'],optimizer_calls=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['analyze','freeze']);args=parser.parse_args()
    if args.action=='analyze':
        decision=calculate();write(DECISION,decision);print(json.dumps(decision))
    else:freeze()
