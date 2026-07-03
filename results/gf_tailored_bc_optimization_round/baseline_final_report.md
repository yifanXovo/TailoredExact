# Baseline Runtime Comparison

Phase 0 was run before algorithmic code changes in this optimization round.

Rows: 8

- baseline_smoke_v4_m1_tailored_60s: status=optimal, certified=true, LB=0, UB=0, gap=0, wall=1.371s
- baseline_smoke_v4_m1_plain_cplex_60s: status=optimal, benchmark_optimal=true, paper_certified=false, LB=0, UB=0, gap=0, wall=0.121s
- baseline_v12_m1_avg_tailored_300s: status=gcap_frontier_not_closed, certified=false, LB=0.34856314104, UB=0.357200583208, gap=0.0241809296353, wall=420.029s
- baseline_v12_m1_avg_plain_cplex_300s: status=optimal, benchmark_optimal=true, paper_certified=false, LB=0.357200583208, UB=0.357200583208, gap=0, wall=185.712s
- baseline_v12_m2_avg_tailored_300s: status=optimal, certified=true, LB=0.718504070755, UB=0.718504070755, gap=0, wall=292.374s
- baseline_v12_m2_avg_plain_cplex_300s: status=not_certified, certified=false, LB=0.62337314027, UB=0.719065249476, gap=0.133078478311, wall=300.139s
- baseline_diag_v12_m1_low_gini_tailored_300s: status=native_exit_noncertified, certified=false, LB=0.0, UB=0.0, gap=1.0, wall=41.235s
- baseline_diag_v12_m1_low_gini_plain_cplex_300s: status=optimal, benchmark_optimal=true, paper_certified=false, LB=0.0280241198263, UB=0.0280241198263, gap=0, wall=22.831s

Plain CPLEX rows are benchmark-only. Their optimality is retained for comparison, but they are not paper-core Tailored-BC certificates.
