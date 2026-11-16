"""Finite reporting from qualified data and the explicitly authored research decision."""
from round169_common import *
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),*['| '+' | '.join(map(str,r))+' |' for r in rows]])+'\n'
def f(x):return format(x,'.9g')
def main():
    arms=read(OUT/'complete_arms.json')['rows'];h=read(OUT/'h_results.json');cost=read(OUT/'cost_report.json');dec=read(OUT/'decision.json')
    pairs=read(OUT/'complete_comparisons.json')['rows'];pool=read(OUT/'h_pool_costs.json')['rows'];provenance=read(OUT/'weight_provenance.json')
    roles=read(OUT/'h_panel_frozen.json')['roles'];by={(a['role'],a['arm']):a for a in arms}
    htable=table(['Input','B = M','C','Delta restart','Delta weight','C source'],
        [[r['role'],f(r['B']),f(r['C']),f(r['Delta_restart']),f(r['Delta_weight']),r['selected_C']] for r in h['rows']])
    paid=table(['Input','B: U / L','M: U / L','C: U / L'],
        [[p['role'],*[f"{f(p[k]['U'])} / {f(p[k]['L'])}" for k in ['B','M','C']]] for p in pairs])
    fees=table(['Input','B path s','M pool s','C pool s'],[[p['role'],f(p['B_path_seconds']),f(p['M_pool_path_seconds']),f(p['C_pool_path_seconds'])] for p in pool])
    complete=table(['Input / arm','Initial U','True U','Qualified L','Rel. gap','State','Process s'],
        [[a['role']+'/'+a['arm'],f(a['initial_U']),f(a['U']),f(a['L']),f(max(0,a['relative_gap'])),'CERT' if a['certificate'] else 'OPEN',f(a['process_outer_seconds'])] for a in arms])
    effort=table(['Input / arm','H s','Build s','LP / MIP','Native s','Work','Nodes'],
        [[a['role']+'/'+a['arm'],f(a['H_seconds']),f(a['all_model_build_seconds']),f"{a['LP']} / {a['MIP']}",f(a['Native_seconds']),f(a['Work']),f(a['nodes'])] for a in arms])
    report=f"""# Round169 paid objective-diversified initialization

{dec['headline']}

{dec['rationale']}

Uniform GI-TBC/B remains default. C166, D167 and C169 remain default off.
This is one frozen known-input, Native Seed 0 short-cap study. It adds no P
run or strict P comparison and makes no population, robustness or OR-theory claim.

## H mechanism and matched restart control

All 35 complete C++ H paths finish and pass original physical verification.
The 1200s screen uses {h['shared_outer_seconds']:.6f}s enclosing time and zero
Optimize. Four of six current roles cross the unchanged E4 threshold. The
seventh R137 motivation role cannot trigger the complete panel. M's selected
F equals B's on all seven inputs under these fixed seeds; this does not reject
multistart generally. Each complete H preserves R73 construction, 24 random
orders plus the constructed 25th order, interroute decoded descent and R83 closure.

{htable}

Delta_restart=F_B-F_M and Delta_weight=F_M-F_C are separate. Each path returns
its terminal search-objective-best fleet; only that fleet is rechecked at the
original lambda. Full per-path G/P/F, seed/search/evaluation weights, checks,
closure counters, raw fleets and initial-order identities are in
`h_path_results.json/.csv` and the new raw carrier.

The following sums share the new diagnostic base once. They describe pool
path expenses, not three independently measured arm wall times. Check counts
and CPU costs differ across weights despite the equal finite call counts.

{fees}

`fleet_changes.json` compares selected M/C to the same new base under all
capacity-compatible vehicle relabelings. C20 changes service (adds15/removes20),
one owner and order/quantities. C35 changes24 owners, order and19 quantities;
B35 changes7 owners, order and24 quantities. X35 adds12/20/29 and changes10
owners. There are no sign flips in these selected C fleets. R137 changes its
service set, order and quantities without an owner change. These are descriptive
fleet differences, not independent causal claims. R168's old final-parent
family certificates are never applied to these new base-H parents.

## All eighteen paid positions

Every position starts from the original input and pays for its own H. There
are {cost['complete_H_calls']} complete-panel H calls. All positions finish
normally under the common {300}/{600}s process caps (shutdown margin6s,
time-limit cap-6, Threads=1, Native Seed 0). Original mathematical T remains
5400/7200/10800 as frozen. All LP/MIP and C++ checks share the original
process clock. The selected original-objective fleet maps to the actual
original-model Start. The independent pure reader verifies every model,
Start, journal commit/return, numerical source and complete interval cover.

{paid}

{complete}

The raw signed gaps, including harmless last-bit negatives at certified
numeric endpoints, remain in `complete_arms.json/.csv`; display gaps above
are nonnegative. OPEN process times are budget endpoints, not certificate
times. The compact comparison separates true U and qualified L and assigns
no composite win score. Old 1200/2400s B/P observations are not paired with
these new shorter runs. The nine n20 observations all certify; C20's C
initialization gain coexists with a longer observed certification process
than B/M. The final research decision accounts for that counterexample.

## Actual expenses and qualification

{effort}

Exactly {cost['actual_Optimize']} C++ Optimize calls occur in the complete
panel: {cost['LP']} LP and {cost['MIP']} MIP, consuming
{cost['Native_seconds']:.6f}s Native Runtime and {cost['Native_Work']:.9g} Work.
The eighteen process outer times sum to {cost['complete_process_outer_seconds']:.6f}s,
below the 8100s nominal cap sum. H, Native, model-building and in-process
checks are nested expenses, not added to that enclosing total. C++ reports
{cost['all_model_build_seconds']:.6f}s total model build; the residual after
Native and H includes all other construction, transformations, verification,
logging, serialization and process overhead. It is not mislabeled as a pure
verifier timer. Post-return independent audit and adapter development are
separately charged in `cost_report.json` and `review/*cost*.json`.

The only bad solver-process invocation was a pre-H CLI spelling error,
preserved and corrected before the screen. Reader development errors cause
no optimizer rerun. `engineering_notes.md` resolves the LF semantic/raw-byte
hash distinction and the diagnostic-only completeness label. The default-off
wrapper and base primitive produce the same representative fleet/G/P/F.
Matched M/C seeds have identical 24 initial random orders. Exception and early
return cleanup restores greedy lambda/scaling. Existing tiny fixtures cover
lambda0, zero penalty, qualified zero, empty routes and loaded return; an
independent Fraction/physical implementation checks all 35 new H fleets.

## Recovered motivation and prior art

The verified old H originals at rho approximately 0.5/1/2 have original-target
F values {', '.join(f(r['H_original_reverified']['objective']) for r in provenance['rows'])}.
The old final rho2 fleet evaluates to0.3365058164688021, better than the
old original final0.40327199886285475 and substantially better than these H
outputs. Its first matching committed witness is event123 in terminal call5.
The validated NEJ1 sidecar records its producer publication/close marker at
2311.5796264s; the external observer first sees it at2311.735s. This recorded
witness availability differs from the unrecorded internal solver discovery
instant. The Native log reports a rounded local2298s; the first outer-store
acceptance is2370.0371459s after return. The producer endpoint is not used
as a first-hit. Exact archive/member/hash
bindings are in `weight_provenance.json`; no old fleet enters any new Start.

Paquete and Stutzle(2003), author manuscript section 2/Algorithm 1 and
sections 4.1-4.2, already combine changing aggregations, chained local search
and a Pareto archive. This study uses independent extra H paths for one fixed
original F and does not rename that chain or claim scalarization/transfer as
new OR theory. The R73/R88/R96/R97, decomposition and bounded-neighborhood
differences are retained in `research_design.md` and the literature memo.

## Manuscript, CSV and delivery

The six-section R137 manuscript keeps the established B/P and adverse evidence.
The finite paid table and interpretation join its existing conclusion, with
full H/fee/arm tables in Supplement S169. The R168 UNKNOWN wording distinguishes
a valid model's rejected numerical lower from a model/API/mapping failure;
no experiment, raw bound, acceptance margin or historical verdict changes.
The three actual independent agent reviews are recorded separately from
human peer review. Current PDFs and source/build/targeted visual QA belong
to the R169 exporter; old figures are not regenerated.

Six qualified B controls are delivered in the original 28-column UTF8-BOM
increment. M/C remain in their separate complete-arm table. New P pairs=0.
The specified 112-row/64951-byte master is absent in the bounded attachment
lookup, so its original bytes cannot be appended or delivered. Actual master
rows added=0; no 118-row master is fabricated. Protected 91/103-row files stay
unchanged. `CSV_reconciliation.json` and `CSV_QA.json` bind the real increment.

One new-only raw/runtime archive and exact member map support the English
Open Draft stacked on R168. Normal science and later receipt commits,
actual head/base/Open/Draft readback, anonymous new-only byte recovery and
zero-delete closeout are separate receipts. There is no merge or Round170.
"""
    (OUT/'final_report.md').write_text(report,encoding='utf-8')
    decision=f"# Research decision\n\n**{dec['decision']}**\n\n{dec['headline']}\n\n{dec['rationale']}\n\nKeep uniform B default and C166/D167/C169 off. The fixed known-role/Seed0 evidence does not establish statistical robustness, a new P-GRB advantage rate, or a general OR method contribution. No extra weight, Seed, cap, mechanism or Round170 is started.\n"
    (OUT/'research_decision.md').write_text(decision,encoding='utf-8')
    (OUT/'author_decision_memo.md').write_text('# Round169 change to the author decision\n\n'+dec['rationale']+'\n\nThe paper remains an integrated GI-TBC/B study. EJOR/TRE assessment can proceed on the established joint-state exact method and certified resource/weight decision intervals. Objective diversification supplies a practical, finite initialization result; it does not fill the remaining broader OR mechanism/theory gap. Keep publication assessment separate from any future independently authorized algorithm confirmation.\n',encoding='utf-8')
    paper=ROOT/'results/unified_exact_round137';body=(paper/'paper_body.md').read_text(encoding='utf-8-sig');supp=(paper/'supplement.md').read_text(encoding='utf-8-sig')
    assert '**Table 11. Paid' not in body and '## S169' not in supp
    paragraph='\n\nObjective diversification has direct local-search precedents [@paquete2003two]. A default-off test retains complete own-H and adds independent half/double-weight H, against two original-weight restarts. All 35 H paths finish; four of six current roles pass the frozen gate. Table 11 gives fully paid same-build outcomes on the six exposed roles at Native Seed 0, with 300/600s caps. C improves U on all n35 roles beyond both controls, raising B35 L slightly and weakening C35/X35 L. All n35 runs remain OPEN. All n20 roles certify; C20-C takes 219.5s versus 211.5/211.1s for B/M. M also improves paid X35 despite an unchanged H Start. Recommend only future independent limited confirmation. B stays main and C166/D167/C169 stay off. This known-role single-Seed panel adds no statistical or new P-GRB win-rate claim. Full path work, costs and fleet changes are in Supplement S169.\n\n**Table 11. Paid original-objective B/M/C endpoints.** Each cell gives true U / qualified global L. B retains base-H, M adds two original-weight complete H paths, and C adds half/double-weight paths. All work is charged to the common process cap.\n\n'+paid
    (paper/'paper_body.md').write_text(body.rstrip()+paragraph+'\n',encoding='utf-8')
    supplement='\n\n## S169 Paid objective-diversified initialization against matched multistart\n\nThe inputs and H seeds were fixed before the screen. The first six known roles alone trigger the complete panel. H-only shares one newly produced base diagnostically; complete B/M/C independently pay for 1/3/3 H calls and never import diagnostic or historical Starts. Search weights are half/double the fixed original lambda, and every transferred fleet is checked and evaluated at that original lambda. Paquete and Stutzle [@paquete2003two] provide direct aggregation/local-search prior art.\n\n**Table S169.1. All seven H screens.** Raw 17-digit G/P/F and every path, seed and workload are retained in the linked study CSV.\n\n'+htable+'\n**Table S169.2. Diagnostic H path/pool expenses in seconds.** Base is shared here; these sums are not three measured solver runs.\n\n'+fees+'\n**Table S169.3. All eighteen paid endpoints and process times.** CERT clocks apply only to qualified closed coverage. OPEN clocks are endpoints. Raw signed numerical gaps are retained in the machine table.\n\n'+complete+'\n**Table S169.4. All eighteen actual H/model/Native expenses.** Counts are actual Optimize calls, not process counts. Native and H are nested within the process totals; post-return independent audits are separately recorded.\n\n'+effort+'\nThe full fixed record, raw carrier/member map, exact source/PE/DLL, qualifications, structural comparisons and decision are in [the Round169 report](https://github.com/yifanXovo/TailoredExact/blob/codex/round169-primal-reweight/results/unified_exact_round169/final_report.md). All six current inputs are exposed and only Native Seed 0 is measured. No new P run is made, and M/C are excluded from the GI-TBC master CSV.\n'
    (paper/'supplement.md').write_text(supp.rstrip()+supplement,encoding='utf-8')
    bib=paper/'references.bib';text=bib.read_text(encoding='utf-8-sig')
    assert 'paquete2003two' not in text
    bib.write_text(text.rstrip()+'\n\n@misc{paquete2003two,\n  author = {Paquete, Luis and St{\\"u}tzle, Thomas},\n  title = {A Two-Phase Local Search for the Biobjective Traveling Salesman Problem},\n  year = {2003},\n  note = {Author manuscript},\n  url = {https://iridia.ulb.ac.be/~stuetzle/publications/EMO03.pdf}\n}\n',encoding='utf-8')
    write(OUT/'manuscript_change_record.json',dict(UTC=utc(),body_added_words=len(paragraph.split()),new_body_sections=0,
        tables_added=['11','S169.1','S169.2','S169.3','S169.4'],prior_results_removed=False,old_figures_regenerated=False,
        R168_change='one UNKNOWN wording clarification only; old experimental data unchanged'))
    print('Wrote final report, research/author decision, finite current components',flush=True)
if __name__=='__main__':main()
