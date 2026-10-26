"""Postproduction report organization only; frozen producer/audit bytes stay intact."""
from round115_common import ROOT, OUT, read, write, sha, budget, LAYER
from pathlib import Path
from fractions import Fraction
import csv, copy, json, time
import read_round115 as reader
import round111_decisions as decisions
import round112_audit as ps_start
import round108_reader as core

csv.field_size_limit(64*1024*1024)

def rows(name):
    with (OUT/'reports_final'/name).open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

def markdown_table(headers, values):
    return '\n'.join(['|'+'|'.join(headers)+'|','|'+'|'.join(['---']*len(headers))+'|']+
        ['|'+'|'.join(str(x) for x in row)+'|' for row in values])

def organize():
    tick=time.perf_counter()
    summary=read(OUT/'reports_final/summary.json')
    assert summary['execution_stage']=='COMPLETE' and summary['new_qualified_measurements']==4
    arms=[reader.namespace['typed'](r) for r in rows('new_arms.csv')]
    for a in arms:
        for k in ['T_produce','T_verify','T_total']:a[k]=float(a[k])
    lookup={a['arm']:a for a in arms};primary=rows('new_pairs.csv')
    identity=read(OUT/'campaign/identity.json');physical={};calls=[]
    for l in identity['launches']:
        d=core.portable(ROOT,l['destination']);ind=read(d/'independent_evidence.json')
        final=core.full_fleet(ROOT,l['panel'],read(d/'result.json'))
        assert final==ind['physical']==read(d/'production_checks.json')['final_physical_verification']
        physical[l['arm']]=dict(final,own_exact_zero=ind['own_exact_zero'],result_SHA=sha(d/'result.json'),
            producer_receipt_SHA=sha(d/'producer_receipt.json'),no_new_route_constructed=True)
        calls.append(dict(arm=l['arm'],counts=ind['counts'],narrow_missing_return=ind.get('narrow_missing_return'),
            original_native_result_U=read(d/'result.json')['upper_bound'],
            original_native_result_L=read(d/'result.json')['lower_bound'],
            final_endpoint_source=lookup[l['arm']]['endpoint_source'],native_proof_qualified=False))
    write(OUT/'physical_completion.json',dict(own_fleets=physical,all_eight_vehicle_fleets_verified=True,
        same_problem=True,no_solution_backfilled=True,Optimize=0))
    write(OUT/'current_source_qualification.json',dict(calls=calls,
        cohort_reconciliation_SHA=sha(OUT/'reports_final/cohort_reconciliation.json'),
        rejected_calls=summary['rejected_calls'],engine_repaired=False,Optimize=0))

    # Full formal Start is already required by rejected_mandatory. Expose its
    # existing all-column/row readback in a report even when ep is source-reduced.
    ps=next(l for l in identity['launches'] if l['arm']=='P-S');d=core.portable(ROOT,ps['destination'])
    core.start_reader.ROOT=ROOT
    start=ps_start.start_audit(ROOT,ps['panel'],d)
    start['mapping_validation_submission_seconds']=read(d/'native.log.round112.start.json')['mapping_validation_submission_seconds']
    write(OUT/'formal_compact_Start.json',dict(start,previous_full_required_audit_already_passed=True,
        report_only_reexposure=True,no_start_resubmitted=True,Optimize=0))

    secondary=[]
    for x,c in read(OUT/'protocol.json')['pairs']:
        a=copy.deepcopy(lookup[x]);b=copy.deepcopy(lookup[c])
        a['complete_seconds']=a['T_total'];b['complete_seconds']=b['T_total']
        v=decisions.pair(a,b)
        original=next(q for q in primary if q['candidate']==x and q['control']==c)
        secondary.append(dict(v,id='G100-R2',measurement_policy='v2',main_clock='T_produce',
            secondary_clock='T_total',formal_qualification_uses_producer_cap=True,
            primary_classification=original['classification'],classification_changed=v['classification']!=original['classification'],
            old_clocks_rewritten=False))
    core.table(OUT/'secondary_total_pairs.csv',secondary)
    ordering={k:[a['arm'] for a in sorted(arms,key=lambda a:a[k])] for k in ['T_produce','T_total']}
    write(OUT/'secondary_time_comparison.json',dict(ordering=ordering,ordering_differs=ordering['T_produce']!=ordering['T_total'],
        actual_clocks=[{k:a[k] for k in ['arm','T_produce','T_verify','T_total']} for a in arms],
        total_exceeds_3600=[a['arm'] for a in arms if a['T_total']>3600],
        secondary_pair_classifications=[dict(candidate=q['candidate'],control=q['control'],classification=q['classification'],
            severe_regression=q['severe_regression']) for q in secondary],
        main_clock_preregistered=True,cross_round_exact_speedup=False,Optimize=0))

    # The admitted checker hard-coded the *prior* unknown-zero statement.
    # Preserve its exact raw output and SHA; amend only current report metadata
    # using sealed own inventories verified above, not an algorithm/certificate.
    mathematical=read(OUT/'objective_sublevel_analysis_raw.json')
    for mode in ['input_decimal','parsed_binary64']:
        m=mathematical['G100-R2'][mode]
        m['zero_optimum_known_at_preregistration']=m.pop('zero_optimum_known')
        zero=[q for q in m['own_fleets'] if q['strict_Y_equals_D'] and Fraction(q['exact_U'])==0]
        assert [q['arm'] for q in zero]==['P-S'] and physical['P-S']['own_exact_zero']
        m['zero_optimum_known_after_R115']=True
        m['zero_optimum_known']=True
        m['zero_proof_source']='R115 P-S sealed own full physical fleet plus preexisting nonnegative floor0'
        m['zero_optimum_witness_arms']=['P-S']
        assert all(not q['sufficient_condition_applies'] for q in m['own_fleets'])
    mathematical['report_metadata_amendment']=dict(admitted_checker_SHA=sha(ROOT/'scripts/round115_sublevel.py'),
        raw_output_SHA=sha(OUT/'objective_sublevel_analysis_raw.json'),
        scope='prior unknown-zero label updated from actual current sealed P-S own zero; rational calculations unchanged',
        producer_or_checker_bytes_changed=False,performance_rerun=False)
    write(OUT/'objective_sublevel_analysis.json',mathematical)

    b=budget();phase=dict(priority='A',execution_stage='COMPLETE',heterogeneous_measurement_policy=True,
        reason='All three current candidates improve cold P; both five-role backend vectors close MIXED with qualified losses; no current positive G100 own U meets the beta sublevel condition.',
        next_priority='Freeze the present research candidate and contribution boundary; prioritize independent external coverage and paper experiments.',
        new_algorithm_or_oracle_authorized=False,automatic_followup=False,main_P_support_preserved=True,
        current_positive_G100_sublevel_condition=False,G50_target_existence_already_known_from_historical_ENS=True,
        G100_target_existence_now_known_from_own_PS=True,remaining_uncertainty='Costs of any target-domain algorithm and broader external generalization remain unmeasured.',
        default_ENS_changed=False,unified_MB_finite_R111_support_retained=True,PS_contribution_control_only=True,
        scientific_summary_SHA=sha(OUT/'reports_final/summary.json'),mathematical_report_SHA=sha(OUT/'objective_sublevel_analysis.json'))
    write(OUT/'research_phase_decision.json',phase)
    (OUT/'research_phase_decision.md').write_text('''# Research phase decision: A

Close this phase, freeze the current research candidate and contribution boundary, and prioritize independent external coverage and paper experiments. Do not automatically run the next phase.

All three new methods are qualified WINs against the same-policy cold P-GRB. ENS-C/P-S and M-B/P-S are severe LOSSs, and M-B/ENS-C is also a severe LOSS. The five eligible roles close ENS W/W/L/W/L and M-B W/W/L/T/L, both MIXED, with heterogeneous timing explicitly retained. This establishes concrete backend benefits and costs without a winner assembled from different instances. Cold P remains the primary benchmark, ENS the default, M-B retains its finite R111 candidate support, and P-S remains a contribution control.

The G50 strict-improvement domain is qualified exactly, but historical ENS already has a legal zero witness. Target existence is therefore known; an arm's own paid discovery/cost is a separate unmeasured algorithm question. The three positive G100 endpoints have U>beta, and P-S has already attained Y=D through the frozen original compact method. Neither fact establishes an untested target oracle's speed or authorizes a new mechanism. R61 already supports full-fleet fixed/partially released inventory routing; that problem formulation is inherited.

Source reduction preserves independently legal physical results and floor0. It does not repair the numerical engine or establish general native-proof reliability. Few seeds and exposed same-source inputs leave external generalization and full paper coverage unknown. These are the next evidence priorities, not a reason to change audit clocks again or start another four-arm qualification loop.
''',encoding='utf-8')

    clock_table=markdown_table(['Arm','Own U','Qualified L','Gap','Endpoint source','T_produce s','T_verify s','T_total s'],
        [[a['arm'],f"{a['U']:.17g}",a['L'],f"{a['gap']:.17g}",a['endpoint_source'],f"{a['T_produce']:.9f}",
          f"{a['T_verify']:.9f}",f"{a['T_total']:.9f}"] for a in arms])
    pair_table=markdown_table(['Candidate/control','Primary T_produce','Severe LOSS','Secondary T_total'],
        [[q['candidate']+'/'+q['control'],q['classification'],q['severe_regression'],
          next(v['classification'] for v in secondary if (v['candidate'],v['control'])==(q['candidate'],q['control']))] for q in primary])
    source=read(OUT/'production_identity.json')
    final=f'''# Round115 final report

execution_stage=COMPLETE. The four new G100-R2 arms ran exactly once in preregistered P-GRB/ENS-C/P-S/M-B order and all four are qualified after complete necessary evidence checks. All six new pairs are evaluable. The descriptive layer has 19 qualified observations over 20 positions and 27 evaluable pairs over 30. The three missing G50 cold-P comparisons stay unqualified. No formal retry, extra seed, new native reference export or production rebuild occurred.

{clock_table}

The prospective measurement v2 uses T_produce as its primary time. Each start precedes input/identity admission and H; the first retains wrapper creation/import. T_produce includes original H and all online physical/model/type/Start/callback/journal/controller checks, native return/cleanup/serialization, original supervision/observations and lightweight full-fleet/normal-return production validation. The source-extracted R90 supervisor prefix, four native argv, 3600 cap, 30 reserve and hard stop cap−2 are unchanged. Required outputs close and are sealed before t_produce. The timestamp receipt is written afterward; its cost is in T_verify. Its pending verification=null record remains immutable.

Full Python historical-witness/model/Start/domain/return/cover audits run serially after sealing and before the next native arm. T_verify is the nonoverlapping interval from the seal time to necessary verification closeout; T_total uses the same t0. The actual final cohort revocation/reconciliation and public delivery are later group engineering costs, excluded from closed arm clocks. Runtime and nested H/LP/MIP diagnostics in reports_final/time_partitions.csv are explanatory only and are never subtracted or added again. The legacy postexit partition denotes producer admission/final production closeout, not the later full independent audit.

ENS-C T_total=3605.713703100 and M-B T_total=3605.476599500 both exceed 3600. These real costs are disclosed and do not disqualify their within-cap producers under the frozen new policy. Ascending producer ordering is {' < '.join(ordering['T_produce'])}; ascending total ordering is {' < '.join(ordering['T_total'])}. The ordering changes between cold P and both warm backends. This adverse total-time view is preserved in secondary_time_comparison.json; the primary metric was not selected after results.

{pair_table}

The secondary pair comparator uses the same four already qualified outcomes and T_total. No classification changes: the two uncertified comparisons against P improve U/gap, and P-S alone owns a complete zero certificate. It is not a retroactive old whole-clock eligibility test. Native proof qualification and physical/independent certificate qualification remain distinct.

P-S's own committed zero event sequence33 was observed by 1306.003669600 producer seconds; the precise native first-discovery time is unknown. The full physical output has K=0, Y=D, U=0 and maximum route duration17946.667700545≤18000. Its own eight-vehicle fleet plus the preexisting nonnegative floor gives OWN_ZERO_CERTIFICATE. The current cohort found one damaged call per arm: P call1, ENS call4, P-S call1, M-B call4. Existing earlier positive bound claims contradict admissible zero witnesses by more than the unchanged 1e−7 consistency policy. The entire bad call is rejected, including later smaller/zero claims, OPTIMAL/INFEASIBLE, dependent positive certificate/pruning/cover. Reversing claim/witness verification order produces identical reconciliation. Raw signed gaps, claims, rejection dependencies and original evidence remain in the carrier. Other independent correct calls are retained. Cross-arm zero is used only to revoke claims, never to replace another arm's U or enter its search.

P/ENS/M-B final qualified L=0 is the independently known floor, not repaired native progress. P-S's native_proof_qualified=false also remains explicit despite its legal own zero. P-S has one actual Optimize, zero journal returned events and one independently verified actual native/API return. It satisfies only the inherited narrow terminal-MIP bound/witness latch + own-zero + normal-return gate. That missing returned event is preserved, not relabelled not_started; no broader exception was added.

Actual current native counts are P 1 MIP; ENS 3 LP+1 MIP; P-S 1 MIP; M-B 3 LP+1 MIP: 10 Optimize in four formal children, zero declared not_started. All models/actual native types, settings and returns are independently verified, including M-B binary state/service and integer quantity identity. P-S's complete original model Start checks {start['columns']} native columns and {start['rows']} original rows; vector submission/readback and before/after matrix identity pass, maximum row violation {start['maximum_row_violation']:.17g}. Formal Start was already checked during necessary source-rejected audit; formal_compact_Start.json exposes that existing check without submitting another Start.

All three warm arms independently complete the identical 25-seed H semantics, accepted actions, inventories and complete capacity-assigned fleets; reports_final/same_H.csv and same_H_fleets.csv retain full comparison. Actual H time differs (ENS274.3902515, P-S271.7262617, M-B272.1285001), which remains paid producer time. Backend exposure is real for all three. No across-arm H/UB/Start/cache/bound sharing occurred.

The descriptive layer is `{LAYER}`. In role order F2/R98-C2/R108-L48/G50-C1/G100-R2, ENS/P-S is W/W/L/W/L and M-B/P-S W/W/L/T/L, both eligible5/5 MIXED with heterogeneous_measurement_policy=true. R112/R113 entries retain their original whole clocks and local pair rules; new G100 uses T_produce. Only within-role classifications are summarized. There is no cross-layer exact speedup, mean, overall WIN rate, unified clock benchmark, statistical significance or per-instance domination claim. R114 old P whole3573.223369551 stays its original qualified historical observation; R114 ENS whole3605.688342700 stays ineligible, and its P-S/M-B remain unstarted. R113 cold G50 P still lacks its old whole clock and formal U/L. None enters the six current pairs.

Zero-Optimize exact arithmetic independently verifies G50 B=sumD527, sumQ120, decimal delta3/500, beta1837/224500. Only sigma−1 passes single-unit total conservation. Existing legal M-B/P-S inventories have exact U=beta under both decimal and parsed-binary64 coefficient interpretations, so strict improvement over those fleets requires Y=D. The minimizers are1,5,7,11,20,27,28,32,33,36,50. G50 ENS's earlier own zero already proves target existence. Finite n2/3 balanced/shortage/surplus/capacity-boundary/empty-J checks and direct Gini/phi checks pass.

G100 B1410, sumD1259, sumQ240, necessary sumY interval[1170,1410], decimal delta1/600 and beta299/108120≈{float(Fraction('299/108120')):.17g}. Current K values P14/ENS2/P-S0/M-B4; all three positive U>beta, so none satisfies 0<U≤beta. P-S independently establishes the zero optimum through its original production run. The admitted arithmetic checker conservatively hard-coded the preregistration unknown-zero label; objective_sublevel_analysis_raw.json preserves that exact output, and final JSON amends only current metadata from P-S's sealed fleet. No arithmetic/producer/checker bytes change, route construction, target oracle, cut, branch, heuristic or postseal improvement is introduced. R60 fixed-Y diagnoses, R61 full-fleet fixed/released-Y time oracle, R96 fixed-route quantities and R105 fixed-local-operation oracle delimit inherited scope; no historical priority or measured reduction speed is claimed.

Priority A closes this phase and freezes candidates/contribution boundaries for independent external coverage and paper experiments. Cold P remains primary; ENS default and M-B's finite R111 support remain unchanged; P-S is a contribution control. All benefits, severe losses and unrepaired numerical engine faults are retained. No next experiment or mechanism is automatically authorized.

Fee ledger: {b['paid_starts']}≤24 conservative paid starts, {b['paid_outer_seconds']:.9f}≤20000 outer seconds; qualification{b['qualification_starts']}≤10 and {b['qualification_seconds']:.9f}≤600 included. Formal wrapper+four children count5, nominal14400; actual formal outer fee12144.883240223 conservatively includes OS-exit observation delay (lower12100.796391631). Nested native/H/audit times are not charged twice. Read-only arithmetic, cohort reconstruction, packaging, restoration and publication costs are separately recorded. Unaggregated early progress observations and human orchestration time remain unknown rather than zero.

Source206 is unchanged at {source['measured_source_commit']}; PE {source['production_PE_SHA']}; DLL {source['DLL_SHA']}. The prospective admission binds final producer/helper/reader/arithmetic bytes, original argv/input/protocol and actual H100 V20/M2 Q13,21 T5100 qualification. Initial managed checkout disk failure was auto-cleaned; isolated sparse E checkout and directed missing-authority/config recovery did not run a native solver or change user files. No new solver/qualification failures occurred. Independent third-party person/agent is unavailable: the separate executable and restored-root arithmetic/source review are implementer-authored. They provide auditable checks, not a third-party rerun.

Public delivery exports one committed compact current carrier into one genuinely fresh empty root. Actual source/raw hash verification, restored-root core reconstruction comparison and the one additional seven-question whole-goal review are recorded only afterward in separate execution receipts. This scientific payload does not claim those future actions have already happened. PE/DLL/licenses/credentials and full old carriers are excluded; only current raw and small signed historical authorities are included. No native performance replay is required.
'''
    (OUT/'final_report.md').write_text(final,encoding='utf-8')
    (OUT/'RESUME.md').write_text(f'''# Round115 resume

execution_stage=COMPLETE. Isolated E:/codes/ExactEBRP-round115 on codex/round115-producer-clock-attribution-closure, verified R114 parent e436748521cf5aabbe84a24a5e9cf3836550563c. Exact source206/PE/DLL and admitted helper/reader/arithmetic bytes unchanged.

finite01/cli01/post01 qualification and admission ACCEPT preceded formal01. Exactly four G100 P/ENS/P-S/M-B arms have completed once and necessary serial per-arm verification is closed. There are no native children or formal wrapper left running. All four final cohort observations qualify, with damaged native calls preserved and source-reduced physical results; P-S owns strict zero. Six current pairs close; 19/20 positions and27/30 descriptive pairs qualify. ENS W/W/L/W/L and M-B W/W/L/T/L are both MIXED across heterogeneous old-whole/new-producer layers. Old G50 cold-P missing clock and R114 ENS overcap remain unchanged.

Paid ledger{b['paid_starts']}/24 starts and{b['paid_outer_seconds']:.9f}/20000 seconds, qualification{b['qualification_starts']}/10 and{b['qualification_seconds']:.9f}/600. Never repeat any existing paid destination. No performance work remains. Priority A: freeze this phase; only external coverage/paper work may be a later explicitly requested task.

Pending delivery actions at scientific-payload creation: one compact committed public export/fresh-root restore, actual restored-reader comparison, one extra seven-question implementer-authored review and stacked English Draft PR publication. Later actual receipts are separate from their exported scientific payload. No independent third-party executor is claimed.
''',encoding='utf-8')
    write(OUT/'engineering_costs.json',dict(paid_budget=b,nested_arm_verify_included_in_paid_wrapper=True,
        read_only_measured_seconds=dict(prospective_admission=6.30438949994,final_reader01=17.811702,
            objective_sublevel_final01=6.4760358,progress_observer_65_calls=14.375240000000005),
        earlier_progress_observer_95_calls_seconds='unknown: not aggregated',human_orchestration_seconds='unknown',
        initial_failed_checkout_and_recovery_seconds='unknown; partial recorded in engineering/initialization01/receipt.json',
        packaging_restore_reconstruction_review_remote_costs='actual later receipts, not yet performed',
        read_only_Optimize=0,no_nested_time_double_count=True))
    write(OUT/'organization_receipt.json',dict(seconds=time.perf_counter()-tick,organized_unix=time.time(),Optimize=0,
        native_starts=0,formal_performance_rerun=False,final_reader_SHA=sha(ROOT/'scripts/read_round115.py'),
        organization_script_SHA=sha(__file__),new_reports_only=True,mathematical_metadata_amendment_disclosed=True))
    print(json.dumps(dict(execution_stage=summary['execution_stage'],priority='A',ordering=ordering,
        formal_Start_columns=start['columns'],formal_Start_rows=start['rows'],budget=b)),flush=True)

if __name__=='__main__':organize()
