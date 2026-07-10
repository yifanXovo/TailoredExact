# Vector-Driven Route Support And Cutset Cuts

Root-limited activation selects candidates from an actual root relaxation and writes only violated global rows into the final model. Callback-limited activation uses the current relaxation vector. Both paths enforce generic subset-size, cut-count, and violation controls. Broad static all-subset generation is not the selected default policy.

The callback/root LP vector is used only to select candidate subsets. It is not
used as proof. Every generated row must be valid for all original feasible
solutions under the compact route convention.

## Support-Duration Cover

For vehicle `k` and station subset `A`, if a conservative lower bound proves
that visiting every station in `A` is impossible within the route time,

```text
depot_cycle_lb(k,A) + handling_lb(k,A) > T_k
```

then the valid cover row is:

```text
sum_{i in A} z[k,i] <= |A| - 1
```

The current implementation uses exact subset permutation cycle lower bounds for
small selected subsets and a conservative minimum handling lower bound.

## Directed Route Cutset

For any subset `A` not containing the depot and representative station `l in A`,
a route that visits `l` must cross the boundary into and out of `A`. The combined
directed cutset row is:

```text
sum_{i notin A,j in A} x[k,i,j] + sum_{i in A,j notin A} x[k,i,j] >= 2 z[k,l]
```

These rows rely on the compact route arc variables `x[k,i,j]` and the usual
depot-indexed flow convention. Candidate subsets can be chosen from root or
callback vectors, but row validity is independent of the observed vector.

Rows generated from heuristic route failure alone are not paper-safe.
