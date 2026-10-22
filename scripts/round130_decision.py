"""Finite claim scope, kept separate from the settled MS2 adoption."""
from round130_common import *

def signal(q,positive=True):
    if positive:return q['classification']=='LEFT_ONLY_CERTIFIED' or q['materiality']=='LEFT_MATERIALLY_FASTER'
    return q['classification']=='RIGHT_ONLY_CERTIFIED' or q['materiality']=='RIGHT_MATERIALLY_FASTER'

def run():
    o=read(OUT/'observations.json');s=read(OUT/'stratified_summary.json');ids=[p['id'] for p in read(OUT/'input_manifest.json')['roles']]
    axes={};reverse=[]
    for name,right in [('same_H_backend','PS'),('outer_control','S2R')]:
        records=[]
        for id in ids:
            qq=[q for q in o['pairs'] if q['id']==id and q['left']=='S2' and q['right']==right]
            assert sorted(q['seed'] for q in qq)==[0,1]
            if right=='PS':
                hh=[x for x in o['same_H'] if x['id']==id and x['left']=='S2']
                attribution=len(hh)==2 and all(x['same_complete_H'] and x['backend_exposed'] for x in hh)
                exposure='complete matched H and both backends' if attribution else 'unmatched or incomplete H/backend unexposed'
            else:
                dd=[x for x in o['differences'] if x['id']==id]
                cc=[x for x in o['costs'] if x['id']==id and x['method']=='S2']
                attribution=len(dd)==2 and all(x['pure_outer_package_attribution_eligible'] for x in dd)
                exposed=len(cc)==2 and all(x['split_count']>0 or x['partial_target_calls']>0 for x in cc)
                attribution=attribution and exposed
                exposure='same effective root; actual split/target package exposed' if attribution else 'same-root or actual split/target exposure insufficient'
            pos=attribution and all(signal(q) for q in qq);neg=attribution and all(signal(q,False) for q in qq)
            status='REPEATED_DIRECT_INCREMENT' if pos else 'REPEATED_REVERSE_REFERENCE_ADVANTAGE' if neg else 'CLOSE_AT_BOTH_SEEDS' if all(q['classification']=='BOTH_CERTIFIED' and q['materiality']=='TIME_CLOSE' for q in qq) else 'UNDETERMINED' if all(q['classification']=='BOTH_OPEN' for q in qq) else 'MIXED_OR_LIMITED'
            row=dict(id=id,status=status,attribution_eligible=bool(attribution),exposure=exposure,
                seed_observations=[dict(seed=q['seed'],classification=q['classification'],direction=q['direction'],materiality=q['materiality'],
                    left_minus_right_seconds=q['left_minus_right_seconds'],threshold=q['material_threshold_seconds']) for q in qq])
            records.append(row)
            if neg:reverse.append(dict(axis=name,**row))
        axes[name]=dict(records=records,repeated_direct_roles=[r['id'] for r in records if r['status']=='REPEATED_DIRECT_INCREMENT'])
    # A repeated reverse result is recorded regardless of the final paper scope.
    # Whether it exposes a core claim gap is an explicit substantive author/reviewer
    # judgement, not an automatic rejection of the earlier selected algorithm.
    scope=read(OUT/'claim_scope_assessment.json')
    assert scope['all_reverse_roles_considered'] and scope['reverse_roles']==[dict(axis=x['axis'],id=x['id']) for x in reverse]
    proof=scope['proof_or_identity_issue']
    if proof:tag='PROOF_OR_IDENTITY_ISSUE_REQUIRES_DECISION'
    elif s['execution']!='COMPLETE':tag='SELECTED_MS2_WITH_SCOPED_OR_MIXED_ATTRIBUTION'
    elif scope['reference_exposes_core_claim_gap']:tag='REFERENCE_CONTROL_EXPOSES_CORE_CLAIM_GAP'
    elif all(axes[k]['repeated_direct_roles'] for k in axes):tag='SELECTED_MS2_WITH_DIRECT_BACKEND_AND_CONTROL_EVIDENCE'
    else:tag='SELECTED_MS2_WITH_SCOPED_OR_MIXED_ATTRIBUTION'
    d=dict(UTC=utc(),execution=s['execution'],tag=tag,
        version_axis='S2/MS2 is the sole adopted method; predecessor numbers retain original labels; repository default unchanged',
        axes=axes,reverse_reference_roles=reverse,claim_scope_assessment=scope,
        R129_candidate_pass_not_reconsidered=True,no_new_method_or_Seed_or_role_or_budget_authorized=True)
    write(OUT/'scientific_decision.json',d)
    lines=['# Round130 claim decision','',f"Execution: **{d['execution']}**. Scientific label: **`{tag}`**.",'',
        'The user adopts the already selected uniform MS2 implementation as the sole proposed GI-TBC method, short ID S2. The E2 identity is `--round127-mode ms2`; E3 preserves it. Full M-B and ENS retain their historical names, and the repository default is unchanged.','']
    for name,axis in axes.items():
        lines+=['## '+name.replace('_',' '),'','| Known role | Two-Seed interpretation | Direct attribution eligible |','| --- | --- | --- |']
        lines += [f"| {r['id']} | {r['status']} | {r['attribution_eligible']} |" for r in axis['records']]
        lines+=['']
    lines += [scope['reason'],'',
        'P remains the primary benchmark. S2/PS measures the full backend/representation/control increment after each method pays H. S2/S2R concerns the entire exposed outer package, not a standalone split formula. S2R/PS also changes representation, preprocessing and cutoff domain. Open endpoints are supplementary; all both-open comparisons are UNDETERMINED. Ratios use only both-certified intersections. Two Seeds are finite path observations, not new problems or a robustness guarantee.','',
        'This fixed study ends here. No Seed2, extra role, tuning, component search, additional long window or promotion of S2R is authorized. Any remaining attribution is stated as limited or mixed.','']
    (OUT/'claim_decision.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(dict(execution=d['execution'],tag=tag,axes={k:v['repeated_direct_roles'] for k,v in axes.items()},reverse_roles=scope['reverse_roles'])))
if __name__=='__main__':run()
