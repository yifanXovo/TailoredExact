"""Final finite proof-limit report; endpoints are never selected from history."""
from round123_common import *
from round123_paper import fmt,table
import csv
import round123_observation_clock as clock

def run():
    tick=time.perf_counter();v=read(OUT/'reconstruction/final/current_core.json');arms=v['arms'];by={a['arm']:a for a in arms}
    i=read(OUT/'campaign/group01/identity.json');details=[];starts=[]
    for l in i['launches']:
        a=by[l['arm']];d=Path(l['destination']);own=next(x for x in v['own_fleets'] if x['arm']==l['arm'])
        obs=read(d/'observations.json');prod=read(d/'producer_receipt.json')
        alignment=clock.alignment(d);available=lambda seconds:clock.upper(seconds,alignment,a['T_produce'])
        hits=[r for r in obs if r['payload']['kind']=='witness' and abs(r['payload']['objective']-a['U'])<=1e-7]
        first=min(hits,key=lambda r:r['effective_available_seconds']) if hits else None
        detail=dict(arm=l['arm'],first_final_quality_record_sequence=first['sequence'] if first else None,
            final_quality_means_within_original_1e_7_not_exact_fleet_identity=True,
            first_final_quality_record_available_upper_seconds=available(first['effective_available_seconds']) if first else None,
            first_final_quality_raw_process_record_seconds=first['effective_available_seconds'] if first else None,
            observation_clock_alignment=alignment,
            minimum_remaining_production_after_availability_upper_seconds=prod['T_produce']-available(first['effective_available_seconds']) if first else None,
            remaining_value_is_lower_bound_not_exact_proof_tail=True,
            internal_first_discovery_time='unknown',known_optimal_primal_plateau=bool(a['certificate']),
            all_later_strict_objective_records=[dict(sequence=r['sequence'],F=r['payload']['objective'],G=r['payload']['G'],available=available(r['effective_available_seconds']),raw_process_available=r['effective_available_seconds'])
                for n,r in enumerate(obs) if r['payload']['kind']=='witness' and any(q['payload']['kind']=='witness' for q in obs[:n])
                and r['payload']['objective']<min(q['payload']['objective'] for q in obs[:n] if q['payload']['kind']=='witness')-1e-12])
        details.append(detail)
        calls=[r['payload'] for r in obs if r['payload']['kind']=='call']
        compat=next(x for x in v['proof_obligations'] if x['arm']==l['arm'])['own_final_fleet_and_call_domains']
        for c in calls:
            p=Path(c['native_log_path']+'.round68.start.json');s=read(p) if p.exists() else None
            scope=next(x for x in compat if x['call']==c['call'])
            starts.append(dict(arm=l['arm'],call=c['call'],leaf=c['leaf'],actual_model_SHA=c['model_sha256'],
                lower_g=c['lower_g'],upper_g=c['upper_g'],cutoff=c['cutoff'],own_final_G=own['final_physical']['G'],
                exact_g_interval_compatible=scope['exact_g_embedding_interval_compatible'],cutoff_compatible=scope['cutoff_compatible'],
                Start_metadata=s,Start_metadata_SHA=sha(p) if s else None,
                submitted=s.get('submitted') if s else False if l['arm']=='P-GRB' else None,
                native_acceptance=s.get('status') if s else 'cold_method_no_Start' if l['arm']=='P-GRB' else 'unknown_or_not_requested'))
    certified=[a for a in arms if a['certificate'] and not a.get('source_reduced')]
    decomposition=[]
    if certified:
        star=certified[0]['U']
        for a in certified:assert abs(a['U']-star)<=1e-7
        for a in arms:
            if a['U'] is not None and a['L'] is not None:
                decomposition.append(dict(arm=a['arm'],numerical_certified_reference_U=star,
                    primal_component=a['U']-star,bound_component=star-a['L'],gap=a['gap'],
                    conditional_numerical_reference_not_rational_exact_Fstar=True))
    text='''# Finite proof capability on PB-C50-S

This study concerns one previously known serialized instance, Seed0 and exactly three complete independently paid methods. It adds zero independent problem samples. Physical T is 10800 seconds; each computational producer cap is 18000 seconds, with the original 30-second native reserve and one total deadline. The predeclared serial order is cold P-GRB, M-B, ENS-C. The prior legal objective 0.3723417754990474 was not loaded or presumed optimal. No old route, bound, tree, basis, cutoff or cache was reused. No second window, Seed, input or mechanism follows this study.

Strict positivity follows from service B 495, target total 562, empty departure, nonnegative returns and positive weighted deviations; the shortage is 67. The exact-decimal explanatory simple bound is 0.24814831875 and the inventory-penalty relaxation is 0.26064825. Parsed binary64 differences and exact/finite checks are preserved. These are qualification of the role's nonzero nature, not production strengthening, and do not predict convergence from an existing percentage gap.

## Own endpoints and three clocks

'''
    text+=table(['Method','final own U','qualified L','signed gap','certified','source-reduced','T_produce','T_verify','T_total'],
        [[a['arm'],fmt(a['U'],17),fmt(a['L'],17),fmt(a['gap'],17),a['certificate'],a.get('source_reduced'),fmt(a['T_produce'],12),fmt(a['T_verify'],12),fmt(a['T_total'],12)] for a in arms])+'\n\n'
    text+='The formal group disposition is **'+v['decision']['research_disposition']+'**. A normal open producer is a completed observation, not execution failure. Complete Round123 delivery additionally requires the paper drafts, extra review, public reconstruction and safe closeout, documented separately in final_report.md. Neither a stage label nor a certificate implies that M-B beats P or ENS in time; the three actual pairs below are retained.\n\n'
    text+=table(['Pair','Class','Severe','dU','dL','d(gap)','certified time ratio'],
        [[q['candidate']+'/'+q['control'],q['classification'],q['severe_regression'],fmt(q.get('dU'),14),fmt(q.get('dL'),14),fmt(q.get('dgap'),14),fmt(q.get('certified_time_ratio'),14)] for q in v['pairs']])+'\n\n'
    text+='''For a comparable pair, d(gap)=dU-dL is an arithmetic endpoint decomposition, not an internal causal fraction. Only two certified methods support a complete certification-time ratio. Capped open windows are not unknown optimality times that can be divided. An UNEVALUABLE pair retains its missing own value rather than importing a historical witness.

'''
    if decomposition:
        text+='At least one method supplies a qualified original-problem numerical certificate. Using its U as a common numerical optimum reference, the following signed decomposition is conditional on the original 1e-7 evidence policy; it is not a rational exact F*. Tiny signed components are retained.\n\n'
        text+=table(['Method','numerical reference U','primal component U-Uref','bound component Uref-L','signed gap'],
            [[r['arm'],fmt(r['numerical_certified_reference_U'],17),fmt(r['primal_component'],17),fmt(r['bound_component'],17),fmt(r['gap'],17)] for r in decomposition])+'\n\n'
    else:text+='No method supplies an original-problem certificate in this window, so F* is unknown. A gap cannot be separated into absolute primal suboptimality and bound shortfall. Pairwise U/L differences are reported, but an unchanged U is not called a known optimal plateau and no linear additional-time forecast is made.\n\n'
    text+='## Final fleet versus historical observations\n\n'
    text+=table(['Method','formal final U','minimum legal observed F including final','record/source','raw process record s','arm availability upper s'],
        [[q['arm'],fmt(q['final_U'],17),fmt(q['historical_minimum_observed_F']['F'],17),str(q['historical_minimum_observed_F']['sequence'])+' / '+q['historical_minimum_observed_F']['source'],fmt(q['historical_minimum_observed_F'].get('process_record_available_seconds'),12),fmt(q['historical_minimum_observed_F']['available'],12)] for q in v['own_fleets']])+'\n\n'
    text+='The final returned fleet defines the formal endpoint. Historical minima describe the trajectory and never replace that endpoint after observing results. Two independently valid U values need no monotonic ordering. Each bound must instead be valid on its own physical/model domain; full-domain bounds are checked against every valid fleet, and restricted bounds against compatible true-G/cutoff fleets. The general group08 regression explicitly verifies this distinction and rejects contradictory-bound fixtures.\n\n'
    text+=table(['Method','first final-quality record','raw process record s','arm availability upper s','minimum remaining production s'],
        [[q['arm'],q['first_final_quality_record_sequence'],fmt(q['first_final_quality_raw_process_record_seconds'],12),fmt(q['first_final_quality_record_available_upper_seconds'],12),fmt(q['minimum_remaining_production_after_availability_upper_seconds'],12)] for q in details])+'\n\n'
    text+='A final-quality record means a legal witnessed objective within the inherited 1e-7 numerical policy of the final U, not proof of identical routes or an internal first-discovery timestamp. Availability is a conservative upper bound, so subtracting it from the actual end supplies only a lower bound on remaining production. A zero in that column need not mean that the fleet first appeared at the end. Remaining work may include both continued incumbent search and bound work; it is not automatically pure proof effort. Only a complete certificate supports a numerical optimality statement. All actual later strict witness improvements remain in proof_limit_details.json.\n\n'
    text+='## Five requested checkpoints and actual endpoints\n\nThe table uses existing committed records, without new Optimize calls, interruption at checkpoints or changed callback frequency. Where no exact checkpoint observation exists, the latest prior legal fleet record and its conservative arm-origin availability upper time are shown; the historical minimum is a separate descriptive column. Raw GetTickCount64 source times and QPC production times are retained. The fixed offline alignment uses the native-end minus wrapper-wall origin and recorded wall-origin pairs, with a 1-second presentation envelope declared before the first 3600-second checkpoint. This is neither an internal discovery timestamp nor a changed feasibility/certificate tolerance. Failed clock alignment leaves prefix values unknown until the actual seal. Independent U and L records can have different times. The final API bound enters only after its real sealed availability. An earlier finished run has one actual endpoint row and an explicit list of later requested points with no continued computation.\n\n'
    cp_rows=[]
    for q in v['checkpoints']:
        end=q['source']=='actual_sealed_endpoint_before_checkpoint'
        cp_rows.append([q['arm'],'end '+fmt(q['actual_end_seconds'],12) if end else q['checkpoint_seconds'],fmt(q.get('U_final') if end else q.get('last_witness_F'),14),
            'sealed' if end else fmt(q.get('last_witness_raw_process_available_seconds'),12),
            fmt(q.get('actual_record_available_upper_seconds') if end else q.get('last_witness_available_upper_seconds'),12),
            fmt(q.get('observed_best_F'),14) if not end else 'see history table',
            fmt(q.get('L'),14),'sealed' if end else fmt(q.get('L_raw_process_available_seconds'),12),
            fmt(q.get('actual_record_available_upper_seconds') if end else q.get('L_available_upper_seconds'),12),
            'actual endpoint' if end else 'prior records'])
    text+=table(['Method','checkpoint / actual end s','last legal F / final U','raw F record s','arm F time upper','descriptive best F','L','raw L record s','arm L time upper','source'],cp_rows)+'\n\n'
    text+=table(['Method','conversion qualified','origin spread s','wall minus producer-QPC duration s','arm offset upper s'],
        [[q['arm'],q['observation_clock_alignment']['valid'],fmt(q['observation_clock_alignment']['observed_origin_spread_seconds'],14),
          fmt(q['observation_clock_alignment']['wall_vs_producer_QPC_difference_seconds'],14),fmt(q['observation_clock_alignment']['offset_upper_seconds'],14)] for q in v['own_fleets']])+'\n\n'
    invalid=[q for q in v['own_fleets'] if not q['observation_clock_alignment']['valid']]
    if invalid:
        text+='The observed '+', '.join(q['arm'] for q in invalid)+' conversion fails the fixed 1-second consistency rule. Its pre-end arm-clock checkpoints therefore remain unknown; the original committed records, raw source times and all 300 existing samples remain available. In ENS-C, record 2 contains the final-quality startup fleet at raw process time 34.312 seconds, but the accepted arm-clock availability upper bound is only the seal. This loose bound does not relocate H to the end or erase its observation. The separately measured QPC T_produce, post-seal T_verify/T_total and sealed endpoint qualification remain intact. The discrepancy is reported without assigning an unrecorded clock-adjustment cause, expanding the guard after seeing the result, or filling earlier points from final API values.\n\n'
    text+='## Original-problem coverage and remaining obligations\n\nThe prior R122 reconstruction is fixed in prior_proof_obligations.md/json. Its first two atomic splits preserved infeasible right halves; its third followed the original AM score. The global L came from the lower-bound controlling leaf, not the stronger sibling, and the own fleet G lay outside the target leaf. The new longer cap is allowed to change that path. The following statements use only the new run\'s actual final cover and calls.\n\n'
    for q in v['proof_obligations']:
        text+='### '+q['arm']+'\n\n'
        if q['full_original_single_call']:
            text+='The method uses one complete cold canonical compact model. Its original-domain native return, own fleet and final bound are checked together; no H/Start is supplied. '+('The full original numerical certificate is qualified.\n\n' if q['certificate'] else 'The complete original-model proof obligation remains open at the paid endpoint.\n\n')
        else:
            text+=table(['Cover unit','true-G lower','true-G upper','saved lower','status','closure source'],
                [[r['leaf_id'],r['gamma_L'],r['gamma_U'],r['lower_bound'],r['status'],r['closure_source']] for r in q['active_cover']])+'\n\n'
            controlling=q['final_controlling_leaf']
            text+=('The remaining controlling leaf is `'+controlling['leaf_id']+'`. ' if controlling else 'No improving leaf remains unresolved under the qualified numerical cover. ')
            text+='The complete lower endpoint is justified across the full cover plus cutoff/Gini complements; the maximum child floor and an individual terminal status are not substituted. Closed improvement regions do not imply unrestricted physical infeasibility. Replaced ancestors are not extra cover units. All actual atomic events and qualified source scopes remain in the typed core.\n\n'
            text+=f'The final cover retains {len(q["unresolved_leaves"])} unresolved improvement obligation(s). A depth/width limit or mathematical target never deletes an unproved region. '
            text+=('The original numerical full-cover closure is qualified.\n\n' if q['certificate'] else 'These obligations, rather than repeated appearance of the own U, prevent a complete certificate at this endpoint.\n\n')
    text+='## Own fleets, restricted domains and actual Starts\n\n'
    text+=table(['Method / call','leaf','true-G interval','own final G','interval compatible','cutoff compatible','submitted Start','native Start status'],
        [[s['arm']+' / '+str(s['call']),s['leaf'],'['+fmt(s['lower_g'],12)+','+fmt(s['upper_g'],12)+']',fmt(s['own_final_G'],12),
            s['exact_g_interval_compatible'],s['cutoff_compatible'],s['submitted'],s['native_acceptance']] for s in starts])+'\n\n'
    text+='This compatibility table concerns the final own fleet. The interval/cutoff booleans use the original 1e-7 evidence policy; exact-g here means setting the epigraph to the computed physical Gini, not a rational exact boundary test. Actual mapped Start rows/bounds/types have their separate saved numerical checks. An earlier actual Start may be a different independently paid same-run fleet; mapping, all-row/type/bound/objective checks, submission/readback and native acceptance remain distinct in each saved Start record. A valid global U whose true Gini is outside a leaf is not forced into that leaf. Unknown acceptance or internal search causes remain unknown.\n\n'
    text+='''## Interpretation and stopping boundary

The evidence is limited to this exact known V50 instance, the three own paid windows, Seed0, the frozen implementation and the original floating numerical policy. Nonzero certification, if observed, has exactly that scope. If a reference certifies while M-B remains open, its same-window proof advantage is reported without inferring M-B's eventual completion time or changing the default. If all remain open, the result records a finite proof limit; it is not a universal impossibility result or an execution BLOCKED label. No observed gap fraction justifies an extrapolated stopping time.

The stage ends here with all required comparisons and adverse/uncertain evidence preserved. Further work prioritizes manuscript organization and a separately justified overall experiment plan. No new mathematical mechanism or repeated trial is automatically authorized by an open result. The exact source/physical/clock/call/coverage, additional self-review and later public recovery/cleanup receipts remain distinct evidence scopes.
'''
    (OUT/'proof_limit_report.md').write_text(text,encoding='utf-8')
    write(OUT/'proof_limit_details.json',dict(stage=v['decision'],trajectory_details=details,own_Start_and_scope=starts,
        optional_numerical_reference_decomposition=decomposition,core_SHA=sha(OUT/'reconstruction/final/current_core.json'),
        main_final_fleet_endpoint_unchanged=True,Optimize=0,seconds=time.perf_counter()-tick,script_SHA=sha(__file__)))
    print('Final finite proof-limit report generated from the three own qualified endpoints')

if __name__=='__main__':run()
