# Reciprocal normalization of the Gini block

Round143 retains the stable R137 GI-TBC route, operation, inventory and selector
structure. The research question is whether a second, normalized use of the same
inventory selectors supplies useful information beyond the old shared-g
products. The objective remains the original \(g+\lambda P\). The penalty is
never multiplied by the reciprocal variable. RN is an intersection with the
old model, with its original integer constraints and stable cuts retained.

## Exact integer extension and compact implementation

Use the actual binary64 coefficient \(c_i\) loaded in the old row \(r_i=c_iY_i\).
Let \(S=\sum_i c_iY_i\) and \(A=\sum_{i<j}|c_iY_i-c_jY_j|\). On a full model
scope with \(0<S_L\le S\le S_U\), put \(L_t=1/S_U\) and \(U_t=1/S_L\), rounded
outward. For the existing station states, RN adds continuous
\(t,w,\widehat Y,\widehat h\):

\[
 L_t\le t\le U_t,\quad L_t s_{iy}\le w_{iy}\le U_t s_{iy},\quad
 \sum_y w_{iy}=t,\quad \widehat Y_i=\sum_y y w_{iy},
\]
\[
 \sum_i c_i\widehat Y_i=1,\quad
 \widehat h_{ij}\ge\pm(c_i\widehat Y_i-c_j\widehat Y_j),\quad
 \sum_{i<j}\widehat h_{ij}\le n g.
\]

All new columns are continuous and nonnegative. The product facets
\(w\ge t-U_t(1-s)\) and \(w\le t-L_t(1-s)\) follow from the station mass equality,
\(\sum_y s_{iy}=1\), and the other states' upper/lower bounds. Omitting them is therefore
an exact compact implementation of RN1. No old state_g, zprod or h column is
reused: they have different physical units.

At integer selectors, every unselected \(w\) is zero and the selected \(w=t\).
Hence \(\widehat Y=tY\) and normalization gives \(tS=1\). The new Gini row says
\(g\ge A/(nS)\). Conversely, any original integer feasible point with \(S>0\)
and any legal epigraph \(g\ge A/(nS)\) extends by \(t=1/S\), \(w=ts\),
\(\widehat Y=tY\), \(\widehat h_{ij}=t|c_iY_i-c_jY_j|\). The original
model \(g\) is retained even when it exceeds physical \(G\); its current g interval
must still be respected. This extension proof does not authorize a physical
MIP Start whose true G lies outside that interval.

Thus RN preserves the original integer problem and its old-space projection
is contained in the old continuous relaxation. Containment alone proves
neither a strict optimum gain nor faster complete search.

The production writer adds two finite caps with the same old-space projection.
\(\widehat Y_i\le M_iU_t\) follows from nonnegative \(w\) and \(\sum_yw_{iy}=t\).
Since \(v_i=c_i\widehat Y_i\ge0\) and \(\sum_i v_i=1\), the minimum necessary
\(\widehat h_{ij}=|v_i-v_j|\) is at most one. Any feasible RN extension can
reduce each \(\widehat h\) to that minimum without changing an old column or
violating the Gini upper row; \(\widehat h_{ij}\le1\) is therefore redundant in the
projection. These finite caps permit the established full-matrix/Start reader
to remain unchanged. They are not an extra integer-count strengthening.

## Full-scope denominator bounds and numerical transport

Empty departure, loaded return and conservation imply
\(B^-=\max(0,B-\sum_kQ_k)\le\tau=\sum_iY_i\le B\), with
\(B=\sum_i b_i\) excluding the depot.
Cumulative pickups are not bounded by fleet capacity. For actual supported
endpoints \(m_i,M_i\), set \(\tau_L=\max(B^-,\sum_i m_i)\) and
\(\tau_U=\min(B,\sum_i M_i)\).
An incompatible interval follows the existing infeasible-domain route and is
never inverted.

Start from \(Y=m\). The minimum \(S\) fills \(\tau_L-\sum_i m_i\) inventory units
in ascending \(c_i\) order; the maximum fills \(\tau_U-\sum_i m_i\) in descending
\(c_i\) order. Positive coefficients make those total-inventory endpoints optimal. This continuous box-budget
problem relaxes support holes and all routing constraints, so its bounds are
valid for the full original scope without another Optimize or enumerating S.
No observed S, incumbent inventory or heuristic sample supplies a bound.

The diagnostic oracle uses Fraction values of actual loaded binary64 c_i.
Production reuses checked common-dyadic __int128 arithmetic from R140 for the
complete coefficient/inventory sums. It converts S_L downward and S_U upward,
then rounds each reciprocal outward. This covers accumulated summation error
before inversion. Checked arithmetic fails closed outside its representable
range. New row coefficients bypass the legacy near-zero/near-one formatter;
an exact positive power-of-two row scale, if necessary, preserves coefficients
that a Native LP parser would otherwise omit. No feasibility/optimality
tolerance is loosened.

Every model uses its own actual supported interval and physical budget. A
parent-valid bound would remain valid on a child, but a local bound is never
exported to a larger scope. The single applicability rule is a proved positive
full-scope S_L. If its lower bound is zero, RN contributes no rows or columns
and the old exact model and S=0 convention remain. The optional zero/positive
disjunction in the goal is not implemented: no evidence currently requires
that second controller.

## Strict separation and an explicit limitation

The exact three-station fixture has \(c=(1,1,1)\), support \(\{0,1\}\),
\(\tau\in[1,2]\), inventory-one selector masses \((1,1/2,0)\), old \(g=1/3\)
and inventory-one old g-products \((1/3,1/3,0)\).
\(H=2\), \(J=2/3\), \(\tau=3/2\) satisfy the declared old Gini,
stock, TC and TC2 blocks. Endpoint pair transport gives the same absolute
differences, and the penalty on this support is linear. This is a specified
relaxation subblock witness, not a fabricated full BRP instance.

RN has \(t\in[1/2,1]\), \(v=(t,1-t,0)\). The middle site's zero-state product is
\(2t-1\ge1/4\), so \(t\ge5/8\) and \(g\ge2t/3\ge5/12\). Equality is attained
at \(t=5/8\) with \(w=((0,5/8),(1/4,3/8),(5/8,0))\).
The strict separation is exactly \(1/12\).

For four stations with \(c_i=1\), support \(\{0,1\}\), fixed \(\tau=3\) and all
inventory-one masses \(3/4\), RN admits \(t=1/3\), \(w_1=1/4,w_0=1/12\) and
\(v_i=1/4\), hence \(g=0\). Old TC gives \(H\ge3\), fixed-inventory stock
gives \(J=3g\), and \(H\le4J\) implies \(g\ge1/4\).
RN alone does not dominate the retained integer-count information and does
not close the full R133 integer-objective mixture gap. This directly supports
the additive design; no replacement-model comparison grid is warranted.

## Twelve fixed-point checks and their scope

The original R140 carrier is bound by SHA256
`2cb1ab936753ce9ac26ae1f970b070b2751190af79f6a80a8b0f5d254902bf5f`.
The separately named supplemental offline ZIP was not present locally. The
portable checker therefore reconstructs all twelve checks from that original
carrier, without loading Native or rerunning any old optimization. These are
newly reconstructed certificates, not an assertion that the missing ZIP was
received. Some reconstructed rank/eta supports are stronger than the rounded
lower bounds stated in the goal; their actual identities are retained.

With selectors fixed, each station's attainable \(v_i\) at \(t\) is an interval
\([\ell_i(t),u_i(t)]\) obtained by exact fractional knapsack. Their endpoint
functions are piecewise linear. The complete feasible t interval satisfies
\(\sum_i\ell_i(t)\le1\le\sum_i u_i(t)\), together with all station product/mass
bounds. For any permutation rank vector \(a_i=2\operatorname{rank}_i-n-1\),
or a convex average at ties, and \(\eta\),

\[
 ng\ge\eta+\sum_i\min\{(a_i-\eta)\ell_i(t),(a_i-\eta)u_i(t)\}.
\]

The checker minimizes this expression at every endpoint and knapsack/
normalization breakpoint of the complete t interval. Six K35/RX20-T1 saved
points are excluded. Rank supports may be selected using a finite search, but
the final lower bound covers the whole interval exactly; unsuccessful sample
search is never an exclusion proof. For K20/RX35-T2, a constructive t and
water-filled attainable v give six extensions with original columns and
objective unchanged. The new columns and binary64 linear residuals are saved.

These checks interpret binary64 c and selector masses as rationals. The old
complete LP points are still numerical feasible optima under the inherited
policy, not rational full-matrix optimality certificates. A separated saved
point need not raise the reoptimized LP optimum; an extendable saved optimum
does not make RN redundant throughout the old model. The four separately
optimized matching LPs test the former question directly.

## Historical and literature position

R88 already developed pair-CDF/endpoint transport; R138 already established
the continuous selected-resource shared-factor hull application. Neither is
renamed as RN. R133's integer objective mixture issue remains a distinct
limitation. Earlier rejection of coarse denominator buckets, approximate
reciprocals and unproved scaling of all integer variables is not an experiment
on this retained-integer finite-selector construction. The R142 count-proof
continuation is closed; its CP/ALL controls are not inherited into the RN
candidate. R137 AM/no-strict-child is also left unchanged.

Reciprocal normalization is standard. Charnes and Cooper (1962) introduce the
linear-fractional change of variables and normalized denominator. Yue,
Guillen-Gosalbez and You (2013) combine that transformation with Glover
linearization for MILFP reformulations; their publisher abstract explicitly
identifies those ingredients. Chen and Hooker (2023), section 4.2 and the
appendix's Gini formulation, already give a normalized linear formulation of
the Gini criterion. Their double-pair normalization is equivalent to A/(nS)
here. The project contribution being tested is the exact connection to its
existing integer inventory/route structure, complementarity with prior
expressions, and complete computational value. No new general fractional
programming principle, full integer hull, or journal-level improvement is
claimed.

Primary sources checked on 1 November 2026:

- [Charnes and Cooper, 1962, DOI](https://doi.org/10.1002/nav.3800090303),
  and the CMU library scan's displayed transformation on p.182.
- [Yue et al., 2013, publisher abstract](https://aiche.onlinelibrary.wiley.com/doi/abs/10.1002/aic.14185).
  Full-text access was not needed or claimed for the above attribution.
- [Chen and Hooker, 2023, author manuscript](https://johnhooker.tepper.cmu.edu/equityGuideAOR3post.pdf),
  section 4.2 and Gini appendix, displayed manuscript pp.13 and 36-37;
  [published article](https://doi.org/10.1007/s10479-023-05264-y).


# Matched LP and complete-method results


RN supplies real complementary LP information, but the two priority same-PE Seed0 pairs do not show a sufficient complete-method benefit. Retain the uniform lift as research-only and stop full expansion this round; stable R137 GI-TBC remains the paper mainline.

RN supplements the old shared-g products with a common reciprocal t, normalized inventory and normalized pair differences. It keeps the original integer route/inventory structure and original penalty. Its integer extension and continuous inclusion are exact on a proved positive-denominator scope. The separate research switch defaults off. Stable R137 remains available.

## Matched continuous objectives

All four new LPs are numerical optima under unchanged 1e-6 feasibility/optimality qualification, explicit Gurobi Seed 0, Threads 1 and affinity mask 4, run serially. The original complete objective, cutoff, support, g interval and old matrix are retained. BASE gains include physical inventory information used for t bounds; TC+stock controls still show information beyond that older resource/count combination.

| Role | Old expression | Old L | RN L | Gain |
| --- | --- | --- | --- | --- |
| K35 | base | 0.200177662 | 0.228090497 | 0.027912835 |
| K35 | tc_stock | 0.218088779 | 0.228090497 | 0.0100017179 |
| RX20-T1 | base | 0.331594316 | 0.389761616 | 0.0581672999 |
| RX20-T1 | tc_stock | 0.37755753 | 0.394121979 | 0.0165644487 |

| Role / expression | Old g | RN g | Old weighted P | RN weighted P |
| --- | --- | --- | --- | --- |
| K35/base | 0.0386391834 | 0.0665520184 | 0.161538479 | 0.161538479 |
| K35/tc_stock | 0.0565503004 | 0.0665520184 | 0.161538479 | 0.161538479 |
| RX20-T1/base | 0.100712705 | 0.17210734 | 0.230881611 | 0.217654276 |
| RX20-T1/tc_stock | 0.14667592 | 0.173850507 | 0.230881611 | 0.220271472 |

| Role / expression | Added rows | Added columns | Added nonzeros | Build / solve s |
| --- | --- | --- | --- | --- |
| K35/base | 2340 | 1170 | 7474 | 1.7644687 / 0.5281877 |
| K35/tc_stock | 2340 | 1170 | 7474 | 1.8504794 / 1.6446136 |
| RX20-T1/base | 708 | 354 | 2232 | 0.4122916 / 0.0574667999 |
| RX20-T1/tc_stock | 708 | 354 | 2232 | 0.4220257 / 0.0796056001 |

Actual denominator bounds, reciprocal endpoints, complete row/column/nonzero counts, Runtime/Work, all quality measures and actual source/solution hashes are in reports/LP.json and LP.csv. These reoptimized full-objective gains are separate from saved-point exclusions. Four diagnostic Optimize calls were sufficient; no RN x TC2 x CP grid was opened.

## Complete same-PE methods

Each method pays for its own H (separate fixed seed 20260626), root/lookahead, online validation and complete Native proof search. The stable carrier is M-B/VD-P, pair-only, AM=.08, depth 8, minimum width 1e-4, AP off; stock, TC/TC2, count disjunction and CP are off. Each entered role receives its original full cap. Diagnostic/historical solutions or bounds are never injected.

| Role | Method | U | Supported L | Relative gap | T cert s |
| --- | --- | --- | --- | --- | --- |
| K35 | stable-off | 0.692854359 | 0.557158766 | 0.195850096 | open |
| K35 | RN | 0.681258498 | 0.542931774 | 0.203045869 | open |
| RX20-T1 | stable-off | 0.64532503 | 0.64532503 | 3.44e-16 | 22.206689 |
| RX20-T1 | RN | 0.64532503 | 0.64532503 | 1.24e-09 | 23.4901348 |

| Role / method | Produce s | Verify s | Total s | Splits |
| --- | --- | --- | --- | --- |
| K35/stable-off | 2371.14246 | 4.1181738 | 2375.26063 | 0 |
| K35/RN | 2371.10851 | 6.0289586 | 2377.13747 | 0 |
| RX20-T1/stable-off | 22.206689 | 1.1920446 | 23.3987336 | 0 |
| RX20-T1/RN | 23.4901348 | 1.4364241 | 24.9265589 | 0 |

| Same-PE role | RN - off U | RN - off L | Produce delta s | Total delta s |
| --- | --- | --- | --- | --- |
| K35 | -0.0115958603 | -0.0142269917 | -0.033952195 | 1.87683261 |
| RX20-T1 | 0 | -7.97e-10 | 1.28344575 | 1.52782525 |

K35 is a real tradeoff: RN lowers verified U by 0.0115958602505 but also lowers supported L by 0.0142269916815. Its signed gap grows from 0.135695592698 to 0.138326724129, and relative gap grows from 0.195850096067 to 0.203045869458. Both remain qualified-open after the full 2400-second caps. Producer time is essentially unchanged; RN adds 1.91078480007 seconds of verification and 1.87683260511 seconds to complete total. RX20-T1 certifies the same verified physical objective 0.645325030386 with both methods; RN raises producer/certificate time from 22.2066890239 to 23.4901347759 seconds and total from 23.3987336238 to 24.9265588757 seconds. The 7.97e-10 returned-L difference is within the inherited numerical policy and is not a substantive mathematical loss or gain.

Open T_cert is null, never the cap. Native returned ObjVal/ObjBoundC and externally merged supported L are separately retained. Root LP, AM decisions, outer splits, terminal nodes/Work and full Native logs explain observed outcomes without equating LP strength with search speed. One Seed does not identify a runtime distribution or attribute every difference directly to a new row.

All four formal positions have zero outer splits. Actual complete root bounds repeat the matched diagnostic improvements, but final Native cut/search behavior is different. K35 terminal nodes decrease from 16825 to 10779 while Work increases from 4691.00560053 to 4999.12908278. RX20-T1 nodes decrease from 2621 to 1620 while Work increases from 29.5418051573 to 34.9746070207. These are descriptive full-method effects, not a proof that fewer nodes mean less computation or that a specific added row caused every difference. Same-PE methods have matching complete own-H semantics and fleets; their full Native/H/Start/quality/lifecycle evidence is qualified.

## Qualifications, boundaries and cost

The three-station exact subblock separates 1/3 from 5/12; the four-station fixed-denominator example allows RN g=0 while retained TC+stock requires 1/4. RN is complementary and is not claimed to dominate the old count information or provide the complete integer objective hull. The original R140 carrier supplied twelve fixed-point checks with zero Optimize: six exclusions and six same-old-point extensions. The separately named offline ZIP was absent; reconstructed rank/eta certificates have their own identities and sometimes stronger bounds. They are not retroactively labeled as the missing old certificate bytes.

Production qualification includes exact dyadic full-scope bounds with directed conversion before reciprocal, actual c_i, zero-lower-bound omission, fixed-S and positive-S fixtures, nonminimal epigraph extensions, complete old/new Start values, preservation of the physical-G Start-domain rule, and actual Native reads of all new rows/coefficients/column types/bounds. K35 RN-off equals the inherited complete BASE matrix. All four affected units were recompiled; hybrid object/archive lineage and actual PE/DLL hashes are saved. Two new diagnostic failures occurred before Optimize, were repaired under new labels, and remain charged. Small offline constructor/search failures are separately recorded.

The conservative new experimental charge is **4880.559825 seconds (1.355711 hours)** of the 28800-second ceiling. This is the complete outer including qualification, failures and mandatory postverification, charged once. Nested H/LP/MIP/Work are nonadditive details. Build time is separately 37.893495 seconds; exact offline reconstruction, writing, independent review, PDF and public I/O are separate. Interactive editing/review does not receive invented timing precision.

The decision is RESEARCH_ONLY_STOP_FULL_EXPANSION_THIS_ROUND. Qualification and integer equivalence pass; nonpromotion follows the observed complete-method tradeoff and lack of proof-clock benefit, not a correctness failure. The code remains a separate uniform default-off research option. The tested result is not that RN is mathematically redundant, generally slower, or incapable of benefiting an untested instance.

No formal K20/RB35-T2 pair, optional K15/RX35-T2 pair or Seed1 is entered. K20 cap90 remains health-only; its saved-root extension is not a complete performance prediction. Other roles could characterize additional behavior, but there is no specific pending adoption/stop decision that their measurement would change after the priority hard-role support-bound regression and the second role's proof-clock result. Seed1 would not erase the retained adverse Seed0 result or establish a runtime distribution. Reopening requires a concrete new mechanism or decision-changing evidence, rather than a missing table. Stopping occurs with substantial budget remaining.

## Reproduction and delivery identity

Actual production source is `85bd2304866942fd5b397970c5ef4099bb1b73fb`; PE SHA256 is `eaa6dc5d0091a1f3a38a0374aeccab28e94bff94606339c62b385b48cb7d44b1`. DLL SHA256 is `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`. The carrier is stable R137 plus uniform RN, not R138-R142 mechanism stacking. Source/PE/helper/input/parameter matrices and actual returned calls are bound separately from later report metadata. The research entry is `scripts/paper_s2_rn.py`, profile `config/gi_tbc_rn_round143.json`, with `--rn on|off`; it expands only unless `--run` is explicit. `RESUME.md` describes safe continuation and the no-repeat rule.

The mathematical/history/literature note and independent reviews separate four evidence levels: standard construction and integer equivalence, strict subblock/saved-point relations, reoptimized LP gains, and complete algorithm performance. Existing R88/R133/R138/R140 results and Charnes-Cooper, Yue et al. and Chen-Hooker antecedents retain their identities. No new general fractional-programming principle or higher-journal claim follows.

The formal stable GI-TBC manuscript is retained. The increment and full reports retain all entered favorable/adverse positions; missing configurations are not inferred. Fixed-science carriers, anonymous public byte/member recovery and bounded current-round cleanup have separate receipts. All new assets stay under ExactEBRP-work, protecting the original user tree and old rounds. No merge or force push is authorized.

The standard antecedents are [@CharnesCooper1962; @Yue2013; @ChenHooker2023].
