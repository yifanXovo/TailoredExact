"""Scientific closeout from already sealed/reviewed evidence; no producer work."""
from pathlib import Path
import collections,time
import round123_common as c
from round123_paper import table,fmt

PAPERS=['paper_methods_draft.md','paper_computational_results_draft.md','paper_claim_matrix.md','proof_limit_report.md']

def run():
    tick=time.perf_counter();out=c.OUT;v=c.read(out/'reconstruction/final/current_core.json')
    post=c.read(out/'review/independent_post.json');math=c.read(out/'review/independent_math_and_R122.json')
    prose=c.read(out/'review/manuscript_review.json')
    assert post['decision']==prose['decision']=='ACCEPT'
    assert math['decision'] in ['ACCEPT','ACCEPT_WITH_STATED_SCOPE']
    assert len(v['arms'])==3 and len(v['pairs'])==3
    assert all(a['actually_executed'] and a['formal_protocol_qualified'] for a in v['arms'])
    assert not v['adjudication']['rejections'] and not post['cross_arm_same_domain_counterexamples']
    assert prose['core_SHA']==c.sha(out/'reconstruction/final/current_core.json')
    for name in PAPERS:
        assert c.sha(out/name)==prose['paper_SHA'][name] and (out/name).stat().st_size>1000
    budget=c.budget();assert not budget['unclosed'] and budget['paid_outer_seconds']<=c.TOTAL_LIMIT
    arm_counts=[];births=[]
    for folder in ['qualification/h100_seed0','campaign/group01']:
        ident=c.read(out/folder/'identity.json')
        for l in ident['launches']:
            d=Path(l['destination']);r=c.read(d/'result.json');birth=c.read(d/'child_process_origin.json')
            births.append(dict(phase=folder,arm=l['arm'],pid=birth['pid'],
                creation_receipt_SHA=c.sha(d/'child_process_origin.json')))
            if l['arm']=='P-GRB':counts=dict(total=r['gurobi_optimize_count'],LP=0,MIP=r['gurobi_optimize_count'])
            else:
                counts=dict(total=r['external_gini_tree_optimize_count'],LP=r['external_gini_tree_lp_optimize_count'],
                    MIP=r['external_gini_tree_partial_mip_optimize_count']+r['external_gini_tree_terminal_mip_optimize_count'])
            assert counts['total']==counts['LP']+counts['MIP']
            arm_counts.append(dict(phase=folder,arm=l['arm'],**counts))
    assert len(births)==6 and len({(b['pid'],b['creation_receipt_SHA']) for b in births})==6
    measured=[]
    for rel in ['reconstruction/attempt01_dependency_finalization/reconstruction_receipt.json','reconstruction/final/reconstruction_receipt.json','review/independent_post.json','proof_limit_details.json','paper_table_sources.json']:
        r=c.read(out/rel);measured.append(dict(path=rel,seconds=r['seconds'],classification='additional post-group read-only science work'))
    extra=sum(x['seconds'] for x in measured)
    # Retain the earlier conservative separately recorded qualification surcharge.
    surcharge=c.read(out/'engineering/qualification_reconstruction_costs.json')['total_seconds_upper']
    origin=c.read(out/'round_wall_origin.json')
    whole_round_wall=time.time()-origin['goal_created_unix_seconds']
    conservative_accounted=max(budget['paid_outer_seconds']+extra+surcharge,whole_round_wall)
    resources=dict(fee_wrappers=budget,additional_measured_science_seconds=extra,
        earlier_conservative_qualification_support_surcharge=surcharge,
        accounted_outer_seconds_lower_for_later_delivery=budget['paid_outer_seconds']+extra+surcharge,
        observed_whole_round_wall_seconds_at_science_close=whole_round_wall,
        conservative_overall_elapsed_not_double_counted=conservative_accounted,
        remaining_of_70000_before_later_publication=c.TOTAL_LIMIT-conservative_accounted,
        measured_post_group_components=measured,native_processes=births,native_Optimize_calls=arm_counts,
        fee_level_process_starts=budget['paid_starts'],distinct_fee_controllers=budget['additional_controllers'],
        read_only_observer='Separate launch/exit receipts; zero native starts, overlaps formal wall',
        nonnative_math_engineering_and_overlapping_review='Individual measured receipts, never infer zero for unknown effort; overlapping formal wall not added twice',
        human_effort_seconds='unknown',native_Runtime_nested_not_added_again=True,
        startup_count_not_a_new_gate=True,publication_recovery_cleanup_costs='separate later receipts')
    assert resources['remaining_of_70000_before_later_publication']>0
    c.write(out/'resource_accounting.json',resources)
    stage=dict(execution_stage='COMPLETE',research_disposition=v['decision']['research_disposition'],
        formal_positions=3,formal_position_denominator=3,pairs=3,new_independent_problems=0,
        paper_reference='frozen M-B',project_default='ENS-C',D1_selection_closed=True,
        no_extra_window_Seed_input_variant_or_group=True,
        extra_review='Self-review through a separate physical/math/pair/source implementation and a manuscript evidence review; no third-party executor claimed',
        scientific_core_SHA=c.sha(out/'reconstruction/final/current_core.json'),
        paper_SHA=prose['paper_SHA'],additional_review_SHA=c.sha(out/'review/independent_post.json'),
        manuscript_review_SHA=c.sha(out/'review/manuscript_review.json'),
        mathematical_review_decision=math['decision'],
        primary_endpoint_clocks_all_qualified=True,
        trajectory_clock_alignment={q['arm']:q['observation_clock_alignment']['valid'] for q in v['own_fleets']},
        allowed_unknown_prefixes_retained=True,
        delivery_scope='Scientific execution complete; actual public recovery, remote Draft PR readback and cleanup have separate later receipts',UTC=c.utc())
    c.write(out/'stage_decision.json',stage)
    text='# Round123: frozen M-B and one finite V50 proof study\n\n'
    text+='The scientific execution is **COMPLETE / '+stage['research_disposition']+'**. This is one previously known PB-C50-S input, Seed0, with three independently paid 18000-second windows in the preregistered order P-GRB, M-B, ENS-C. Physical T is 10800 seconds. The study adds zero independent benchmark problems and changes no production model, heuristic, AM rule, parameter, default or D1 selection conclusion.\n\n'
    text+=table(['Method','final own U','qualified L','signed gap','nonzero certificate','T_produce','T_verify','T_total'],
        [[a['arm'],fmt(a['U'],17),fmt(a['L'],17),fmt(a['gap'],17),a['certificate'],fmt(a['T_produce'],15),fmt(a['T_verify'],15),fmt(a['T_total'],15)] for a in v['arms']])+'\n\n'
    text+=table(['Pair','Classification','Severe','dU','dL','d(gap)','certified time ratio'],
        [[q['candidate']+'/'+q['control'],q['classification'],q['severe_regression'],fmt(q.get('dU'),15),fmt(q.get('dL'),15),fmt(q.get('dgap'),15),fmt(q.get('certified_time_ratio'),15)] for q in v['pairs']])+'\n\n'
    text+='Only two certified arms support a proof-time ratio. For open arms the cap is a censored observation, not time-to-optimal. Final fleets define all main U endpoints; separately audited historical minima remain trajectory descriptions. Existing committed records supply the requested checkpoints with raw source times and conservative arm-origin availability, without final-bound backfill or fictitious continued computation after an actual endpoint. The complete cover, own-fleet/call compatibility and unresolved obligations are in proof_limit_report.md and the typed core. Unknown internal search causes and unknown F* remain explicit.\n\n'
    text+='ENS-C fails the fixed observation-clock alignment test: origin spread 1.5845544376352336 seconds and wall-versus-producer-QPC duration difference -1.5585018387646414 seconds exceed the declared 1-second presentation envelope. Its four pre-end arm-clock checkpoints remain unknown, with all original records and raw times retained. The sealed endpoint and separately measured QPC producer/verification clocks are qualified; this trajectory limitation is reported without enlarging the guard or claiming that its early H witness first formed at sealing.\n\n'
    text+='R122 remains COMPLETE / BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION: its 32 arms, 48 pairs and all 9 LOSS/MIXED outcomes are retained and independently recalculated. D1 misses the fixed two-new-role promotion condition; M-B remains the existing paper reference and ENS-C remains default. All V35/V50 R122 roles stay open in their original windows. No result here rewrites those clocks, endpoints or group08 recovery wait.\n\n'
    text+='The English manuscript deliverables are '+', '.join('`'+p+'`' for p in PAPERS)+'. They provide the physical model, implicit service integrality, valid A/B rows, exact inventory-product embedding, scoped cutoff/coverage proofs, complete algorithm pseudocode, all old outcomes and the separate finite long study. Exact rational checks establish strict positivity and the two saved V35 conditional-row redundancy results; they are offline explanation, with zero new native LP/MIP calls and no production-bound injection. Gurobi defaults, standard ideas and the project composition remain separately attributed.\n\n'
    text+='Three real H100 (V20) CLI qualifications precede the three formal producers. The original 216 source bindings and 96 frozen helper bindings, actual loaded PE/DLL snapshots and actual argv establish identity. A second implementation independently replays all three formal fleets, pairs, scoped source/cover obligations and checkpoint records. This is self-review, not a claimed third-party native replication. The portable group08 fixture checks 156 original witnesses and 64 bounds, preserves both legal U values and rejects bad lower-bound fixtures.\n\n'
    text+='Actual fee-wrapper outer cost is '+fmt(budget['paid_outer_seconds'],16)+' seconds; qualification contributes '+fmt(budget['qualification_seconds'],16)+'. Workers/native children account for '+str(budget['paid_starts'])+' fee-level starts and '+str(budget['additional_controllers'])+' distinct controllers. Native Optimize counts are recorded per method in resource_accounting.json. Nested native time and overlapping observation/review wall are not added twice. Additional measured read-only science costs and the earlier conservative support surcharge leave '+fmt(resources['remaining_of_70000_before_later_publication'],16)+' of 70000 seconds before later delivery costs. Pure mathematical/engineering receipts and unknown human effort remain separately stated.\n\n'
    text+='All new research files use E:/codes/ExactEBRP-work, sharing the verified existing PE/DLL and Git objects. One necessary current carrier will contain the current three formal arms, finite qualification/math evidence and necessary contracts; prior campaigns/carriers and runtime binaries/licenses/HTML/secrets are excluded. The actual pinned public export, empty-root typed reconstruction, remote stacked Draft PR and authorized owned-path cleanup are attested only by later delivery receipts, which are kept outside the immutable scientific payload. No merge or further experiment is performed.\n'
    (out/'final_report.md').write_text(text,encoding='utf-8')
    c.write(out/'engineering/scientific_close_receipt.json',dict(seconds=time.perf_counter()-tick,UTC=c.utc(),
        source_SHA=c.sha(__file__),Optimize=0,stage=stage['research_disposition'],later_delivery_not_yet_attested=True))
    print(stage['execution_stage']+' / '+stage['research_disposition'])

if __name__=='__main__':run()
