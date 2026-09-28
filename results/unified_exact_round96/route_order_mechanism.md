# F5-final: a measured travel-time barrier released by order

The independent sequence is saved under `route_order/F5_final/order/`.
Original R83 already changes ownership and quantities from the R87 witness,
ending at F=.30232787703800834. Its subsequent exhausted closure is the baseline
for the incremental order test; this is not the original fixed-owner diagnostic
set and its improvement is credited to R83.

The one new neutral move transfers station 35 within vehicle 3 from near the
end to the front, keeping all operations, owners, served stations and F fixed:

- Before: 0,14,4,6,7,18,28,49,38,35,46,0; duration 7149.3757100992862.
- After: 0,35,14,4,6,7,18,28,49,38,46,0; duration 7060.1792697386227.

Travel falls by 89.1964403606635 s. The original R76 quantity closure can then
make the same-route pair change Y4:12→13, Y49:2→1: one additional drop at 4 and
pickup at 49. Its net inventory change is zero, but total pickups rise by one,
so full handling increases by 120 s. New duration is 7180.1792697386227≤7200.
Without this reorder the same quantity proposal would require
7269.3757100992862>7200. Original objective falls to .3015296068778552.

Thus this specific incremental gain has a directly verified time-feasibility
mechanism. It does not require a new objective surrogate or a larger quantity
direction: an existing pair move becomes feasible. Other vehicles retain their
durations. Complete F5 fixed-original-route quantity optimality remains a
separate result; the new closure changes that structure and still does not
match the old verified P witness .2999915384940973.

D7 has larger incremental gains but also interleaved old intervehicle moves;
they are reported as the compound finite order/physical closure, not assigned
to a single pure permutation. Both U6 snapshots shorten durations without an
incremental original-F gain, which is a retained negative for the mechanism.
