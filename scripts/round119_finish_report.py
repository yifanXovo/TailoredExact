"""Report only completed fixed records; never creates solver evidence."""
from round119_common import *
import csv,inspect

STAGES={'ADVANCE_MB_PC_TO_INDEPENDENT_CONFIRMATION','RETAIN_PROOF_CLOSURE_ONLY','STOP_TESTED_CONFIGURATION'}
def num(v):return '—' if v is None else f'{v:.10g}'
def finish(stage,reason):
    assert stage in STAGES
    tick=time.perf_counter();values=[]
    for n in [1,2,3,4]:
        p=OUT/'reconstruction'/f'group{n:02d}'/'current_core.json'
        if p.exists():values.append(read(p))
        else:assert n==4 and (OUT/'confirmation_cancellation.json').exists()
    assert len(values)>=3 and not budget()['unclosed']
    assert all(a['formal_protocol_qualified'] and a['certificate_qualified'] for v in values for a in v['arms'])
    candidate=read(OUT/'candidate_identity.json')
    assert all(v['PE_SHA']==candidate['production_PE_SHA'] and v['DLL_SHA']==candidate['DLL_SHA'] for v in values)
    gate=read(OUT/'development_admission.json')
    exposed=any(m.get('committed',0)>0 for v in values for m in v['mechanism'] if m['arm']=='MB-PC')
    wins=[v['group']['id'] for v in values for p in v['pairs'] if p['candidate']=='MB-PC' and p['control']=='M-B' and p['classification']=='WIN']
    if stage=='ADVANCE_MB_PC_TO_INDEPENDENT_CONFIRMATION':
        assert gate['admitted'] and len(values)==4 and wins
        assert not next(p for p in values[-1]['pairs'] if p['candidate']=='MB-PC' and p['control']=='P-GRB')['severe_regression']
    if stage=='RETAIN_PROOF_CLOSURE_ONLY':assert exposed
    from round108_reader import portable
    import compare_round112_startup as comparison
    source=inspect.getsource(comparison.compare).replace("values['P-S']","values['M-B']").replace("name=='P-S'","name=='M-B'").replace("control='P-S'","control='M-B'")
    namespace=dict(vars(comparison));exec(compile(source,__file__+'::actual_full_H_MB_PC_comparison','exec'),namespace)
    H=[]
    for v in values:
        i=read(OUT/v['group']['campaign']/'identity.json')
        h=namespace['compare'](ROOT,i['launches'][0]['panel'],{l['arm']:portable(ROOT,l['destination']) for l in i['launches'] if l['arm']!='P-GRB'})
        assert all(c['qualified'] for c in h['comparisons'])
        H.append(dict(id=v['group']['id'],comparison=h))
    write(OUT/'formal_full_H_comparisons.json',H)
    b=budget();assert b['paid_starts']<=40 and b['paid_outer_seconds']<=48000
    assert b['qualification_starts']<=12 and b['qualification_seconds']<=2400
    write(OUT/'resource_summary.json',dict(b,maximum_starts=40,maximum_outer_seconds=48000,
        qualification_maximum_starts=12,qualification_maximum_outer_seconds=2400,
        all_failed_fees_retained=True,nested_native_seconds_added=False,engineering_separate=True,human_seconds='unknown'))
    N=next(v for v in values if v['group']['id']=='N40-R1-S')
    n40=next(a for a in N['arms'] if a['arm']=='MB-PC')
    decision=dict(stage=stage,reason=reason,development_gate=gate['conditions'],fixed_confirmation_completed=len(values)==4,
        fixed_confirmation_canceled=len(values)==3,formal_arms=sum(len(v['arms']) for v in values),
        actual_formal_contraction_exposure=exposed,material_MB_PC_over_MB_WIN_roles=wins,
        V40_MB_PC_nonzero_complete_certificate=n40['certificate'] and n40['U']>1e-12,
        default_ENS_changed=False,no_automatic_further_test=True,not_independent_generalization_or_statistical_superiority=True)
    write(OUT/'stage_decision.json',decision)
    lines=['# Round119 fixed-candidate result','',f'**{stage}**. {reason}','',
        f'The fixed panel completed {decision["formal_arms"]} current arms with one PE SHA `{candidate["production_PE_SHA"]}` and the frozen Gurobi13.0.2 DLL. ENS-C remains the default. R118 results remain unchanged.',
        '', '## Complete endpoints and clocks','',
        '| Role | Method | own U | qualified L | signed gap | Original certificate | T_produce | T_verify | T_total |',
        '|---|---|---:|---:|---:|---|---:|---:|---:|']
    for v in values:
        for a in v['arms']:
            lines.append('| '+' | '.join([v['group']['id'],a['arm'],num(a['U']),num(a['L']),num(a['gap']),str(a['certificate']),
                num(a.get('T_produce',a.get('complete_seconds'))),num(a.get('T_verify')),num(a.get('T_total'))])+' |')
    lines+=['','Signed gaps are preserved, including tiny negatives. A local interruption, local infeasibility or interval shrink is not a complete original certificate. Ratios of final proof time are not inferred for two open arms.',
        '', '## Three fixed pairs per role','', '| Role | Pair | Classification | Severe regression vs control | Basis |','|---|---|---|---|---|']
    for v in values:
        for p in v['pairs']:
            lines.append(f'| {v["group"]["id"]} | {p["candidate"]}/{p["control"]} | {p["classification"]} | {p["severe_regression"]} | {p["basis"]} |')
    lines+=['','Materiality is unchanged: a_U=max(.001,.01*abs(U_control)), a_gap=max(.001,.10*abs(gap_control)), a_t=max(30,.10*t_control); complete certificates have priority. Cross-arm physical witnesses can revoke a source-scoped numerical claim but never replace an arm\'s own fleet.',
        '', '## Mechanism exposure and full-solving cost','']
    for v in values:
        m=next(m for m in v['mechanism'] if m['arm']=='MB-PC')
        lines.append(f'{v["group"]["id"]}: paid child certificates {m.get("paid_certificates",0)}, own updates {m.get("own_updates",0)}, strict termination requests {m.get("strict_requests",0)}, committed contractions {m.get("committed",0)}, rebuilt MIPs {m.get("actual_rebuilt_MIPs",0)}.')
        for c in m.get('contracts',[]):
            lines.append(f'Actual commit at producer process time {num(c["process_seconds"])}s: [{num(c["old_lower"])},{num(c["old_upper"])}] to [{num(c["new_lower"])},{num(c["new_upper"])}], depth{c["depth"]}; source call{c["proof_call"]}; next actual Optimize calls {c["next_Optimize_calls"]}. Full request/return/commit times, old scope/cutoff, own witness, complements and Start readback remain in the event journal and reconstructed tables.')
    from round119_mechanism_account import account
    account();mechanism=read(OUT/'mechanism_account.json')
    lines+=['','Each candidate actually used one strict proof event and retained half its old interval. Own-update counts above include the initial incumbent; strict new counts are one less. The native call counts are P1, M-B5 (3LP+2MIP), MB-PC9 (6LP+3MIP) on every role; M-B has three distinct scoped model SHAs and MB-PC six.',
        '', '| Role | Source proof registered | own U record | Termination requested | Real return | Atomic commit | New retained-root LP | Global L at commit |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for e in mechanism['events']:
        lines.append('| '+' | '.join([e['id']]+[num(e[k]) for k in ['source_registered_process_seconds','own_verified_record_process_seconds',
            'termination_request_process_seconds','actual_return_record_process_seconds','atomic_commit_process_seconds','new_retained_root_LP','global_L_at_commit']])+' |')
    lines+=['','These are actual C++ journal/event process timestamps. `mechanism_account.json` also binds next actual LP/MIP identities, the closed request record after model construction, externally observed producer-clock upper bounds, integer Y, original scope/cutoff, predicate margin and both old child bounds. Exact model-build start/API-entry and internal first discovery remain unknown. Every real requested stop returned INTERRUPTED before its transaction. Actual complete own Starts were submitted and checked on the new MIPs.',
        'F2 complete-certificate production time is 150.9622661s versus M-B717.4892725s (ratio0.2104035166); this is an actual full proof benefit on a known role. N40 is an open TIE with slightly worse U/gap; R98-C2 is a severe LOSS against both controls. Every new retained-root LP reproduces its already paid old-left LP bound to the recorded precision. On N40 that is0.4789746698, only about0.000382452 above the original root LP0.4785922180 and below the inherited old MIP bound0.5609817266. The removed0.7875472937 is never treated as a new global bound.',
        'The current traces cannot identify whether unhelpful removal, changed native branching/cuts/heuristics or rebuilding dominates a negative role. There is no extra counterfactual run. Old search-tree, local-cut and basis migration is not claimed. All rebuild/Start/LP/MIP costs are paid under one deadline. A paired endpoint change does not isolate an internal Gurobi cause; lost-tree cost and an unrun counterfactual cannot be measured by subtracting wall times.',
        '', '## Admission, certification and resource closure','',
        'Development admission: '+json.dumps(gate['conditions'],sort_keys=True)+'.',
        'The fixed E50-C1 three-arm confirmation was completed.' if len(values)==4 else 'All three E50-C1 positions are CANCELED_NOT_ADMITTED, unrun and not counted as completed.',
        'V40 MB-PC obtained a qualified nonzero original-problem certificate.' if decision['V40_MB_PC_nonzero_complete_certificate'] else 'This round did not close the V40 nonzero proof; its qualified U/L/gap remain open.',
        f'Nonrefundable solver/qualification accounting: {b["paid_starts"]}/40 conservative starts, {b["paid_outer_seconds"]:.6f}/48000 outer seconds; qualification {b["qualification_starts"]}/12 starts and {b["qualification_seconds"]:.6f}/2400 seconds.',
        'qual01 retains the successful native chain and failed old MB-PC call-view wiring; the read-only fix reused sealed output without rerunning that slot. qual02 retains all three H100 positions and the recorded parent-shell exit upper bound. qual03 retains the finite two-contraction prefix and failed expected empty-fleet assertion; the corrected physical-tail test was not rerun, and pure physical mathematics/source review is separately labeled.',
        'Qualification exit accounting excludes the long subsequent assistant idle interval using an original command-completion event; it does not change any producer, verification or total clock. Engineering/build/scan/export/restore costs are separate. Human elapsed effort is unknown, not zero.',
        'formal01 retains all three successful sealed/verified arms and its failed group-summary attempt caused by a missing campaign-local cold-reference path. reader_repair01 was separately billed, copied only the existing frozen zero-Optimize exporter reference bytes, preserved the failed directory, and rebuilt the same three-arm summary without changing producer/reader bytes or rerunning a formal position.',
        '', '## Evidence, delivery and limitations','',
        'Current reconstruction tables include own fleets/UB, target availability, actual call/model/scope/epoch/Start, LP and native ledger, physical rejection, cover, event records and all three clocks. `candidate_identity.json`, `pre_formal_freeze.json`, `argv_freeze.json`, `protocol.json` and fee receipts bind the positions and versions.',
        'The successful native chain, finite physical native embeddings, pure mathematical completion, formal performance, subsequent empty-root reconstruction and separate extra review are distinct layers. The implementation author conducts the separate review process; no third-party native reproduction is claimed.',
        'Named development/confirmation roles were already exposed. This is finite configuration evidence within V<=50, not geographic/Seed stability, statistical superiority or uniform P dominance. Standard bound pruning is not a new general theorem. No default promotion, merge, future grid or automatic research continuation follows this decision.',
        'The current safe carrier contains only necessary current raw/source and small named safe authorities. Actual export/recovery, extra review and remote observations are recorded separately in `delivery/` and the delivery summary; these scientific records do not attest their own future commits or all Git history.', '']
    (OUT/'final_report.md').write_text('\n'.join(lines),encoding='utf-8')
    write(OUT/'engineering/report_receipt.json',dict(seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,stage=stage))
    print(json.dumps(decision),flush=True)
if __name__=='__main__':finish(sys.argv[1],Path(sys.argv[2]).read_text(encoding='utf-8').strip())
