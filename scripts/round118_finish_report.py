"""Render the completed scientific core; no optimization or new evidence."""
from pathlib import Path
import csv,json,time
from round118_data import ROOT,OUT,read,write,sha,utc
from round118_common import budget

def cells(path):
    with path.open(encoding='utf-8-sig',newline='') as file:return list(csv.DictReader(file))

def number(value):return '—' if value is None else f'{value:.9g}'

def finish():
    tick=time.perf_counter();core=read(OUT/'reconstruction01/current_core.json')
    assert core['decision']['execution_stage']=='COMPLETE' and len(core['arms'])==4 and len(core['pairs'])==6
    b=budget();assert not b['unclosed'] and b['paid_starts']<=20 and b['paid_outer_seconds']<=28000
    assert b['qualification_starts']<=13 and b['qualification_seconds']<=1200
    arms=core['arms'];pairs=core['pairs'];lookup={a['arm']:a for a in arms};decision=core['decision']
    assert all(a['actually_executed'] and a['formal_protocol_qualified'] and a['T_produce']<=5400 and not a['own_exact_zero'] for a in arms)
    targets=cells(OUT/'reconstruction01/target_discovery.csv');partitions=cells(OUT/'reconstruction01/time_partitions.csv')
    reliability=cells(OUT/'reconstruction01/numerical_reliability.csv');counts=cells(OUT/'reconstruction01/native_counts.csv')
    contracts=read(OUT/'campaign/raw/02_N40-R1-S_S0_M-B/round118_model_contracts.json')
    assert contracts['actual_M_B_quantity_type']=='C' and contracts['independent_ENS_Q_flag'] is False
    assert all(c.get('full_original') or c['quantity_type']=='C' and c['frozen_A_B_rows_checked']==80 for c in contracts['contracts'])
    primary=next(p for p in pairs if p['candidate']=='M-B' and p['control']=='P-GRB')
    control=next(p for p in pairs if p['candidate']=='M-B' and p['control']=='P-S')
    mbH=next(h for h in core['same_H'] if h['candidate']=='M-B')
    interpretation={
        'PROOF_RELIABILITY_PRIORITY':'At least one recorded same-domain native claim or dependent closure is contradicted by a verified physical fleet. The affected call and dependencies are revoked. Physical fleets remain useful, but other wins do not hide the proof failure. The next priority is one smallest correctness/numerical issue.',
        'PRIMARY_BENCHMARK_RISK_ON_THIS_ROLE':'M-B has a material LOSS against the primary cold benchmark on this one role. Its primal/bound/proof/cost nature is retained below. Assess its effect alongside all previously frozen positive and negative evidence; this one result neither automatically revokes historical support nor mandates a pointwise algorithm patch.',
        'NONZERO_PROOF_INCREMENT_ON_THIS_ROLE':'M-B provides a qualified complete nonzero numerical certificate and WIN against both cold P and the qualified same-H P-S control. This confirms a local proof increment on this role and supports organizing a finite preregistered frozen-candidate paper benchmark, without a general dominance or stability claim.',
        'LIMITED_OR_MIXED_ROLE_EVIDENCE':'The completed role does not meet the frozen nonzero-proof-increment condition. Distinguish material open-endpoint progress, common certification, weak increment, backend cost and any missing exposure. Open improvements are not complete nonzero proof evidence.'
    }[decision['research_disposition']]
    lines=['# Round118 final scientific report','',
        f"Execution is **COMPLETE**. The unique research disposition is **{decision['research_disposition']}**. M-B/cold P: **{primary['classification']}**; M-B/P-S: **{control['classification']}**; P-S attribution eligible: **{mbH['attribution_eligible']}**.",'',interpretation,'',
        'One prospectively frozen N40-R1-S problem was generated once and all four methods ran once in the fixed order cold P-GRB → M-B → P-S → ENS-C. Each received a5400-second producer cap. This is one problem, not four independent samples or a population WIN rate. ENS-C remains the default; M-B retains its finite R111 candidate identity. No algorithm, cut, representation, branching, AM or solver parameter was developed here.','',
        '## Qualified endpoints and three clocks','',
        '| Method | Own U | Qualified L | Signed U−L | Complete certificate | T_produce s | T_verify s | T_total s | Proof evidence |',
        '|---|---:|---:|---:|---|---:|---:|---:|---|']
    for a in arms:lines.append('| '+ ' | '.join([a['arm'],number(a['U']),number(a['L']),number(a['gap']),str(a['certificate']),number(a['T_produce']),number(a['T_verify']),number(a['T_total']),a['proof_evidence']])+' |')
    lines += ['', 'T_produce includes admission, independently paid H where applicable, model/Start/callback work, native cleanup, supervision, serialization and sealing. T_verify begins after the producer seal; T_total has the same origin. No component is subtracted to create an unexecuted score. Necessary cross-arm reconciliation is a separately recorded paid group phase. Ordinary open/LOSS results are complete execution, not BLOCKED.', '',
        '## Six fixed comparisons','',
        '| Candidate / control | Classification | Severe regression | Backend attribution | Exact certified-time ratio |',
        '|---|---|---|---|---:|']
    for p in pairs:lines.append('| '+ ' | '.join([p['candidate']+'/'+p['control'],p['classification'],str(p['severe_regression']),str(p['backend_attribution_eligible']),number(p.get('certified_time_ratio'))])+' |')
    lines += ['', 'Certificate priority and the frozen absolute materiality thresholds are unchanged: a_U=max(.001,.01|U_control|), a_gap=max(.001,.10|gap_control|), a_t=max(30,.10 t_control). Exact certification-time ratios require both sides to certify. Open endpoints do not estimate unknown final certification times. Tiny signed gaps are retained. ENS/P-S and M-B/ENS outcomes are disclosed without becoming hidden pointwise vetoes.', '',
        '## Own primal progress, proof and costs','',
        'The own complete fleets, original objectives and committed UB flow are in `reconstruction01/fleets.csv` and `own_UB_flow.csv`. The earliest verified record of each final U is in `target_discovery.csv`; its availability is an upper bound on publication/observation, not exact internal discovery. Native calls, actual Optimize counts, LP/MIP runtimes, model sizes, work/nodes and controller splits are recorded separately. Equal U with different gap concerns qualified LB; similar LB with different U concerns primal progress. One M-B/ENS table does not isolate A/B, branching or AM causality.','',
        '| Method | First verified final-U record available s | Certificate completion s |','|---|---:|---:|']
    for row in targets:lines.append(f"| {row['arm']} | {row.get('target_record_available_upper_seconds') or '—'} | {row.get('complete_producer_certificate_seconds') or '—'} |")
    lines += ['', 'Full25-seed H semantics, accepted actions, final Y and capacity-assigned fleets are compared in `same_H_fleets.json`; scalar U equality is insufficient. Actual M-B p/d are continuous, Y/load integer and service/state/direction binary, with the existing80 A/B rows. Independent ENS-Q remains false. The original P-S full matrix/rows/types/bounds/objective and all-column Start API submission/readback are checked. Each method pays its own H, UB, Start and cache.','',
        '## Numerical reliability and provenance','',
        f"Cross-arm reconciliation contains {len(core['group_reconciliation']['rejections'])} proved same-domain claim rejection(s). See `numerical_reliability.csv` and `claim_revocations.csv` for exact calls, scopes, witness counterexamples and dependent revocation. A damaged claim is not repaired by a later small value, another arm, offline arithmetic or floor0. UNRESOLVED model/return/clock attribution cannot qualify an endpoint.",'',
        'Every actual Optimize segment is bound to its serial call, immutable complete model, scope/cutoff, ledger, raw-byte span/SHA and actual return. Healthy and rejected paths use that same attribution. Numeric epoch labels absent from raw are not invented. Saved LP relaxation/type restoration, applicable original domains and complete regional coverage remain necessary. Local statuses do not establish original global optimality, and sibling bounds are combined by complete-cover minima. Certificates retain the original floating-point1e−7 policy, not rational exactness.','',
        '## Prospectively fixed data and positive optimum','',
        'Pre-generation freeze commit2ccf331b734af9b6fa677f6e1a162b5bfaf0054e pins the new FAMILY, selection_id, original four-anchor/regional-r1 selection and inherited target/stock/weight mathematics. Input SHA cdbbadbb6fd4e1742cb063001003686e55ba2b5045f584b84d2fd238ba616c7a is new relative to the measured-input index. The source is the same865-station Capital Bikeshare static snapshot, not a new city or independent source; overlap with four old subsets is recorded. No network replacement, projection change, H/LP/MIP screening, redraw, extra Seed, V60/V100 run or extended window occurred.','',
        'B=239, Dsum=279 and shortage40. Whole-system stock includes return load; station totals need not be conserved. Empty routes remain feasible. With positive lambda/weights and positive targets≤capacity, F≥δs>0. Exact input-decimal δs=.2479344 and penalty-relaxation L_pen=.254132725 are explanatory only. They were never injected into H, models, Starts, cutoffs, online bounds, official L or certification. See `positive_objective_proof.md` and the exact decimal/parsed-binary64 arithmetic in `positive_objective_analysis.json`.','',
        'The pre-export argv froze all literal algorithm/input/order/deadline arguments with one deterministic cold-reference fingerprint readback slot. The zero-Optimize exporter resolved that slot once; complete numeric argv were bound before any H100 or formal Optimize. No discretionary recipe or command parameter changed after export. The main PE was copied unchanged; only the read-only exporter was compiled.','',
        '## Qualification and nonrefundable budget','',
        f"Final qualification passes33 zero-Optimize finite cases plus actual H100 P-S1/M-B5 Optimize calls, full original P-S Start and complete matching H. Qualification paid13 conservative starts/{b['qualification_seconds']:.9f} observed outer seconds. The author explicitly raised8→11→13; qualification1200s and total20/28000 remained fixed. Total closed research fees are{b['paid_starts']} starts/{b['paid_outer_seconds']:.9f} outer seconds. Failed declared slots were never refunded and nested component timers were not added again.",'',
        'Finite01/finite02 and cli01 failed on documented synthetic fixture mistakes before native children. cli02 P-S returned normally, then a new read-only assertion compared pre-Start API and post-Start log fingerprints. The corrected verifier retains full matrix/type/bound/objective/Start checks; Gurobi includes Start attributes in Fingerprint. The sealed P-S was not rerun. Its original producer identity, protocol, raw hashes and times are preserved under the explicit reuse authorization; the final verifier receives a separate identity. Its real intervening post-seal delay is disclosed in qualification T_verify/T_total and is not formal performance. cli03 started only the unrun M-B child and finished finite/post/admission in one wrapper.','',
        '## Paper contribution and bounded next priority','',
        'The substantive unified specification is `paper_algorithm_spec.md`; `paper_claim_evidence_map.md` distinguishes supported claims, finite observations and unknowns. Integrated original problem/formulation, exact inventory-product representation conditional on valid domains, physical H composition and verified scoped proof integration are specified. General multistart, relocation, disjunction, MIP Start, implicit integrality and the shortage inequality are not claimed as new general theory.','',
        'Historical F2/C2 benefits, L48/G50/F5 costs and the finite R111 candidate evidence remain at their original clocks/identities. R117’s observed16-arm/four-role V20/V50 layer is descriptive; its seven nonzero certificates come from two V20 problems and all V50 endpoints remain open. R116’s original six-role panel stays historical BLOCKED, with positions19–24 canceled and position18 technical history. One new V40 role is not pooled into heterogeneous speedups or claims of V50/Seed/source stability.','',
        f"The single next priority is{decision['research_disposition']}, as specified in `next_experiment_spec.md`. No second batch is executed or automatically scheduled. If all four endpoints remain open, nonzero proof capability on this V40 problem remains unverified and this round ends with its qualified endpoints.",'',
        '## Scientific payload and later delivery observations','',
        'This scientific report and core precede the actual safe carrier/export/empty-root reconstruction/extra review/remote observations. Those later receipts are separate and do not certify their own future commits. Only current required safe raw, small static source and limited safe qualification authorities are packaged; no PE/DLL/solver license/credential or contaminated old carrier is published.','',
        'R117’s current safe tree/carrier containment does not purge old refs, deleted-side PR differences, caches or issuer state. Alert1 remains open/validity unknown absent a later valid receipt; owner notification/history rewrite/alert closure remain pending owner actions. No such action is taken here.','']
    (OUT/'final_report.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    map_path=OUT/'paper_claim_evidence_map.md'
    text=map_path.read_text(encoding='utf-8').replace('**Pending actual four-arm evidence**; current execution/qualification stage must be reported explicitly',
        f"**Completed one-role evidence: {decision['research_disposition']}**; M-B/P{primary['classification']}, M-B/P-S{control['classification']}; M-B proof{lookup['M-B']['proof_evidence']}")
    map_path.write_text(text,encoding='utf-8',newline='\n')
    next_path=OUT/'next_experiment_spec.md'
    next_path.write_text(next_path.read_text(encoding='utf-8')+f"\nActual Round118 outcome: execution COMPLETE; unique priority **{decision['research_disposition']}**. M-B/P={primary['classification']}, M-B/P-S={control['classification']}, qualified nonzero M-B certificate={lookup['M-B']['proof_evidence']=='CLEAN_NONZERO_CERTIFICATE'}, P-S attribution={mbH['attribution_eligible']}. This is the selected priority, not authorization for another run.\n",encoding='utf-8',newline='\n')
    write(OUT/'scientific_closeout.json',dict(observed_UTC=utc(),execution_stage='COMPLETE',decision=decision,budget=b,
        current_core_SHA=sha(OUT/'reconstruction01/current_core.json'),final_report_SHA=sha(OUT/'final_report.md'),
        formal_arms=4,pairs=6,new_problem_count=1,no_performance_retry=True,source_PE_DLL_unchanged=True,
        stronger_offline_bound_not_injected=True,engineering_seconds=time.perf_counter()-tick,
        future_delivery_review_remote_observations_separate=True,native_starts=0,Optimize=0))
    print(json.dumps(dict(decision=decision,budget=b)),flush=True)

if __name__=='__main__':finish()
