# Round127 v3: methods, masks and proof contract

**Qualification disposition:** P/PT/MB/MR/MG/MS2 are eligible subject to the sealed evidence gate. **MD is blocked before formal evaluation.** The intended inclusive-root definition below fails the retained equality-closure boundary; see `review/preformal_cutoff_boundary_review.md` and the actual vectors in `qualification/boundary_vectors.json`. MD's S12 native smoke is functional qualification evidence only. No formal MD result or D-effect claim is manufactured.

The sole paper method is the frozen **M-B**, described as a tailored branch-and-cut framework with Gini-interval decomposition (GI-TBC). MD/MR/MG/MS2 are deletion diagnostics. No result chooses a method, preset, support allocation, H effort, AM threshold or native parameter per evaluation instance. The historical ENS-C default remains unchanged.

| ID | Representation and startup | Static rows | External control | Binary |
|---|---|---|---|---|
| P | Original cold compact; no H/Start/A/B/cutoff | Original compact | None | E0 in main/tiny; E1 in training/core |
| PT | Same complete compact and cold state as P | Same as P | None; one frozen two-parameter configuration | E1 only |
| MB | Own complete H; VD-P, continuous p/d, binary direction; integer Y/load; original A/B | R+C_R+C_G | Original K1, NEXT and AM | E0 in main/tiny; E1 in core |
| MD | Same H and representation as MB | Same complete root as MB | Root LP then one full root MIP; no NEXT/AM/child LP/rebuild | E1 |
| MR | Same H and representation as MB | R+C_G; omit C_R | Original controller | E1 |
| MG | Same H and representation as MB | R+C_R; omit C_G, retaining the original derived domains | Original controller | E1 |
| MS2 | Same H and representation as MB | Same as MB, omit triple support only | Original controller | E1 |

R retains the exact inventory/Gini representation, routing/connectivity, prefix load and complete duration, unique nonzero one-direction service, state products, A/B, global handling, singleton reachability, other transfer rows, the original non-strict own cutoff row, true-G cap/floor, the separately documented no-strict-improver penalty-LB closure and movement requirements. Vehicles depart empty and may return loaded. Sum pickup may exceed capacity; each prefix may not. Duration is travel plus `(pickup_time+drop_time)*sum pickup`, excluding depot service. The objective is true Gini plus lambda-weighted target deviation; travel is not an additional objective. Zero-denominator semantics are inherited.

## Exact finite packs

| Pack/family | Formula or scope | Dedicated columns | Active emission sites |
|---|---|---|---|
| C_R ordered supply | `d_kj <= sum_{i != j: dist(0,i)+dist(i,j)+dist(j,0)+cunit <= T+1e-9} p_ki` | None | CplexBaseline ordered compatibility block; factory registry only |
| C_R pair/triple cover | `sum_{i in A} z_ki <= |A|-1` when cycle LB plus `cunit*ceil(|A|/2)>T+1e-9` | None | CplexBaseline pair/triple support block |
| C_R conditional handling | `cunit*sum_A p_ki + B_A*sum_A z_ki <= T-cycleLB+B_A*|A|` otherwise | None | Same block |
| C_G H spread | `(n-1)h_ij <= n*gU*sum r` | None | IntervalRowFactory and direct writer fallback |
| C_G fixed centering | Both directed `r_i-r_j <= n*gU*S_U/(n-1)` | r_min/r_max in legacy extended writer; unused in shared projection | Same two emission paths |
| C_G variable-S centering | Both directed `(n-1)(r_i-r_j) <= n*gU*sum r` | None | Same two emission paths |
| C_G linear estimator | `sum h + n*S_U*lambda*sum omega*e <= n*S_U*U` | None | Shared factory and fallback |
| C_G product estimator | Four McCormick rows for `W_SP=S*P` and `sum h+n*lambda*W_SP <= n*U*sum r` | W_SP and its bounds | Shared factory and fallback; column creation in writer |

Here `cunit=pickup_time+drop_time=120`, `P=sum omega_i*e_i`, and `S=sum r_i`. For a support A, `cycleLB` is the minimum depot cycle over its two or six orders, and `B_A=T+cycleLB+cunit*max(1,sum_{i in A} min(b_i,Q_k))`, exactly as in Appendix A.5.4. On the unchanged rectangle `[S_L,S_U] x [P_L,P_U]`, the four product rows are `W>=S_L*P+P_L*S-S_L*P_L`, `W>=S_U*P+P_U*S-S_U*P_U`, `W<=S_U*P+P_L*S-S_U*P_L`, and `W<=S_L*P+P_U*S-S_L*P_U`; the actual serialized W bounds are retained in each original model. The factory projects the legacy extrema to directed pair rows, so r_min/r_max are unused dedicated columns in the active shared path; MG omits them along with W_SP.

The active entry points are `writeCompactLp` in CplexBaseline and `buildRound18StaticIntervalRows` in IntervalRowFactory. Ordered supply depends on the original strengthened compatibility flag; support depends on the original strengthened duration flag, max size and shared subset cap. H-spread/centering retain the original low-Gini/direct-row prerequisites; linear and SP estimators retain their original option, cutoff and rectangle prerequisites. The MB preset activates these fixed choices. The masks alter emission after those prerequisites; they do not enable another preset or a new domain calculation.

The masks act on **row emission**, not on domain-generating options. In particular MG retains low-Gini-derived Y bounds, denominator/penalty domains, direct true-G cap/floor, g×state hulls, penalty closure and deviation upper bounds. Deleting C_G does not delete all fairness structure. Gurobi's generic Cuts parameter remains Auto in all M-B diagnostics; project-row deletion is not `Cuts=0`. Start mapping and independent evaluation iterate actual columns; absent W_SP/r_min/r_max are not fabricated, and every remaining row is checked.

The shared factory and fallback writer are masked together. Family registry metadata follows the emission mask, while the inherited domain option remains configured. Actual differences use duplicate-preserving row Counters, full objective, all types and all retained bounds. Support exposure reports cover/conditional and pair/triple separately from actual rows; old pair/triple counters combine both branch types.

## MD intended completeness obligation — not qualified

After its own unchanged H supplies U0, MD preserves the original startup-zero certificate. Otherwise its intended relevant domain is `[0,min(U0,(n-1)/n)]` with `F_model<=U0` (the n=1 convention is inherited). For every physical solution with F<=U0, true G<=F and true G<=(n-1)/n, so its Gini lies in that interval. Embedding it in all retained root rows is a separate mandatory obligation; that obligation fails at the equality closure below. F>U0 cannot improve the same-run witness. Native scoped bounds combine with this cutoff complement; raw native bounds and signed gaps remain in evidence.

MD validates the complete singleton root, executes the original LP, restores original VTypes and performs one terminal root MIP without a native target. NEXT, adaptive child LPs, splitting and cutoff-epoch rebuilding are disabled. LP optimality or a bound target alone is never used as MD's final problem certificate. Own U0 Start is injected by the unchanged shared backend. Root LP/MIP infeasibility is a consistency fault. An improved native physical incumbent can update own U after the call, with no second model or tree.

The retained penalty-LB closure can append `0<=-1` when `gL+lambda*P_LB>=U0-1e-9`. R126 Appendix A.5.6/A.7 already identifies this as numerical **no-strict-improver** closure, not infeasibility of the inclusive non-strict cutoff set. In the artificial V2 empty-stock, T=60, cunit=120 case, Y=0 is forced, P_LB=2 and U0=.3: the equal-U0 empty fleet violates only this impossible row by 1. No strictly better solution exists at exact equality, but the requested inclusive embedding and legal own Start are false. Changing that retained policy would change MD's authorized specification. All three MD formal positions are therefore unstarted and blocked; other masks still delete only the declared rows from the unchanged frozen numerical formulation. This finding does not revoke the inherited no-strict-improver cutoff-complement conclusion.

## Uniformity and numerical identity

The active path is argv → original preset overrides → canonical spec → writer/shared factory → existing controller → Gurobi API. The new diagnostic is an explicit process-local switch and leaves SolveOptions/SolveResult ABI unchanged. Complete replaced translation units are linked ahead of the frozen source archive using the same compiler and flags; E0 bytes remain in place. E0/E1 default MB/P equivalence is checked on full matrices and actual native types/bounds/objective, not only fingerprints. No assertion of equal wall time follows from this qualification.

The H seed is 20260626, with 24 shuffled plus one constructive decoded-descent start, decode cache maximum 200000 entries. Controller constants remain K1 initial interval, midpoint split, balanced-normalized-closure score, threshold .08, maximum depth 8, minimum width 1e-4, split factor 2. NEXT/AM are the original policies. Dynamic project cuts and root cut rounds remain off. Metric travel and homogeneous-capacity symmetry are mathematical preconditions, not instance-name dispatch. Filenames/directories affect artifact names only; small/medium rename exports must retain settings and matrices.

Support candidates are enumerated per vehicle, pairs then triples. Each model shares one 50000 candidate budget across vehicles. `max_size=4` still has only the existing pair/triple loops. At V50/M4 the 83300 candidates would be allocated 20825,20825,8350,0 before the cap; no V50 solve is added and the allocation is unchanged. Core totals 1120,2660,21420 are below the cap, so MS2 does not reallocate a binding truncation budget.

Threads=MIP threads=1; affinity mask 4; Presolve Auto; requested MIPGap=MIPGapAbs=0; original FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6. Every arm pays admission, complete H, model, LP/MIP, Start, online checks, return and required output within its cap. Shutdown reserve 30 seconds, native offset 6 and hard-stop offset 2 remain. T_verify is separate; T_total is also reported. T_cert=T_produce only after full qualification, otherwise null.

## Bounded P selection

The immutable manifest expands all 36 positions: three development inputs × Seeds 2/3 × six predeclared MIPFocus/Cuts settings, with the prescribed cyclic order. Only those two parameters can be parsed, only in original cold P. They are loaded after preset processing and read back from the actual model environment before Optimize, including NumStart=0. No Seed, gap, tolerance, thread, time-limit or model parameter is selected. The selected PRM is committed before E1 core evaluation. q0 means PT is a named alias of the same P result, with no duplicate run or independent observation.

Gurobi documentation: [Parameter Reference](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html), [Parameter Tuning Tool](https://docs.gurobi.com/projects/optimizer/en/13.0/features/tuning.html), [Parameter Guidelines](https://docs.gurobi.com/projects/optimizer/en/current/concepts/parameters/guidelines.html). The local 13.0.2 C API's set/get return codes and actual values are authoritative; the finite selection rule is this study's certification-first rule, not grbtune's general objective or a global tuning claim.

The inherited PE hardcodes Seed0 in one native-precondition boolean. R122's existing normal-return, actual-matrix/setting/Start/scope qualification is extended to Seeds2/3. Raw flags and callback global-availability fields are unchanged. Returned scoped proofs are reconstructed after full read-only checks; no legacy flag is silently promoted in recorded bytes.
