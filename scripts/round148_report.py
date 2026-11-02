"""Scientific narrative from saved endpoints; never solves or loads Native."""
from round148_common import *


def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)+'\n'


def lp():
    results=[read(p) for p in sorted((OUT/'LP').glob('*/iteration1/result.json'))]
    text='''# Matched LP increment: one added common-S row

Five complete saved R146 LP domains on three physical instances were
reoptimized once each. K20 BASE/joint/STOCK are three carriers of one
instance. The original objective and constant, all old rows, support,
variable bounds, g interval and cutoff are exactly retained. No old LP
is reoptimized and no variable is fixed at its old fractional value.
Each new row is bound to the saved model/primal SHA. The old GD high
and low rows remain. All five actual Native readbacks equal the signed
compiled rows. Seed0, Threads1, affinity4, serial execution.

'''
    text+=table(['Role','Carrier','Old objective','New objective / qualified numerical LP bound','Gain','g','Weighted penalty'],[
        [r['role'],r['carrier'],f"{r['old_L']:.12f}",f"{r['L']:.12f}",f"{r['gain']:.12f}",f"{r['g']:.12f}",f"{r['weighted_penalty']:.12f}"] for r in results])
    text+=table(['Role/carrier','Rows added','Row NZ','Construction/readback s','Native runtime s','Outer s','RHS box loss bound','Remaining violation'],[
        [r['role']+'/'+r['carrier'],1,r['new_row_nonzeros'],f"{r['construction_seconds']:.6f}",f"{r['Runtime']:.6f}",
         f"{read(OUT/'fees'/('LP_'+r['role']+'_'+r['carrier']+'_1')/'receipt.json')['outer_seconds']:.6f}",
         f"{r['transport']['box_loss_bound']:.4g}",f"{r['remaining_separation']['transported_violation']:.12f}"] for r in results])
    text+='''The final column is separation at the returned new point; it is not
another optimized increment. No optional closure rounds were entered:
one row already gives clear information on D carriers and beyond the
joint carrier. These LP diagnostic domains are not automatically the
current full algorithm's root domain.

The full objective matters. On K20 BASE, g decreases from about .065068
to .061062 while weighted penalty rises from about .170943 to .177218;
their sum increases by .002269. On K35 the weighted penalty remains
.161538478571 and g supplies the .005381 increase. Point activity cannot
substitute for either optimized comparison.

All results are numerical OPTIMAL values with every inherited quality
measure and independent full-matrix residual at most 1e-6. The numerical
dual objective/gap and any adverse reduced cost at an infinite bound are
reported separately in result.json. Neither the old floating-point
optimum nor these values are represented as exact rational optimality
certificates. The exact rational certificate here concerns the new row's
valid coefficient direction. Initial LP values, Native root-after-cuts
bounds and final external supported L are separate evidence layers.

The E1 decision is to implement one uniform, default-off own-root row
and one additional root LP on standalone D, then first test the K35
same-new-PE full pair. It is not an adoption decision. No STOCK/joint
combination grid, exact LP closure or second inequality family is opened.
'''
    (OUT/'LP_report.md').write_text(text,encoding='utf-8',newline='\n')


def final():
    configure();assert not budget()['unclosed']
    full=read(OUT/'reports/full.json');decision=read(OUT/'candidate_decision.json')
    cost=read(OUT/'cost_report.json');manifest=read(OUT/'candidate_manifest.json')
    assert not full['pending'] and decision['study_complete']
    arms=full['formal_arms'];comparisons=full['comparisons']
    endpoints=table(['Role','Method','U','External supported L','Gap %','T produce','T cert','T verify','T total'],[
        [r['role'],r['method'],f"{r['U']:.12f}",f"{r['L']:.12f}",f"{100*r['relative_gap']:.6f}",
         f"{r['T_produce']:.6f}",'open' if r['T_cert'] is None else f"{r['T_cert']:.6f}",
         f"{r['T_verify']:.6f}",f"{r['T_total']:.6f}"] for r in arms])
    roots=table(['Role/method','Initial LP','After added row LP','Printed Native root-after-cuts','Final Native ObjBoundC','Simplex total','Native Work','Terminal nodes','Outer splits'],[
        [r['role']+'/'+r['method'],r.get('initial_root_L'),r.get('actual_root_after_strengthening_L'),
         r.get('printed_root_after_cuts_bound'),r.get('terminal_native_return_ObjBoundC'),
         r.get('Native_total_simplex_iterations'),r.get('Native_total_Work'),r.get('terminal_nodes'),r.get('actual_split_count')] for r in arms])
    report='# Round148: shared-denominator low GD affine rows\n\n'
    report+=f"Decision: **{decision['decision']}**. {decision['decision_discussion']}\n\n"
    report+='''## Mathematical and optimized information

The shared-S affine family retains a common denominator first moment in
each station's conditional mixture. The low-only oracle needs at most
three nodes per state. An exact two-station fixture gives g>=|a-d|/6
where both old GD rows are zero; it is an isolated-block strictness result
consistent with pair-CDF, not a full-model novelty or routing-hull theorem.
The exact oracle/convexification argument is in
[mathematical_analysis.md](mathematical_analysis.md), and the paper-ready
LaTeX section is [manuscript.tex](manuscript.tex).

Five saved GD points, belonging to three physical instances, are strictly
separated. One newly appended row improves every matched full-domain LP:
K20 BASE/joint/STOCK by .002269286408/.002459563403/.004554385894;
K35 BASE by .005381130879; RX20 BASE by .016631649658. Old optima and
all original objective/constants/support/bounds/cutoff/rows are reused
without baseline Optimize. No old variable is frozen. All new numerical
LP optima pass the existing quality policy; neither old nor new optima
are represented as exact rational certificates. The coefficient direction
is checked exactly. See [LP_report.md](LP_report.md) for construction,
Native/outer costs, row NZ, transport loss and remaining separation.
There are no optional closure rounds or rank/eta experiments. The goal's
reported prior negative rank/eta screen is historical context, not a
newly replicated claim when its review attachment is unavailable.

## Complete same-new-PE experiment

The frozen mechanism adds at most one uniform low affine/moment row
and one root LP on standalone D. Its slopes come from the arm's own
normal root point, never an injected saved historical point. Both arms
pay complete own-H, construction, solving and necessary validation.
The original physical horizon and lambda, H seed20260626, Gurobi Seed0,
Threads1, M-B/VD-P, pair-only, AM=.08, depth8, minimum width1e-4 and AP-off
policies remain. New-PE D is the actual incremental control.

'''
    report+=decision['complete_discussion']+'\n\n'+endpoints+'\n'+roots
    report+='''Open T_cert remains null. Caps, slightly different total/verification
times and unfinished searches are not convergence times. Printed Native
root-after-cuts values are log observations at their printed precision;
they do not replace either initial LP or final external supported L.
Native returned bounds, physical G/penalty, target paths, complete Work,
simplex, nodes and outer splits remain separate machine-readable fields
in [reports/full.json](reports/full.json). Committed, physically verified
incumbent trajectories use producer availability clocks in
[reports/verified_U_trajectories.csv](reports/verified_U_trajectories.csv).
No unique causal allocation among static rows, Native branching and AM
is inferred from this complete comparison.

## Historical counterpoints retained

R147 D remains a limited uniform paper-enhancement candidate, not the
historical strongest or broadly robust algorithm. Its Seed0 K35 and
RB35 incumbents improve over B by about 3.13% and 2.54%, but K35 supported
L decreases, K20 does not certify and RX20 certifies about 2.34s later.
The same-old-PE K20 STOCK/STOCK+GD certificates at about 94.261/74.916s
remain strong. R140 old TC+STOCK has K35 U/L about .650438712/.5682885263
and RB35-T2 about .3190804927/.2339272621, both stronger endpoints than
R147 D. Its Seed1 adverse evidence and source/PE/V2-transport differences
remain disclosed; those results are not a pure seed-only intervention.
R144 RN-P's K35 gains, R145's strict complementarity/root-preservation
conclusions and R138-R142's mixed results are retained. No per-instance
best-version switching or fresh full historical factorial is proposed.

## Qualification, failures, identity and cost

Focused qualification covers the low three-node oracle, actual finite
slopes and signed conservative coefficients, positive-S/zero-old-GD,
fixed/omitted domains, compatible sub-support, old GD SHA migration,
actual Native signed readback, complete and nonminimal epigraph Starts,
and OFF matrix identity. The short K20 cap90 lifecycle producer has
six returned calls and four unique models. Its initial reader attempt
encountered an old one-LP/one-control-status assumption. A narrow view
excludes only the original root's never-installed bound from cover
reconstruction. All calls remain in model/Native/quality/lifecycle/cost
audits, and the same sealed producer was reverified without Optimize.
Other CLI/qualification/reviewer-script failures are retained and charged.
No failed search is rerun to obtain a better endpoint.

'''
    report+=f"All {full['complete_Native_Optimize']} entered complete/qualification Native calls returned; five standalone diagnostic LP calls are separate. Charged new outer cost is **{cost['charged_new_experiment_seconds']:.9f}s / 18000s**, including all own-H, construction, solve, failure and necessary verification costs once. Builds are {cost['build_seconds_separate']:.9f}s separately. The charge includes conservative reviewer enclosing intervals and a disclosed 5s allowance for unmeasured startup/serialization, rather than pretending those are exact process timings. Nested Native runtime/Work is not charged twice. Pure offline mathematics, document authoring and public I/O are separate; old R146/R147 fees remain historical.\n\n"
    report+=f"Production source is `{manifest['source_commit']}`; PE SHA256 is `{manifest['production_PE_SHA']}`. The three changed TUs were rebuilt from verified inherited dependencies. The [manifest](candidate_manifest.json) records the compiler, source, objects, PE and DLL. Production, wrapper, fixed-science and late-delivery commits have separate identities. Stable R137, old D/SD entries/profiles and all prior results retain their bytes. Original user modifications are protected.\n\n"
    report+='''## Scope and closeout

'''+decision['scope_discussion']+'\n\n'
    report+='''The [independent final review](review/final_scientific_review.json),
[cost report](cost_report.json), [reuse index](reuse_index.json) and
[RESUME](RESUME.md) give the scientific and actual delivery status.
Only necessary new evidence is packaged. Fixed old carrier/member hashes
avoid copying historical large bundles. Normal push and an English Draft
PR are followed by bounded anonymous public byte/member recovery and
current-round-only metadata screening/cleanup. Neither delivery step
triggers Optimize, compilation or commercial Native loading. No merge,
force push, old-history deletion or stable-default replacement is made.
'''
    (OUT/'final_report.md').write_text(report,encoding='utf-8',newline='\n')
    math_text=(OUT/'mathematical_analysis.md').read_text(encoding='utf-8')
    (OUT/'manuscript.md').write_text(math_text+'\n\n# Complete algorithm evidence\n\n'+decision['complete_discussion']+'\n\n'+endpoints+'\n'+decision['decision_discussion']+'\n\n'+decision['scope_discussion']+'\n',encoding='utf-8',newline='\n')
    tex=OUT/'manuscript.tex';base=tex.read_text(encoding='utf-8').split('% ROUND148_COMPLETE_RESULTS')[0]
    addition='\nThe registered complete comparisons are as follows. All costs include own H and necessary validation.\n\\begin{center}\n\\begin{tabular}{llrrr}\nRole & Method & Physical U & Supported L & Gap (\\%)\\\\\n\\hline\n'
    for r in arms:
        method='D+common S' if r['method']=='D_SHARED_S' else 'D'
        addition+=f"{r['role']} & {method} & {r['U']:.9f} & {r['L']:.9f} & {100*r['relative_gap']:.5f}\\\\\n"
    addition+='\\end{tabular}\n\\end{center}\n'
    addition+=decision['paper_conclusion_tex']+'\n'
    addition+=f"The newly charged outer cost is {cost['charged_new_experiment_seconds']:.6f} seconds of the 18000-second ceiling; build cost is {cost['build_seconds_separate']:.6f} seconds separately. Nested solver runtime and Work are not added twice.\n"
    tex.write_text(base+'% ROUND148_COMPLETE_RESULTS\n'+addition,encoding='utf-8',newline='\n')


if __name__=='__main__':globals()[sys.argv[1]]()
