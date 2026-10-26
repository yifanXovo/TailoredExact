# Round137 independent scientific preflight

Reviewer: separate internal agent `/root/independent_review`, 2026-10-27
(Asia/Shanghai). This is independent of the implementation agent; it is not
external replication. Scope: goal, current source and inherited definitions.
No Optimize, build, performance run or historical raw restoration was executed.
The concrete Round137 implementation, input manifest and frozen argv are still
to be reviewed before expensive evaluation. This note does not admit an unseen
matrix or certify future outcomes.

## Mathematical definitions

1. The shortage floor is valid under the stated premises. Empty departure and
   nonnegative returned load imply sum(Y)=sum(b)-sum(R)<=sum(b), hence
   sum(D)-sum(Y)>=s>0. With every omega_i>0 and D_i>0,
   a=min(omega_i/D_i)>0 and P>=a*sum|D-Y|>=a*s. Since G>=0 and
   lambda=rho/Omega>0 for the planned positive rho values, F>=lambda*a*s>0.
   Compute s, a, Omega, lambda and the floor from the actual serialized input;
   an intended shortage recipe alone does not establish its premise.
2. rho=lambda*Omega and P_avg=P/Omega give the exact algebraic rewrite
   F=G+rho*P_avg when Omega>0. Fixed rho controls total penalty scale, not all
   instance differences or relative weights. Keep B1 fixed-lambda and B2/B3
   fixed-rho reporting distinct.
3. Increasing only the physical route horizon gives feasible-set inclusion
   X(T1) subset X(T2) and the optimal-value inequality. Neither elapsed proof
   time nor finite-budget U/L is forced to be monotone. Preserve both members
   of each pair regardless of observed difficulty or binding resource.
4. The A/B deletion retains the same physical problem: integer b and Y,
   binary unique service/assignment and direction, original nonnegative
   quantities and direction upper bounds imply p=b-Y,d=0 or d=Y-b,p=0 on the
   unique served vehicle. Thus continuous p/d remain implicitly integer.
   Original nonzero-service rows exclude a spurious visit at Y=b. This covers
   zero direction capacities and does not divide by those capacities. It is
   exactly the premise of the inherited Round100 proof, not a new integrality
   theorem for split service or simultaneous pickup/delivery.
5. Loaded return and complete handling remain essential: station handling plus
   unloading td*R equals (tp+td)*sum(p) using R=sum(p-d). Capacity applies to
   every route prefix, not cumulative pickup. Do not impose station-stock
   conservation or count the depot in the objective.

## Minimal correct controls and source boundaries

Keep `--round127-mode ms2`, M-B/VD-P, AP off, original H and proof policy for
the full method and the three group deletions. Add independent, default-off
research controls; changing to old `mr`/`mg` is not a valid final-method
single-group ablation because `round127EmitTriple()` enables triples there.

| Arm | Correct minimal source change / identity | Required retained scope |
| --- | --- | --- |
| GI-TBC-R | Existing `--round127-mode s2-root` | Post-R130 inclusive root, pair-only full strengthening, own H/Start, complete root LP then MIP; no outer probe/target/split scheduling |
| minus A/B | Guard the final movement/visit reconstruction emission block in `src/CplexBaseline.cpp`, original lines 3030-3034 | Keep `round98_state_service=m-binary`, state/products, all variable types/domains/physical rows and physical quantity verification |
| minus C_R | Extend `round127EmitCR()` with the independent deletion predicate | Ordered supply (writer original line 1730+) and support cover/conditional handling (2051+); keep other physical/domain/handling rows and zero triples |
| minus C_G | Extend `round127EmitCG()` with the independent deletion predicate | Shared/fallback geometry and objective estimator emissions and dedicated auxiliaries only; retain original Y/S/P domains, state products, direct G cap/floor, own cutoff and physical rows |

The A/B expressions may still be accumulated at original lines 2988-3011;
guarding their actual emission is sufficient and introduces no auxiliary
variables. The active ms2 configuration has no linked-direction reconstruction
row. Do not turn off the whole state-service mode or use the mutually exclusive
Round100 flag to accomplish this deletion.

C_G dependencies are already routed through `round127EmitCG()` in:

- `src/CplexBaseline.cpp`: low-Gini auxiliary creation around 931,
  W_SP creation around 1000, spread fallback around 2929 and linear-estimator
  fallback around 3303.
- `src/IntervalRowFactory.cpp`: family registry around 428-446 and actual
  spread, centering, linear estimator and SP emissions around 613, 654, 720,
  766. Both paths must use the same predicate.

Keep the domain-generating option flags enabled. Masking emission differs from
disabling all fairness/domain processing or Gurobi Cuts. C_G is the complete
declared pack, whereas the narrower Round132 `geom` expression omits only three
geometry families and is not this arm.

Use accepted `s2-root`, never the originally rejected R127 `md`. Current
`round128InclusiveRoot()` identifies `s2-root`; `round127Md()` selects the
root-only chain. Current R133+ code has removed the artificial interval
no-improver infeasibility marker. The historical R127 rejection must retain its
historical identity rather than being attributed to the accepted later root
workflow.

## AM and randomness

Current first-class K1 uses `options.split_threshold` (default .08) in
`src/PaperExternalGiniTree.cpp` around 1809 and passes it to
`evaluateC6AdaptiveMassSplitDecision()` around 7133. The old
`--round47-c6-adaptive-mass-tau` changes a compatibility field and does not vary
this first-class threshold. No first-class threshold CLI exists in the inspected
main. A minimal explicit override must be applied after `applyAlgorithmPreset`
(main original line 2702), validated in [0,1], and recorded/read back as the
effective controller threshold before any parameter comparison is admitted.

The inspected AM evaluator (original lines 1015-1120) checks valid child LPs
first. Infeasible child logic returns before the finite-score threshold;
first-class K1 disables the alternate contraction mode. For finite valid
children it clips normalized improvements and computes eta*mu, with the actual
bound/score tolerances. A post-split bound without strict improvement triggers
terminal exact closure before the threshold test. Otherwise score plus its
tolerance reaching tau splits, and a lower score requests a native bound
target. Report these distinct action causes. An offline replay ceases to be a
complete timing counterfactual after its first changed action.

H's fixed seed 20260626 and full 24 shuffled plus one constructive policy are
separate from the Gurobi seed. Preset application overwrites H fields, so any
future conditional H-seed study would require post-preset effectiveness checks;
there is no reason to add that matrix by default. Solver Seed0/1 comparisons do
not represent identical random trajectories or a runtime distribution.

## Finite pre-run audit and budget

The goal's arithmetic is consistent: B1 50,400 + B2 43,200 + B3 21,600 +
C1 10,800 + C2 21,600 = 147,600 seconds (41 hours); D2 adds 27,000 seconds
(7.5 hours); 41,400 seconds reserve gives 216,000 seconds total. Nominal
positions are 96+24=120 with real shared default baselines. Missing baselines,
diagnostic native solves and affected-case repairs consume the same overall
budget. Count the measured complete outer process once; nested H/LP/MIP are
observations, not extra charges. Reading, ordinary compilation and PDF work
must be separately recorded and not mislabeled native computation.

Before expensive runs, use the existing zero-Optimize exporter and reader on
a nonzero known fixture to check full objective, actual variable types/bounds
and duplicate-preserving row differences. The only A/B differences should be
the two declared rows per station; C_R/C_G differences should match the named
packs; triple rows must stay absent. Preserve failure evidence, not blanket
retries. A same-domain root comparison must fix the initial domain/objective
and cutoff while allowing auxiliaries to reoptimize. Existing local audit
tools are sufficient; no new qualification framework is needed.

Every actual position must bind serialized input and source rows, objective
weight, physical T, Seed, cap, source/PE/DLL/config and independent startup.
Baseline reuse requires those facts plus environment and clock/proof-policy
compatibility, not just an arm name. Keep old evidence at its actual version;
do not relabel old R132 source-reduced data as current qualified performance.
No cross-arm incumbent, bound, tree or Start may enter production. Preserve
adverse and open results, null certificate times on open arms and separate
U/L trade-offs. Root strengthening alone does not prove complete-time gain.

Preflight disposition: mathematical plan is sound under its explicit premises;
the three implementation hazards (historical MR/MG triple restoration,
ineffective compatibility tau flag, and overbroad A/B removal) are identified.
Concrete code and frozen matrix review remains pending before expensive runs.
