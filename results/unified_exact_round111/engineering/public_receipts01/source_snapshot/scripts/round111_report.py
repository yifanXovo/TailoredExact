"""Publish current finite decision, clocks, budget, and scoped research claims."""
from round111_common import *
import csv, shutil

def rows(path):
    with Path(path).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def main():
    reports=OUT/'reports_final';selection=read(reports/'selection_decision.json')
    assert selection['evidence_layer']=='R110_MAIN_36_PLUS_R111_SEED_6'
    shutil.copyfile(reports/'selection_decision.json',OUT/'selection_decision.json')
    arms=rows(reports/'arms.csv');assert len(arms)==6
    ident=read(OUT/'campaign/identity.json');timings=[]
    for launch in ident['launches']:
        dest=Path(launch['destination']);native=read(dest/'native_end_receipt.json');audit=read(dest/'postexit_audit_receipt.json');whole=read(dest/'whole_arm_receipt.json')
        timings.append(dict(number=launch['number'],old_R110_number=launch['old_R110_number'],id=launch['id'],arm=launch['arm'],cap_seconds=launch['cap_seconds'],
            native_end=native['complete_seconds_until_native_end'],audit_end=audit['complete_seconds_until_audit_end'],whole=whole['complete_seconds'],
            native_only_within_cap=read(dest/'completion.json')['within_cap'],full_clock_within_cap=whole['complete_seconds']<=launch['cap_seconds'],
            required_postexit_seconds=audit['complete_seconds_until_audit_end']-native['complete_seconds_until_native_end'],
            metrics_written_before_whole=True,receipt_SHA=sha(dest/'whole_arm_receipt.json')))
    write(OUT/'strict_full_clock_assessment.json',dict(current=timings,all_current_complete_clocks_qualified=all(v['full_clock_within_cap'] for v in timings),
        old_R110_arm42=dict(native_end=3571.0120709999464,audit_end=3600.707823600038,whole=3600.7215734999627,cap=3600,formal_qualified=False,classification='UNEVALUABLE'),
        current_dynamic_checks_in_cap=True,old_clock_not_recomputed_from_new_replays=True))
    engineering=[]
    for p in sorted((OUT/'engineering').glob('*/receipt.json')):
        value=read(p);engineering.append(dict(label=p.parent.name,seconds=value.get('seconds'),exit_code=value.get('exit_code'),
            native_processes=value['native_processes'],Optimize=value['Optimize'],receipt_SHA=sha(p),
            unknown_time=value.get('seconds') is None))
    independent=[]
    for p in sorted((OUT/'review').glob('*/receipt.json')):
        value=read(p)
        seconds=value.get('engineering_elapsed_seconds',value.get('seconds'))
        independent.append(dict(label=p.parent.name,seconds=seconds,exit_code=value['exit_code'],receipt_SHA=sha(p)))
    fee_graph=[]
    for path in sorted((OUT/'fees').glob('*/launch.json')):
        launch,receipt=read(path),read(path.parent/'receipt.json')
        fee_graph.append(dict(label=path.parent.name,wrappers=launch['actual_wrapper_processes'],
            actual_native_children=receipt['actual_native_children_with_launch'],declared_starts=receipt['conservative_process_starts']))
    actual_starts=sum(v['wrappers']+v['actual_native_children'] for v in fee_graph)
    write(OUT/'resource_accounting.json',dict(research=budget(),engineering_process_receipts=engineering,
        independent_engineering_receipts=independent,engineering_seconds=sum(v['seconds'] for v in engineering if v['seconds'] is not None),
        engineering_receipts_without_measured_time=[v['label'] for v in engineering if v['seconds'] is None],
        independent_engineering_seconds=sum(v['seconds'] for v in independent if v['seconds'] is not None),
        accounted_receipts_as_of_unix=time.time(),later_final_public_remote_receipts_separately_recorded=True,
        manual_time='unknown',engineering_nested_phase_seconds_not_added=True,declared_unstarted_slots_refunded=False,
        actual_research_process_starts=actual_starts,conservative_research_process_starts=budget()['paid_starts'],research_process_graph=fee_graph,
        qualification_outer_interval=read(OUT/'fees/qualification_cli02/outer_accounting_interval.json'),
        native_nested_seconds_not_added=True))
    stage=selection['stage'];pairs=selection['seed_primary_pairs'];cost=budget()
    r2_zero=any(a['id']=='G100-R2' and a['certificate']=='True' and a['certificate_qualified']=='True' and
        a['numbers_qualified']=='True' and float(a['U'])==0. for a in arms)
    r2_statement=('A current R111 own exact physical F=0 with a qualified full-domain floor establishes G100-R2 Fstar=0; this is a new current proof, not a change to historical R110 evidence.' if r2_zero else
        'G100-R2 has no established zero-optimum proof in the retained historical or new current observations.')
    lines=[f'# Round111 final report\n\n**{stage}** — `R110_MAIN_36_PLUS_R111_SEED_6`.\n',
        'The six fixed current Seed1 arms ran once, serially, under the independently admitted equivalent audit wrapper and the unchanged R110 PE/DLL/205 production bindings. The main36 are an explicit immutable R110 import; they were not measured under this wrapper. No independent sample is added. ENS-C remains default; cold P-GRB remains the primary benchmark.\n',
        '## Current six observations\n\n|New / old|Role|Method|own U|qualified L|certificate|whole / cap seconds|\n|---|---|---|---|---|---|---|']
    for a,t in zip(arms,timings):lines.append(f"|{t['number']} / {t['old_R110_number']}|{a['id']}|{a['arm']}|{a['U']}|{a['L']}|{a['certificate']}|{t['whole']:.9f} / {t['cap_seconds']}|")
    lines+=['\n## Fixed Seed pairs\n\n|Role|Current classification|Severe P regression|Seed0 WIN to current LOSS|\n|---|---|---|---|']
    for rid,v in pairs.items():lines.append(f"|{rid}|{v['classification']}|{v['severe_regression']}|{rid in selection['Seed0_WIN_to_Seed1_LOSS']}|")
    lines += [f"\nStage reasons: {selection['reason_codes']}; blocking reasons: {selection['blocking_reasons']}. The same preregistered materiality and severity rules apply, with no ENS pointwise veto.\n",
        '## Immutable main evidence and costs\n\nR110 M-B/P and ENS/P each remain **11 WIN / 1 TIE**, with the same eleven P-WIN roles. M-B/ENS remains **5 WIN / 3 TIE / 4 LOSS**, including severe G50-C1 and G100-R2 losses. All costs and original signed tiny negative gaps remain visible. Main15/17/25/26 qualification follows their original outward full-clock intervals and signed current-call proofs; the original table blanks, raw false flags and exact clock nulls are preserved. Returned journals are present for15/26 and remain missing for17/25. This import does not redo historical raw matrix auditing.\n',
        'R110 remains **BLOCKED**. Its old arm42 still records native_end3571.0120709999464, audit_end3600.707823600038 and whole3600.7215734999627 > cap3600. Its original G100-R2 Seed1 pair remains UNEVALUABLE. New good outcomes never replace old records or retroactively change that decision; no cross-wrapper exact speedup is reported.\n',
        '## Equivalent engineering audit\n\nThe thin adapter replaces each station’s repeated column scan with one exact string/suffix index and reuses only pure parse/row Counter data within an arm. Every reuse rehashes current model bytes and binds parser/contract identity; every call separately retains Seed/settings/type, true-G/cutoff/epoch, return, cover and provenance checks. Arm cache is cleared in finally. A/B retain Counter>=1 semantics. No production source, native argv, model, search window, Python runtime, library or 30-second reserve changes.\n',
        'Eight fixed fresh-process postexit measurements were .148434, .2544211, 3.9463729, .7192857, 4.3080297, 14.3152228, 14.4745831 and 14.5150123 seconds. All mathematical and unknown fields match the old audit exactly; only two explicitly listed replay timers differ. With the measured final metric-write cost, the maximum is14.5154 seconds. This is finite fixed-machine experience, not a worst-case guarantee. The original instrumented arm42 profile is60.2785013 seconds; its nested phase measurements must not be added or used as a precise speed ratio to the historical29.6957526-second necessary audit. All failed engineering attempts are retained.\n',
        'Two actual H100 Seed1 CLIs (actual V20/M2, each cap120 seconds) passed the necessary LP/MIP/type/Start/physical/normal-return paths. A missing --qualification flag first stopped a wrapper before any native start; its three declared slots remain paid. The actual CLI wrapper wrote its fee before qualification trailer work and stamped the whole clock before writing audit metrics. The finite final correction moves those operations inside their proper clocks and covers actual retained-raw normal/failure engineering paths. Original CLI/raw/identity/fee bytes are preserved; this is explicitly a limited closure, not a byte-identical second native CLI run.\n',
        f"## Resources\n\nConservative research starts: **{cost['paid_starts']} /24**, including qualification **{cost['qualification_starts']} /8**; actual research processes{actual_starts}. Paid outer seconds: **{cost['paid_outer_seconds']:.9f} /18000**. Qualification uses the outward **583.7201481292723 /600** upper charge. CLI02 original lower receipt173.01180821377784 is retained; its582.8230838775635 upper includes real exit-observation delay and is not an exact duration or a measured trailer cost. Native child time is nested and not added again. Zero-Optimize engineering/reviewer times and failed attempts already completed at document generation are listed in resource_accounting.json with its actual cutoff; later final/public/remote receipts are separately recorded. Manual time is unknown.\n",
        '## Research scope and delivery\n\nHistorical R108 C2 supports the candidate’s distinct repair of an ENS/P benchmark gap; R108 F5 and R110 ENS regressions remain costs. R108 L48 has two real parent splits per method and at most two related active leaves; R110 has zero actual splits and at most one. G50-C1’s repeated one-bike gap is not independent Seed stability or an HGA-only result. '+r2_statement+' The contribution map and inherited uniform pseudocode state these limits, fixed objective scaling and geographic/synthetic overlap. No new algorithm contribution, statistical guarantee or completed paper benchmark is claimed.\n',
        'The final independent current-raw review and public restoration records identify their actual execution roots, source hashes, exit codes and retained historical import. Public recovery rebuilds every current CSV/JSON from the restored root; it reads no private PE/DLL/license or original worktree. Public validation and remote PR receipts are later observations with their own commits, not evidence that a commit contains its future receipts.\n',
        'Only two falsifiable future questions are recorded: whether G50-C1’s one-bike gap survives controlled separation of representation and integer-search trajectory (causal identification is missing), and whether remaining Windows/IO variability can consume the empirical reserve (finite observations give no hard bound). No follow-up solver task or mechanism is started.\n']
    (OUT/'final_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    old=(OLD_ROOT/OLD/'paper_candidate_spec.md').read_text(encoding='utf-8')
    mathematics=old[old.index('## Problem and physical meaning'):old.index('## Numerical evidence and the entry repair')]
    paper_title={'CONFIRMATION_SUPPORT':'Frozen ENS-MB research candidate',
        'CONFIRMATION_NOT_SUPPORTED':'ENS-MB candidate confirmation not supported','BLOCKED':'ENS-MB candidate confirmation blocked'}[stage]
    paper=f'# {paper_title}\n\nRound111 stage: **{stage}**. Evidence layer: `R110_MAIN_36_PLUS_R111_SEED_6`.\n\n'
    paper+='This is the unchanged R110 production candidate and equivalent engineering audit, with inherited36 main observations plus six new fixed Seed1 observations. ENS-C remains default; cold P-GRB remains primary. The old R110 BLOCKED and arm42 UNEVALUABLE are immutable. All six current arms ran once; no new independent sample or cross-wrapper exact speedup is claimed.\n\n'+mathematics
    paper+='\n## Current finite support and limits\n\n'+f"Current fixed Seed pairs: {', '.join(r+' '+v['classification'] for r,v in pairs.items())}. Stage reason codes: {selection['reason_codes']}; blockers: {selection['blocking_reasons']}.\n\n"
    paper+='Main M-B/P and ENS/P each11WIN/1TIE on the same eleven roles. M-B/ENS5WIN/3TIE/4LOSS includes severe G50-C1/G100-R2 costs. R108 C2 is the distinct historical benchmark-gap repair; F5 and other ENS costs remain disclosed. No ENS pointwise-dominance gate is introduced.\n\n'
    paper+='R108 L48 has two real parent splits per method, one INF-half retaining partition and one AM positive-score split, at most two relevant active leaves. R110 has zero real splits and at most one leaf. Lookahead/child-target models do not establish committed multileaf decomposition. G50-C1 repeatedly shows equal initial fleets,3LP+terminal MIP and the one-bike gap under the same Seed0; its prescribed pickup20-minus-one replay violates the later vehicle1 prefix at47. That finite fact identifies no general cause. R110 G100-R2 was mostly an own-UB gap. '+r2_statement+' F2 separately distinguishes a target-valued witness from completed certification.\n\n'
    paper+='Single-source geographic coordinates/capacities, synthetic inventories/targets/fleets/T, overlapping subsets, fixed lambda/max-normalized weights and few Seeds limit external validity. V100 startup/LP/MIP costs depend on role; constant lambda does not imply scale-invariant tradeoffs. The audit reduction is engineering, not a new mathematical mechanism. Numerical native-bound rejection still needs an exact in-domain current-call counterexample and removal of all dependent claims; root zero is outside a positive-G right domain. OwnU>0 with floor0 is open; missing raw events and null times remain missing/null.\n\n'
    paper+='Two remaining questions: (1) Does the G50-C1 one-bike gap survive controlled causal separation of representation and integer-search trajectory? Equal starts and calls are known; identification is missing. (2) Can a valid Windows/IO trace consume the measured reserve? Finite replay costs qualify this campaign but do not prove a worst-case bound. No further mechanism, solver run or default change is authorized by this specification.\n'
    (OUT/'paper_candidate_spec.md').write_text(paper,encoding='utf-8',newline='\n')
    print(json.dumps(dict(stage=stage,current_arms=len(arms),budget=cost)),flush=True)

if __name__=='__main__':main()
