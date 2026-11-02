# When direct Gini deviation rows help a complete algorithm

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

B, S, D and SD all retain stable GI-TBC; S enables BOTH STOCK and D enables the state-conditioned GD mechanism (at most two rows on an applicable domain). Every new arm pays for its own complete H (seed 20260626), all LP/MIP calls and mandatory physical, Start, model-scope, numerical-quality, lifecycle and R134 proof verification. Gurobi Seed=0, Threads=1, MIPThreads=1 and affinity=4; timed runs are serial. M-B/VD-P, pair-only, AM=.08, depth=8, minimum width=1e-4 and AP off remain fixed. Physical horizons, original lambda and process caps are bound in the matrices. No prior solution, cut or H state is injected into a new arm.

| Role | Method | U | Supported L | Gap % | T_cert s | T_total s |
|---|---|---|---|---|---|---|
| K20 | B | 0.716806546278 | 0.704791696972 | 1.676163 | — | 1221.994321 |
| K20 | S | 0.716806546278 | 0.716806546278 | 0.000000 | 94.2613895 | 96.93159066 |
| K20 | D | 0.716806546278 | 0.704202765473 | 1.758324 | — | 1205.656318 |
| K20 | SD | 0.716806546278 | 0.716806546278 | 0.000000 | 74.9164195 | 77.55368205 |
| RX20-T1 | B | 0.645325030386 | 0.645325030386 | 0.000000 | 22.3248979 | 23.67424096 |
| RX20-T1 | S | 0.645325030386 | 0.645325030386 | 0.000000 | 14.7557736 | 15.89297379 |
| RX20-T1 | D | 0.645325030386 | 0.645325030386 | 0.000000 | 24.6661437 | 26.34534032 |
| RX20-T1 | SD | 0.645325030386 | 0.645325027365 | 0.000000 | 12.0531594 | 13.65904567 |
| K35 | B | 0.692854358631 | 0.564290795837 | 18.555640 | — | 2374.92896 |
| K35 | D | 0.67117979642 | 0.552835648924 | 17.632257 | — | 2378.192407 |
| RB35-T2 | B | 0.344642625592 | 0.218985949603 | 36.459993 | — | 2375.143924 |
| RB35-T2 | S | 0.401200217839 | 0.229181599664 | 42.876003 | — | 2374.898921 |
| RB35-T2 | D | 0.33588358895 | 0.219475150151 | 34.657376 | — | 2378.839312 |
| RB35-T2 | SD | 0.377816983545 | 0.233498944436 | 38.197870 | — | 2379.922442 |

The table has seven new R147 arms (K20, RX20 and K35 B/D; RB35 D) and seven sealed same-PE R146 references (K20 and RX20 S/SD; RB35 B/S/SD). In particular, RB35 B is a cross-round sealed reference, while K20/RX20/K35 B are new R147 controls. References retain their original dates and fees; equal PE, input, objective, cap, resources and H semantics do not imply identical host load. Open T_cert values remain absent. No cap is substituted for convergence time, and the LP interaction is not applied to wall-clock certificates.

K20 B and D both return U=.7168065462777502 and remain open after their complete cap1200 windows. Supported L changes from .7047916969720031 to .7042027654726336; the relative gap increases from 1.676163% to 1.758324% (+.082160 percentage points). This is not a useful standalone certificate gain. The sealed same-PE S/SD cells certify the same U in 94.261389/74.916420s; their strong proof advantage is preserved as a real counterpoint. RB35 D instead returns U/L=.3358835889496765/.21947515015073324 against sealed same-PE B=.34464262559194814/.2189859496034747. U improves 2.5414838421%, L rises .0004892005473, and gap falls from 36.459993% to 34.657376% (-1.8026165231 percentage points). The L gain is small; the main independent benefit is physical incumbent quality. All four RB35 cells are open. D improves U and gap against SD but has lower L than SD's .23349894443616206, so it does not dominate the combination at both ends. Actual new D models have two GD rows and zero STOCK rows; the comparison is not inferred from method labels.

The committed physical-witness records locate the hard-role benefit in finding better incumbents, not certification. RB35 D already has U=.3372904684849699 at 668.391s, below B's eventual final U, and reaches its own final U at 1346.250s. B reaches its different final U at 2366.781s. K35 D first beats B's final U at 1338.656s with U=.6791034678575588; B reaches its final U at 1758.516s. D then has U=.6767988451958106 at 1686.187s and finds the final .671179796420249 at 2364.047s. That last improvement is near cap and is disclosed; the earlier strict gains establish that the benefit does not arise solely from the last seconds. Different-quality final-U discovery times are not convergence speedup ratios. K20 reaches the common final U at 224.546s for B and 417.765s for D. D's 16.338s lower complete total there is mainly a verification-cost decrease (49.467897 to 33.581330s), not faster proof. All 14 entered/reused formal cells have zero outer splits. Native root-after-cuts values, simplex, Work and node differences describe changed search but do not identify a unique cause. For example, K35's printed root bound rises .42856 to .44681 and root simplex increases 5188 to 11374, while final supported L is lower; stronger root information does not force stronger final proof.

R146's positive S→SD findings remain unchanged: K20 certifies about 20.52% sooner at the same U; RX20 retains certification with a small absolute 2.702614s certificate gain; RB35 improves U by 5.8283%, increases L by .004317345 and lowers gap by 4.6781 percentage points. Against BASE, that same SD pressure result had U higher by 9.6257%, L higher by .014512995 and gap larger by 1.7379 percentage points, a mixed tradeoff rather than two-end regression. RX20 SD's approximately 3.02e-9 positive U−L remains certified under the original R134 policy; no new floating-point repair or solve is introduced. R138's K15/K20 STOCK certificate benefits, its disclosed V2 transport identity in the finite Seed1 evidence, R144's RN-P K35 gains and R145's structural complementarity/root-retention results remain at their original versions. The Seed1 history is not a pure seed-only intervention, and no universal STOCK regression law is inferred. The strong historical RN-P K35 incumbent remains a research reference; no new matched RN-P bridge or claim of D beating every research variant is made. Fixed-domain K20 LP interaction remains a numerical fact, not complete-search synergy or general supermodularity.

**Uniform decision: Standalone GD (D).** Recommend standalone GD (D) as one uniform paper-enhancement candidate for author review. Against controlled stable BASE, it improves the physical incumbent on both entered difficult roles (RB35 by 2.5415%, K35 by 3.1283%) and reduces both relative gaps. It avoids the measured STOCK+GD combination's RB35 incumbent regression. The important remaining tradeoff is K35 supported L: D lowers it by .011455146913 (2.0300%), even while U and gap improve. K20 keeps the same U and remains open with slightly weaker L; RX20 retains certification with a 2.341246s delay. These measured disadvantages are retained rather than hidden in an aggregate score. The two hard-role incumbent/gap gains, with no observed incumbent regression on any of the four roles, support this bounded uniform recommendation; this is not a general proof-speed or dominance claim. D does not retain STOCK's strong K20 certificate benefit. S/SD remain valuable sealed research references, and no role-specific D/SD switching is proposed. The concrete proposal is the new standalone entry/profile for the next enhanced paper version; stable R137 and its manuscript retain their original bytes pending author review of the Draft PR.

After both core roles completed, the real RB35 independent incumbent gain justified the finite extension with the same D profile. RX20 B/D both certify U=.6453250303858205. Certificate times are 22.324898/24.666144s: D is slower by 2.341246s (10.4872%); complete totals are 23.674241/26.345340s (+2.671099s). This small absolute delay preserves the certified role and is not used as a one-cell veto. The frozen K35 B/D cap2400 pair then returns U=.6928543586313136/.671179796420249, supported L=.5642907958373754/.5528356489241707 and gap=18.555640%/17.632257%. U improves 3.1282999004% and gap falls .9233832014 percentage points, while L decreases .0114551469132 (2.0300077545%). Both remain open; total costs 2374.928960/2378.192407s differ by 3.263447s and are not convergence times. This is an explicit incumbent/bound tradeoff, not two-end dominance. Stop the finite selection study here. Seven new full own-H arms and the seven sealed references are sufficient for this scoped candidate recommendation; no automatic 24-configuration/120-position panel, full K35 factorial, extra seed, K15 boundary, current S/SD clock repeat or RN-P bridge is needed. There is no material decision resting on a tiny cross-round clock difference. Unused budget is not unfinished work. Wider claims would require separately justified validation; that is not asserted or queued by this completed study.

New complete/qualification outer cost is 9613.600887800 seconds, within 18000; all 34 new Native Optimize calls returned. There were no new source or standalone LP optimizations or production builds. Full physical, Start, domain, quality and proof verification was retained. This is finite evidence on known roles and one seed, not an independent validation set, broad dominance theorem or multi-seed robustness claim. The standalone mechanism remains mathematically valid regardless of adoption.

The reproducible companion [scientific report](final_report.md), [mathematical note](mathematical_analysis.md), [four-cell data](reports/four_cell_evidence.csv), [trajectories](reports/verified_U_trajectories.csv) and [decision](candidate_decision.json) retain original identities and limitations.
