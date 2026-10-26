# Active formulation families

Round 55 re-audited the complete stable set below. The pair and triple
support-duration cover families showed no activity, no nonzero dual
participation, and no isolated root-bound contribution in the frozen
162-diagnostic census, but a
uniform live removal of triple covers (SF-R1) failed the severe-regression
gate. Both families therefore remain active. See `cut_family_efficacy.md`.

The machine-readable source of truth is the Round 54
`active_family_manifest.csv`/`.json`, generated against
`paper-k1-am-sf`. The active set contains 17 families:

- interval Gini bounds and direct Gini cap/floor;
- interval-tight G-times-binary McCormick hull;
- final-inventory penalty and movement-reachability domains;
- inventory conservation and visit--inventory links;
- verified-incumbent objective row, objective lower estimator, and penalty
  lower-bound closure;
- W_SP McCormick rows and its paper-safe objective estimator;
- pair and triple support-duration covers;
- connectivity-flow extended formulation;
- iterative domain propagation and tight denominator bounds.

The representative D1 fixed-interval model contains 3,764 rows, 1,404 columns,
16,888 nonzeros, and zero exhaustive subset-duration rows. Some domain and
propagation counts are exposed as bound bundles rather than individual model
rows; the manifest states that limitation instead of inventing telemetry.

Inactive families include the exhaustive subset-duration block, Gini-spread,
required-movement, transfer-cutset, subset-inventory, dynamic support-duration,
all tailored dynamic user cuts, inventory--route root closure, custom branching
priorities, and symmetry research. No family is claimed novel without a
completed literature review; unverified candidates are explicitly marked
pending. Round 55 does not make a novelty claim for MC4, VD-P, or VD-J.

The research policies `round55-sf-mc4`, `round55-vd-p`, and `round55-vd-j`
replace or extend only the documented product block for controlled
qualification. They are not part of `paper-k1-am-sf`. Aggregate McCormick rows
are exact and strictly strengthen some root relaxations, while VD-P/VD-J are
exact station-state extensions; neither fact alone establishes faster MIP
performance.

VD-P passed fixed-interval confirmation and long checks but failed full K1
integration because of one severe regression on the frozen major witness.
It remains default-off as `research-k1-am-sf-vdp`; the stable F0-CLEAN active
family set is unchanged.
