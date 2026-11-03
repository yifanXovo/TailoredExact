"""Assemble final evidence and paper prose from accepted entered cells only."""
from round149_common import *


def number(value,digits=12):return '—' if value is None else f'{value:.{digits}f}'


def build():
    full=read(OUT/'reports/full.json');choice=read(OUT/'stage_decision.json')
    assert not full['pending'] and full['complete_Native_Optimize']==full['complete_Native_returned']
    order={'K-35-U':0,'R-B35-S-T2':1,'K-20-S':2}
    formal=sorted(full['formal_arms'],key=lambda r:(order[r['role']],r['method']))
    comparisons=sorted(full['comparisons'],key=lambda r:order[r['role']])
    assert formal and len(formal)%2==0
    assert all(r['performance_eligible'] and r['native_proof_qualified'] and r['H_complete'] for r in formal)
    decision=dict(choice,study_complete=True,stable_R137_unchanged=True,R147_limited_D_status_preserved=True,
        default_replacement=False,automatic_merge=False,Seed0_scope_only=True,
        formal_roles=sorted({r['role'] for r in formal}),formal_arms=len(formal),
        new_PE_SHA=read(OUT/'candidate_manifest.json')['production_PE_SHA'],
        serious_double_open_regression_roles=[c['role'] for c in full['comparisons'] if c['serious_double_open_regression']],
        no_additional_panel_queued=True)
    write(OUT/'candidate_decision.json',decision)
    lines=['# Round149: penalty floors in state-product envelopes','',
        f"Decision: **{decision['decision']}**.",'',decision['reason'],'',
        'The study separates four claims. The resource floor and integer validity are mathematically established; the product block is strictly stronger; three same-domain numerical LP increments are positive; complete algorithm value is assessed only by the entered new-PE own-H pairs below. No historical beta or incumbent is injected into a complete arm.','',
        '## Entered complete results','',
        '| Role | Method | Physical U | Supported L | Signed U−L | Relative gap % | Certified | T_produce | T_cert | T_verify | T_total |',
        '|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|']
    for r in formal:
        lines.append(f"| {r['role']} | {r['method']} | {number(r['U'])} | {number(r['L'])} | {number(r['signed_gap'])} | {100*r['relative_gap']:.6f} | {r['certificate']} | {r['T_produce']:.6f} | {number(r['T_cert'],6)} | {r['T_verify']:.6f} | {r['T_total']:.6f} |")
    lines+=['','U is recomputed from the physical fleet and original objective. L is the external supported proof-cover lower value. Open T_cert entries are null. Complete arms pay their own H, construction, all LP/MIP calls and necessary verification. Small cap-near total-time differences on open runs are not convergence or certification speed. All admitted difficult windows were retained.','',
        '## Comparisons and search observations','']
    for c in comparisons:
        lines.append(f"For {c['role']}, PF changes U by {c['delta_U']:+.12f}, L by {c['delta_L']:+.12f}, signed gap by {c['delta_signed_gap']:+.12f}, and relative gap by {100*c['delta_relative_gap']:+.6f} percentage points. U improvement is {c['U_improvement_percent']:+.6f}% and L improvement {c['L_improvement_percent']:+.6f}%. Serious double-open regression under the inherited reference rule: {c['serious_double_open_regression']}.")
        lines.append('')
    lines+=['| Role | Method | Initial formal LP L | Printed Native root-after-cuts | Final supported L | Native Work (all calls) | Simplex iterations | Terminal nodes | Outer splits |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in formal:
        lines.append(f"| {r['role']} | {r['method']} | {number(r['initial_root_L'])} | {number(r.get('printed_root_after_cuts_bound'),5)} | {number(r['L'])} | {r['Native_total_Work']:.6f} | {r['Native_total_simplex_iterations']:.0f} | {r['terminal_nodes']:.0f} | {r['actual_split_count']} |")
    lines+=['','The LP, printed Native root-after-cuts and final supported L are different evidence layers. Witness trajectories, per-target logs/Work and AM records are retained in reports and raw carriers. Keeping the AM geometry does not keep Native target/search paths identical. These observations locate changes without uniquely attributing them to one static row, branch, target or AM decision.','',
        '## Mathematics, LP signal and qualification','',
        'See mathematical_analysis.md for the continuous-resource primal/dual construction, outward floor and upward beta, whole-block facet implication, strict example, valid nonminimal completions and compatible child/proof-cover scope. The scalar G bound was already implicit in the old LP. LP_report.md gives three positive PF optima and one redundant scalar control. All old variable domains and objective semantics are retained. No extra root LP, new column or source optimization is added.','',
        'The K35 PF floating primal-dual diagnostic difference is about .000619046, while its diagnostic dual still exceeds the old saved primal. Scalar-only differs by -3.225e-7 within the inherited quality tolerance. The resource arithmetic uses exact diagnostic certificates; the actual LP optima are qualified floating evidence, not exact rational optimality proofs. No old LP or tiny-gap search was repeated.','',
        'Qualification includes exact actual-weighted resource primal/dual checks, positive/zero floors, safe coefficient direction, real writer and Native matrix readback, child domination/compatibility, OFF, complete and feasible nonminimal g/e Starts, SHA-selected zero-GD context, actual dry CLI and one short cap90 own-H producer. All existing accepted H, physical input/objective, Start, quality, lifecycle and R134 proof predicates are reused. The short producer is a health check, not a performance comparison.','',
        'Two no-Optimize fixture corrections are preserved: raising e requires a compatible W_SP completion; a fixed W_SP box can forbid nonminimal e, and r_max must not be counted as a station ratio. A separate boundary test initially assumed an old RB35 GD block had zero rows; the mistaken test assumption is preserved and corrected. None required a production source change, old qualification panel or extra baseline Optimize. The current zero-GD matrix test labels its synthetic call wrapper explicitly.','',
        '## Historical and adoption boundaries','',
        'R137 GI-TBC remains stable. R147 D remains its previously limited unified enhancement candidate: known Seed0 hard-role U gains do not establish broad robustness, and K20 was unproved and K35 L once declined. K20 STOCK/STOCK+GD certification around94.261/74.916s remains strong prior evidence. R140 TC+STOCK Seed0 K35 U/L≈.650438712/.5682885263 and RB35≈.3190804927/.2339272621 remain stronger historical endpoints; accompanying Seed1 losses and source/PE/V2 transport differences prevent interpreting them as pure seed interventions.','',
        'R47 eta/mu, R48/R49 primal-dual/formulation work, corrected R52 three severe false-retains and its true correct-retain negative anchor (parent Work≈843.456 proved; forced midpoint≈2651.321 capped), and R130/R137 root-only evidence are preserved. R119 dynamic incumbent rebuilding and R120–R122 domain/conditional propagation are distinct predecessors. R131 left this product feedback incomplete. R88, R133, R144 and R145 remain context, not an obligation to replay a historical grid.','',
        'R148 produced positive five-model/three-instance Shared-S LP increments but a serious RB35 incumbent/signed-gap loss. It remains research only. This round does not rescue it through Shared-S/STOCK/RN/AM combinations, extra seeds, instance-name switches or timed algorithm switching. The present decision concerns only the frozen PF implementation and entered known Seed0 scope.','',
        '## Cost, identities and reproducibility','',
        'cost_report.json counts all new outer experiment, qualification, failure and necessary verification once, including complete own H. Nested solver Runtime/Work is descriptive, never added a second time. Necessary compile time and pure manuscript/public I/O are separate. The ceiling is18000s; released nominal capacity is never counted twice. No more optimization is queued.','',
        'candidate_manifest.json and identity_index.json separate production source, PE/DLL, executed wrapper/helper, fixed scientific and delivery identities. The default-off research entry is scripts/paper_s2_penalty_feedback.py with config/gi_tbc_penalty_feedback_round149.json; --pf off uses the same new PE control. Original profiles, historical evidence and the protected user tree retain their bytes. New carriers contain necessary incremental evidence; fixed R146 references avoid copying old large history. Independent final review, public recovery and bounded current-round cleanup are recorded separately.','']
    lines+=['The formal scopes are K35: 35 stations / 3 vehicles, physical T10800, lambda .15, cap2400; RB35-T2: 35/3, T7200, rho1, original lambda 1/Omega, cap2400; K20: 20/2, T5400, lambda .15, cap1200. All use Seed0/Threads1, H seed20260626, pair-only, AM .08, depth8, width1e-4, AP off, Shared-S/STOCK off. No RX20 full arm, extra seed or other clarification is entered.','',
        'The RB35 reference-rule flag is false: its U loss is below 5% and its signed-gap loss is below 25%. The adoption decision instead reflects the complete mixed value and the absent K20 certification gain. This is not an all-cases-must-win rule. K20 necessary verification extends complete totals beyond the nominal production cap; the actual extra time is retained and charged from the reserved verification capacity.','']
    (OUT/'final_report.md').write_text('\n'.join(lines),encoding='utf-8')
    manifest=read(OUT/'candidate_manifest.json')
    matrices={p.name:sha(p) for p in OUT.glob('*_matrix.json')}
    write(OUT/'identity_index.json',dict(production_source=manifest['source_commit'],
        production_PE=manifest['production_PE'],PE_SHA256=manifest['production_PE_SHA'],
        DLL=manifest['DLL'],DLL_SHA256=manifest['DLL_SHA'],
        executed_wrapper_commit=git('rev-parse','840292079').decode().strip(),matrices=matrices,
        source_hash_manifest_SHA=sha(OUT/'candidate_manifest.json'),
        fixed_science='recorded after scientific commit in publication_pin.json',
        delivery_head='actual PR readback, not production source',separate_identities=True))
    doc=f"""# Round149 penalty-product feedback study

{decision['reason']}

The [full report](../results/unified_exact_round149/final_report.md),
[mathematics](../results/unified_exact_round149/mathematical_analysis.md),
[matched LPs](../results/unified_exact_round149/LP_report.md),
[decision](../results/unified_exact_round149/candidate_decision.json) and
[delivery record](../results/unified_exact_round149/RESUME.md) retain the actual
scope, limitations, full costs and separate identities. The research entry is
`scripts/paper_s2_penalty_feedback.py`; it is separate from stable R137.
The scalar G bound was already implied; the intervention propagates it into
existing products before the first formal solve, without an extra root LP.
"""
    (ROOT/'docs/round149_research.md').write_text(doc,encoding='utf-8')
    print(json.dumps(dict(report=True,decision=decision['decision'],formal_arms=len(formal))))


def cost():
    configure();assert not budget()['unclosed'];b=budget();full=read(OUT/'reports/full.json')
    write(OUT/'cost_report.json',dict(UTC=utc(),charged_new_experiment_seconds=b['G1_seconds'],
        ceiling_seconds=18000,experiment=b,build_seconds_separate=b['separately_reported_seconds'],
        standalone_LP_Optimize=4,baseline_Optimize_new=0,
        complete_Native_Optimize=full['complete_Native_Optimize'],complete_Native_returned=full['complete_Native_returned'],
        includes_all_own_H_construction_solves_qualification_failures_necessary_verification=True,
        nested_H_LP_MIP_Runtime_Work_not_added=True,historical_cost_not_recharged=True,
        pure_math_authoring_public_IO_separate=True,external_costs='infra/external_costs.json',
        measurement_basis='Metered outer process receipts plus disclosed conservative independent-review/startup allowances'))
    marker='\n<!-- ROUND149 COST -->\n'
    report=OUT/'final_report.md'
    if report.exists():
        base=report.read_text(encoding='utf-8').split(marker)[0]
        report.write_text(base+marker+f"Charged new experimental outer cost: **{b['G1_seconds']:.9f}s / 18000s**. Necessary build: **{b['separately_reported_seconds']:.9f}s separately**. All {full['complete_Native_Optimize']} complete/qualification Native calls returned; four standalone diagnostic LP calls are separate. Public I/O and offline authoring are separate.\n",encoding='utf-8')
    paper=OUT/'manuscript.tex'
    if paper.exists() and (OUT/'candidate_decision.json').exists():
        marker='% ROUND149 FINAL EVIDENCE'
        base=paper.read_text(encoding='utf-8').split(marker)[0]
        choice=read(OUT/'candidate_decision.json')
        tail=[marker,r'\paragraph{Complete comparisons.}',
            r'\begin{center}\small\begin{tabular}{llrrrr}',
            r'Role & Method & Physical $U$ & Supported $L$ & Gap (\%) & Total (s) \\',r'\hline']
        for r in full['formal_arms']:
            method=r['method'].replace('_',chr(92)+'_')
            tail.append(f"{r['role']} & {method} & {r['U']:.9f} & {r['L']:.9f} & {100*r['relative_gap']:.4f} & {r['T_total']:.3f} "+r'\\')
        tail+=[r'\end{tabular}\end{center}',
            'All arms use Seed0/Threads1, independent complete own H, the original physical objective and a matched same-new-executable control. Open runs have no certificate time; cap-near timing differences are not convergence speed.']
        for c in full['comparisons']:
            tail.append(f"For {c['role']}, PF changes physical U by {c['delta_U']:+.9f}, supported L by {c['delta_L']:+.9f}, and signed gap by {c['delta_signed_gap']:+.9f}.")
        tail.append('Adoption decision: '+r'\texttt{'+choice['decision'].replace('_',r'\_')+'}.')
        reason=choice['reason'].replace('_',chr(92)+'_').replace('%',chr(92)+'%').replace('&',chr(92)+'&')
        tail.append(reason)
        tail.append(f"Charged experimental outer cost is {b['G1_seconds']:.6f}s of 18000s, including own H, construction, solves, qualification, failures and necessary verification once. Build takes {b['separately_reported_seconds']:.6f}s separately. Nested solver runtimes and Work are not charged twice. Stable R137 and the previous limited R147 D status are preserved; no additional experiment is queued.")
        paper.write_text(base+'\n'.join(tail)+'\n',encoding='utf-8')


def run():
    configure();assert metered('final_report_assembly','diagnostic',[PYTHON,'-B',__file__,'build'],60,120)==0
    cost()


if __name__=='__main__':globals()[sys.argv[1]]()
