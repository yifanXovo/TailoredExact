# Round 38 global-frontier research protocol

## Fixed mainline and exactness contract

The reference is C6-HGA-FULL with K=4, rho=0.01, verified HGA startup,
single-threaded Gurobi seed 0, proof normalization, and the established
open-leaf lifecycle. No K/rho/startup sweep is permitted. All decisions use
complete valid LP bounds, interval geometry, existing certificate tolerances,
and structural leaf ordering only.

Every accepted split must atomically replace its parent with two children whose
closed intervals exactly cover the parent. Pilot LPs are diagnostic until their
bounds are incorporated through the existing exact leaf state. The verified
incumbent, proof cutoff, unresolved-leaf accounting, terminal exact closure,
and final certificate verifier are unchanged.

## Frozen quantities

For complete initial open-leaf bounds b_1,...,b_K, let L=min_j b_j. For
eligible controlling cell i, midpoint children have complete bounds b_iL and
b_iR, with b_i_plus=min(b_iL,b_iR). Define:

* local lift: Delta_local=b_i_plus-b_i;
* hypothetical global bound:
  L_i_plus=min(b_i_plus,min_{j != i} b_j);
* global lift: Delta_global=L_i_plus-L;
* next strict frontier t: the smallest complete open-leaf bound strictly above
  L by more than certificate tolerance;
* frontier completion: min(b_i_plus,t)-b_i, when a strict frontier exists;
* completion indicator: b_i_plus >= t within certificate tolerance.

The sorted initial and hypothetical post-refinement bound vectors, frontier
plateau size, refined-descendant controlling persistence, immediate bottleneck
displacement, target/requeue/split/closure sequences, common-UB final gap,
common-window proof AUC, valid LB, certificate, Work, nodes, and exact/process
time are recorded. Time, Work, nodes, instance IDs, V/M, scenario labels, and
historical outcomes never enter a decision.

## Hypotheses and staged decision

* **G2-A diagnostic/candidate:** refine only the unique current controlling
  initial cell when its complete midpoint child bound reaches the next strict
  frontier within tolerance. If no next strict frontier exists, the minimum is
  tied, or completion fails, resume unchanged C6.
* **G2-B exploratory alternative:** only if G2-A evidence requires it, compare
  a small structurally defined candidate set by lexicographically maximizing
  the hypothetical sorted open-bound vector. It must be frozen separately
  before any confirmatory use.
* **G2-C diagnostic:** measure whether descendants remain controlling, how
  quickly another leaf displaces them, the initial frontier gap/plateau, and
  later descendant target/requeue/terminal-bottleneck participation.

First run read-only trajectory forensics on the stable Round 37 positive and
regression witnesses. Implement the minimum default-off telemetry/policy needed
for the resulting structural test. Exploratory smoke uses 120--180 second
paired runs on a predeclared subset. A candidate advances only with zero false
certificates, complete exactness/lifecycle records, genuine mechanism exposure,
and evidence beyond the original positive witness. Any serious diagnostic
stage uses 300--600 seconds. Selected confirmations use 900--1200 seconds;
1800 seconds is reserved for a genuinely necessary predeclared difficult
confirmation. No run may use 3600 seconds or more.

G2-A is not promising if it retains the stable Round 37 V50 regression or wins
only the original V20 witness. No outcome changes C6 automatically. A coherent
candidate becomes at most a later broad-validation candidate.

