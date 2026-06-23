# Long-run Round 17 Local Notes

Git SHA: 52e825ec6c2f0c9108961a6c7b3b51ba6f8886e3
Branch: main
Build command: fallback MSYS2 g++ build; CMake unavailable on PATH.
CPLEX available: True

Campaign control: user requested a mid-run change. The currently running v12_m2_ablation_plus_operation_budget_1200s row was allowed to finish, then the remaining scheduled rows were stopped and recorded in skipped_or_shortened_runs.csv.

Commands actually run are listed in commands.md and run_exit_summary.csv.

Main 3600s results:
- v12_m1_paper_bpc_core_3600s: status=gcap_frontier_not_closed, UB=0.357200583208, LB=0.33773400095, gap=0.0544976217113, certified=False, unresolved=2, open_nodes=2
- v12_m2_paper_bpc_core_3600s: status=gcap_frontier_not_closed, UB=0.719065249476, LB=0.698710208326, gap=0.0283076412958, certified=False, unresolved=3, open_nodes=3
- v12_m1_paper_exact_portfolio_3600s: status=gcap_frontier_not_closed, UB=0.357200583208, LB=0.337729365558, gap=0.054510598711, certified=False, unresolved=2, open_nodes=2
- v12_m2_paper_exact_portfolio_3600s: status=gcap_frontier_not_closed, UB=0.719065249476, LB=0.698710208326, gap=0.0283076412958, certified=False, unresolved=3, open_nodes=3

Completed V12 M2 ablation rows:
- v12_m2_ablation_base_bpc_1200s: UB=0.719065249476, LB=0.698710208326, gap=0.0283076412958, certified=False
- v12_m2_ablation_plus_dominance_1200s: UB=0.719065249476, LB=0.698710208326, gap=0.0283076412958, certified=False
- v12_m2_ablation_plus_movement_projection_1200s: UB=0.719065249476, LB=0.69259968374, gap=0.0368055134852, certified=False
- v12_m2_ablation_plus_operation_budget_1200s: UB=0.719065249476, LB=0.698710208326, gap=0.0283076412958, certified=False
- v12_m2_ablation_plus_vehicle_relaxation_1200s: UB=0.719065249476, LB=0.719065249476, gap=0, certified=True

Result integrity audit failed rows: 0
Certified result count: 5
No CPLEX/plain compact benchmark rows were run after the mid-run stop request; they are listed as skipped.

Suggested next experiment: resume the skipped ablation rows first (+branching, full_paper_bpc_core, paper_bpc_experimental) before launching CPLEX/compact comparisons, so the component story remains complete.
