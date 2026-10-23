"""Finite reports, nonoverlapping accounting and normally pushed delivery."""
from round131_benchmark import *
from round131_documents import table,fmt

def accounting():
    receipts=[]
    for p in sorted((OUT/'fees').glob('*/receipt.json')):
        launch=read(p.parent/'launch.json');r=read(p)
        receipts.append(dict(label=p.parent.name,kind=launch['kind'],command=launch['command'],**r))
    # Group management is already inside each full child interval; 720 is a
    # planning reference and is not added again. The final small allowance is
    # explicit, bounded, and is not described as exact measured CPU time.
    measured=sum(r['outer_seconds'] for r in receipts)
    value=dict(total_outer_limit=TOTAL_LIMIT,closed_child_outer_seconds=measured,
        preledger_setup_allowance_seconds=900,final_small_metadata_allowance_seconds=120,
        charged_upper_seconds=measured+1020,remaining_upper_seconds=TOTAL_LIMIT-measured-1020,
        by_kind={k:sum(r['outer_seconds'] for r in receipts if r['kind']==k) for k in sorted({r['kind'] for r in receipts})},
        receipts=receipts,qualification_limit=QUAL_LIMIT,production_compilations=0,
        formal_nominal_seconds=33360,management_reference_seconds=720,management_reference_added_again=False,
        nested_H_LP_MIP_Work_added=False,allowances_are_not_exact_CPU_measurements=True,
        concurrent_author_preparation_not_added_to_formal_outer_intervals=True,
        future_recovery_or_metadata_not_claimed_measured=True)
    assert value['charged_upper_seconds']<=TOTAL_LIMIT
    assert value['by_kind'].get('qualification',0)<=QUAL_LIMIT
    write(OUT/'resource_accounting.json',value)
    return value

def report():
    s=read(OUT/'stratified_summary.json');a=read(OUT/'scientific_assessment.json')
    review=read(OUT/'review/final_independent_evidence.json');pdf=read(OUT/'review/pdf_visual_review.json')
    assert review['status']=='PASS' and pdf['status']=='PASS' and pdf['PDF_SHA']==sha(OUT/'manuscript.pdf')
    o=read(OUT/'observations.json');fees=accounting()
    clocks=table(['Layer / input','Seed / repeat','Method','Certificate','T_cert','T_produce','T_verify','T_total','U','L','signed U-L'],
        [[x['layer']+' / '+x['id'],f"{x['seed']} / {x['repeat']}",x['method'],x['certificate'],fmt(x['T_cert']),fmt(x['T_produce']),fmt(x['T_verify']),fmt(x['T_total']),f"{x['U']:.12g}",f"{x['L']:.12g}",f"{x['signed_gap']:.12g}"] for x in o['arms']])
    body=f'''# Round131 final report

Execution **{s['execution']}**. Stage exit **`{s['stage_exit']}`**. Scientific assessment **`{a['scientific_assessment']}`**.

{a['synopsis']}

The fixed final-S2 version now has a directly citable complete SC main benchmark, a separate absolute tiny-overhead table, and finite V35 scope evidence. S2 adoption was settled before this round. There is no algorithm change, production compilation, new input, tuning, extra Seed, longer window or per-instance candidate selection. All observed losses, normal open returns, zero certificates and absent backend exposure are retained. The complete direction-by-direction answers and limitations are in benchmark_assessment.md.

## Exact task and evidence

The task starts at R130 head `{BASE}`, with frozen production source `{SOURCE}`. PR192 was actually checked open, Draft and unmerged; its recorded head and the remote ref matched. A sparse linked worktree reuses the original shared Git objects. New task files stay below E:/codes/ExactEBRP-work. The main checkout's three preexisting tracked dirty files have a directed hash baseline; this is not an all-files byte-integrity claim.

The same E3 PE `{PE_SHA}` and original Gurobi 13.0.2 DLL `{DLL_SHA}` serve all 52 formal positions. Complete S2 argv follows R130; P uses the original cold compact. Both independently pay admission, own startup H where applicable, modeling, all LP/MIP and Start checks, online validation and required output under the original deadline policy. Threads/MIPThreads=1, affinity=4, H_seed=20260626, lambda=.15, pickup/drop60, PresolveAuto, MIPFocus0, Cuts-1, strict requested gaps and original tolerances are unchanged. The complete caps remain 600/1200/90/2400 by frozen role; reserve30, native offset6 and hard-stop offset2 remain, including tiny runs. No WorkLimit is substituted.

The input_manifest and exact per-group identity/argv freeze bind all original byte hashes, Q vectors, physical T and scenario/geography. Scenario is service-station total inventory, excluding depot. No generator, new station source or fresh difficulty screen is used. Ten inputs are known. A has six inputs/twelve comparisons, B two/twelve and C two/two. This is not 26 new problems, and the layers are never pooled as a success rate or unconditional geometric mean.

Incremental qualification reuses the original verified R130 P/S2 bridge, MS2 deletion evidence and source/return/cover/Start/numerical contracts. It verifies the actual E3/DLL/exporter bytes and source seal, constructs ten no-Optimize cold structural references and exercises the corrected same-vehicle classifier. The initial synthetic row used pickup rather than binary service variables, so its assertion failed; an ensuing prepare call found the missing qualification prerequisite. A separate FunctionType default-argument omission also failed before any arm. All failures, scripts and costs are retained, repaired before formal execution, with zero Optimize. The unchanged valid E3 is never rebuilt. Git byte-preservation metadata was then added; committed frozen files were checked against local byte hashes without modifying a producer or source seal.

A separate internal executor checked all 10 inputs, all 52 complete commands, all 26 exact groups/orders/repeats, three-layer denominators, 217 source bindings, 84 adapter hashes, time policy, live original assets and the actual Seed2 inheritance chain before admission. A disclosed preflight receipt metadata correction preserves its prior version: the dynamic Seed2 test imported reader modules but never read formal raw. ACCEPT and the execution binding stayed unchanged.

After all formal arms, that executor independently recomputed all 26 comparisons and nulls, three layer statistics, all tiny Seed/repeat records, and the qualified endpoint evidence within the exact scope recorded in review/final_independent_review.md. It replays all final fleets with the established physical reader and independently samples a nonempty fleet, a complete optimal chain and a real pair-only model where available. This is another internal executor, not author self-review, external replication, or a global rational proof. The raw signed gaps and old top-level flags stay unchanged; actual returned-call qualifications and endpoints are separate. Cross-arm same-input witnesses can reveal contradictions, never transfer a UB or certificate to another method.

mechanism_costs.csv and native_call_index/model_index/physical_evidence_index retain actual H, LP/MIP time/Work/nodes, split/target exposure, Starts, corrected pair-cover/conditional and ordered-supply counts, and all submitted model domains. Missing diagnostics stay unknown. Triple support must be zero in every observed S2 model. Semantic improving-domain proof closures are tied to their analytic premise/domain/cutoff and are not read as physical-domain infeasibility.

## Manuscript and historical migration

One maintained full manuscript and complete PDF add the A/B/C experiments, final-version identity and scope limits while preserving the R125 formulas, cuts, H and controller appendices byte-for-byte from R130. The existing export pipeline is reused. The actual affected PDF pages and cross-references were inspected; review/pdf_visual_review.json binds the inspected bytes. Scientific result status and PDF export status remain separate.

evidence_registry.csv registers every current run and the finite cited historical tables with their original source authority, byte hashes, method/build, numerical/clock policy, Seed/repeat, cap and role. Actual current run identity includes the producer receipt. Historical receipt/destination identities are used where recorded, with exact endpoint-record hashes explicitly labelled where process identity is unavailable. The registry never chooses a cross-round best time or promotes a repeated input to a new input. Old R126/R127 SC/tiny full-M-B records remain predecessor measurements. R129 stays prospective at selection time and known thereafter, with protection separate. R130 PS/S2R mixed/reverse/open attribution, R127 tuned-P holdout negative evidence and R128/R129 reversals remain visible. Old V50/V60 MB/ENS observations do not validate final S2 at those sizes.

{a['decision']}

## Delivery, budget and stop

The English stacked Draft PR targets `codex/round130-ms2-paper-attribution`. No merge or force push is authorized. Current-only lossless carriers and exact small dependencies exclude PE/DLL, credentials, licenses, fonts and external full texts. A single anonymous public empty-root recovery is pinned to the scientific commit after publication; its actual outcome and guarded owned cleanup are added as separate metadata without recursively repacking receipts or repeating science.

The currently closed outer charge plus explicit setup/final-small-metadata allowances is {fees['charged_upper_seconds']:.6f}/{TOTAL_LIMIT} seconds. Final resource_accounting.json is authoritative after remaining delivery children close. Each full group child pays its own production/verification/reconciliation; nested H/LP/MIP is not added again. The 720-second management figure is a planning reference, already included in group outer intervals rather than double-counted. The 900/120-second allowances are conservative and are not represented as exact CPU measurements. No unobserved early finish savings were pre-spent on extra experiments.

Execution completion does not require a favorable scientific result. Normal timeouts, losses, no split and no speed benefit are final outcomes. The study ends after final-version evidence review; no new selection loop follows.

## Every formal arm

{clocks}
'''
    (OUT/'final_report.md').write_text(body,encoding='utf-8')
    (OUT/'review_actions.md').write_text('''# Round131 review actions

| Obligation | Actual evidence |
| --- | --- |
| Parent, original asset, input and full command admission | remote_preflight.json; E3_binding.json; input_manifest.json; argv_freeze.json; review/performance_admission.json |
| Retained failed no-Optimize preparation | closed qualification/prepare fees; review/preformal_adapter_failures/ |
| All fixed outcomes and nulls | arms.csv; pairs.csv; stratified_summary.json; tiny_summary.json |
| Physical/source-return-cover, real rows/calls and numerical limits | physical_evidence_index.csv; native_call_index.csv; model_index.csv; numeric_policy_impacts.json; cross_arm_bound_consistency.json |
| Separate executor final arithmetic and evidence review | review/final_independent_evidence.json; review/final_independent_review.md |
| Version migration without relabelling old results | evidence_registry.csv; paper_version_manifest.json; benchmark_assessment.md |
| Complete paper and actual PDF inspection | manuscript_lineage.json; pdf_export.json; review/pdf_visual_review.json |
| Actual payload scan and one public recovery | raw_archive_manifest.json; export_manifest.json; review/publication_scan.json; public_restore_receipt.json when present |
| Safe owned cleanup, protected dirty baseline and exact accounting | cleanup_receipt.json and resource_accounting.json at closeout |

The scientific conclusion and execution status are separate. No outcome triggers a rerun, switch, tuning or additional experiment. Only an actual proof/identity contradiction takes priority and requires a scoped decision.
''',encoding='utf-8')
    (OUT/'PR_BODY.md').write_text(f'''The main SC and tiny tables in R126/R127 measured the full three-station M-B predecessor. This PR closes the final-version evidence gap with the already-adopted frozen S2/MS2 and original cold P, without changing the algorithm or selecting a faster variant per input. It is stacked on `codex/round130-ms2-paper-attribution` at `{BASE}`.

Execution: **{s['execution']}** / `{s['stage_exit']}`. Scientific assessment: **`{a['scientific_assessment']}`**.

{a['synopsis']}

- **A, main benchmark:** all six known SC inputs, both Seeds, 24 independently paid arms and 12 strict certification comparisons, including SC-C20-S and every unfavorable/open outcome.
- **B, tiny overhead:** both known V8/V10 roles, three Seeds and two opposite-order repeats per Seed, 24 arms; complete directions, medians/ranges, >=10-second delays and P-only risks are separate from A.
- **C, scope boundary:** both original V35 roles, Seed0, four arms under their original 2400-second complete caps. Both-open results have unknown final certification-time ordering. No final-S2 V50/V60 claim is made.
- The exact original E3/DLL, full argv, inputs, physical/source-return-cover and numerical policies are bound. No new input, tuning, production build, algorithm change, extra Seed or normal-result retry. All 26 comparisons are independently recomputed by a separate internal executor; actual fleets, a certificate chain and a pair-only model are reviewed within the stated finite scope.
- The full manuscript/PDF uses S2 as the sole method, preserves R125 formulas/H/controller and accurate predecessor identities, and retains R129 selection/protection, R130 scoped/mixed attribution, tuned-P negatives and earlier reverse/open findings. Affected PDF pages are actually inspected. No pooled cross-layer Win rate or unconditional speedup is supplied.

Review entry points: `benchmark_assessment.md`, `arms.csv`, `pairs.csv`, `stratified_summary.json`, `tiny_summary.json`, `evidence_registry.csv`, `review/final_independent_review.md` and `manuscript.pdf` under `results/unified_exact_round131/`. The public recovery and guarded owned cleanup outcomes are appended only after their actual receipts. This is a Draft research PR; no merge or force push.
''',encoding='utf-8')
    (OUT/'RESUME.md').write_text('Round131 science and independent/PDF review completed. No further experiment authorized. Scientific publication, one public empty-root recovery and guarded owned cleanup remain until actual receipts record completion.\n',encoding='utf-8')
    print(json.dumps(dict(report=True,stage_exit=s['stage_exit'],budget=fees['charged_upper_seconds'])))

if __name__=='__main__':{'report':report,'accounting':accounting}[sys.argv[1]]()
