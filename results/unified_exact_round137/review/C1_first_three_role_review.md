# Independent interim AM review: first three roles

Disposition: **PASS for these nine observations and the inspected Section6.1
prose**. Separate reviewer `/root/independent_review`, 2026-10-28
(Asia/Shanghai), while K35 tau.04 is active. Selected the exact default and
extra launches by declared role/method: defaults3/7/12 and extras73-78.
Read only their small endpoints, control readbacks and two small decision CSVs.
The actual `am_decisions` function was source-extracted and evaluated with
stdlib CSV reads, without importing the heavy project reader graph. No native
run/build, LP/journal parsing, full aggregation, archive, PDF or native asset
was used. Only this review was written.

The experimental costs below come from three actual independent complete
native runs per role. Source extraction/CSV joining describes this review's
read-only audit, not an offline substitute for those experiments. The latest
K15 manuscript wording makes that actual-run distinction explicit.

## Configuration and recorded decisions

All nine observations are qualified and performance-eligible. Within each
role, input, PE, physical parameters, cap and Seed0 match. All own H executions
are complete, with matching nonempty semantic/fleet hashes across the three
thresholds. Post-preset parameter JSONs report the actual .04/.08/.16
thresholds, all group deletions false; their readback hashes and pre-closeout
audit flags match.

| Role | Finite gate score in each run | Recorded sequence in each run |
| --- | ---: | --- |
| K-15-S | .00035668721841524304 | native-target; non-strict terminal exact-close |
| K-20-S | .00047846635674276053 | native-target; non-strict terminal exact-close |
| UC-B20-B | .00031862963447695959 | three logical one-child-infeasible splits; native-target; non-strict terminal exact-close |

Each finite gate has negative tolerance-adjusted margin at every tested tau.
The joined ledger classifies the later exact-close rows separately as
FINITE_TERMINAL_NO_STRICT. UC's three split rows per run have null finite
score/margin and explicitly do not depend on tau; they are not three finite
threshold crossings. The inspected authoring source preserves that distinction.

## Complete outcomes and materiality

Certificate times, in tau .04/.08/.16 order, are:

| Role | .04 seconds | .08 seconds | .16 seconds |
| --- | ---: | ---: | ---: |
| K-15-S | 113.062180668 | 112.769303117 | 113.314699567 |
| UC-B20-B | 4.219656583 | 4.148974274 | 4.081174040 |

Both roles certify at every threshold. Their maximum observed time spreads,
.545396450s and .138482543s, are below the declared max(10s,10% of faster
certificate time) thresholds. No substantive time difference is established.

All three K-20-S runs remain open at the same own U=.7168065462777502, with
null T_cert. Their L values, again .04/.08/.16 order, are
.7053663427702909/.7053557934942464/.705385999952154. The small capped
dual differences do not establish a general tau ranking. In particular, the
exact-close action schedules an exact parent solve; it is not an assertion
that a certificate was completed. The K20 paragraph uses this counterexample
correctly.

The latest manuscript describes observed gate/action agreement and actual
complete-run cost, and confines its sensitivity conclusion to these finite
comparisons. K20 is not used to establish a general tau ranking. The existing
mathematical rule that offline replay after a first divergent action is not a
full speed counterfactual remains separate from these actual runs. The prose neither converts
the logical splits into score evidence nor treats terminal labels as proof
status. No concrete correction was found in this limited scope.

The K35 role, complete C1 summary, actual Seed1 repeats and final120/PDF review
remain pending. No rerun or forced split is warranted by this review.
