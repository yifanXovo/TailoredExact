# Preregistered first paper panel

Six new problems come from two existing safe station sources: the CITI
R57 station table (443 original rows, 442 qualified physical rows), and
the CABI frozen response/safe table (865 rows). Their exact SHA256 values,
row mappings and unchanged loader identities are in source_recipe.json and
input_manifest.json. No website or GBFS acquisition occurs in Round122.

Before generation, commit e8b02d6b4 froze the thin adapter, exact
source-specific FAMILY strings and complete eight-group schedule. The
six serialized inputs were then generated once with R57 selection and
R109 landscape mathematics: original four anchors/hash ties, .44-.56
target fractions, three-decimal coordinates, six-decimal max-normalized
weights, total correction/sign repair and artificial centroid depot.
Only each instance's first line changes to its preregistered Q vector.
Selection and landscape both bind the exact source-specific FAMILY.
No H/LP/MIP screening, difficulty filter, resampling or result-based salt
change is allowed. Zero-Optimize original compact exports establish
parser/model references only.

| Problem | Source | V/M | Geometry/replicate | Stock | Q | T | Arm cap |
|---|---|---|---|---|---|---:|---:|
| PB-C20-B | CITI | 20/2 | compact/1 | balanced | 30,30 | 3600 | 900 |
| PB-B20-S | CABI | 20/2 | regional/2 | shortage | 20,40 | 7200 | 900 |
| PB-C35-U | CITI | 35/3 | regional/1 | surplus | 20,25,30 | 10800 | 2400 |
| PB-B35-B | CABI | 35/3 | compact/2 | balanced | 25,25,25 | 7200 | 2400 |
| PB-C50-S | CITI | 50/4 | compact/1 | shortage | 30,30,30,30 | 10800 | 3600 |
| PB-B50-U | CABI | 50/4 | regional/2 | surplus | 20,25,35,40 | 18000 | 3600 |

All problems use lambda=.15, pickup/drop60/60 and original Euclidean/1.5
travel. Source-specific historical and within-panel station overlaps,
sum(w), lambda*sum(w), initial totals and empty-fleet G/penalty are retained.
The source/scale/regime/geometry/Q/T combinations vary together. This is
not a full factorial design, six cities or an IID sample, and cannot
separately estimate a causal size or inventory-regime effect. Changing
total weights must not be described as a pure scale effect.

The first six groups use Seed0 and four complete methods each: cold
P-GRB, ENS-C, M-B and MB-D1. The last two repeat PB-B35-B and PB-C50-S
with fixed Seed1 and all four methods. In the schedule below, P denotes
cold P-GRB, ENS denotes ENS-C, MB denotes M-B and D1 denotes MB-D1.

| Group | Problem | Gurobi Seed | Serial method order | Cap per arm | Nominal group seconds |
|---:|---|---:|---|---:|---:|
| 1 | PB-C20-B | 0 | P → ENS → MB → D1 | 900 | 3600 |
| 2 | PB-B20-S | 0 | ENS → MB → D1 → P | 900 | 3600 |
| 3 | PB-C35-U | 0 | MB → D1 → P → ENS | 2400 | 9600 |
| 4 | PB-B35-B | 0 | D1 → P → ENS → MB | 2400 | 9600 |
| 5 | PB-C50-S | 0 | D1 → MB → ENS → P | 3600 | 14400 |
| 6 | PB-B50-U | 0 | P → D1 → MB → ENS | 3600 | 14400 |
| 7 | PB-B35-B | 1 | ENS → P → D1 → MB | 2400 | 9600 |
| 8 | PB-C50-S | 1 | MB → ENS → P → D1 | 3600 | 14400 |

Every arm independently pays for its own applicable H, models, proofs and
Starts. Each group has the same six directed comparisons: D1/P, MB/P,
ENS/P, D1/MB, D1/ENS and MB/ENS. The panel therefore contains 32 mandatory
positions, 79200 nominal producer seconds and 48 comparisons. Its primary
new-problem layer is six Seed0 roles; its two Seed1 blocks are sensitivity
evidence on the same inputs. All eight groups remain required after an
unfavorable observation. No best-of-Seed, substituted Seed0 winner, pooled
independent-sample win rate or automatic extra batch is formed.

Pair decisions reuse the unchanged R108/R120 certificate-first rules.
For two open methods, own U and qualified L give signed gap=U-L;
a_U=max(.001,.01*abs(U_control)) and
a_gap=max(.001,.10*abs(gap_control)). A material decrease in either U or
gap with no material increase is WIN; the reverse is LOSS; opposing
material changes are MIXED; otherwise the comparison is TIE. Severe open
regression requires both
U_candidate-U_control >= max(.001,.05*abs(U_control)) and
gap_candidate-gap_control >= max(.005,.25*abs(gap_control)).

A candidate-only qualified certificate is WIN. A control-only qualified
certificate is LOSS and severe. With two certificates, the production
time threshold is a_t=max(30,.10*time_control): a saving or excess at least
a_t gives WIN or LOSS, respectively; smaller changes give TIE. A certified
time regression is severe only if time_candidate >= 2*time_control and
time_candidate-time_control >= 120 seconds. Only actual certified times
are divided. Tiny signed gaps are retained; a negative signed gap is not
used in a percentage-gap ratio. Missing necessary evidence remains
UNEVALUABLE, without shrinking denominators.

The single stage decision uses the following priority order. Proven
invalid proof sources or pruning take PROOF_RELIABILITY_PRIORITY.
Necessary execution, input/production identity, physical, clock, storage
or recovery evidence that cannot be established within authorized
resources takes BLOCKED. Once all 32 positions are valid, any severe D1/P
regression among the eight groups, or at least two D1/P LOSS observations
among the six new Seed0 roles, takes DO_NOT_SELECT_D1_AS_PAPER_PRIMARY.

Without those vetoes, FREEZE_D1_AS_PAPER_BENCHMARK_CANDIDATE requires all
of these finite conditions:

- All six new Seed0 D1/P comparisons are evaluable, with at least four
  WIN and at most one LOSS.
- At least three new roles actually execute an installed D1 extension,
  including at least one V35 or V50 role. At least two exposed new roles
  have a material D1/M-B WIN or a certificate that M-B does not obtain.
- D1 obtains at least as many certificates as M-B across the six new
  roles. Individual exchanges are allowed; there is no separate ENS-C
  dominance gate.
- Both fixed Seed1 D1/P comparisons are evaluable, non-LOSS and nonsevere,
  and remain displayed beside their corresponding Seed0 observations.
- No proof reliability risk remains unresolved.

All other complete panels take BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION.
Pure performance loss, all-open results or unexposed D1 remain valid
observations. Every outcome ends this batch without automatic further
sampling. A positive decision freezes a paper candidate while retaining
ENS-C as default; it does not establish universal acceleration or
statistical significance. A nonpositive decision retains an existing
complete method as the paper reference, chosen from the actual tradeoffs
and stated explicitly in the final report. New V35/V50 nonzero numerical
certificates are counted separately from zero certificates and open
quality improvements.

The outer resource ceiling is 100000 seconds. Qualification/necessary native
diagnosis has a 3000-second soft plan and 6000-second authorized ceiling,
with no hard process-count gate. Full actual and uncertain starts,
failed attempts, nested native timers and engineering/review/publication
scopes are retained. Storage/path measures support reproducible execution;
they are not mathematical contributions.
