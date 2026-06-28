# Penalty Movement Lower-Bound Cuts

Date: 2026-06-28

The option:

```text
--penalty-movement-lb-cuts true|false
```

adds a valid necessary condition derived from the incumbent cutoff.  Let
`P0` be the penalty at the initial inventories and let `Pmax` be the penalty
budget implied by the incumbent cutoff and interval Gini floor.  One unit of
inventory movement at station `i` can reduce penalty by at most `w_i / T_i`.
Therefore any improving solution must move at least:

```text
ceil((P0 - Pmax) / max_i(w_i / T_i))
```

inventory units when `P0 > Pmax`.  The relaxation can safely impose this as a
minimum aggregate movement row.  If the required movement is nonpositive, no
cut is added.

This is a lower-bound strengthening only.  It does not use incumbent routes,
sampled route pools, or heuristic evidence.

