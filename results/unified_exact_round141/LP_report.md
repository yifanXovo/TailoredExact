# Round141: what the count disjunction adds

The three source-matched continuous domains provide new numerical lower-bound
information beyond a Gini midpoint split. Conditional TC2 chords account for
the substantial cover gains. The D1 scalar projection separates two actual D0
optima, but D1 does not increase the reoptimized common-root objective on any
of these domains. These are separate findings.

## Domain and experiment identity

The selected R140 archive members and their hashes are in
`inherited_dependencies.json`. The five saved-point scores reproduce the
governing goal; only K35, RB35-T2 and K20 enter new LP optimization. Thresholds
are physical exact dyadic values. K35 uses
9700060735874915/9007199254740992; the other two use
18014398509481983/18014398509481984, which must not be replaced by decimal 1.
The selected count intervals are [2,33], [0,31] and [0,18], respectively.

Every count/D0/D1 comparison within a domain holds the input, objective (including
ObjCon), support, Gini interval and actual serialized improvement cutoff
fixed. Parent old TC and TC2 rows remain in every restricted child. Count
restrictions are explicit canonical rows; conditional variants append a
new numerator chord after nested count propagation. The plain variant uses
the same restriction without the new conditional chord.

Thirty-nine continuous optimizations were performed: three reconstructed
parent controls, 24 restricted children (two pivots, two sides, plain and
conditional), six common-source D0/D1 roots, and six actual Gini midpoint
children. Each uses explicit Gurobi Seed0, one thread, serial execution and
affinity mask 4. Canonical ordinary MPS is serialized, hashed, and read back
before Optimize. Objectives are numerical optima with the inherited quality
checks, not exact rational certificates. These offline sources are never
injected into complete methods.

## Count restriction and conditional chords

The default threshold maximizes the weighted parent chord remainder, with
the smaller physical threshold resolving a tie. Balanced and LP-floor
pivots are compared without changing thresholds. LP-floor has the stronger
qualified conditional cover in all three diagnostic domains and is frozen
as the single online pivot rule before the full pilot.

The table gives raw numerical optimal values, prior to the common 1e-7
downward floor margin. Both restricted sides are retained; a cover is their
minimum, never their maximum or average.

| Role | Parent | Plain balanced cover | Conditional balanced cover | Plain LP-floor cover | Conditional LP-floor cover |
|---|---:|---:|---:|---:|---:|
| K35 | .226044051468 | .226044149486 | .235747225222 | .226044225897 | .240140105053 |
| RB35-T2 | .135449234777 | .135449234777 | .142324211877 | .135463276624 | .146301752943 |
| K20 | .234821877885 | .234821877885 | .251586407105 | .234833819923 | .255556702786 |

The saved parent optimum remains feasible on one balanced plain side, so
that split alone has no genuine cover increment there. K35's balanced
difference of about 9.8e-8 and LP-floor difference of about 1.74e-7 are
numerical scale and do not establish substantive plain gains. LP-floor
can remove a fractional count in the open integer gap; the RB35-T2 and K20
plain increments are about 1.4e-5 and 1.2e-5. Appending the conditional chords gives
the much larger increments in the last column. A saved H-row violation is
not substituted for an optimized objective increment.

## Comparison with the original Gini axis

The Gini children are exported with the actual full writer, including all
support and product rows. Their parent has exactly the same row multiset,
bounds, types and objective as the corresponding source-matched parent;
`gini_match.json` records this check. Merely changing a G bound would not
establish that identity. The following are conservative qualified floors.

| Role | Gini midpoint cover | Count conditional cover | Difference |
|---|---:|---:|---:|
| K35 | .227601297782 | .240140005053 | .012538707272 |
| RB35-T2 | .135641397962 | .146301652943 | .010660254981 |
| K20 | .235396128950 | .255556602786 | .020160473836 |

Thus this finite count axis yields information not obtained by the matched
Gini midpoint on these domains. It is not a dominance theorem over all Gini
pivots, all possible domains or the full algorithm.

## Common floor versus conditional floor

D0 and D1 are built from identical two-sided qualified floors. D0 retains
the binary and both links but uses the common minimum; D1 uses the side's
conditional value. The scalar projection minimizes over every feasible
fractional binary value. No arbitrary fixed-b violation is counted.

| Role | Pivot | beta0 | beta1 | D0 optimum | D1 optimum | D1 projection violation at actual D0 optimum |
|---|---:|---:|---:|---:|---:|---:|
| K35 | 8 | .241539845750 | .240140005053 | .240140005053 | .240140005053 | 0 |
| RB35-T2 | 5 | .146301652943 | .150566842398 | .146301652943 | .146301652943 | .000804724405 |
| K20 | 7 | .255556602786 | .268192485045 | .255556602786 | .255556602786 | .002669272228 |

D1 changes the feasible projection for two actual optima but admits other
points with the same optimal objective. The last-bit negative differences
on reoptimization are floating-point scale and are not a D1 weakening.
Independent review also checks the actual serialized objective endpoints
and ObjCon when computing this separation.

These floors are weak compared with the same carrier's observed Native
root/early bounds: K20's two floors are below about .44698 at displayed
0 seconds; RB35-T2's are below about .15862 at 9 seconds; K35's are below
about .26602 at 4 seconds. This limits the expected direct bound effect.
It is an observation from those search paths, not a redundancy theorem for
a different integer model or every future node. The qualified cover gains,
two projection separations and inexpensive online probes support a finite
four-role complete-method pilot, not automatic eight-role expansion.

## Costs, failures and limits

`reports/LP.csv` includes construction and Optimize wall times for both
sides of each variant; `reports/projection.csv` gives each D0/D1 cost.
The diagnostic meter charges actual experimental outers once, including
failed attempts, and separates pure analysis. No MIP is optimized in this
standalone LP study. Full methods independently pay their own H, root LP,
two new probes, model construction and validation.

An initial compressed-MPS serialization/read failure occurred before
Optimize and is retained. Nine initial Gini exports used displayed U;
two had last-bit cutoff mismatches with the source. They are retained
as unmatched construction attempts and were not optimized. The corrected
exports use the exact serialized cutoff and pass parent identity checks.
No healthy sealed solver output was repeated to repair a report or reader.

The separate saved-point safe-M screen supplied by the goal does not show
projection separation for directly activating two conditional TC2 rows with
one fractional binary. This study therefore does not open that second full
production panel. The current evidence concerns conditional count LPs and
their objective floors, with the strict scalar scope proved in
`mathematical_analysis.md`.
