# Route-Profile Full-Frontier Final Report

## Decision

The selected directed route-cutset callback is paper-safe, but the tested
profile should remain **experimental rather than paper-default**. The fresh
matrix confirms stability on all four controls and exposes real size-4
callback cuts, but none of the four hard rows certifies and plain CPLEX has the
stronger valid gap on three matched hard cases. This round has no matched
Tailored-BC-without-callback arm, so it cannot attribute the full-framework
difference causally to the callback alone.

## Required Answers

1. **Were all results fresh and package-local?** Yes. All 35 root rows and all
   child artifacts were generated under
   `results/gf_tailored_bc_route_profile_full_frontier_round/`. The
   cross-round audit reports zero failures.
2. **Was any old UB or fixed-interval solution imported?** No. Commands used
   same-run verifier-gated HGA-TGBC incumbents for the tailored upper bound and
   never read prior result folders, archive incumbents, known UBs, external
   incumbents, or manual fixed-interval solutions.
3. **Does the route-cutset callback preserve paper-strict boundaries?** Yes.
   The relaxation vector selects candidate subsets only. Every submitted row
   is the proved directed depot-route cutset inequality. Diagnostic vectors
   and plain CPLEX rows are excluded from the certificate ledger.
4. **Which easy controls certified?** All four. V12 M1 certified at 1200 s
   (`0.357200583208`), V12 M2 at 1200 s (`0.718504070755`),
   `tight_T_seed3101` at 300 s (`0.107252734134`), and
   `high_imbalance_seed3202` at 1200 s (`1.74931345205`).
5. **Which hard cases certified, improved, regressed, or failed?** None
   certified. `high_imbalance_seed3201` remained at tailored gap `0.2870`
   through 14400 s while plain reached `0.1311`. `moderate_seed3301` remained
   at tailored gap `0.75`, versus plain `0.1564`. `moderate_seed3302` regressed
   from tailored gap `0.75` at 3600 s to `0.8125` at 14400 s; its plain 14400 s
   run was stopped for memory and is retained as a resource-error row, while
   the valid plain 3600 s gap is `0.4721`. `tight_T_seed3102` retained tailored
   gap `0.2506` and ended through a wrapper/native-exit artifact; plain reached
   `0.1994`.
6. **Did `moderate_seed3301` certify?** No. Its 14400 s tailored row has
   LB `0.0122881381662`, UB `0.0491525526647`, gap `0.75`, and open frontier
   leaves.
7. **Did the route-cutset profile improve full-frontier progress relative to
   plain CPLEX?** The complete tailored framework did on V12 M2,
   `tight_T_seed3101`, and `high_imbalance_seed3202`, where tailored certified
   and matched plain remained open. On the hard set, plain had the better valid
   gap wherever both long rows completed normally. Callback-specific causality
   is inconclusive because no same-round no-callback tailored baseline was run.
8. **Did plain CPLEX outperform route-profile Tailored-BC anywhere?** Yes.
   Plain certified V12 M1 at 300 s while tailored needed 1200 s, and plain had
   smaller valid gaps on `high_imbalance_seed3201`, `moderate_seed3301`, and
   `tight_T_seed3102` at matched hard budgets.
9. **Did `moderate_seed3302` regress?** Yes. Its selected tailored global LB
   decreased from `0.0489090516373` at 3600 s to `0.0366817887279` at 14400 s.
   Both rows remain noncertified; the regression is not hidden or merged away.
10. **Did `tight_T_seed3102` crash again or certify?** It did not certify. The
    14400 s process ended without a normal final solver JSON, and the wrapper
    preserved only a noncertified valid checkpoint. The campaign runner itself
    remained stable and retained all logs.
11. **Should the callback profile be default, low-Gini-only, or experimental?**
    Experimental. It is mathematically admissible but the present full-frontier
    evidence does not establish uniform benefit or a low-Gini advantage.
12. **Were all paper-core cuts valid and audited?** Yes. Certificate, callback,
    paper-strict, vector-route, callback-parser, and structural-summary audits
    all pass. The implementation fix also makes the dedicated route subset
    size/cut limits effective; fresh rows include 41 size-4 cuts.
13. **Were diagnostic rows used as evidence?** No. Diagnostics, telemetry,
    wrapper-only heartbeats, and plain CPLEX remain noncontributing.
14. **Was the LaTeX chapter generated?** Yes, under `Manuscript/`, with the
    problem, framework, active inequalities, route-cutset proof, CPLEX boundary,
    certificate ledger, computational protocol, and fresh generated table.
15. **Did LaTeX compile?** Yes. MiKTeX 25.12 produced `Manuscript/main.pdf` by
    a multi-pass build; the complete transcript is in `compile_log.txt`.
16. **What exact next step remains?** Run a matched full-frontier tailored
    no-callback control at the hard budgets to isolate callback causality, while
    repairing the hard-leaf native-exit/finalization path. Then target the
    low-Gini denominator/root-bound weakness on `moderate_seed3301` without
    adding instance-specific logic.

## Callback Inventory

Across 18 tailored root rows, six rows generated callback cuts. The parser
aggregated 5,123 candidates and 550 accepted cuts: 102 pair, 407 triple, and
41 quadruple cuts. Maximum recorded violation was `1.42857142857`. These
counts prove activation and implementation correctness; they do not by
themselves prove performance benefit.

## Audit Summary

All 14 required package audits pass: BPC-certificate self-test and result
audit, callback audit, summary cleanup, thread fairness, objective convention,
time-profile finalization, certificate sources, no-instance-special-case,
paper-strict scope, no-cross-round mixing, vector-route validity, callback
vector parser, and structural vector summary. No optimal paper claim failed.

## Engineering Notes

The two simultaneous moderate plain 14400 s CPLEX jobs grew beyond 18 GB and
reduced free physical memory below 0.3 GB. Per the stated resource-priority
policy, `moderate_seed3302_plain_14400s` was stopped and retained as an honest
resource-error artifact so the prioritized `moderate_seed3301` comparison and
both tailored runs could finish. No result from that stopped row is used as a
bound or certificate.
