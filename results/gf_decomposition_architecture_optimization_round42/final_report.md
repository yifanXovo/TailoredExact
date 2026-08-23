# Round 42 decomposition-architecture optimization

## Outcome

**bounded_systematic_negative_result**

No stable improvement was found within the tested static-single-tree,
paired-block, and terminal-sibling-coalescing architecture families. This is a
bounded result about the six frozen Family A/B/C implementations, not a claim
that every future decomposition algorithm is impossible. The validated default
remains **C6-HGA-FULL, K=4, rho=0.01**; every Round 42 mechanism remains
explicit and default-off.

All 6 promotion candidates completed the 10-instance development panel. None
passed every frozen gate. Validation was therefore ineligible and the final
holdout remained sealed. Across 100 development/reference rows there are
0 false certificates; 95 rows are strict. All
three default-off sentinels match Round 41 in all 25 deterministic fields and
trajectory hashes.

## Causal references

At fixed K2 granularity, ST-K2 uses one proof tree instead of External-K2's two.
Its development geometric means are 1.026238 Work and 1.028505 shifted time:
the architecture is dramatically better on the major witness (0.452427 Work,
0.451140 shifted time) but worse on the strongest control (1.331848 and
1.297014). A single tree is therefore not uniformly beneficial even at fixed K.

Contemporary exact K1 reduces the major witness to 0.782874 Work and 0.758360
shifted time, but loses quarter-width interval strength on the strongest K4
control: 5.531719 Work and 5.361040 shifted time. It is a useful reference, not
a stable candidate. P-GRB was not rerun because no Round 42 candidate passed
development or supported a repaired-C6 claim requiring new P-GRB adjudication.

## Family results

Family A proves that ST-K4 is technically feasible: every static K4 row uses
one exact model and one native optimize, with zero false certificates. Flat
ST-K4 meets the major witness threshold (0.780848 Work, 0.750059 time) but fails
the strongest control (1.329846, 1.299000) and has two catastrophics.
Hierarchical selectors greatly improve the witness (0.426242, 0.409840) but
worsen the strongest control to 1.570105/1.570243. The root K4 bound is unchanged,
so remaining regressions are integer-search effects.

Family B's paired cover is exact but does not interpolate favorably. On the
major witness it uses 4,132.98 Work versus C6's 3,898.99 and flat ST-K4's
3,044.52. Factoring grows average paired nonzeros from 166,368 to 167,556 and
worsens the major ratios from 1.060013/1.050692 to 1.133939/1.114984.

Family C exercises real adaptive sibling geometry with atomic coverage. On the
major witness both variants coalesce two pairs and replace four terminal
leaves. Base/factored counted proof jobs fall from 8
to 4, but one union
remains unresolved at the shared cap and both correctly refuse certification.
Factoring lowers Work from 4,023.49 to 3,754.73 but does not close the union.
On the strongest control the same mechanism reduces proof jobs from
7 to
5 while regressing
to 1.489296 Work (base) or 1.421817 (factored).

## Model, relaxation, and lifecycle diagnosis

The root audit contains 78/90 valid diagnostic rows.
All 60 standalone static/composite rows are valid. Twelve C6-derived initial
census rows are explicitly unavailable on four instances and are left blank,
not imputed. On the major witness, C6 and every K4 static/paired formulation
share root bound `0.028210692227...`; ST-K2/External-K2 share
`0.024872307367...`. Root solves take seconds, while exact runs take up to the
cap, locating the dominant cost in integer proof search. Binary/integer/
continuous counts and model build/read times are retained for every static and
composite row. C6 union ledgers expose total rows/columns/nonzeros and timings
but not a variable-type split; those cells are explicitly blank.

Coverage is valid and lifecycle-complete in all 100 evidence rows. The sibling
audit records considered/accepted pairs, replaced leaf IDs, atomic events,
fallbacks, and unresolved unions. Incomplete union bounds remain union-only.
Complete external covers certify only when every native component is exact,
the minimum component bound equals the independently verified union objective,
and the original-space verifier passes.

## Frozen selection and confirmation

The best lexicographically ranked exact family is PAIRED-K4, but it fails the
major and strongest-control gates and has one catastrophic regression. Its
required uniform factoring refinement worsens the major witness and aggregate
shifted time, so there is no clear general signal for an optional second
refinement. No candidate may advance to validation. `validation_comparison.csv`
and `holdout_comparison.csv` record this non-run status; no holdout candidate
result was inspected.

## Required questions

1. **Fixed-K2 architecture effect:** one tree gives a huge witness win but
   overall gmeans of 1.026 Work/1.029 shifted time, so it is unstable.
2. **ST-K4 feasibility:** yes—exact, deterministic, one model/one optimize.
3. **K4 strength versus fragmentation:** root strength is preserved and the
   witness improves, but control regressions prevent stability.
4. **Common-row factoring:** mathematically exact, empirically inconsistent;
   it does not produce a stable search improvement.
5. **Hierarchical encoding:** it materially improves flat K4 on the witness but
   materially worsens the strongest control.
6. **Paired-K4:** no; it is worse than C6 and both ST-K4 variants on the major
   witness.
7. **Sibling repair of the witness:** no; it reaches the cap with an unresolved
   union and an honest certificate regression.
8. **Sibling preservation of the positive case:** certification is preserved,
   performance is not (1.489 base, 1.422 factored Work ratios).
9. **Proof jobs removed on the major witness:** A removes 7 of 8, B removes 6,
   and C removes 4; fewer jobs alone does not guarantee less Work.
10. **Remaining causes:** unstable monolithic integer search, duplicated paired
    search, larger selector-weighted factored models, and cap-bound union proof.
11. **Completed work:** every A/B/C base and required refinement completed.
12. **Development pass:** none.
13. **Validation pass:** none; validation was ineligible and not run.
14. **Holdout pass:** none; holdout remained sealed and was not run.
15. **Stable broad-qualification candidate:** no.
16. **Rejected bounded space:** flat/hierarchical static single-tree K4,
    adjacent paired K4 with/without common-row factoring, and structural
    terminal-sibling coalescing with/without common-row factoring.

## Verification

- Frozen executable SHA-256:
  `82178ffbbb8106c06661fcec8fd57ce7fe63b1fb9b6340b9d85bd269fc013fbe`.
- C++ tests at implementation freeze: 20/20 passed.
- Round 42 protocol tests: 7/7 passed before final packaging.
- Default C6 equivalence: 3/3 sentinels, 25/25 deterministic fields each.
- Large raw logs and models remain local; compact hashes, manifests, audits,
  and reproduction scripts are retained here.
