# Split-point counterfactual

The frozen gamma-veto timing rule activated a point decision on two development
rows. Direct PMM differed from midpoint on 2 of 2
activated runs and reduced total Work on 1 of 2 rows.
Both rows were false-split cases because the matched retain arm used less Work
than midpoint, PMM, and FPMM. PMM and FPMM were identical on both rows, so
frontier clipping supplied no additional benefit.

The implementation used the allowed deterministic monotone-root fallback. It
solved the same continuous left/right LP value functions directly, validated
both children and monotonicity at every query, and never evaluated an empirical
point list. All selected nonmidpoint intervals passed exact-coverage and
minimum-width audits.
