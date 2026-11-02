# Round147: standalone GD and the STOCK tradeoff

**Decision: RECOMMEND_D_AS_UNIFORM_PAPER_ENHANCEMENT_CANDIDATE. Uniform recommendation: Standalone GD (D).**

Recommend standalone GD (D) as one uniform paper-enhancement candidate for author review. Against controlled stable BASE, it improves the physical incumbent on both entered difficult roles (RB35 by 2.5415%, K35 by 3.1283%) and reduces both relative gaps. It avoids the measured STOCK+GD combination's RB35 incumbent regression. The important remaining tradeoff is K35 supported L: D lowers it by .011455146913 (2.0300%), even while U and gap improve. K20 keeps the same U and remains open with slightly weaker L; RX20 retains certification with a 2.341246s delay. These measured disadvantages are retained rather than hidden in an aggregate score. The two hard-role incumbent/gap gains, with no observed incumbent regression on any of the four roles, support this bounded uniform recommendation; this is not a general proof-speed or dominance claim. D does not retain STOCK's strong K20 certificate benefit. S/SD remain valuable sealed research references, and no role-specific D/SD switching is proposed. The concrete proposal is the new standalone entry/profile for the next enhanced paper version; stable R137 and its manuscript retain their original bytes pending author review of the Draft PR.

## Complete evidence and scope

B, S, D and SD all retain stable GI-TBC; S enables BOTH STOCK and D enables the state-conditioned GD mechanism (at most two rows on an applicable domain). Every new arm pays for its own complete H (seed 20260626), all LP/MIP calls and mandatory physical, Start, model-scope, numerical-quality, lifecycle and R134 proof verification. Gurobi Seed=0, Threads=1, MIPThreads=1 and affinity=4; timed runs are serial. M-B/VD-P, pair-only, AM=.08, depth=8, minimum width=1e-4 and AP off remain fixed. Physical horizons, original lambda and process caps are bound in the matrices. No prior solution, cut or H state is injected into a new arm.

| Role | Method | Evidence | U | Supported L | Gap % | T_cert s | T_verify s | T_total s |
|---|---|---|---|---|---|---|---|---|
| K20 | B | new R147 | 0.716806546278 | 0.704791696972 | 1.676163 | — | 49.4678967 | 1221.994321 |
| K20 | S | sealed R146 | 0.716806546278 | 0.716806546278 | 0.000000 | 94.2613895 | 2.6702012 | 96.93159066 |
| K20 | D | new R147 | 0.716806546278 | 0.704202765473 | 1.758324 | — | 33.58133 | 1205.656318 |
| K20 | SD | sealed R146 | 0.716806546278 | 0.716806546278 | 0.000000 | 74.9164195 | 2.6372625 | 77.55368205 |
| RX20-T1 | B | new R147 | 0.645325030386 | 0.645325030386 | 0.000000 | 22.3248979 | 1.3493431 | 23.67424096 |
| RX20-T1 | S | sealed R146 | 0.645325030386 | 0.645325030386 | 0.000000 | 14.7557736 | 1.1372002 | 15.89297379 |
| RX20-T1 | D | new R147 | 0.645325030386 | 0.645325030386 | 0.000000 | 24.6661437 | 1.6791966 | 26.34534032 |
| RX20-T1 | SD | sealed R146 | 0.645325030386 | 0.645325027365 | 0.000000 | 12.0531594 | 1.6058863 | 13.65904567 |
| K35 | B | new R147 | 0.692854358631 | 0.564290795837 | 18.555640 | — | 3.82351 | 2374.92896 |
| K35 | D | new R147 | 0.67117979642 | 0.552835648924 | 17.632257 | — | 7.1262137 | 2378.192407 |
| RB35-T2 | B | sealed R146 | 0.344642625592 | 0.218985949603 | 36.459993 | — | 3.7957558 | 2375.143924 |
| RB35-T2 | S | sealed R146 | 0.401200217839 | 0.229181599664 | 42.876003 | — | 3.8268902 | 2374.898921 |
| RB35-T2 | D | new R147 | 0.33588358895 | 0.219475150151 | 34.657376 | — | 7.7228106 | 2378.839312 |
| RB35-T2 | SD | sealed R146 | 0.377816983545 | 0.233498944436 | 38.197870 | — | 8.8321238 | 2379.922442 |

A dash in T_cert means open, not a cap-valued convergence time. Signed/relative gaps and T_produce/T_cert/T_verify/T_total remain in [full JSON](reports/full.json) and [four-cell CSV](reports/four_cell_evidence.csv). Native ObjBoundC/ObjVal are separate fields from external proof-supported L. T_total is complete producer plus necessary verification; outer fees additionally include launcher/accounting overhead. An open arm with a smaller verification cost has not thereby converged faster. Same-PE cross-round references retain their original dates, fees and raw identities; identical system load or simultaneous execution is not assumed.

K20 B and D both return U=.7168065462777502 and remain open after their complete cap1200 windows. Supported L changes from .7047916969720031 to .7042027654726336; the relative gap increases from 1.676163% to 1.758324% (+.082160 percentage points). This is not a useful standalone certificate gain. The sealed same-PE S/SD cells certify the same U in 94.261389/74.916420s; their strong proof advantage is preserved as a real counterpoint. RB35 D instead returns U/L=.3358835889496765/.21947515015073324 against sealed same-PE B=.34464262559194814/.2189859496034747. U improves 2.5414838421%, L rises .0004892005473, and gap falls from 36.459993% to 34.657376% (-1.8026165231 percentage points). The L gain is small; the main independent benefit is physical incumbent quality. All four RB35 cells are open. D improves U and gap against SD but has lower L than SD's .23349894443616206, so it does not dominate the combination at both ends. Actual new D models have two GD rows and zero STOCK rows; the comparison is not inferred from method labels.

R146's positive S→SD findings remain unchanged: K20 certifies about 20.52% sooner at the same U; RX20 retains certification with a small absolute 2.702614s certificate gain; RB35 improves U by 5.8283%, increases L by .004317345 and lowers gap by 4.6781 percentage points. Against BASE, that same SD pressure result had U higher by 9.6257%, L higher by .014512995 and gap larger by 1.7379 percentage points, a mixed tradeoff rather than two-end regression. RX20 SD's approximately 3.02e-9 positive U−L remains certified under the original R134 policy; no new floating-point repair or solve is introduced. R138's K15/K20 STOCK certificate benefits, its disclosed V2 transport identity in the finite Seed1 evidence, R144's RN-P K35 gains and R145's structural complementarity/root-retention results remain at their original versions. The Seed1 history is not a pure seed-only intervention, and no universal STOCK regression law is inferred. The strong historical RN-P K35 incumbent remains a research reference; no new matched RN-P bridge or claim of D beating every research variant is made. Fixed-domain K20 LP interaction remains a numerical fact, not complete-search synergy or general supermodularity.

## Search observations

| Role | Method | Initial LP | Printed root/cuts | Native Work | Root simplex | Terminal nodes | Splits | Rows / NZ |
|---|---|---|---|---|---|---|---|---|
| K20 | B | 0.195149152 | 0.55666 | 1758.1396 | 3349 | 412565 | 0 | 6637 / 38286 |
| K20 | S | 0.204590439 | 0.58526 | 149.0264 | 2465 | 22823 | 0 | 6641 / 38410 |
| K20 | D | 0.236010302 | 0.559 | 1792.0328 | 2962 | 372567 | 0 | 6639 / 38616 |
| K20 | SD | 0.25101611 | 0.58619 | 120.70941 | 2624 | 13366 | 0 | 6643 / 38740 |
| RX20-T1 | B | 0.331594316 | 0.52281 | 30.217417 | 1262 | 2621 | 0 | 6023 / 35158 |
| RX20-T1 | S | 0.37755753 | 0.53642 | 21.627214 | 1408 | 1882 | 0 | 6027 / 35282 |
| RX20-T1 | D | 0.365004646 | 0.54027 | 35.220172 | 1360 | 2064 | 0 | 6025 / 35255 |
| RX20-T1 | SD | 0.398702049 | 0.54633 | 14.514094 | 1409 | 1520 | 0 | 6029 / 35379 |
| K35 | B | 0.200177662 | 0.42856 | 4990.527 | 5188 | 18583 | 0 | 23624 / 163516 |
| K35 | D | 0.204187028 | 0.44681 | 5032.8331 | 11374 | 17834 | 0 | 23626 / 163921 |
| RB35-T2 | B | 0.12891074 | 0.17634 | 5785.3879 | 9564 | 6707 | 0 | 23666 / 165717 |
| RB35-T2 | S | 0.129151292 | 0.18287 | 5723.7619 | 7886 | 10202 | 0 | 23670 / 165931 |
| RB35-T2 | D | 0.135292104 | 0.18147 | 5344.1751 | 13554 | 6410 | 0 | 23668 / 166124 |
| RB35-T2 | SD | 0.136190944 | 0.18634 | 5677.5804 | 12683 | 8934 | 0 | 23672 / 166338 |

Initial LP and printed terminal-root-after-cuts values are different observations. The latter have native log precision; Work, simplex, nodes, density and splits describe the observed search and do not identify a unique causal internal mechanism. [Verified incumbent trajectories](reports/verified_U_trajectories.csv) use committed producer availability, not solver runtime or total time.

The committed physical-witness records locate the hard-role benefit in finding better incumbents, not certification. RB35 D already has U=.3372904684849699 at 668.391s, below B's eventual final U, and reaches its own final U at 1346.250s. B reaches its different final U at 2366.781s. K35 D first beats B's final U at 1338.656s with U=.6791034678575588; B reaches its final U at 1758.516s. D then has U=.6767988451958106 at 1686.187s and finds the final .671179796420249 at 2364.047s. That last improvement is near cap and is disclosed; the earlier strict gains establish that the benefit does not arise solely from the last seconds. Different-quality final-U discovery times are not convergence speedup ratios. K20 reaches the common final U at 224.546s for B and 417.765s for D. D's 16.338s lower complete total there is mainly a verification-cost decrease (49.467897 to 33.581330s), not faster proof. All 14 entered/reused formal cells have zero outer splits. Native root-after-cuts values, simplex, Work and node differences describe changed search but do not identify a unique cause. For example, K35's printed root bound rises .42856 to .44681 and root simplex increases 5188 to 11374, while final supported L is lower; stronger root information does not force stronger final proof.

## Mathematics, qualification and identities

The [self-contained mathematical note](mathematical_analysis.md) proves standalone validity without requiring formal STOCK rows. R146 exact arithmetic, inventory units, actual STOCK-off writer/Native readback, complete and nonminimal Starts, subset inheritance and unchanged OFF matrices are reused. The zero-row reader now selects the saved original model using actual root metadata; a no-model H-completion control path is preserved. New targeting checks exercise the wrapper, actual CLI and zero-lower saved fixture with zero Optimize/Native load. No production rebuild, repeated native health test, standalone LP, new mechanism, placement grid or tuning was needed.

Production source `1f470aa5d6a8289347b9d4323764e6e74fa83b2b` and PE SHA256 `da8fabd315ac6228432b0f3afeba07efef3baf83300e650112d6dcdf9aca2309` are unchanged. R146 fixed science is `8ec2aebe46398485019623d9b18a3e30617d4997`. New wrapper/registration versions are recorded in [wrapper identity](wrapper_version.json) and the [core matrix](core_matrix.json); later scientific and publication commits remain distinct. All old entries, profiles, R137 manuscript bytes, historical results and protected original user changes are preserved.

## Cost, decision gate and delivery

New charged outer experiment/qualification cost is **9613.600887800 seconds** (2.670444691 hours), below 18000. All 34 new Native Optimize calls returned; new standalone LPs=0, source solves=0, builds=0. H, solver calls, qualifications, failures and necessary postverification are counted once. Nested runtime/Work and the original R146 fees are not added. Pure authoring, mathematical review, packaging and public recovery are separate. See [cost](cost_report.json) and the immutable per-process fee receipts.

After both core roles completed, the real RB35 independent incumbent gain justified the finite extension with the same D profile. RX20 B/D both certify U=.6453250303858205. Certificate times are 22.324898/24.666144s: D is slower by 2.341246s (10.4872%); complete totals are 23.674241/26.345340s (+2.671099s). This small absolute delay preserves the certified role and is not used as a one-cell veto. The frozen K35 B/D cap2400 pair then returns U=.6928543586313136/.671179796420249, supported L=.5642907958373754/.5528356489241707 and gap=18.555640%/17.632257%. U improves 3.1282999004% and gap falls .9233832014 percentage points, while L decreases .0114551469132 (2.0300077545%). Both remain open; total costs 2374.928960/2378.192407s differ by 3.263447s and are not convergence times. This is an explicit incumbent/bound tradeoff, not two-end dominance. Stop the finite selection study here. Seven new full own-H arms and the seven sealed references are sufficient for this scoped candidate recommendation; no automatic 24-configuration/120-position panel, full K35 factorial, extra seed, K15 boundary, current S/SD clock repeat or RN-P bridge is needed. There is no material decision resting on a tiny cross-round clock difference. Unused budget is not unfinished work. Wider claims would require separately justified validation; that is not asserted or queued by this completed study.

The [paper section](manuscript.md), [independent review](review/final_scientific_review.json), [reuse index](reuse_index.json), [decision](candidate_decision.json) and [continuation record](RESUME.md) form the finite handoff. Current carriers include necessary new evidence; fixed parent carriers and member hashes identify inherited assets without copying the old history. Public byte/member acceptance, actual English Draft PR readback and bounded current-round cleanup are recorded as late delivery metadata.
