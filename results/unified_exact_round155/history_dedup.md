# Finite history check and Round155's actual increment

This is a bounded read of the existing source and compact reports. No historical
producer, solver, build or large archive restoration was run. Paths below are
repository-relative. Unless a different fixed science commit is named, historical
text was read from the verified R154 base
`c0b64d66cb0fda36528f764e9b1264df68f45c8b`. Old observations retain their original
builds, scopes and budgets; they are not new same-pool timing comparisons.

| Existing work | Checked implementation / compact evidence | Consequence for this round |
|---|---|---|
| PR58 exact-S toy and earlier objective structure | Local history contains merge `9bc673377b42779cf9d59aa942df67a4c207c9c8` for PR58; R154 `mathematical_analysis.md` retains the exact-S attribution | No claim to invent exact denominator enumeration or parametric objective transformations |
| Existing SP estimator | `docs/sp_product_objective_estimator.md`, `docs/disaggregated_sp_estimator.md`: valid product domain and McCormick relaxation of `S P` in the objective cutoff | R154 signed residual products are a different pricing object, with inherited classical product-envelope principles |
| R133/R152/R153 inventory objective structure | R154 `mathematical_analysis.md`; R153 `mathematical_analysis.md`, `scripts/round153_pricing.py` and `scripts/round153_coupled.py` | Reuse legal inventory domain, true completion, zero branch, RN pricing and the full-Q coupling |
| R153 persistent Master and reoptimization | `scripts/round153_coupled.py` and `scripts/round153_lp.py` | Persistent master, Method=1, basis output and later-column feedback predate R155 |
| R153 near-optimal and midpoint selection | `scripts/round153_stabilize.py:near_optimal_dual_band`; `round153_coupled.py` sets the level band's width from `(lower+candidate_upper)/2` | Midpoint really entered the dual LP; it was not merely a logged price target. A later feasible level revision must acknowledge this |
| R153 multiple incumbents and large pool | `results/unified_exact_round153/reports/research_phases.csv`: K near-optimal pool has 1114 columns; continued primal pool 33882. NC near-optimal pool has 427; primal pool 54187; post-primal level 54210 | Batch columns and pool growth are inherited mechanisms; column counts alone do not establish useful hull progress |
| R153 level results | Same phase table: K level/level-zero lower .27886445393292747/.2790149638765465, upper .28749181051555994; NC post-primal level lower .1833218484555365, upper .1899568005655939 | These are earlier intermediate pools, not replacements for the actual A1 R154 starts |
| R154 residual, strengthened products and goal stop | `scripts/round154_residual.py`, `round154_strengthened.py`, `round154_goal_oracle.py`, qualified `goal_stop_v1` evidence | Keep the formulations and price conversion. R155 changes direction acquisition, continuation and evidence storage |
| R154 fixed midpoint price | R154 NC matched internal-target task and reports | This is one frozen direction/price task, distinct from R153's midpoint dual selection and from a complete level loop |
| R154 eight-iteration bottleneck | R154 reports and retained loop records: K selection failed eight times, then basic dual; NC selection succeeded | Eliminate known K selection waste without asserting the same failure on NC. Fresh first/bounded arms start from identical final pools |
| R154 proof consumer | `include/Round154Research.hpp`, unchanged producer/consumer and nine-arm audits | E's existing NB35 supported-bound gain is retained. New offline prices are not supplied to complete arms |
| R63 cumulative time resource and projection | `results/gf_cumulative_time_resource_round63/final_report.md`; `include/Round63TimeResource.hpp` | Valid time-resource/projection strength and isolated gains already existed, with protection/confirmation failures; no generic new routing-cut claim |
| R64 shared arc load/time | `results/gf_shared_load_time_round64/final_report.md`; `include/Round64SharedResource.hpp` | Real shared-resource increments were tested; mixed full-cost results did not upgrade the stable default |
| R65 bounded projection service | `results/gf_budgeted_proof_round65/final_report.md`; `include/Round65Projection.hpp` | Persistent vehicle proof services and outward-checked combinations already existed; mathematical admissibility did not guarantee complete-method benefit |
| R66 arc-load replacement | `results/unified_exact_round66/final_report.md` | Default-off replacement improved some roles but did not repair the principal CitiBike proof deficit |
| R91/R92 handling rounding | R91 `handling_real_decision.md`; R92 `g1_v2_decision.md`; `include/Round92HandlingActivation.hpp` | Existing continuous versus integer-rounded travel/activation attribution and physical-envelope qualification must be retained |
| R97 physical route closure | `results/unified_exact_round97/final_report.md` | Native integer-route improvement and feedback already reused older R83/R76 closure; mixed confirmation did not promote the default |
| R101 fleet event covers | `results/unified_exact_round101/final_report.md`; `include/FleetEventCuts.hpp` | Complete necessary assignment DP, directional resource ranks and matching were already qualified; the frozen candidate was not adopted |
| R105 inventory-route feasibility learning | `results/unified_exact_round105/final_report.md` | Full operation/membership patterns and re-proved conflicts formed a valid complete loop; its tested cost/quality result was negative |
| R106/R107 structural route events | Their `final_report.md` files; `include/Round107Research.hpp` | Dynamic MST and exact/threshold conflicts, assignment master and original-frontier integration were tested and retained only as research components |

The new experiment is a sustained complete-Q loop on the actual R154 final
large pools. It compares direct qualified basic dual plus first counterexample
with a predeclared bounded multi-incumbent residual price, then uses observed
column quality and full primal/dual progress to select a substantive continuation.
Removing a failed auxiliary selection is an implementation/cost improvement;
using returned columns, improving an individual price proof, improving the full
inventory hull, and improving the complete route algorithm are separate outcomes.

Historical phase labels such as `RUNNING_PRIMAL_DISCOVERY` are preserved evidence,
not active work. The K primal-pool phase with that label has a closed nonzero-exit
receipt and a separately recorded continuation. It is not restarted here.

Classical LP optimal-face geometry, column generation, McCormick products and
stabilization keep their established attribution. See `mathematical_analysis.md`
for the exact statement, proof and primary literature. No R155 general theory
claim or untested routing/loading follow-up is inferred from this table.
