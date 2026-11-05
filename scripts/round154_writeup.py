"""Write final prose from sealed reports; no solver or Native dependency."""
from round154_common import *

def run(audit_label='final_evidence_v2'):
    science=read(OUT/'reports/scientific_table.json')['rows']
    prices=read(OUT/'reports/pricing_results.json')['rows']
    panel=read(OUT/'reports/complete_pairs.json');pairs=panel['pairs'];assert not panel['missing_positions'] and len(pairs)==4
    cost=read(OUT/'cost_report.json');assert not cost['budget']['unclosed']
    audit=read(OUT/'qualification'/audit_label/'result.json');assert audit['PASS']
    failed=[r for r in cost['receipts'] if r['exit']!=0]
    def md_table(header,rows):
        return '\n'.join(['| '+' | '.join(header)+' |','|'+'|'.join(['---']*len(header))+'|']+
                         ['| '+' | '.join(map(str,row))+' |' for row in rows])
    hull=md_table(['Domain','R154 lower','R154 upper','Width','Upper reduction','Columns/supports'],
        [[r['role'],f"{r['lower']:.12f}",f"{r['upper']:.12f}",f"{r['width']:.9f}",f"{r['upper_reduction']:.9f}",f"{r['columns']}/{r['supports']}"] for r in science])
    complete=md_table(['Role','B U / L','E U / L','E−B absolute gap','E own floor'],
        [[r['role'],f"{r['B_U']:.9f} / {r['B_L']:.9f}",f"{r['E_U']:.9f} / {r['E_L']:.9f}",f"{r['E_minus_B_gap']:+.9f}",f"{r['own_floor']:.9f}" if r['own_floor'] is not None else 'unavailable'] for r in pairs])
    pricing=md_table(['Direction / phase','Oracle','Target hull','Fresh price lower','True price upper','Proof / rejection'],
        [[r['direction']+' / '+r['phase'],r['implementation'],f"{r['target_hull']:.9f}",f"{r['fresh_price_lower']:.9f}",f"{r['true_price_upper']:.9f}",str(r['target_proved'])+' / '+str(r['target_disproved'])] for r in prices])
    gains=max(r['lower_gain'] for r in science);nb=next(r for r in pairs if r['role']=='N-B35-S')
    route='Temporarily close this inventory-pricing branch and prioritize the remaining full routing/loading coupling.' if gains<1e-6 else 'Retain the finite useful bound gains, while treating unresolved pricing as an explicitly bounded research question.'
    decision=dict(UTC=utc(),stable_method='R137 GI-TBC',stable_entry_unchanged=True,default_candidate='B',E_default=False,J_default=False,
        E_status='research-only',residual_status='qualified research oracle; no universal RN dominance or speed claim',
        recommendation=route,precision=1e-4,full_hull_target_met={r['role']:r['target_met'] for r in science},
        science_evidence={r['role']:r['result'] for r in science},
        full_confirmation_positions=9,all_own_H=True,same_PE=True,no_instance_conditioned_hybrid=True,
        fixed_direction_rejection_is_not_full_hull_rejection=True,LP_upper_is_not_physical=True,
        unresolved=['K35/NC20 full-hull interval where width exceeds1e-4','General value of E beyond this four-role single-seed panel',
                    'Full routing and loading coupling not represented by inventory-only completion'],
        audit=f'qualification/{audit_label}/result.json',independent_review='review/final_scientific_review.md')
    write(OUT/'candidate_decision.json',decision)
    body=f'''# Round154: target integer prices and independent proof floors

The signed state-product residual is a qualified interruptible pricing oracle.
Its product block is stronger than Cartesian aggregate McCormick, with the
hard-total limitation stated below. Actual signed directions do not establish
a general proof-cost advantage over normalized RN. The complete hull results
and the independently paid complete-method experiment are different objects.
E remains research-only; the stable GI-TBC entry and profile are retained.
In the same-PE NB35 comparison E preserves B's U and improves supported L by
{nb['E_minus_B_L']:.9f}; E's U is {nb['J_U']-nb['E_U']:.9f} below J's.
K35, RB35 and NC20 retain identical B/E endpoint bounds and certificate
statuses. This is finite positive proof-placement evidence with paid costs.

## Complete inventory hull, same original free Q

{hull}

The inherited numerical reference values are .39297895351863926 (NB35),
.2788644539329308 (K35) and .17476912471357817 (NC20). Bounds include the
entire original inventory support, hard total and physical Gupper. Every
new stock is validated at its exact declared coefficients. All accumulated
support rows are replayed with every original Q variable free. Qualified
RMP primals evaluate the last added columns; no final refresh obligation
remains. These upper bounds concern the strengthened LP value and are not
physical fleet incumbents. The finite-support LP upper is never substituted
for this full-hull upper. No accuracy target was relaxed beyond1e-4.

## Pricing tasks and targeted deepening

{pricing}

The first K saved near-optimal task had direct room near the inherited RMP
upper. The strengthened3600s price produced raw lower .06825209584795439,
below inherited same-direction .07003842216867079, and a true stock reducing
the individual certificate ceiling to .2861237647323068. This rejects the
old target, so the scheduled identical RN long target was skipped. It is
not a matched-long speed comparison. NC's original fresh direction was also
rejected by a true inventory. These counterexamples supply columns; none
is a full-hull upper or a rejection of the inventory hull itself.

The next stage uses a saved complete RMP upper minus1e-4 as the target,
updates directions against all current stocks and saves every Q certificate
before pricing. A verified original stock below tau terminates that task;
a qualified bound reaching tau proves it. Selection time limits give no
bound. A uniformly applied fallback uses the already optimal current RMP
basic dual and still requires full-Q residual qualification. The failed
initial K selection is preserved, not counted as a pricing result. NC's
updated saved direction also receives a midpoint proof task at hull
.18659477577615025, below its updated true-stock ceiling .18863295659503387.
Its matched goal-directed trials use identical starting stocks, target,
scope, coefficients, platform, Seed0 and Threads1. Long trials are omitted
only after the declared target has already been proved or disproved.
The per-iteration report records outcomes and costs. Prices from different
directions are never concatenated into a monotone convergence trajectory.

## Integer equivalence and attribution

For positive S, R_tau=S(p−tau) equals the maximum of the floor and Gini
residual branches. Complete one-hot products z_iy=S*x_iy, all four binary
product rows and station mass identities give W=S*D at integer states.
Absolute-value epigraphs preserve every legal stock, and beta>=0 prevents
nonminimal auxiliary A from creating a lower true price. q may be negative;
legal zero stock is separate. Beta=0 removes no resource or Gupper row.

The state lift implies all four aggregate McCormick rows on Cartesian
station cost bounds, including signed potentials. The two-station strict
product example and hard-total counterexample in mathematical_analysis.md
state the precise boundary. This is not a complete-Q or RN dominance
theorem. The single stronger model adds conditional denominator bounds,
total-resource products and products using hard-total DP cost bounds.

Written residual coefficients on nonnegative activities are rounded
downward; the physical G cap is outward. The saved guard is in residual
units. A guarded lower ell converts to tau+ell/u when ell>=0 and tau+ell/l
when ell<0. Zero is combined by minimum, whole-domain DP and qualified
same-direction information by maximum. Every MIPSOL stop reevaluates true
resources/G/price. Native status alone is never a certificate. Finite tests
include signed rounding, negative residuals, nonminimal completion and actual
statuses2/11/15 plus unsupported fallback. The23 goal-stop fixtures pass.

The residual identity follows classical fractional parameterization;
McCormick, Dantzig–Wolfe and proof ledgers are established techniques.
See mathematical_analysis.md for primary references, derivations and exact
source/transport rules. Historical PR58, existing SP/cross-multiplication,
R104/139/144/145 and the substantial R153 exploration are explicitly
inherited. The inherited169-row41/1080 example is fixed-marginal, not a new
strict complete-routing witness. Compatible common inventory distributions
already exist at all three reference marginals; incompatibility or observed
unary penalty slack is not the explanation used here.

## Independent complete-method placement experiment

{complete}

All nine arms use the same matched PE and independent own-H (seed20260626),
Gurobi Seed0/Threads1. NB35 B/E/J and K35/RB35 B/E have2400s caps; NC20 B/E
have1200s caps. RB35 retains lambda=.055125275219827186,T=4800. All own-H,
helper, model construction, producer and verification costs use the existing outer
accounting. No cross-arm H, stock, incumbent or historical floor is supplied.
The own-floor producer is unchanged from R153 J (4096 nodes, price absolute
gap1e-4). J writes a formal total-objective floor row. E consumes the same
scoped floor only in the proof scheduler, retaining raw Native/LP/AM search
inputs and no formal floor row. A same-domain formal-model comparison and
first AM records support that placement distinction. They cannot isolate
AM as the sole cause of any U difference. Paid time and legal proof pruning
can change subsequent trajectories.

Covered leaves use max(raw_L,min(U0,floor)); the frontier proof lower is
their minimum. Uncovered leaves retain their original bounds. Source scope,
cutoff complement, complete root coverage and descendant restrictions are
checked. A rejected source retains B information. NB35 same-PE J has
U={nb['J_U']:.12f}, L={nb['J_L']:.12f}; the complete pair/mechanism tables retain
the direct placement comparison. Open arms have no T_cert. Detailed U/L/gap,
T_produce/T_verify/T_total/T_cert are in reports/complete_pairs.json.

## Cost, failures and reproducibility

Current closed outer G1 is {cost['budget']['G1_seconds']:.6f}s, below144000s;
compilation is separately reported ({cost['budget']['separately_reported_seconds']:.6f}s).
No nested Runtime/Work/helper/own-H is charged twice. Necessary final audit
and failed attempts are included. Pure theory, writing and public I/O are
separate. Prelaunch hashes, source snapshots and history bookkeeping are
not fully wall-clocked; this is not a complete elapsed-work accounting.
There are {len(failed)} nonzero-exit metered receipts, all preserved with
stderr and source-byte snapshots. They include the initial conditional-S
qualification interpretation, NC ingest path formatting and K stabilization
selection failure, where present. Metadata correction and a pre-restore
writer syntax failure are also retained and never recast as solver evidence.

Production source d834d62c7a1be599867db04a427f1d43dd3631cb matches PE
0d3a94183285cc2794676c717a23dc75a47c872ad48c26d2237dd8634f1a5a01;
DLL9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88.
source_manifest.json binds frozen helpers and per-run source bytes. Raw
science/failures and the necessary PE/DLL stay local. New-only public
carriers reference the fixed R153 science/member hashes instead of
repacking its old4.7GB evidence. Fixed-commit anonymous recovery and
post-PR bounded cleanup are recorded separately; no performance rerun is
part of recovery. The temporary PR base is verified again at delivery.

## Finite conclusion and next research decision

{route} The data establish neither universal residual dominance nor a
general complete-method advantage for E. The limits of this finite stage
are signed-direction proof hardness, the remaining reported hull intervals,
the four-role single-seed panel and full routing/loading restrictions beyond
inventory completion. Do not launch the same direction/partition/CDF/flow
grid automatically. Any next inventory experiment must identify a new
observed structural bottleneck and a concrete proof/value threshold.

The independent final nonimplementer review covers actual math, matrices,
scope, identities, fees, failures and manuscript claims. Its disposition
and the publication/cleanup readback are in review/ and RESUME.md.
'''
    (OUT/'final_report.md').write_text(body,encoding='utf-8')
    tex=r'''\section{Target integer pricing and independent proof bounds}
We retain the complete free routing relaxation $Q$ and every original legal
inventory state. Let $S=\sum_i c_iY_i>0$, $A=\sum_{i<j}|c_iY_i-c_jY_j|$,
$f=\max\{\gamma_L,A/(nS)\}$, $D=\sum_i d_i(Y_i)$ and $p=\beta f+D$.
Classical fractional parameterization gives
\[
R_\tau=S(p-\tau)=\max\{S(\beta\gamma_L+D-\tau),\beta A/n+S(D-\tau)\}.
\]
We use no continuous convergence guarantee. With complete one-hot states,
four binary-product inequalities and $\sum_y z_{iy}=S$ impose
$z_{iy}=Sx_{iy}$ at integer points, including signed state potentials.
The epigraph permits negative residuals. Legal zero inventory is evaluated
separately; hard totals and the physical Gini cap remain when $\beta=0$.

On Cartesian station-cost bounds the state-product block implies the four
aggregate McCormick inequalities, with a strict two-station example.
It does not automatically imply products from tighter hard-total cost
bounds, nor does it dominate the complete normalized pricing formulation.
Our strengthened variant retains valid total-resource products, conditional
denominator bounds and hard-total DP cost products. Written coefficients,
outward transport and the Native numerical guard are saved explicitly.
A qualified residual lower $\ell$ gives price lower
$\tau+\ell/u$ for $\ell\ge0$ and $\tau+\ell/l$ otherwise.

For a certified $Q$ residual $C_Q$, true-column intercept $a_K$ and qualified
full-domain price lower $L_m$, the hull lower is
$C_Q+\min\{a_K,L_m\}$. A true stock price upper only limits this individual
certificate; it is not a full-hull upper. Verified stocks below the target
terminate that proof task and enter the complete column pool. Each new
direction, certificate and target is frozen before pricing. All supports
are replayed in the complete free $Q$, and the final columns are evaluated
by a qualified complete RMP primal. RMP uppers are LP-value bounds, not
physical routing incumbents. Table data are in reports/scientific_table.csv
and reports/pricing_results.csv.

The separate candidate E pays the same own-root producer as the previous
row candidate J, but uses its floor in the scoped proof ledger. Native rows,
raw LP bounds, ordering and adaptive-mass inputs remain the base inputs on
the same domain. Covered leaves use $\max\{L_j,\min(U_0,\ell_j)\}$, with
the cutoff complement and coverage checked before taking the frontier
minimum. Nine same-PE independent-own-H arms compare B/E in four roles and
B/E/J for NB35. Their full outcomes and timing are recorded in
reports/complete_pairs.csv; no causal claim assigns all trajectory changes
to adaptive-mass decisions. Open runs have no certificate time.

The finite data support a qualified research oracle and a research-only
proof-placement candidate. Stable GI-TBC remains the algorithmic reference.
We make no universal formulation dominance, pricing speed, fleet-performance
or journal-tier claim. The inherited $\Theta=H+\Gamma$ decomposition,
compatible reference marginals and fixed-marginal $41/1080$ strict example
retain their original scope. Exact equations, citations, actual numerical
tables, failures, source identities and independent review accompany this
section in the Round154 evidence packet.
'''
    tex+='\n\\begin{table}[ht]\n\\centering\n\\begin{tabular}{lrrr}\nDomain & Hull lower & Hull upper & Width \\\\ \\hline\n'
    for r in science:
        tex+=f"{r['role']} & {r['lower']:.9f} & {r['upper']:.9f} & {r['width']:.9f}"+' \\\\\n'
    tex+='\\end{tabular}\n\\caption{Complete inventory hull in the same free $Q$. Uppers are qualified numerical LP-value bounds.}\n\\end{table}\n'
    tex+='\n\\begin{table}[ht]\n\\centering\n\\begin{tabular}{llrrr}\nRole & Method & Own feasible $U$ & Supported $L$ & Absolute gap \\\\ \\hline\n'
    for r in pairs:
        for method in ['B','E','J']:
            if method+'_U' not in r:continue
            tex+=f"{r['role']} & {method} & {r[method+'_U']:.9f} & {r[method+'_L']:.9f} & {r[method+'_gap']:.9f}"+' \\\\\n'
    tex+='\\end{tabular}\n\\caption{Nine same-PE independent-own-H complete arms, Seed0/Threads1. Caps2400s except NC20 at1200s.}\n\\end{table}\n'
    (OUT/'manuscript.tex').write_text(tex,encoding='utf-8')
    (ROOT/'docs/round154_research.md').write_text('''# Round154 research evidence

The [final report](../results/unified_exact_round154/final_report.md) records
signed state-product target pricing against the complete inherited Q and
an independent same-producer proof-placement candidate E. Read its
[mathematical account](../results/unified_exact_round154/mathematical_analysis.md),
[hull table](../results/unified_exact_round154/reports/scientific_table.csv),
[complete pairs](../results/unified_exact_round154/reports/complete_pairs.csv),
[decision](../results/unified_exact_round154/candidate_decision.json),
[paper insertion](../results/unified_exact_round154/manuscript.tex),
[independent final review](../results/unified_exact_round154/review/final_scientific_review.md)
and [publication/continuation record](../results/unified_exact_round154/RESUME.md).

The residual is a qualified research oracle; product-block strength is not
a normalized-RN dominance theorem. LP-value uppers and individual price
ceilings have distinct meanings. E and the old J remain research-only and
default OFF. Stable GI-TBC retains its original entry and profile. Nine
same-PE arms use independent own-H; the finite evidence does not authorize
an instance-conditioned hybrid or a universal performance claim. New-only
carriers and the fixed R153 member references support bounded recovery
without old producers, compilation or performance reruns.
''',encoding='utf-8')
    print(json.dumps(dict(written=['final_report.md','candidate_decision.json','manuscript.tex','docs/round154_research.md'],G1=cost['budget']['G1_seconds'])),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
