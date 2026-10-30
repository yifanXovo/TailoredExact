"""Independent research appendix; compile only after timed work is idle."""
from round141_common import *
from round141_analyze import require_idle
from round141_report import table,selected,LABELS
import inspect,shutil

SHORT={'K-15-S':'K15','K-20-S':'K20','K-35-U':'K35','R-B35-S-T2':'RB35-T2',
    'R-X20-S-T1':'RX20-T1','R-B35-S-T1':'RB35-T1','R-X35-S-T1':'RX35-T1','R-X35-S-T2':'RX35-T2'}

def assemble():
    require_idle();assert read(OUT/'PDF_marker.json')['success']
    decision=read(OUT/'candidate_decision.json');assert decision['study_complete']
    full,new,refs,ordered=selected();lp=read(OUT/'reports/LP.json');b=budget()
    body=r'''# Conditional objective bounds from physical threshold counts

Round141 independent research appendix, 30 October 2026. This section extends
the maintained Round137 inventory-Gini routing manuscript and the
Round138-Round140 research increments. The complete model, physical objective
and stable GI-TBC method are retained. The study asks whether a station-count
axis supplies information beyond the original Gini axis, and whether qualified
conditional information improves a complete method. It is a finite study of
known research configurations, not an independent validation set.

## 1. Integer count domains and conditional numerator chords

Only stations are counted. For actual finite inventory support
\(\mathcal Y_i\), let \(\sum_y s_{iy}=1\),
\(Y_i=\sum_y y s_{iy}\), and \(r_i=c_iY_i\). The positive distinct supported
ratios form \(0=t_0<t_1<\cdots<t_M\), with
\(\Delta_j=t_j-t_{j-1}\). Define

\[
 K_j=\sum_i\sum_{y:c_iy\ge t_j}s_{iy},\qquad
 A=\sum_{i<l}|r_i-r_l|.
\]

For integer selectors, each threshold separates exactly
\(K_j(n-K_j)\) station pairs. Summing their threshold lengths proves

\[
 A=\sum_j\Delta_jK_j(n-K_j).
\]

```{=latex}
\Needspace{7\baselineskip}
```

Round140 obtains valid integer ranges \(\ell_j\le K_j\le u_j\) from actual
supports and the physical inventory budgets
\(\max\{0,B-\sum_kQ_k\}\le\sum_iY_i\le B\).
For the inherited numerator epigraph \(H_\Sigma\), TC2 retains the old TC row
and adds the concave chord

\[
 H_\Sigma\ge\sum_j\Delta_j[(n-\ell_j-u_j)K_j+\ell_ju_j].
\]

The remainder of one term is
\((K_j-\ell_j)(u_j-K_j)\). It measures chord slack, not complete-model
objective error. Choose \(\ell_j\le m<u_j\) and partition a physical parent
domain into \(D_0=D\cap\{K_j\le m\}\) and
\(D_1=D\cap\{K_j\ge m+1\}\). Integer counts make this a mutually exclusive
complete cover. The sides are not two Gini intervals.

Nested threshold counts imply the zero-Optimize propagation

\[
 D_0:\ u_h'\leftarrow\min(u_h,m)\ (h\ge j),\qquad
 D_1:\ \ell_h'\leftarrow\max(\ell_h,m+1)\ (h\le j).
\]

Each restricted model appends the resulting conditional TC2 aggregate.
Parent TC and TC2 remain. Integer-valid ranges need not already constrain
every fractional parent point, so replacement would not justify unconditional
LP dominance. Incompatible intervals are not clipped into a valid range.
If \(d=u_j-\ell_j\) and \(m=\ell_j+\lfloor d/2\rfloor\), each child width
is at most \(\lfloor d/2\rfloor\). The selected term's continuous worst
remainder decreases from \(\Delta_jd^2/4\) to at most
\(\Delta_jd^2/16\). This is not a fourfold BRP bound or speed theorem.

## 2. Qualified side floors and a scalar disjunction

Suppose a qualified relaxation of side \(D_i\), intersected with the
improvement cutoff \(F\le c_i\), gives lower bound \(\lambda_i\). Use
\(\beta_i\le\min\{\lambda_i,c_i\}\), with the inherited fixed numerical
margin and downward arithmetic. A physical solution below the cutoff has a
legal extension to this model; one above the cutoff already has
\(F\ge c_i\). This proves the floor on the entire corresponding physical
side within its source support/domain. Qualified infeasibility below the
cutoff may supply its conservative cutoff floor. It does not prove that the
whole physical side is empty, delete that side, or fix a binary. Unqualified
returns do not supply new floors. An incomplete pair keeps ordinary valid
parent information unless a source rejection requires the existing fail-closed
disposition. The complete count-cover floor is \(\min\{\beta_0,\beta_1\}\).

One binary \(b\) links the physical count to the two sides:

\[
 K_j\le m+(u_j-m)b,\qquad
 K_j\ge\ell_j+(m+1-\ell_j)b.
\]

The complete linear objective, including ObjCon, receives

\[
 \mathrm{D1}:\quad F\ge\beta_0+(\beta_1-\beta_0)b.
\]

D0 independently pays the same selection and proofs and keeps both links
and the binary, replacing only this row by
\(F\ge\min\{\beta_0,\beta_1\}\). Each physical integer improvement solution
in the source support/domain chooses its unique side from inventory \(Y\), not from a virtual auxiliary
Gini value. Both signs of the floor difference and nonzero ObjCon receive
directed endpoint guards. The serialized endpoints do not exceed the
qualified floors; outward rounding can weaken the ideal scalar formula.

For fixed \(K\in[\ell,u]\), feasible fractional binary values satisfy

\[
 \max\{0,(K-m)/(u-m)\}\le b\le
 \min\{1,(K-\ell)/(m+1-\ell)\}.
\]

When \(\beta_1\ge\beta_0\), eliminating \(b\) gives
\(F\ge\beta_0\) and
\(F\ge\beta_0+(\beta_1-\beta_0)(K-m)/(u-m)\).
In the reverse case it gives \(F\ge\beta_1\) and
\(F\ge\beta_1+(\beta_0-\beta_1)(m+1-K)/(m+1-\ell)\).
Together with the count interval, these describe the convex hull of the two
scalar interval epigraphs \([\ell,m]\times[\beta_0,\infty)\) and
\([m+1,u]\times[\beta_1,\infty)\). This is a standard disjunctive device
[@Balas1998R138], not the full BRP hull.

For \((\ell,u,m,\beta_0,\beta_1)=(0,4,1,0,2)\), the scalar point
\((K,F,b)=(2,0,1/3)\) satisfies D0 and violates D1. The point
\((2,1,1/2)\) satisfies continuous D1 but admits no binary D1 extension.
These are scalar witnesses only. A chosen-b violation is not a projection
separation test; all feasible fractional binary values must be considered.

## 3. Matched continuous evidence

Five saved-point scores reproduce the supplied goal without new Optimize.
Three domains enter 39 new continuous solves: three parent controls, 24
plain/conditional count children, six common-source D0/D1 roots and six fully
rebuilt Gini-midpoint children. All use explicit Seed0, one thread and serial
timing. Ordinary MPS is serialized, hashed and read back before Optimize.
These are numerical LP optima, not rational certificates or Native MIP root
bounds. Offline diagnostic sources never enter a complete method.

K35's physical threshold is \(\frac{9700060735874915}{9007199254740992}\); the other
two use \(\frac{18014398509481983}{18014398509481984}\). The latter is close to one but
cannot be replaced by decimal one. Count/D0/D1 comparisons fix the source
objective, support, Gini interval and actual serialized cutoff. The Gini
comparison instead verifies an identical full parent, then rebuilds its
actual restricted children, including their support and product rows.

The threshold maximizes the weighted chord remainder; the smaller physical
threshold breaks a tie. Explicit count-range violations precede that score.
Balanced and LP-floor pivots are compared. LP-floor has the stronger
conditional cover in all three domains and is frozen as the uniform online
rule. Online scoring uses long double; threshold membership and dyadic
coefficient arithmetic are exact. It is not an exact-rational online score
ordering claim. The following first table uses raw optimal values.

'''
    chosen=[r for r in lp['rows'] if r['selected_for_projection']]
    balanced={r['role']:r for r in lp['rows'] if r['pivot_kind']=='balanced'}
    body+=table(['Role','Parent L','Plain LP-floor cover','Conditional balanced','Conditional LP-floor'],[
        [SHORT[r['role']],r['parent_L'],r['plain_raw_cover'],balanced[r['role']]['conditional_raw_cover'],r['conditional_raw_cover']] for r in chosen])
    body+='A balanced plain side retains the saved parent optimum. K35\'s plain differences at roughly 1e-7 are numerical scale, not substantive gains. The LP-floor integer gap can give small plain gains on RB/K20, while conditional chords produce the larger increments. All qualified covers below use the same conservative floor policy.\n\n'
    body+=table(['Role','Count conditional cover','Gini midpoint cover','Difference'],[
        [SHORT[r['role']],r['conditional_cover'],r['gini_cover'],r['conditional_cover']-r['gini_cover']] for r in chosen])
    body+='This establishes finite new count-axis information beyond the matched midpoint, not dominance over every Gini pivot or domain. D0 and D1 next use exactly the same two qualified side floors.\n\n'
    body+=table(['Role','beta0','beta1','D0 optimum','D1 optimum','Projection violation'],[
        [SHORT[r['role']],r['beta0'],r['beta1'],r['D0_L'],r['D1_L'],r['projection_violation']] for r in lp['projection']])
    body+='D1 separates two actual D0 optima after minimizing over fractional b, but admits other points with the same objective; no reoptimized common-root objective gain is observed. Both floors are already below the carrier\'s observed Native early bounds (approximately .44698 for K20, .15862 for RB35-T2, and .26602 for K35). That limits expected direct bound value, without proving global redundancy across different Native paths. The cover/projection evidence and small probe cost justify the finite pilot.\n\n'
    body+='## 4. Complete methods and attribution\n\n'
    body+='The uniform carrier is BOTH stock + old TC + TC2. Every new method pays complete own H (seed20260626), normal root/lookahead, construction, two count proofs, validation and Native search. Gurobi Seed0 is explicit for primary solves; any limited Seed1 keeps its registered identity. Threads1, affinity4, M-B/VD-P, pair-only, AM=.08, depth8, minimum width1e-4 and AP off remain common. K roles retain lambda=.15; resource roles retain rho=1 and the frozen binary64 lambda=1/Omega. Physical T is separate from experimental cap.\n\n'
    panels=[g['launch'] for g in read(OUT/'pilot_matrix.json')['groups']]
    body+=table(['Role','Stations / vehicles','Physical T s','lambda','Cap s'],[
        [SHORT[l['id']],str(l['panel']['V'])+' / '+str(l['panel']['M']),l['panel']['T_seconds'],l['panel']['lambda'],l['cap_seconds']] for l in panels])
    body+=decision['complete_discussion']+'\n\n'
    body+=table(['Role','Method','Seed','Verified U','Supported L','T_cert s'],[
        [SHORT[r['role']],LABELS[r['method']],r.get('seed',0),r['U'],r['L'],r['T_cert'] if r['T_cert'] is not None else 'open'] for r in ordered])
    body+='Open certificate times remain null; no cap is imputed as convergence. Historical references preserve actual original source/PE and complete clocks, pinned to accepted R140 science and its dependencies. They are not same-PE causal interventions. The actual panel and missing TC2 cells are not enlarged by inference. Both-certificate timing uses the inherited substantive threshold max(10 s, 10% of the smaller clock).\n\n'
    body+=decision['conditional_discussion']+'\n\n'
    body+=table(['Role','D1-D0 U','D1-D0 L','D1-D0 produce s','D1-D0 total s'],[
        [SHORT[r['role']],r['delta_U'],r['delta_L'],r['delta_T_produce'],r['delta_T_total']] for r in full['conditional_pairs']])
    body+='For exposed pairs, root/probe matrices and floors match exactly. The actual first integer models are also identical after removing only the verified objective-floor row. This distinguishes D1\'s conditional value from D0\'s count links/common floor, while D0 versus TC2 measures their combined change.\n\n'
    body+=decision['mechanism_discussion']+'\n\n'
    body+=table(['Role','Mode/Seed','Produce s','Verify s','Total s','Relative gap'],[
        [SHORT[r['role']],r['method']+'/'+str(r['seed']),r['T_produce'],r['T_verify'],r['T_total'],r['relative_gap']] for r in new])
    body+='These are every new formal position; cap90 qualifications are separate. Full-precision U/L, signed gaps, Native returned ObjVal/ObjBoundC versus external merged L, root/probe/target/terminal times, Work, nodes and controls remain in the CSV/JSON authorities. Later independent reviews and supplemental chain checks are separate costs. Rounded logs do not establish exact physical-incumbent discovery clocks.\n\n'
    if (OUT/'figures/pilot_endpoints.png').exists():
        body+='![Initial four-role Seed0 pilot. Bars span supported L to verified U; they are not confidence intervals. Historical references retain their original identities. The complete tables include every entered position.](figures/pilot_endpoints.png)\n\n'
    body+='## 5. Implementation scope, history and decision\n\n'
    body+='One root selection uses formal selector fields from the already required LP, not an observational CSV or extra duplicate Optimize. The two canonical count requests are independent local proofs, not scheduler children. Count settings survive parameter readback; independently verified final inventory determines witness side. A single side never becomes global/Gini-cover evidence. Source rejection invalidates dependent use under the inherited fail-closed policy. Later artifacts may inherit the pair only with the same input, contained Gini interval, nonexpanded cutoff and supported-inventory subsets, remapping the frozen physical threshold. Start b is computed from physical inventory. Original probe types are restored then each probe is immediately discarded. Default BranchPriority remains zero, without a custom branching callback or unobserved branching-on-b claim.\n\n'
    body+='Finite tests cover both signs, nonzero ObjCon, both physical Start sides, same/opposite-side witnesses, source revocation, invalid scope, default-off reset, one contained successor and actual Native row/type reads. The first cap90 v5 producer failed the required disposable-probe type-restoration lifecycle check; raw/cost are retained outside performance. V6 fixes that lifecycle, followed by two healthy qualifications. Pure-reader corrections never rerun a sealed healthy producer. The controlled hybrid production build and final targeted repair retain their actual source/PE lineage.\n\n'
    body+='R50/R51 studied variable-family priorities and sparse probing; R62 used single-station thresholds, R88 two-site CDF envelopes, and R120-R122 already used one-binary Gini-axis objective floors with mixed outcomes. The distinction here is an all-station physical count axis, integer gap, nested propagation and conditional numerator chord. McCormick/RLT and disjunctive constructions remain standard tools [@mccormick1976; @AdamsSherali1990R138; @Balas1998R138].\n\n'
    body+='The supplied same-objective R138 K35 numerical return-bound witness supersedes R140\'s prior priority suggestion. It has R\'=(6.306613194,5.773547225,18.919839581), satisfies both stated return upper bounds with about 1.82e-12 maximum residual, and retains its full packet identity in the mathematical note. This is neither a general heterogeneous-vehicle symmetry theorem nor a rational optimality certificate, and is not a new Round141 Optimize or repeated replay. No return-product full benchmark is opened.\n\n'
    body+=decision['conditional_work_discussion']+'\n\n'+decision['decision_paragraph']+'\n\n'+decision['remaining_question']+'\n\n'
    body+='## 6. Cost and reproducibility\n\n'
    body+=f'New charged experimental computation is {b["G1_seconds"]:.6f} s ({b["G1_seconds"]/3600:.6f} h), within 36000 s. Qualification and failed experimental attempts count. Complete experimental outers including postverification are also checked against the ceiling; builds, pure analysis, documents and public I/O are separately measured. Nested H/LP/MIP/Work is not charged twice. Old references keep their original clocks with zero new Optimize. Interactive reading/editing receives no invented precision.\n\n'
    body+='The source/PE/DLL, inputs, configurations, exact physical/objective parameters, canonical matrices and helper identities are bound by manifests and frozen batches. Stable R137 and the R138-R140 entry/profile bytes remain unchanged. The separate count-proof switch defaults off. Local scientific validation, once-only new-carrier public byte/member readability and final Draft-PR/cleanup receipts are distinct facts. Public reading performs no Optimize, build or commercial Native load. All new assets remain under ExactEBRP-work; original user content and old rounds are protected.\n'
    (OUT/'manuscript.md').write_text(body,encoding='utf-8',newline='\n')
    shutil.copyfile(ROOT/'results/unified_exact_round138/references.bib',OUT/'references.bib')
    write(OUT/'document_assembly.json',dict(UTC=utc(),manuscript_SHA=sha(OUT/'manuscript.md'),
        references_SHA=sha(OUT/'references.bib'),Optimize=0,inherited_manuscripts_unchanged=True,
        lineage='Independent Round141 research appendix extending retained R137/R138/R139/R140 material'))

def pdf():
    require_idle();assert read(OUT/'PDF_marker.json')['success']
    import round138_documents as old
    source=inspect.getsource(old.pdf).replace('date=29 October 2026','date=30 October 2026').replace(
        'Round138 standalone increment: manuscript.md assembled from mathematical_analysis.md and qualified reports/decision; references.bib and three scientific figures',
        'Round141 independent appendix: count-domain mathematics, matched LP/full evidence, history and decision; references and endpoint figure')
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,read=read,write=write,budget=budget,environment=environment)
    exec(compile(source,__file__+'::accepted_increment_export','exec'),ns);ns['pdf']()

if __name__=='__main__':globals()[sys.argv[1]]()
