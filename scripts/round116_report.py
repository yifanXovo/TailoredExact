"""Organize current-only formal evidence and explicit qualification appendices.

The admitted reader remains unchanged. This offline organizer separates H100
from the formal proof/Optimize/decision denominator and never changes an arm.
"""
import argparse,collections,csv,json,shutil,time
from pathlib import Path
import read_round116 as reader
import round108_reader as core

def text(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(value.rstrip()+'\n')
def organize(root,raw,dest):
    tick=time.perf_counter();root=Path(root).resolve();out=root/reader.ROUND;raw=Path(raw);dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    current=core.read(raw/'current_core.json');ids={p['id'] for p in core.read(out/'input_manifest.json')['roles']}
    reliability=[];native=[]
    for p in sorted(raw.iterdir()):
        if p.suffix!='.csv':continue
        rows=core.rows(p)
        if rows and 'id' in rows[0]:
            formal=[r for r in rows if r['id'] in ids];qual=[r for r in rows if r['id'] not in ids]
            if formal:core.table(dest/p.name,formal)
            if qual:core.table(dest/('qualification_'+p.name),qual)
            if p.name=='numerical_reliability.csv':reliability=formal
            if p.name=='native_counts.csv':native=formal
        else:shutil.copyfile(p,dest/p.name)
    # JSON core comparisons keep typed values, not CSV-coerced booleans/counts.
    typed_reliability=[]
    for r in reliability:
        q=dict(r);q['rejected_calls']=int(q['rejected_calls']) if q['rejected_calls']!='unknown' else 'unknown';typed_reliability.append(q)
    summary=dict(current['summary']);complete=summary['execution_stage']=='COMPLETE'
    decision=reader.phase_decision(current['arms'],current['pairs'],complete,typed_reliability)
    # Original reconstruction includes4 qualification arms; make each actual
    # process/Optimize denominator explicit without modifying the frozen reader.
    summary.update(decision=decision,actual_native_Optimize_formal=sum(int(r['actual_Optimize']) for r in native),
        actual_native_Optimize_including_H100=current['summary']['actual_native_Optimize'],
        proof_reliability_formal_denominator=24,qualification_separate_from_stage_A=True,
        Optimize_count_scope='qualified lifecycle arms only; excludes the failed pending arm',
        failed_pending_arm_reported_Optimize=core.read(out/'execution_stop.json')['reported_failed_arm_Optimize'])
    current['summary']=summary
    for name in ['backend_conclusions.json','cohort_reconciliation.json']:shutil.copyfile(raw/name,dest/name)
    core.write(dest/'summary.json',summary);core.write(dest/'current_core.json',current)
    core.write(out/'engineering/report_organization_receipt.json',dict(seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
        admitted_reader_SHA=core.sha(reader.__file__),organizer_SHA=core.sha(__file__),
        change='explicit formal/H100 table and Optimize/phase-A denominator separation only',
        arm_endpoints_pairs_receipts_unchanged=True,source_reconstruction_preserved=str(raw),output=str(dest)))
    return summary

def report(root):
    root=Path(root).resolve();out=root/reader.ROUND;summary=core.read(out/'reports_final/summary.json');data=core.read(out/'reports_final/current_core.json')
    snapshot=core.read(out/'source/snapshot.json');manifest=core.read(out/'input_manifest.json');decision=summary['decision'];backends=core.read(out/'reports_final/backend_conclusions.json')
    disposition=dict(decision,failed_role='E100-C1',failed_arm='ENS-C',failed_global_launch_number=18,
        formal_children=summary['actual_formal_children'],qualified_formal_arms=summary['qualified_formal_arms'],
        evaluable_pairs=summary['evaluable_pairs'],remaining_unstarted_positions=[19,20,21,22,23,24],
        unique_evidence_gap='Full six-role completion and the pending return/scope qualification under a valid frozen contract.',
        default_changed=False,formal_retry_authorized=False,next_phase_automatically_executed=False)
    core.write(out/'research_phase_decision.json',disposition)
    counts=collections.Counter(a['proof_evidence'] for a in data['arms'])
    stop=core.read(out/'execution_stop.json')
    lines=['# Round116 final report','',f"execution_stage={summary['execution_stage']}. {summary['actual_formal_children']}/24 actual formal children, {summary['qualified_formal_arms']}/24 qualified arms and {summary['evaluable_pairs']}/36 evaluable fixed pairs. Main time is T_produce; T_verify and same-origin T_total are disclosed separately. Every formal destination is used at most once.",'',
        f"Launch18, E100-C1 ENS-C, returned normally and sealed a pending producer output at {stop['failed_arm_T_produce']:.6f}s, within its3600s cap. Its required serial return audit failed because three LP log paths each contain two Optimize headers and are each referenced by two ledger calls. The frozen audit requires exactly one header per call log. The ledger and unique logs both report ten Optimize calls; the assertion does not by itself prove a hidden extra call or a solver error. Individual epoch/return/scope qualification was not completed under the admitted predicate. No completed T_verify/T_total or usable formal endpoint is assigned to this arm. Positions19–24 were never started. The admitted helper identity, sealed bytes and original pending state remain unchanged; there is no formal retry or patched continuation.",'',
        'The sole remaining evidence gap is full-panel completion, including the failed return/scope qualification, under one valid frozen contract. This campaign stops with BLOCKED and receives no complete-panel A–D conclusion. Local qualified comparisons and call-level contradictions are reported below; they cannot supply the missing six-role denominator.','',
        f"One official GBFS2.3 static station response, SHA256 `{snapshot['station_response_SHA']}`, supplied all six inputs. The first HTTP-successful structurally valid complete response contains865 eligible entities, with preserved station IDs/UTF-8 sorting, original row mapping, capacities, WGS84 and pinned pyproj3.7.2/PROJ operation to UTM18N. Request/UTC/final URL/bytes/version/last_updated/license, every original row decision and projection/inverse-axis checks are retained. No second station snapshot, source substitution, result-based redraw, seed grid, extra formal arm or production rebuild occurred.",'',
        'Only coordinates/capacities change source. Inventories, targets, max-normalized weights, vehicles/Q, physical T and the centroid depot are deterministic same-family synthetic fields. All six subsets come from the same snapshot and may overlap. This is finite cross-source evidence, not independent cities, IID sampling, real-demand scheduling validation or a complete paper benchmark. Raw source is a non-commercial research appendix under the [official license](https://capitalbikeshare.com/data-license-agreement); no standalone data service, logo or external-system endorsement is offered.','',
        '|Role|Method|Own U|Qualified L|Signed gap|Proof evidence|T_produce s|T_verify s|T_total s|',
        '|---|---|---:|---:|---:|---|---:|---:|---:|']
    def num(v):return 'unknown' if v is None else f'{v:.12g}'
    for a in data['arms']:lines.append(f"|{a['id']}|{a['arm']}|{num(a['U'])}|{num(a['L'])}|{num(a['gap'])}|{a['proof_evidence']}|{num(a['T_produce'])}|{num(a['T_verify'])}|{num(a['T_total'])}|")
    lines+=['','|Method/control|Six-role vector|Eligible|Severe losses|','|---|---|---:|---|']
    for key,entry in backends.items():
        vector='/'.join(v['classification'] for v in entry['six_role_vector']);lines.append(f"|{key}|{vector}|{entry['eligible']}/6|{','.join(entry.get('severe_losses',[])) or 'see36-pair table'}|")
    severe=[p for p in data['pairs'] if p['severe_regression'] is True]
    negative=[a for a in data['arms'] if a['gap'] is not None and a['gap']<0]
    changed=[p for p,s in zip(data['secondary_pairs'],data['pairs']) if p['classification']!=s['classification']]
    rel=core.rows(out/'reports_final/numerical_reliability.csv')
    contrad=sum(int(r['rejected_calls']) for r in rel if r['rejected_calls']!='unknown')
    structure=core.rows(out/'objective_structure.csv')
    lines+=['',
        'The four fully qualified roles give ENS/P and M-B/P WIN/WIN/WIN/WIN; the two V100 comparisons remain UNEVALUABLE. P-S/P is LOSS/WIN/WIN/WIN/UNEVALUABLE/UNEVALUABLE: on E20-C1 both methods attain the same certified positive objective, while P-S costs653.031s versus cold P552.221s. This loss is retained. Both ENS/P-S and M-B/P-S have four eligible WINs, but the six-role attribution is INCOMPLETE_ATTRIBUTION. The fixed denominator is not replaced with the four completed roles.',
        f"Severe regressions among the24 evaluable pair positions: {len(severe)}; the12 unevaluable positions carry no assessed severity. Same-origin verification totals {sum(a['T_verify'] for a in data['arms'] if a['T_verify'] is not None):.6f}s over17 qualified arms. Secondary T_total changes {len(changed)} pair classifications. Tiny negative signed gaps are preserved for {', '.join(a['id']+' '+a['arm'] for a in negative) or 'no arms'}; no clamp or misleading relative percentage is used.",
        f"There are {contrad} rejected calls among the qualified formal lifecycle records. This says that the performed same-domain checks found no contradiction in those records; the failed pending and unstarted records remain unknown. The7 clean nonzero certificates occur in the two V20 roles. No qualified own-zero certificate or source-reduced endpoint was observed. The V50 results remain open; their feasible-solution and safe-gap gains do not turn into full nonzero proofs.",'',
        '|Role|B_lo..B|sum D|W|lambda W|delta|beta|Cold rows/columns|Matrix abs min/max|',
        '|---|---|---:|---:|---:|---|---|---|---|']
    for s in structure:
        lines.append(f"|{s['id']}|{s['B_lo']}..{s['B_hi']}|{s['sumD']}|{s['W_float']}|{s['lambda_W_float']}|{s['delta']}|{s['beta']}|{s['cold_reference_rows']}/{s['cold_reference_columns']}|{s['matrix_coefficient_min_abs']}/{s['matrix_coefficient_max_abs']}|")
    lines+=['',f"Proof evidence counts over the24 formal positions: {dict(counts)}. `numerical_reliability.csv` separates actual/journal/independently verified/qualified/rejected calls, exact source/model/scope/counterexample identities and rejected dependencies. None found in the performed checks is not a general numerical-correctness guarantee. Clean nonzero certificates are numerical original-domain certification under the frozen1e-7 protocol, rather than rational branch-and-bound proofs. Own Y=D plus F>=0 is independent zero certification and does not repair or credit a damaged native call. Source-reduced own U/floor0/safe-gap comparisons do not recover potentially wrong pruning or establish engine proof progress.",'',
        'Every warm arm independently pays the original25-seed H semantics, actions, inventory and capacity-owned fleet. Complete H/actual backend exposure and explicit ineligible reasons are in same_H and backend_conclusions. The six-role denominator remains6 even when H is incomplete or common H closes zero before the backends. Matching only U does not establish matching fleets. The controller and native tables retain actual atomic splits, nodes/Work/iterations, visible cuts, model sizes/coefficient evidence and native returns. Unrecorded internal causes remain unknown.','',
        'The prospective measurement-v2 producer includes admission/H/online physical/model/type/Start/callback/controller work, native cleanup/output closure, original supervision and lightweight final checks. It seals before pending verification; serial independent checks do not reenter native or create new fleets/bounds. Verification/total costs remain real even above an arm cap. Per-arm closed receipts are unchanged by actual final cohort revocation, which has its own timestamps and group engineering cost. Current secondary total-time comparisons retain adverse orderings. Old R115/old-whole measurements are not merged into a common clock benchmark.','',
        'Exact inventory analysis reports B_lo=max(0,B-sumQ)<=sumY<=B, delta=min(lambda*w/D)>0, F>=delta*K and necessary beta/strict-K domains under literal decimal and parsed-binary64 coefficient interpretations. Every own U/G/P/lambdaP/K is recomputed only from its sealed existing integer Y. Necessary inventory restrictions do not prove routing sufficiency, a whole-fleet infeasibility result, a global objective lattice, or a faster target oracle. They neither strengthen formal LB nor enter production. Fixed lambda with varying W gives lambda*W times mean weighted deviation; cross-V differences are not a pure size effect. Shortage roles remain included when stock conservation excludes Y=D.','',
        'The limited old G100 impact appendix verifies the exact old input SHA, Q/T/handling/objective coefficients and the sealed R115 P-S own zero fleet. Six published R110/R111/R114 positive global claims lose current trust; four affected paired primitives are recomputed without changing their descriptive classifications. Old own U, raw, clocks, overcaps, missing comparisons and phase decisions are unchanged. No conclusion about every local positive-G leaf or a unique native cut/presolve cause is drawn; no historical performance is rerun.','',
        f"Actual paid budget: {summary['budget_starts']}≤56 conservative starts and {summary['budget_seconds']:.9f}≤65000 outer seconds, with qualification included and every failed declaration permanent. Actual wrapper-exit observation delay is conservatively included, including the delayed close of failed group05; this is not producer/search time. Group05 retains five declared slots although only two children started. Qualified formal lifecycle Optimize count is {summary['actual_native_Optimize_formal']}; including qualified H100 it is {summary['actual_native_Optimize_including_H100']}. The failed pending arm separately reports ten calls without completed lifecycle qualification. Six zero-Optimize native reference exports occur within one disclosed exporter child. Nested native/H/audit times are not added twice. Pure source/data/dependency compilation/arithmetic/reconstruction/export/restore/publication costs are engineering; uninstrumented manual time is unknown, not zero.",'',
        f"Unique disposition: `{decision.get('priority')}` / `{decision.get('decision','BLOCKED')}`. Apply the preregistered A→B→C→D order only to a complete panel; a blocked panel receives no complete A-D conclusion. These thresholds allocate finite research resources, not statistical probability. ENS-C stays default, cold P-GRB primary, M-B the finite R111 candidate and P-S a contribution control. No role-wise winning-method splice, default change, merge or next round is executed.",'',
        'The final producer/helpers/admitted reader, original PE/DLL/source206, all24 argv and policies are bound to actual H100 qualification/admission. Review execution is accurately identified as implementer-authored separate checks; no third-party native reproduction is claimed. The current-only carrier has explicit source/helper/config/CSV-capacity dependencies and small signed old authorities. Actual one-export/fresh-empty-root restore/core equality and the required additional seven-question organized-result review have subsequent receipts. This scientific report does not claim its own future commits or remote observations are already verified.']
    text(out/'final_report.md','\n'.join(lines))
    spec='''# Frozen exact methods: Round116 finite external evidence

Production source d0014a7163e3996fe120471420e56b089c9715ae, PE a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8 and Gurobi13.0.2 DLL9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88 are unchanged. ENS-C is the full research-round83-vds-equal-net-exchange default; M-B adds only the frozen round98 m-binary state/service representation with ENS-Q false; cold P is the original compact without H/Start/external UB; P-S independently pays that same H and submits one fully verified all-column Start to the unchanged original compact. No input/size/clock dispatch or new mechanism is present.

The original physical problem remains empty departure, single-vehicle one-time nonzero one-direction integer station service, inventories[0,C], every prefix/return load[0,Q], loaded return with unloading, and travel+(pickup+drop)*total pickups. Q bounds load rather than cumulative pickups; min_ratio is compatibility only. F=G_true+lambda*sum w*abs(Y/D-1), with the original zero-denominator convention, lambda=.15 and maximum-normalized weights. M-B's valid A/B rows and quantity integrality implied by integer inventory plus binary service/direction retain the original domain; actual model/types/Start/scope/cover remain necessary.

R111 finite CONFIRMATION_SUPPORT and historical costs remain their original phase, clocks and source. R115 completed its four G100 arms; own P-S zero establishes optimum0 and all four have damaged native calls. ENS/P-S W/W/L/W/L and M-B/P-S W/W/L/T/L are mixed historical classifications with heterogeneous clock layers. The finite old global-claim appendix adds current knowledge while leaving local positive-G scope claims and old performance records untouched.

Round116 uses one external official station-coordinate/capacity snapshot and six synthetic same-family roles,24 once-only arms/36 pairs, common Seed0 and measurement-v2. See final_report and numerical_reliability for actual primary P results, public ENS/P-S costs and the three separate execution/comparison/proof axes. The unique ordered resource disposition is in research_phase_decision.json. Reliable nonzero numerical certificates, independent own zero, reliable positive-LB open evidence, source reduction and unverifiable records are different categories. No WIN count validates a damaged proof engine. One-city finite transfer, overlapping subsets, synthetic demand and fixed lambda with varying weight sum limit scope; no universal city, IID, significant or final paper-benchmark claim is made.

Freeze the four methods and stop after the actual stated Round116 result. No default change, merged PR, mechanism search, additional draw, solver setting repair, performance retry or automatically started next phase is authorized by this specification.
'''
    text(out/'paper_candidate_spec.md',spec)
    text(out/'research_phase_decision.md',f"# Round116 resource disposition\n\n{json.dumps(disposition,indent=2)}\n\nActual complete-panel conditions follow the frozen A/B/C/D priority. No next phase is automatically run.")
    pr=['Round116 freezes the original ENS-C, M-B, cold P-GRB and independently paid P-S on six preregistered inputs from one official external station snapshot. Coordinates/capacities are external; inventories/targets/weights/fleet/T remain synthetic.','',
        f"Execution: {summary['actual_formal_children']}/24 actually started, {summary['qualified_formal_arms']}/24 qualified formal arms and {summary['evaluable_pairs']}/36 evaluable comparisons; stage {summary['execution_stage']}. E100-C1 ENS-C returned within cap but required verification rejected reused LP logs; positions19–24 are unstarted. The frozen helper/producer identity was retained, with no retry or patched continuation.",'',
        f"M-B/P vector: {'/'.join(v['classification'] for v in backends.get('M-B/P-GRB',{}).get('six_role_vector',[]))}. Full primary/control vectors and public P-S tradeoffs are retained, with complete-H/backend eligibility separate.",'',
        f"Formal proof categories: {dict(counts)}. Call-level contradictions/dependency revocations, source-reduced feasible results, independent own-zero and reliable nonzero numerical certificates remain distinct. Unique disposition: {decision.get('decision','BLOCKED')}.",'',
        'T_produce includes original online checks/Start and native cleanup; independent T_verify and same-origin T_total are disclosed. Producer/measurement/source206/PE/DLL/Seed/tolerances/default are unchanged. No formal retry, redraw or additional performance seed.','',
        f"Actual budget: {summary['budget_starts']}/56 starts, {summary['budget_seconds']:.3f}/65000 outer seconds, qualification included. Official snapshot/projection/license, old G100 global-claim impact, exact inventory necessary conditions and every sealed own fleet are retained.",'',
        'Actual export/empty-root reconstruction equality, extra organized-result review and remote head/base/open/draft/OID checks are recorded by separate subsequent delivery receipts. No third-party native rerun, merged PR, universal city inference, final paper benchmark or next round is claimed.']
    text(out/'pr_body_science.md','\n'.join(pr));return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['organize','report']);parser.add_argument('--root',required=True);parser.add_argument('--raw');parser.add_argument('--out');a=parser.parse_args()
    v=organize(a.root,a.raw,a.out) if a.mode=='organize' else report(a.root);print(json.dumps(v),flush=True)
