"""Assemble the paper section and finite decision from verified idle evidence."""
from round147_common import *

SHORT = {'K-20-S': 'K20', 'R-X20-S-T1': 'RX20-T1', 'R-B35-S-T2': 'RB35-T2', 'K-35-U': 'K35'}
LABEL = {'BASE': 'B', 'STOCK': 'S', 'GD': 'D', 'STOCK_GD': 'SD'}


def number(value, digits=12):
    return '—' if value is None else f'{value:.{digits}g}'


def table(headers, values):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '|' + '---|' * len(headers)] +
        ['| ' + ' | '.join(str(v) for v in row) + ' |' for row in values]) + '\n\n'


def assemble():
    configure()
    assert not budget()['unclosed']
    full, cost, decision = [read(OUT / name) for name in ['reports/full.json', 'cost_report.json', 'candidate_decision.json']]
    assert not full['pending'] and decision['study_complete']
    manifest = read(OUT / 'candidate_manifest.json')
    values = full['four_cell_rows']
    measured_roles = {r['role'] for r in full['new_arms']}
    core = [r for r in values if r['role'] in measured_roles]
    evidence = table(['Role', 'Method', 'Evidence', 'U', 'Supported L', 'Gap %', 'T_cert s', 'T_verify s', 'T_total s'],
        [[SHORT.get(r['role'], r['role']), LABEL[r['method']], 'new R147' if r['round'] == 147 else 'sealed R146',
          number(r['U']), number(r['L']), f'{100 * r["relative_gap"]:.6f}', number(r['T_cert'], 9),
          number(r['T_verify'], 9), number(r['T_total'], 10)] for r in values])
    compact = table(['Role', 'Method', 'U', 'Supported L', 'Gap %', 'T_cert s', 'T_total s'],
        [[SHORT[r['role']], LABEL[r['method']], number(r['U']), number(r['L']),
          f'{100 * r["relative_gap"]:.6f}', number(r['T_cert'], 9), number(r['T_total'], 10)] for r in core])
    metrics = table(['Role', 'Method', 'Initial LP', 'Printed root/cuts', 'Native Work', 'Root simplex', 'Terminal nodes', 'Splits', 'Rows / NZ'],
        [[SHORT[r['role']], LABEL[r['method']], number(r.get('initial_root_L'), 9),
          number(r.get('printed_root_after_cuts_bound'), 9), number(r.get('Native_total_Work'), 8),
          r.get('native_root_simplex_iterations', '—'), number(r.get('terminal_nodes'), 9), r['actual_split_count'],
          f'{r.get("terminal_rows", "—")} / {r.get("terminal_nonzeros", "—")}'] for r in core])
    protocol = ('B, S, D and SD all retain stable GI-TBC; S enables BOTH STOCK and D enables the state-conditioned '
        'GD mechanism (at most two rows on an applicable domain). Every new arm pays for its own complete H (seed 20260626), all LP/MIP calls and mandatory physical, '
        'Start, model-scope, numerical-quality, lifecycle and R134 proof verification. Gurobi Seed=0, Threads=1, '
        'MIPThreads=1 and affinity=4; timed runs are serial. M-B/VD-P, pair-only, AM=.08, depth=8, minimum width=1e-4 '
        'and AP off remain fixed. Physical horizons, original lambda and process caps are bound in the matrices. '
        'No prior solution, cut or H state is injected into a new arm.\n\n')
    interpretation = ('A dash in T_cert means open, not a cap-valued convergence time. Signed/relative gaps and '
        'T_produce/T_cert/T_verify/T_total remain in [full JSON](reports/full.json) and [four-cell CSV](reports/four_cell_evidence.csv). '
        'Native ObjBoundC/ObjVal are separate fields from external proof-supported L. T_total is complete producer plus '
        'necessary verification; outer fees additionally include launcher/accounting overhead. An open arm with a smaller '
        'verification cost has not thereby converged faster. Same-PE cross-round references retain their original dates, '
        'fees and raw identities; identical system load or simultaneous execution is not assumed.\n\n')
    report = '# Round147: standalone GD and the STOCK tradeoff\n\n'
    report += f'**Decision: {decision["decision"]}. Uniform recommendation: {decision["uniform_recommendation"]}.**\n\n'
    report += decision['decision_discussion'] + '\n\n'
    report += '## Complete evidence and scope\n\n' + protocol + evidence + interpretation
    report += decision['core_discussion'] + '\n\n' + decision['historical_discussion'] + '\n\n'
    report += '## Search observations\n\n' + metrics
    report += ('Initial LP and printed terminal-root-after-cuts values are different observations. The latter have native '
        'log precision; Work, simplex, nodes, density and splits describe the observed search and do not identify a unique '
        'causal internal mechanism. [Verified incumbent trajectories](reports/verified_U_trajectories.csv) use committed '
        'producer availability, not solver runtime or total time.\n\n')
    report += decision['trajectory_discussion'] + '\n\n'
    report += '## Mathematics, qualification and identities\n\n'
    report += ('The [self-contained mathematical note](mathematical_analysis.md) proves standalone validity without requiring '
        'formal STOCK rows. R146 exact arithmetic, inventory units, actual STOCK-off writer/Native readback, complete and '
        'nonminimal Starts, subset inheritance and unchanged OFF matrices are reused. The zero-row reader now selects the '
        'saved original model using actual root metadata; a no-model H-completion control path is preserved. New targeting '
        'checks exercise the wrapper, actual CLI and zero-lower saved fixture with zero Optimize/Native load. No production '
        'rebuild, repeated native health test, standalone LP, new mechanism, placement grid or tuning was needed.\n\n')
    report += (f'Production source `{manifest["source_commit"]}` and PE SHA256 `{manifest["production_PE_SHA"]}` are unchanged. '
        f'R146 fixed science is `{SCIENCE146}`. New wrapper/registration versions are recorded in [wrapper identity](wrapper_version.json) '
        'and the [core matrix](core_matrix.json); later scientific and publication commits remain distinct. All old entries, '
        'profiles, R137 manuscript bytes, historical results and protected original user changes are preserved.\n\n')
    report += '## Cost, decision gate and delivery\n\n'
    report += (f'New charged outer experiment/qualification cost is **{cost["charged_new_experiment_seconds"]:.9f} seconds** '
        f'({cost["charged_new_experiment_seconds"] / 3600:.9f} hours), below 18000. '
        f'All {full["new_Native_Optimize"]} new Native Optimize calls returned; new standalone LPs=0, source solves=0, builds=0. '
        'H, solver calls, qualifications, failures and necessary postverification are counted once. Nested runtime/Work and '
        'the original R146 fees are not added. Pure authoring, mathematical review, packaging and public recovery are separate. '
        'See [cost](cost_report.json) and the immutable per-process fee receipts.\n\n')
    report += decision['extension_discussion'] + '\n\n'
    report += ('The [paper section](manuscript.md), [independent review](review/final_scientific_review.json), '
        '[reuse index](reuse_index.json), [decision](candidate_decision.json) and [continuation record](RESUME.md) '
        'form the finite handoff. Current carriers include necessary new evidence; fixed parent carriers and member hashes '
        'identify inherited assets without copying the old history. Public byte/member acceptance, actual English Draft PR '
        'readback and bounded current-round cleanup are recorded as late delivery metadata.\n')
    (OUT / 'final_report.md').write_text(report, encoding='utf-8', newline='\n')
    write(OUT / 'document_inputs.json', dict(UTC=utc(), full_SHA=sha(OUT / 'reports/full.json'),
        cost_SHA=sha(OUT / 'cost_report.json'), decision_SHA=sha(OUT / 'candidate_decision.json'),
        generator_SHA=sha(__file__), Optimize=0, Native_load=0))
    return full, cost, decision, compact, protocol


def paper(full, cost, decision, compact, protocol):
    text = r'''# When direct Gini deviation rows help a complete algorithm

The stable GI-TBC algorithm uses complete own H, M-B/VD-P state linking,
pair-only support and the original objective \(g+\lambda P\). STOCK adds
four inventory-product RLT rows. Direct GD adds at most two rows on the
original selectors, without variables, a source solve or a new controller.
The previous study established useful optimized LP information and complete
incremental benefits when GD was added to STOCK. It left a material RB35
incumbent/gap tradeoff against stable BASE. The present finite experiment
asks whether GD alone retains useful value while avoiding that tradeoff.

Let \(r_i=c_iY_i\ge0\), \(S=\sum_i r_i>0\),
\(A=\sum_{i<j}|r_i-r_j|\), and \(G=A/(nS)\). For any station set J,
\(A\ge |J|S-n\sum_{i\in J}r_i\). Choosing the components below their
normalized mean proves the classical Gini–Hoover bound
\(G\ge\sum_i(1/n-r_i/S)_+=\sum_i(r_i/S-1/n)_+\).
On the necessary continuous inventory box conditional on \(Y_i=y\),
valid bounds \(0<D^-_{iy}\le S\le D^+_{iy}\) therefore give

\[
ng\ge\sum_{i,y}(1-nc_iy/D^-_{iy})_+s_{iy},\qquad
ng\ge\sum_{i,y}(nc_iy/D^+_{iy}-1)_+s_{iy}.
\]

These bounds follow from physical total inventory and actual support,
independently of whether formal STOCK rows are present. The production
construction generates root coefficients once with directed arithmetic,
omits an unproved positive-denominator domain, sets infeasible conditional
states to zero and inherits rows only to compatible sub-supports. This
uniform mathematical rule is unchanged. On domains where \(S>0\) is proved,
the zero-stock consequence \(ng\ge\sum_i s_{i0}\) closes the earlier
half/half binary epigraph example (whose \(S>0\))
at \(g\ge1/2\); it is not a complete routing-hull result or a new general
inequality theorem. It does not apply at \(S=0\), where the original
convention is \(G=0\); the production scope rule omits GD on an unproved
positive-denominator domain.

For a common fixed LP domain let B=BASE, S=STOCK, D=BASE+GD and
SD=STOCK+GD. Their feasible sets obey \(P_{11}=P_{10}\cap P_{01}\), so
\(v_{11}\ge\max(v_{10},v_{01})\ge v_{00}\) for minimization. The inherited
K20 optima are .19514915244120534, .20459043917810038,
.2360103023423648 and .2510161099222611 for B, S, D and SD respectively.
GD's two numerical marginal increments are .04086114990115946 and
.04642567074416072. The interaction of approximately .00556452084300124
is one fixed-domain LP observation; it establishes neither general
supermodularity nor an ordering of complete search performance. These
LPs and the other qualified R146 LP/witness evidence were reused without
new optimization.

'''
    text += protocol + compact
    text += ('The table has seven new R147 arms (K20, RX20 and K35 B/D; RB35 D) and seven sealed '
        'same-PE R146 references (K20 and RX20 S/SD; RB35 B/S/SD). In particular, RB35 B is a '
        'cross-round sealed reference, while K20/RX20/K35 B are new R147 controls. References retain their original '
        'dates and fees; equal PE, input, objective, cap, resources and H semantics do not imply identical '
        'host load. Open T_cert values remain absent. No cap is substituted for convergence time, and '
        'the LP interaction is not applied to wall-clock certificates.\n\n')
    text += decision['core_discussion'] + '\n\n' + decision['trajectory_discussion'] + '\n\n'
    text += decision['historical_discussion'] + '\n\n'
    text += f'**Uniform decision: {decision["uniform_recommendation"]}.** ' + decision['decision_discussion'] + '\n\n'
    text += decision['extension_discussion'] + '\n\n'
    text += (f'New complete/qualification outer cost is {cost["charged_new_experiment_seconds"]:.9f} seconds, '
        f'within 18000; all {full["new_Native_Optimize"]} new Native Optimize calls returned. '
        'There were no new source or standalone LP optimizations or production builds. Full physical, '
        'Start, domain, quality and proof verification was retained. This is finite evidence on known '
        'roles and one seed, not an independent validation set, broad dominance theorem or multi-seed '
        'robustness claim. The standalone mechanism remains mathematically valid regardless of adoption.\n\n'
        'The reproducible companion [scientific report](final_report.md), [mathematical note](mathematical_analysis.md), '
        '[four-cell data](reports/four_cell_evidence.csv), [trajectories](reports/verified_U_trajectories.csv) '
        'and [decision](candidate_decision.json) retain original identities and limitations.\n')
    (OUT / 'manuscript.md').write_text(text, encoding='utf-8', newline='\n')


def navigation(full, cost, decision):
    guide = '# Round147: standalone GD and the STOCK tradeoff\n\n' + decision['decision_discussion'] + '\n\n'
    guide += ('[Scientific report](../results/unified_exact_round147/final_report.md), '
        '[paper section](../results/unified_exact_round147/manuscript.md), '
        '[mathematics](../results/unified_exact_round147/mathematical_analysis.md), '
        '[four-cell data](../results/unified_exact_round147/reports/four_cell_evidence.csv), '
        '[cost](../results/unified_exact_round147/cost_report.json) and '
        '[decision](../results/unified_exact_round147/candidate_decision.json) retain the finite scope.\n\n'
        'The new `scripts/paper_s2_gd_only.py` uses `config/gi_tbc_gd_round147.json`. '
        'Its default is D (GD on, STOCK off); `--gd off` is B. The old '
        '`scripts/paper_s2_gd.py` retains SD on / S off. Both use the verified existing R146 PE. '
        'Required arguments are `--input`, `--out-dir` (new), `--T`, `--cap` and `--seed`; '
        '`--lambda` must match the original physical objective and defaults to .15. '
        'Plans print without execution unless `--run` is supplied. New assets belong under '
        '`E:/codes/ExactEBRP-work`; formal evidence also requires the campaign postverification.\n\n'
        'The stable R137 entry/profile and manuscript keep their identity. New launchers are '
        'separate reproducible research entries; no per-instance switching or automatic merge is introduced. '
        'Actual publication, English Draft PR readback and bounded cleanup are recorded in '
        '[RESUME](../results/unified_exact_round147/RESUME.md).\n')
    (ROOT / 'docs/round147_research.md').write_text(guide, encoding='utf-8', newline='\n')
    marker = '\n\n<!-- Round147 evidence -->\n\n'
    addition = ('The [Round147 standalone-GD study](round147_research.md) fills the missing '
        'K20 B/D and RB35 D cells using the unchanged R146 PE and seven sealed same-PE references. '
        + decision['navigation_discussion'] + '\nThe '
        '[decision](../results/unified_exact_round147/candidate_decision.json) and '
        '[delivery record](../results/unified_exact_round147/RESUME.md) preserve the actual scope and identities.\n')
    for name in ['current_mainline.md', 'unified_exact_research_index.md']:
        path = ROOT / 'docs' / name
        old = path.read_text(encoding='utf-8').split(marker)[0]
        path.write_text(old.rstrip() + marker + addition, encoding='utf-8', newline='\n')
    resume = '# Round147 continuation and delivery record\n\n'
    resume += f'Science is complete. Decision: **{decision["decision"]}**; uniform recommendation: **{decision["uniform_recommendation"]}**.\n\n'
    resume += (f'New arms: {len(full["new_arms"])}; sealed R146 formal cells reused: 7. '
        f'All {full["new_Native_Optimize"]} new Native calls returned and every entered arm passed complete validation. '
        f'Charged new outer cost: {cost["charged_new_experiment_seconds"]:.9f}s / 18000s. '
        'No automatic further experiment is queued. Never repeat a fee label or sealed producer.\n\n'
        f'Production source: `{read(OUT / "candidate_manifest.json")["source_commit"]}`. '
        f'Delivery base: `{BASE}` / `codex/round146-direct-gini-deviation`; main had not absorbed it at entry. '
        'Wrapper/registration versions, measured source, PE and scientific/publication commits are separate.\n\n'
        'Scientific publication is followed by normal push, an English Draft PR, anonymous bounded '
        'byte/member recovery and current-round-only cleanup. Their actual late state is recorded in '
        '`publication_pin.json`, `PR_delivery.json`, `PR_readback.json`, `public_restore_receipt.json` '
        'and `cleanup_record.json`. No merge, force push, old-round deletion or global setting change is authorized. '
        'All raw, failures, necessary runtime and active trees remain retained.\n')
    (OUT / 'RESUME.md').write_text(resume, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    inputs = assemble()
    paper(*inputs)
    navigation(*inputs[:3])
