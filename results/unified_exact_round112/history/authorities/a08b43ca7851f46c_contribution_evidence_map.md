# Contribution and evidence scope

This round optimizes an equivalent engineering audit. The algorithm and
mathematical contributions remain inherited. Its finite supplementary Seed
block does not add independent geographic samples.

|Claim|Actual source / fixed evidence|Supported scope|Unsupported inference|
|---|---|---|---|
|Original physical inventory/routing objective and full integer fleet|src/Evaluator.cpp; src/GurobiBaseline.cpp; include/CanonicalCompactModel.hpp; R100 mathematical_algorithm.md|One vehicle, one nonzero direction per station; empty departure, every prefix/return load bounded; loaded return and depot unload included; G of inventory/target ratios plus .15 weighted penalty|Cumulative pickup <= Q; station-stock conservation without depot; a min_ratio floor; arbitrary split service|
|Continuous declarations of p/d retain integer complete solutions; A/B are valid|include/Round98StateService.hpp; src/GurobiBaseline.cpp; R100 mathematical_algorithm.md; R108 representation_contract.md|Integer b/Y, binary unique assignment/direction, original direction bounds and inventory balance imply integer physical quantity; original A/B reinforce legal state/service|LP quantities are integers; A/B are necessary for implicit integrality; p/d-only causal speed attribution|
|Scoped original-domain bounds and complete cover|src/PaperExternalGiniTree.cpp; src/GurobiBaseline.cpp; R110 current_numerical_evidence.md and final signed review|Matching model, actual type/return, true-G interval, cutoff/epoch and full improving-domain coverage; reject every damaged call lower claim and dependent discharge|rc0 implies numerical correctness; root zero refutes a positive-G right LP; a local OPTIMAL leaf alone certifies globally|
|ENS framework gains versus original cold P|R110 fixed main36/pairs: ENS/P and M-B/P each 11WIN/1TIE|The same 11 P-WIN roles support the full framework's finite value|Assign all common gains to the M-B increment; claim M-B dominates ENS|
|Distinct historical M-B value and disclosed costs|R108 bridge C2: ENS/P LOSS, M-B/P WIN; R108 F5 severe ENS LOSS; R110 main ENS5WIN/3TIE/4LOSS|M-B repaired an observed primary-benchmark gap on C2; costs remain public on R110 G50-C1/G50-C2/G100-C1/G100-R2, severe C1/R2|Hide ENS losses behind the P result; introduce an ENS pointwise-dominance gate|
|Actual decomposition exposure|R108 L48 raw parent atomic splits and AM/controller tables; R110 mechanism_analysis.json|Each R108 ENS/M-B has two actual parent splits (one infeasible-half retaining partition, one AM positive-score split), <=2 relevant active leaves; R110 zero actual splits, <=1 leaf|AM score split count equals all atomic_split count; child lookahead models demonstrate committed multileaf search|
|G50-C1 repeated completion gap|R109 mechanism_correction01; R110 mechanism_analysis.json and fixed final report|Same Seed0 initial full fleets, each 3LP+terminal MIP; ENS native MIPSOL reaches zero, M-B finishes one bike below target. Actual R110 pickup20-minus-one replay makes vehicle1 later prefix at47=-1|Independent Seed stability; HGA-only or zero Optimize; assume the same causal constraint explains G100-R2|
|G100-R2 finite ENS cost|R110 Seed0 own M-B U=.011434738339920945 versus ENS .005528455284552848; tiny LB difference|The observed gap difference is mostly own UB; every published fleet still satisfies its prefix/return/time constraints|Fstar=0 has been proved; all historical deficits are primal. F2 separately distinguishes finding the target witness from completing its certificate|
|Conditional zero floor/AM interpretation|R100 mathematics; R110 paper_candidate_spec.md|lambda>0 and positive weights imply F=0 iff Y=D. For proved Fstar=0, L0 is exact; zero minimum AM gain additionally needs ownU>0, zero feasible in root/left, both child LPs feasible and actual scoring. Startup zero closure and INF partition remain separate|Apply the zero-optimum argument to unproved G100-R2; all zero-optimum roles never split|
|Measured cost and external validity|R110 time_partitions/structure_statistics/source_subset_overlap; R111 audit_cost_profile.md|V100 startup/LP/MIP costs vary by role. Single-source coordinate/capacity subsets, synthetic stock/targets/fleet/T, overlapping subsets and few Seeds bound interpretation|Fixed lambda and max-normalized weights fix cross-V tradeoffs; statistical guarantees, new cities, or a complete paper benchmark|
|Equivalent audit overhead reduction|scripts/round111_seed_audit.py; qualification/replays; counterexamples01|Single exact string/suffix classification, duplicate Counter>=1, content/parser/contract keyed arm-local data; each call still separately verified and every reused Counter rehashed|A new algorithm, weaker certificate predicates, cross-arm reuse or cap-free validation|

No new route counterfactual, solver, operator, cut, target oracle or mechanism
is implemented here. The existing G50-C1 replay is carried as a fixed
historical result. No prescribed G100-R2 adjustment is claimed invalid without
an actual specified replay.

Two falsifiable research questions remain within these evidence limits:

1. Does G50-C1's same one-bike completion gap survive a controlled separation
   of representation and integer-search trajectory? Equal initial fleets and
   3LP+terminal MIP are known; controlled causal identification is missing.
2. Can the remaining fixed-machine audit/IO variability consume the measured
   empirical reserve? Finite <=15s replays qualify this task but do not prove
   a hard upper bound. A valid over-reserve trace would refute that envelope.
