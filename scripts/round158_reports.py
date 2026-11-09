"""Pure report assembly from accepted saved results; no new scientific solve."""
import csv
from fractions import Fraction as F
from round143_math import outward
from round158_common import *
from round158_delivery import serial_idle

def table(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,lineterminator='\n');writer.writeheader();writer.writerows(rows)

def run():
    serial_idle();tick=time.perf_counter()
    review=read(OUT/'review/final_scientific_review.json');assert review['PASS'] and not review['own_receipt_pending_seal']
    main=read(OUT/'level/rx35_raw_quarter_deep_v3/result.json')
    lp=read(OUT/'qualification/lp_fractional_ownership_v2/result.json');b=budget();assert not b['unclosed']
    assert main['classification']=='UNKNOWN' and main['NodeCount']==258972 and lp['exact_rational_feasible_in_both_models']
    reports=OUT/'reports';reports.mkdir(exist_ok=True);fees=[]
    for p in sorted((OUT/'fees').glob('*/receipt.json')):
        r=read(p);fees.append(dict(label=p.parent.name,exit_code=r['exit_code'],outer_seconds=r['outer_seconds'],G1_seconds=r['G1_seconds'],
            timeout=r['timeout'],receipt=p.relative_to(OUT).as_posix(),receipt_SHA=sha(p)))
    table(reports/'fees.csv',fees)
    intervals=read(OUT/'initial_intervals.json');candidate=read(OUT/'candidates.json');interval_rows=[]
    for role,r in intervals.items():
        r.update(F_F_lower=r['L_I'],F_F_upper=outward(F(candidate[role]['J_exact']),True) if role.startswith('R-') else r['U_I'],
            F_R_lower=r['L_I'],F_R_upper=r['U_R'],new_resource_assignment_upper=None,new_physical_U=None,new_original_J_lower=None,
            level_status='UNKNOWN' if role.startswith('R-') else 'NOT_RUN',
            D_F_definition='D_I minus original R157 26 RX35 vectors only' if role.startswith('R-') else 'D_F=D_I',
            scope_note='Coarse inherited root-scope intervals; physical upper projects to resource upper; no complete-arm endpoint change')
        interval_rows.append(dict(role=role,**r))
    write(OUT/'final_intervals.json',intervals);table(reports/'value_intervals.csv',interval_rows)
    finite=[]
    for role,label in (('R-X35-S-T2','rx35_y3_v1'),('N-B35-S','nb35_continue_v1')):
        r=read(OUT/'resource'/label/'result.json');condition=read(OUT/'resource'/label/'condition.json')
        finite.append(dict(role=role,members=len(condition['members']),J=float(F(candidate[role]['J_exact'])),
            original_T=6300 if role.startswith('R-') else 7200,classification=r['classification'],
            queried_v1_hypot_time_lower=r['required_time_lower'],queried_relaxed_time_upper=r['raw_resource_time_upper'],
            actual_CPP_original_guarded_T_exclusion_transferred=True,novel_U_R='',physical_U='',
            outer_seconds=read(OUT/'fees'/('resource_rx35_y3' if role.startswith('R-') else 'resource_nb35_continue')/'receipt.json')['outer_seconds'],
            scope='Only this preselected exact-price family; numeric time lower belongs to queried v1 coefficients'))
    table(reports/'finite_queries.csv',finite)
    levels=[]
    for p in sorted((OUT/'level').glob('*/result.json')):
        r=read(p);label=p.parent.name;f=read(OUT/'fees'/('level_'+label)/'receipt.json')
        levels.append(dict(label=label,status=r['status'],classification=r['classification'],SolCount=r['SolCount'],
            NodeCount=r['NodeCount'],Runtime=r['Runtime'],Work=r['Work'],IterCount=r['IterCount'],outer_seconds=f['outer_seconds'],
            model_SHA=r['model_SHA'],new_global_J_lower='',novel_U_R='',physical_U=''))
    table(reports/'level_calls.csv',levels)
    cost=dict(UTC=utc(),G1_seconds=b['G1_seconds'],hours=b['G1_seconds']/3600,capacity_seconds=TOTAL,
        remaining_seconds=TOTAL-b['G1_seconds'],all_fees_closed=True,fees=fees,failures=[r for r in fees if r['exit_code']],
        nested_Runtime_Work_helper_added=False,exact_receipts='reports/fees.csv',
        accounting='All scientific construction, qualification, failed/controlled calls and required scientific readers counted once by outer receipt.',
        pure_writing='Not continuously timed; no invented writing hours. Report assembly, PDF compilation/render and publication I/O have separate actual receipts.',
        compile_render=None if not (OUT/'paper_qa/render_receipt.json').exists() else read(OUT/'paper_qa/render_receipt.json')['pure_writing_compile_render_seconds'])
    write(OUT/'cost_report.json',cost)
    decision=dict(UTC=utc(),study_complete=True,scientific_question_resolved=False,science_question_open=True,
        disposition='ACCEPT_SUBSTANTIVE_COMPUTATIONAL_NEGATIVE_AND_EXACT_LP_OBSTRUCTION',
        main_status='UNKNOWN',full_declared_Native_capacity_completed=True,Native_Runtime=main['Runtime'],main_outer_seconds=read(OUT/'fees/level_rx35_raw_quarter_deep_v3/receipt.json')['outer_seconds'],
        new_original_J_lower=None,new_resource_assignment_upper=None,new_physical_U=None,
        finite_family_exclusions=['RX35 preselected Y3 exact-price family (10 vectors)','NB35 preselected singleton'],
        bare_LP_witness='qualification/lp_fractional_ownership_v2/result.json',bare_LP_is_not_integer_upper=True,
        EplusR_candidate=None,conditional_panel_entered=False,production_changes=False,default='stable GI-TBC/B',enhanced_baseline='E+',
        stop_reason='The complete hard quarter-gap level received the full predeclared 36-hour Native capacity after repairs. Both finite free-assignment queries excluded their stated families, while no novel integer resource upper, whole-level lower or route was obtained. Exact full-matrix fractionality documents an explicit LP obstruction. This is an accepted finite computational negative under goal D3/F, not an answer that resource value is negligible.',
        next_research='Keep the integer resource-value question open. Seek justified information about multi-vehicle integer ownership or stronger physical travel/load structure before another substantially unchanged long call; do not infer a same-resource value ceiling from this LP witness.',
        paper_and_public_delivery='Required separate gates; study_complete here describes scientific disposition, not whole /goal completion')
    write(OUT/'final_decision.json',decision)
    assert round(cost['hours'],1)==37.1
    fee_text='\n'.join(f"| {r['label']} | {r['exit_code']} | {r['outer_seconds']:.9f} |" for r in fees)
    report=f'''# Resource-coupling value and a complete objective level

The full RX35 hard level J <= .2519564273646922 completed its declared36-hour Native capacity and returned **UNKNOWN**: no integer point and no whole-level exclusion. The final result is258972 nodes,160559495 simplex iterations,Runtime129600.0039999485 andWork318526.526959261. Its actual outer fee is129601.83248030022 seconds. The constant-zero feasibility bound is not an original-J lower. The resource-value scientific question remains open; this is a substantive finite computational negative accepted by goal D3/F, rather than a claim that the resource branch has negligible value.

The two finite free-assignment queries exclude RX35's preselected Y3 exact-price10-member family and NB35's preselected singleton at original/guarded T. The queried v1/hypot time lowers are6310.129749041621 and7206.982290055626, respectively. They are not relabeled as byte-identical unconditional C++-coefficient time minima. The actual C++ coefficient audit checks every integer budget at nominal and guarded T; identical budgets transfer the fixed-T exclusions. Relaxed-time uppers6878.190504140177 and7238.006414765686 are neither original-T resource uppers nor route-time uppers. Stored-family ranks are not proved global k-best ranks.

## Domains, intervals and interpretation

All minima use the same qualified improving inventory scope and J=G+H, with lambda already in H. D_P(T) is contained in D_R(T), contained in D_F, contained in D_I. RX35 D_F deletes only the original26 R157 vectors; NB35 D_F=D_I. The new family exclusions do not silently redefine D_F. Strict set contraction does not prove a strict optimum increase.

RX35 retains L_I=.2360521029074557, U_I=.23612171136420015, inherited coarse U_R=U_P=.2996694007364017. Its D_F inventory-only upper remains Y3's price approximately.23685400930608236. NB35 retains L_I=.3959564087240911, U_I=.39604654895666136 and inherited coarse U_R=U_P=.450291503262878. The inherited physical controls supply these coarse resource uppers by projection. There is no novel lower-price integer resource assignment. These are root-scope value intervals, not new complete-arm endpoints; no physical U/L is changed. Exact rows are in [value_intervals.csv](reports/value_intervals.csv).

A true original-T integer resource witness U_R would bound every original-objective floor from cuts whose domain contains that same D_R. An inventory-only price or fractional point cannot provide that ceiling. Stronger physical travel/load information and route production have different scope.

## Complete level, one expression alternative and an exact LP obstruction

The main model preserves all original1467 RN columns and2143 RN rows, all inventory supports/hard total and free vehicle assignments. It adds the conservatively emitted hard original-J cutoff, without the old tiny-coefficient known-lower row. The actual C++ raw MPS hash is05c8d7e903195896d459e444dfebede8b788e2f2e666550b0f536a244f3c038b. Seed0, Threads1, MIPFocus1, SolutionLimit1 and NodeLimit2000000000 are recorded. Model T6300 is distinct from the129600-second experiment window. The partial Y3 selectors are unfixed; an out-of-level physical control was not used as a level start.

The sole alternative rounds total-pickup budgets under the shared R92 physical/emitted envelope and guarded acceptance horizon, and deletes dominated subsets. It never substitutes P_k<=Q_k. RX35 retains4087 of7175 subsets, including81 minimal forbidden subsets out of264 negative budgets; NB35 retains4755 and four minimal forbidden subsets. Actual binary RHS implication is checked for all21525 raw vehicle/subset rows per role. Two RX35/five NB35 budgets cross an integer threshold under the acceptance margin, so nominal bare floors would be incorrect. The raw diagnostic returned at594 nodes/753.3065505 outer seconds; rounded reached512 nodes/847.8244789 seconds. These are unequal observed node counts and show no demonstrated compression speedup. Raw was selected for the substantive capacity, with all earlier costs retained.

After the main call closed, an exact rational saved-point reader split each changed station of Y3 equally among three vehicles. P=D=56, ownership1/3, and return per vehicle0. The same point satisfies all24154 raw rows and14890 rounded rows, and every bound of2673 columns, with exact maximum row/bound violation0. There are102 fractional integer columns, maximum integrality violation1/3. Its price is approximately.23685400930608236; exact point and fractions are in qualification/lp_fractional_ownership_v2. This upper-bounds the original-price minima of the two fixed bare LPs only. It is no integer U_R, no ceiling on integer-valid cuts, no Native-root-cut optimum and no proof of a strict global F_R-F_I gap. It documents an explicit ownership fractionality obstruction, without identifying the unique cause of the Native cost.

## Scientific decision and complete algorithm boundary

The full declared capacity has been completed after the necessary coefficient repair. Short unchanged bounds were never used to terminate it. The finite exclusions and exact LP obstruction are useful structural/finite findings, while the integer resource-value question remains unresolved. Another substantially unchanged call has no demonstrated online affordability; a justified change in integer ownership or stronger physical information is the next research question. No unmeasured resource ceiling or route claim is used to close it.

There is no new original-J lower or true route benefit from which to freeze a useful, plausibly self-paid E+R. Therefore no E+R and no empty eight-arm conditional panel are claimed. Stable GI-TBC/B stays default, E+ stays the enhanced baseline, and production C++/configuration, AM and splitting are unchanged. No new build or production-PE execution occurred. The unqualified physical prototype was not executed. Historical R155/K35/NC20 and K20 offline route loops were not reopened.

## Qualification, failures, costs and retained evidence

The pre-long gates cover actual cutoff omissions/RHS, complete RN preservation, physical controls outside the level, R92 near-one and physical-comparison boundary cases, integer rounding/dominance and actual durable normal termination. Actual C++ duration rows correct the earlier hypot coefficient identity omission; all integer budgets agree and rounded matrices remain byte-identical. The final saved-original review freshly checks RN preservation, all exact LP point rows/bounds, finite scopes/prices, final main log, fees/source bytes and protected user modifications. Reviews are separate routines by the same agent, not an independent reviewer identity.

R157's erratum is limited to at least774 displayed nodes/4094s, unfinished Optimize and no final NodeCount/Work. Its11 unpersisted incumbent log values remain unqualified. The first R158 preparation failed on a member path; a long-supervisor label-index error caused a normally stopped short call; deep-v2 was normally stopped for the actual coefficient-binding repair. The first LP reader failed converting an infinite bound to Fraction. All original source versions, errors, fees and controlled stops are retained. The bound reader correction changes neither matrix nor tolerance. See the explicit correction records, [fees](reports/fees.csv), [level calls](reports/level_calls.csv), [finite queries](reports/finite_queries.csv), [scientific review](review/final_scientific_review.json), [source manifest](source_manifest.json) and [reproduction boundaries](reproducibility.md).

Current closed scientific outer charge is **{cost['G1_seconds']:.9f} seconds = {cost['hours']:.9f} hours /72h**, with{len(fees)} closed receipts. This includes failures, controlled stops and required readers, once each. Nested Runtime/Work/H/helper is not added. Exact final costs remain in cost_report.json and the fee CSV; assembly can be refreshed after the last paper-claim check. Pure writing was not continuously timed and no writing hours are invented. PDF compile/render and publication/recovery I/O are separately recorded. All new build/raw/temp/restore areas are below E:/codes/ExactEBRP-work; old trees and necessary runtimes remain read-only.

| Outer fee label | Exit | Seconds |
|---|---:|---:|
{fee_text}

The [thematic paper source](manuscript.tex) and actual PDF are separate from the unchanged stable Round137 paper. Scientific acceptance does not substitute for actual paper visual QA, normal push/Draft PR readback, one bounded public recovery, protected-byte readback and current-round cleanup. The final delivery state is recorded in RESUME.md and publication/recovery metadata.
'''
    (OUT/'final_report.md').write_text(report,encoding='utf-8')
    empirical=r'''\section{Finite queries and a complete hard-level campaign}
Two preselected free-assignment queries were tested first. RX35's retained
Y3 exact-price family contains ten members; NB35's saved-best family is a
singleton. Both were excluded at their original/guarded time horizon.
The queried v1 distance reconstruction gives necessary-time lowers
$6310.129749041621$ and $7206.982290055626$ seconds, respectively, against
original horizons $6300$ and $7200$. These numeric time lowers belong to
the queried v1 models. A finite audit of the actual C++ physical duration
rows found identical integer budgets at both nominal and guarded horizons,
which transfers the fixed-time exclusions; it does not relabel the old
numbers as identical unconditional C++-coefficient time minima. Their
relaxed-time assignments are neither original-time resource uppers nor
physical routes. Family scope remains explicit.

\begin{table}[htbp]
\centering
\begin{tabular}{lrrr}
\toprule
Role & $L_I$ & $U_I$ & Inherited $U_R=U_P$\\
\midrule
RX35 & .2360521029 & .2361217114 & .2996694007\\
NB35 & .3959564087 & .3960465490 & .4502915033\\
\bottomrule
\end{tabular}
\caption{Retained coarse root-scope intervals. The physical upper projects
to a resource upper; no novel low-price integer resource assignment or
new physical upper was obtained. RX35's $D_F$ upper remains the
inventory-only Y3 price, approximately $.2368540093$.}
\end{table}

The one qualified expression alternative retains $4087$ RX35 subsets
instead of $7175$, reducing the full model from $24154$ to $14890$ rows
while keeping $2673$ columns. A finite raw diagnostic returned at $594$
nodes in $753.307$ outer seconds; the rounded diagnostic reached $512$
nodes in $847.824$ seconds. These are unequal observed node counts, not a
matched-node speed comparison. No compression speedup was demonstrated,
and the raw expression was selected for the substantive capacity.

The actual C++-coefficient raw hard level at
$\tau_*=.2519564273646922$ then completed its full declared $129600$-second
Native window. All inventory and vehicle decisions remained free, with
Seed $0$, one thread, MIPFocus $1$ and SolutionLimit $1$. The objective was
constant-zero feasibility under the hard original-price cutoff. Original
model $T=6300$ seconds is separate from the experimental window.
The call returned normally with status TIME\_LIMIT, no integer solution,
$258972$ final nodes, $160559495$ simplex iterations and
$318526.526959$ work units. Native Runtime was $129600.004$ seconds and
the charged outer time was $129601.832$ seconds. Its zero feasibility bound
is not an original-$J$ lower. The full level is therefore UNKNOWN and the
table's prior intervals are retained.

After that call closed, an exact rational saved-point check instantiated
the fractional-ownership construction at Y3. Its total pickups and drops
are both $56$; each vehicle owns $1/3$ of every changed station and has
zero returned load. The same point satisfies every actual row and bound
of both admitted matrices, with exact maximum violation zero. It has
$102$ fractional integer columns, maximum integrality violation $1/3$,
and original price approximately $.23685400930608236$. A separate saved
readback repeats all exact row and bound checks. Thus the two bare LPs
retain this integer stock through fractional ownership even though its
integer resource family is excluded. This is no integer resource upper,
no limit on stronger integer-valid cuts, and no proof that the global
resource minimum strictly exceeds the inventory minimum. It documents a
specific obstruction without identifying the unique cause of search cost.

The total scientific outer charge rounds to $37.1$ hours, including failed
preparation, the normally stopped watchdog/coefficient-repair calls,
necessary qualification, and saved-original readers. All receipts are
closed; nested Runtime and Work are not charged again. The first exact
LP reader failed on an infinite-bound conversion; its original bytes and
fee remain, and only the signed infinite-bound readback was corrected.
PDF compilation/rendering, pure writing and publication I/O are separate.
Current results and exact final costs accompany the saved evidence.

This completes a substantive finite computational negative under the
predeclared capacity. Whether $F_R-F_I$ is worthwhile remains open.
No new original-objective lower or true route benefit justifies freezing
E+R, so the conditional eight-arm panel was not entered. The next research
question concerns justified information about integer vehicle ownership
or stronger physical travel/load structure. Stable GI-TBC/B remains the
default and E+ the enhanced baseline; no production change or complete-arm
benefit is claimed.
'''
    (OUT/'empirical_results.tex').write_text(empirical,encoding='utf-8')
    write(OUT/'engineering/report_assembly.json',dict(UTC=utc(),report_assembly_IO_seconds=time.perf_counter()-tick,
        not_G1=True,Optimize=0,pure_writing_and_metadata=True,manual_writing_hours_not_measured=True))
    print(json.dumps(dict(scientific_disposition=decision['disposition'],fees=len(fees),G1_seconds=cost['G1_seconds'],paper_empirical_source_written=True)),flush=True)

if __name__=='__main__':run()
