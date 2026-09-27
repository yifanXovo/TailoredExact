## Finding

The proposed five-station fleet-event inequality needs a test against the complete ENS-C canonical LP before it can be treated as a distinct mechanism. This change adds a standalone exporter using the frozen core and one fixed three-arm diagnostic; it changes no formal algorithm preset, frozen source, CMake target or benchmark.

On the same complete root relaxation, maximizing the five target-state selectors gives **5 originally, 4 with two per-vehicle handling-rounding rows, and 4 with the event row**. The two vehicle rows algebraically imply the event row. The event-row arm's full numerical primal violates each vehicle row by 0.5 while satisfying the original model, showing why equal objective values do not imply equal feasible regions. This is numerical LP evidence, not a rational proof, an original-objective bound improvement or a MIP speed claim.

The [root decision](results/unified_exact_round91/decision.md) does not admit a production cut. Ordinary rounding is already LP-redundant on 18 of the 19 planned benchmark scenarios; D3 is the exception. A [travel-and-activation follow-up](results/unified_exact_round91/handling_rounding_next_gate.md) records the mathematical and numerical requirements for any later relevance diagnostic, without implementing it or claiming novelty.

## Validation and evidence

The [zero-Optimize qualification](results/unified_exact_round91/qualification_001/report.md) uses the real parser, physical verifier and canonical model writer. Its accepted witness has F=17/60. One standalone compile/link/export costs 4.6371862s in measured commands; the frozen Round90 core/main/source identities remain unchanged. A CRLF-only text-audit false negative and its correction are retained.

The [three-arm diagnostic](results/unified_exact_round91/diagnostic_001/report.md) makes exactly three Optimize calls in one 0.8804413s outer process under a common research deadline. Each arm retains 244 columns and all 555 original rows, with 0/2/1 added rows. Full primal, every original/added row residual, every bound residual, parameter readback, source/model hashes and costs are included directly. All three return numerical OPTIMAL and pass residual checks; [independent evidence review](results/unified_exact_round91/diagnostic_001_independent_review.md) accepts this limited conclusion.

This stacked research PR is based on Round90 and preserves its separate pending F2/D6 performance screen. No mainline promotion or broad long-time campaign occurs here.
