# Round 38 representative trajectory comparisons

The machine-readable rows are in `representative_trajectory_comparisons.csv`.
All gaps below use the pair's common verified upper bound.

## Stable V20 positive (ordinal 8, 900 seconds)

C6 initially targets `L1` from `0.206824` to `0.271766`. G2-A first
completes the four-cell census, rejects midpoint children with
`b+=0.208433 < t=0.289176`, discards them, targets the unchanged `L1` to
`0.289176`, then targets `L2` and reaches `0.329851`. The common-UB gap
improves by `0.112251` and AUC by `0.094528`. No G2-A child becomes a live
descendant.

## Stable V50 adversarial witness (ordinal 10, 900 seconds)

G2-A rejects `b+=7.461556 < t=7.555718`, then its two native target steps
match the C6 bound milestones. Final common-UB gaps tie; G2-A AUC is worse by
`0.000789`. Again, the sequence differs only because the rejected pilot and
complete census precede the same parent-target progression.

## Confirmed V50 tight-T regression (ordinal 11, 900 seconds)

C6 first targets `L1` to `0.514198`, reaches `0.558341`, and then performs an
atomic child-infeasibility split before reaching lower bound `0.613715`.
G2-A rejects `b+=0.540854 < t=0.623055`, discards its children, sends the
unchanged parent directly toward `0.623055`, and remains deadline-open at
`0.607633`. The common-UB gap change is `-0.009008` and the AUC change is
`-0.010889`. This is the decisive bidirectional target/split reordering.
