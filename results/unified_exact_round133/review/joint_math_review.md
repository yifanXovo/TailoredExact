# Independent review of the joint-objective explanation

Status: PASS for the finite E mathematical explanation and exact metric
reconstruction. This is internal independent code/proof review and a small
independent arithmetic replay, not third-party experiment replication or
validation of an invisible native MIP tree.

Reviewed `joint_objective_gap_note.md`, the complete
`scripts/round133_joint_check.py`, its exact receipt and historical source
manifest. Directly reread R55's station-state exactness and final cover gate,
and R101's actual inventory-event rank/Hall index and necessary resource
domain. The cited distinction between implemented but not admitted penalty
cover and empirical failure is correct. The simple conflict fixes vehicle
labels; a realizable inventory projection cannot be excluded by inventory-
only inequalities without additional information.

`independent_joint_review.py` uses a distinct direct fleet enumeration:
choose the unique owner and signed quantity at each station, then test route
orderings separately for each vehicle. It does not use the author's saved
single-car enumeration as its domain. It independently recovers 59 and 66
full service projections for J2/J3, maximum simple conflict one, and
integer optimum `14411518807585587/36028797018963968`. It independently
evaluates the complete saved joint primal on every actual rationalized row
and bound: 583 rows with 284/298 bounds, LP value
`5404319552844595/36028797018963968`, gap exactly `1/4`.

The authoritative corrected receipt is
`independent_joint_review_receipt_v2.json`. The first checker counted a
pickup as negative delivery in its diagnostic conflict expression. This
could not alter its displayed maximum for these universes, but that
expression was corrected to zero contribution for pickups and rerun. The
v1 receipt remains, with the earlier source identity. Both runs have the
same fleet counts, exact objectives and gap. Measured E outer times are
0.08119739999528974 and 0.07835900003556162 seconds, counted once each;
neither run loaded a native solver or called Optimize.

The proof correctly handles variable integer total inventory tau, loaded
return, S=0, equal-target and equal-weight restrictions, the larger
route-free domain used for the balancing lower bound, and attainable
endpoint fleets. The general nonnegative-lambda minimum formula is
correct; the two intermediate totals are dominated by tau=3. The ideal
decimal and actual loaded coefficient are kept distinct. Recomputing Gini
at a mean on the fixed-total slice can reduce cost even when every column
has that same denominator. The three expensive J2 mixture columns are
correctly reported as `7/12+3 lambda_hat`, not 0.40.

The support RHS direction, outside-station relaxation, and requirement to
prove every full fleet maps into that relaxation are correct. Cumulative
pickup is not replaced by capacity. No complete-facet, general-new-hull,
integer-epigraph-nonredundancy or full-size objective/performance claim
follows from this tiny study. No E mathematical blocker was found.
