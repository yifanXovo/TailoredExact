"""Finite English handoff documents and actual, explicitly bounded accounting."""
from round126_common import *
import csv

def report():
    s=read(OUT/'certification_summary.json');pairs=[];arms=[]
    for n in range(1,7):
        c=read(OUT/f'reconstruction/group{n:02d}/current_core.json');pairs.append(c['pair']);arms.extend(c['arms'])
    b=budget();assert b['paid_outer_seconds_upper']<=TOTAL_LIMIT
    measured=b['paid_outer_seconds_upper']-b['preledger_setup_charge_upper_seconds']
    formal=sum(read(OUT/f'fees/formal{n:02d}/receipt.json')['outer_seconds_upper'] for n in range(1,7))
    formal_processes=sum((Path(l['destination'])/'child_process_origin.json').is_file()
        for n in range(1,7) for l in read(OUT/f'campaign/group{n:02d}/identity.json')['launches'])
    actual_calls=sum(a['native_Optimize'] for a in arms) if all(a.get('native_Optimize') is not None for a in arms) else None
    accounting=dict(b,measured_closed_task_wall_seconds=measured,formal_six_group_outer_wall_seconds=formal,
        formal_nominal_production_seconds=10800,maximum_outer_seconds=18000,
        actual_formal_native_processes=formal_processes,zero_Optimize_reference_processes=2,actual_new_qualification_solver_CLI=0,
        formal_Optimize_calls=actual_calls,
        actual_total_is_not_nominal_cap_sum=True,inner_Runtime_H_LP_MIP_not_added_twice=True,
        unmetered_allowance_is_conservative_not_measured_CPU=True,
        allowance_scope='Brief shell/Git/setup/status/source-authoring and final-receipt bookkeeping commands; no unmetered native optimization. Not elapsed conversation time.',
        process_wall_including_network_is_not_called_CPU=True,human_reasoning_and_waiting_not_synthetic_machine_CPU=True)
    write(OUT/'resource_accounting.json',accounting)
    expected={r['path']:r['sha256'] for r in read(ROOT/'results/unified_exact_round125/evidence/production_bindings.json')['bindings']}
    assert expected==bindings() and len(expected)==216 and sha(PE)==PE_SHA and sha(DLL)==DLL_SHA
    init=read(OUT/'initialization.json');dirty={n:sha(MAIN/n) for n in init['main_dirty_SHA']};assert dirty==init['main_dirty_SHA']
    write(OUT/'review/frozen_source_and_user_protection.json',dict(R125_binding_ledger_SHA=sha(ROOT/'results/unified_exact_round125/evidence/production_bindings.json'),
        production_bindings_compared=216,all_production_bindings_equal=True,PE_SHA=sha(PE),DLL_SHA=sha(DLL),main_dirty_SHA=dirty,
        no_production_compilation=True,no_default_or_algorithm_change=True))
    tables=[]
    for p in (ROOT/'results/unified_exact_round125/tables').iterdir():
        if p.is_file():
            assert sha(p)==sha(OUT/'tables'/p.name)
            tables.append(dict(file=p.name,SHA256=sha(p),bytes=p.stat().st_size))
    assert len(tables)==6
    write(OUT/'review/unchanged_historical_tables.json',dict(files=tables,byte_identical=True,new_displays_one_way_only=True))
    pdfqa=OUT/'review/pdf_visual_review.json'
    doc='READY' if (OUT/'manuscript.pdf').is_file() and pdfqa.exists() and read(pdfqa).get('status')=='PASS' else 'CONTENT_GAP' if not (OUT/'manuscript.md').is_file() else 'PDF_EXPORT_BLOCKED'
    public=OUT/'review/public_restore_A.json';public_done=public.exists() and read(public).get('status')=='PASS'
    science_commit=read(public)['commit'] if public_done else 'not yet published; the actual B receipt will identify content commit A'
    both=s['both_certified_subset'];pm=s['per_method'];cat=s['categories']
    slower=[dict(id=p['id'],speedup=p['speedup'],materiality=p['time_description']) for p in pairs if p['speedup'] is not None and p['speedup']<1]
    rows=[]
    def claim(id,kind,text,evidence,limit):rows.append(dict(claim=id,kind=kind,statement=text,evidence=evidence,limit=limit))
    claim('single_method','design','M-B is the sole proposed method on all six fixed inputs.','paper_method_config.json; protocol.json; argv_freeze.json','ENS-C remains historical/default; no per-instance selection or new algorithm.')
    claim('ideal_validity','mathematical','Representation, valid strengthening, objective-preserving embedding and complete coverage hold under the stated physical/scope premises.','manuscript Sections4-5; model_appendix A.1-A.8; algorithm_appendix B.1-B.11; unchanged 216 bindings','Exact-arithmetic statements do not establish a runtime theorem or rational certification of native floating-point operations.')
    claim('numerical_admission','numerical', 'Complete own physical evidence and lifecycle/source/cover gates plus signed 1e-7 policy are required.','arms.csv; evidence/arm_index.json; raw carriers; AppendixB.4.1','Native one-sided predicate or an LP optimum alone is insufficient; raw L is never clipped.')
    claim('direct_panel','empirical',json.dumps(dict(categories=cat,per_method=pm,decision=s['scientific_judgment'])),'certification_pairs.csv; certification_summary.json; six source-bound raw/reconstruction carriers','Six non-IID constructed problems from two station sources; fixed budgets and no population/universal dominance claim.')
    claim('conditional_time','empirical',json.dumps(both),'certification_pairs.csv; all twelve original producer/verification receipts','Both-certified intersection only; no cap substitution, PAR-2, best-of-Seed or time claim for open arms.')
    claim('positive_objective','mathematical/data','Four shortage problems have an independently positive objective floor under the exact-decimal coefficient interpretation.','shortage_positive_objective.json; inputs/*_parsed.json','No new LP/route solve; no floor injected into models or backfilled into L; empty fleets remain legal.')
    claim('history','historical','R122 keeps six new Seed0 problems, two fixed repeats,32 arms/48 directed endpoint comparisons; R123 is one known V50 long-window role.','six byte-identical historical tables; historical_attribution.md','Old6 WIN does not mean six faster certifications; open endpoints and unknowns are not pooled certification times.')
    claim('attribution','scope','The new comparison concerns complete own M-B versus cold P without H.','protocol; actual native launches and saved return chains','It does not identify causal contributions of cuts, AM or H, and adds no P-S ablation.')
    with (OUT/'claim_evidence_map.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
    priority='Submit this accurately limited complete draft to the user for substantive academic review; no additional solving is recommended within this round.' if s['w']>0 and s['scientific_judgment'] not in ['PROOF_RELIABILITY_PRIORITY','INCOMPLETE_CERTIFICATION_EVIDENCE'] else 'One minimal, unexecuted follow-up question: what exact unresolved source/coverage obligation on the first recorded nonzero uncertified role prevents the core certification claim? Define that question before authorizing any further work.'
    (OUT/'research_decision.md').write_text(f"# Round126 research decision\n\nScientific judgment: **{s['scientific_judgment']}**. Supporting nonzero problems: {', '.join(s['supporting_nonzero_problems']) or 'none'}. Material opposite cases: {', '.join(s['adverse_problems']) or 'none'}.\n\n{priority}\n\nThis is one next priority, not an automatic Round127, extension, Seed, extra sample, variant or fusion. M-B remains the sole paper method regardless of the result.\n",encoding='utf-8')
    (OUT/'reproducibility.md').write_text(f'''# Round126 reproduction and evidence scope

The maintained reading sources are [manuscript.md](manuscript.md), [Appendix A](model_appendix.md), [Appendix B](algorithm_appendix.md) and [references.bib](references.bib). [The PDF](manuscript.pdf) combines these with complete historical-result displays. TeX/combined Markdown/PNGs are generated intermediates, not competing maintained manuscripts.

The source base is open Draft PR187 at `{BASE}`. Production source is `{SOURCE}`; all 216 R125 file bindings remain equal. PE SHA256 is `{PE_SHA}` and DLL SHA256 is `{DLL_SHA}`. They are used in place and never redistributed. [paper_method_config.json](paper_method_config.json) and [argv_freeze.json](argv_freeze.json) contain the single M-B entry and exact twelve positions. Their working directory is `E:/codes/ExactEBRP-work/worktrees/round126` (or an exact reconstructed equivalent containing the recorded relative inputs). Native argument vectors are invoked by the inherited complete-clock supervisor, not timed by Gurobi Runtime alone. Native/default values without separate flags are fixed by the explicit configuration and PE identity. ENS-C's library default is unchanged and is not a second proposed method.

[source_recipe.json](source_recipe.json) was committed before six once-only draws; [input_manifest.json](input_manifest.json) binds each input, complete parameters and selection/inventory mapping. Four shortage positivity arguments are explanatory only. No H/LP/MIP difficulty preview, redraw, source switch or new projection occurred. [Station overlap](station_overlap.csv) covers new pairs and the explicitly available small historical manifests; no full-history carrier was restored for de-duplication.

Every formal method builds and pays its own complete work. P receives no H, Start, route, bound or other arm's certificate. Own outputs remain sealed. [arms.csv](arms.csv), [certification_pairs.csv](certification_pairs.csv) and [certification_summary.json](certification_summary.json) are direct authorities; [the arm/source index](evidence/arm_index.json) locates full own fleets, native model/interval/cutoff/parameter/return chains, Start and coverage evidence. [Raw carriers](raw_archive_manifest.json) retain actual bytes and checksums. First failures and source-equivalent repairs remain recorded; existing saved V20 qualification is not a new performance sample.

Pure reconstruction uses `scripts/round126_public_restore.py` with one science-A commit, one new E-root destination and an outside receipt. Content commit A: `{science_commit}`. Use that exact A commit for the finite export manifest; the later B head adds actual receipts and updated bookkeeping and is not recursively bound by A. It fetches only the finite manifest, materializes exact frozen hashes (declared LF/CRLF conversion only), extracts/checks the carriers, regenerates the same six inputs through the original rule chain and recomputes six pure paired outcomes with all twelve sealed clocks/endpoints. Tuple/JSON coordinate arrays represent the same ordered data. It does not start native optimization, run H or restore R122's whole campaign. The optional complete document compilation compares actual extracted PDF text; PDF creation timestamps are not scientific differences. Current public recovery status: {'PASS; see review/public_restore_A.json' if public_done else 'pending actual science-A publication/recovery; no future receipt is claimed'}.

The six historical table files are byte-identical to R125. New `tables/historical_display.md` is one-way display only; full-precision old CSV/Markdown bytes remain. R125's rational/sample-row/controller/H-move checks are inherited, not rerun as a new all-matrix qualification. Native matrices remain floating point and the 1e-7 evidence policy is not a rational exact proof or accumulated-error theorem. Independent review records identify the actually replayed fleets, sources, classifications, PDF pages, repairs and remaining scope.

[resource_accounting.json](resource_accounting.json) separates measured closed-task process wall, formal group costs and a 120-second conservative unmetered setup/bookkeeping allowance. That allowance is not measured CPU. Nested native/LP/MIP/H Runtime is not charged again; network wall and human reading are not presented as numerical CPU. Outer charged upper total at this receipt is {b['paid_outer_seconds_upper']:.6f}s of 18000s; formal nominal production caps sum to 10800s. [RESUME.md](RESUME.md) records process/seal recovery policy. No formal performance retry, extra Seed, extra window or automatic follow-up is authorized.
''',encoding='utf-8')
    text=f'''# Round126 final assessment

Experiment execution: **{s['experiment_execution']}**. Manuscript package: **{doc}**. Scientific judgment: **{s['scientific_judgment']}**.

This scope replaces the earlier Round126 zero-new-solves/document-only request. The six fixed new V15/V20 problems received exactly 12 own cold-P/M-B arms, Seed0, per-method caps 600/1200s, with the frozen production executable/DLL. There was no default change, candidate development, data-dependent dispatch, time extension, redraw or new Seed.

The fixed denominator remains six problems, with five categories: {json.dumps(cat,sort_keys=True)}. M-B certifies {pm['M-B']['certified']}/6 ({pm['M-B']['nonzero_certified']} nonzero, {pm['M-B']['zero_certified']} zero, {pm['M-B']['startup_zero']} startup-zero); P certifies {pm['P-GRB']['certified']}/6 ({pm['P-GRB']['nonzero_certified']} nonzero, {pm['P-GRB']['zero_certified']} zero). The main categories are recorded independently of supplementary U/L/gap improvements. One problem certified by both is still one problem. Certified physical numerical values are in the summary and arm table.

Supporting nonzero roles (w={s['w']}): {', '.join(s['supporting_nonzero_problems']) or 'none'}. Material opposite roles (l={s['l']}): {', '.join(s['adverse_problems']) or 'none'}. All actual P-faster ratios, including below-materiality cases, are retained: {json.dumps(slower)}. Both-certified intersection: {', '.join(both['ids']) or 'empty'}, n={both['n']}, median P/M-B={both['speedup_median']}, geometric mean={both['speedup_geometric_mean']}. This is conditional on both certification, not an entire-panel mean; open times are null, not cap-filled. T_total remains an explicit secondary view. On the both-open SC-C20-S, M-B production ends 2.524297 seconds earlier but its total including verification is 1.126600 seconds longer; neither ordering yields a certification-time inference.

All three clocks include the original reserve and complete-work policy. Measured closed-task wall is {measured:.6f}s; the separately labelled conservative setup/bookkeeping allowance is 120s; charged upper total is {b['paid_outer_seconds_upper']:.6f}s, below 18000s. Formal six-group outer wall is {formal:.6f}s; the 10800s formal figure is a nominal cap sum, not an actual bill. Actual formal native processes: {formal_processes}; read-only reference exporter processes: 2 with Optimize 0; new qualification solver CLI: 0. Actual formal Optimize calls: {accounting['formal_Optimize_calls']}. Every failed metered attempt remains charged.

The full English reading manuscript preserves the R125 model, all enabled strengthening derivations, complete H/controller algorithms, numerical boundaries, references and two appendices. The new direct certification section is separate from the unchanged R122 32-arm/48-pair and known R123 V50 endpoint layer. Mathematical validity is not a runtime theorem; this comparison is complete M-B versus cold P, not separate component causality or universal dominance. The four shortage positive-objective cases and any zero subset remain visible.

Actual review, repair rereading and its limits are recorded in [review_actions.md](review_actions.md). The saved-reader first attempt failed only a four-file LF/CRLF identity comparison; exact text equivalence was established and the first attempt/fees kept. An intermediate commentary misread observational audit top-level fields as final; the final endpoint/return/source reconstruction was promptly checked and the communication corrected. No scientific output was altered to create a certificate.

Public science-A empty-root recovery: {'PASS' if public_done else 'pending; B will contain the actual receipt, not a prediction'}. Scope: current necessary R126 carriers and dependencies, exact input regeneration, all sealed clocks/endpoints and six pair arithmetic, plus conditional manuscript compile/affected-page reread; no native re-solving or full historical campaign restoration. Later verification/cleanup receipts do not recursively prove future receipts.

The single next priority is: {priority}
'''
    (OUT/'final_report.md').write_text(text,encoding='utf-8')
    print(json.dumps(dict(experiment=s['experiment_execution'],manuscript=doc,judgment=s['scientific_judgment'],budget=b)))

if __name__=='__main__':report()
