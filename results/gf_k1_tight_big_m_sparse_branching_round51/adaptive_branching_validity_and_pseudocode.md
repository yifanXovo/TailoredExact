# A1 root-guided sparse adaptive branching

## Fixed design

`a1-root-sparse-2x2` is developed only on `m1-tight-big-m-v0`: M1 row-specific subset-duration coefficients, v0 cardinality symmetry, and otherwise the frozen Round 50 fixed-interval formulation and Gurobi settings. Candidate selection is root-state dependent but rule-invariant. It uses no MIP pilot, callback, learned classifier, instance feature classifier, historical lookup, known optimum, or post-start policy change.

Eligible variables are original integer or binary semantic primitives in this fixed ordinal order: routing arcs, visit selections, operation modes, pickup quantities, drop quantities, vehicle loads, and final inventories. Continuous variables, auxiliary encodings/selectors, fixed domains, and values integral within `1e-6` are excluded.

At most four variables are admitted, in decreasing root fractionality order with semantic-family ordinal and canonical name tie-breaks. At most two may come from one family. Each candidate receives exactly two child LP probes, so at most eight child LP reoptimizations occur. At most two variables receive positive priority. After those variables are resolved, native Gurobi branching controls the remaining tree.

## Disposable lifecycle and cleanliness

The root is solved once as `PaperLpRelaxation`; that result supplies the root objective, primal values, original types, and original bounds. No duplicate root solve is launched. Each child probe independently reads the immutable canonical M1-v0 LP, applies one bound override, reads the bound back exactly, relaxes all types, optimizes, and destroys its model. Independent copies are used rather than claiming basis restoration.

After every probe model has been destroyed, the terminal MIP freshly reads the immutable canonical LP. It has no child bound override, presolved state, basis, incumbent, or retained model. The backend assigns an all-zero BranchPriority vector plus the selected sparse priorities, updates the model, and reads the complete vector back exactly. If application or readback fails, that unoptimized model is destroyed and a fresh default-priority terminal model is used with the remaining global time.

The same external process cap covers model construction, the root LP, all probes, priority handling, the terminal MIP, and evidence finalization. Official Work is the sum of root, probe, and every terminal-attempt Work. Terminal-only metrics are diagnostic and never promotion metrics.

## Pseudocode

```text
root = solve PaperLpRelaxation once on immutable M1-v0 model
if root is infeasible or closes cutoff:
    fallback = default branching
else:
    eligible = original nonfixed fractional integer/binary primitives
    sort eligible by (-fractionality, family ordinal, canonical name)
    pool = first <=4 while admitting <=2 from each family

    for j in pool:
        down = fresh LP copy with ub[j] = floor(root[j])
        up   = fresh LP copy with lb[j] = ceil(root[j])
        G0 = max(cutoff - root_objective, 1e-9)
        delta(direction) =
            G0                              if proven infeasible
            max(0,min(G0,Lchild-L0))        if optimal
            invalid                         otherwise
        if both directions valid:
            score[j] = max(delta_down,1e-7)*max(delta_up,1e-7)

    rank valid j by (-score, original pool order)
    if none valid or all have zero improvement:
        fallback = default branching
    else:
        priority[best] = 2
        priority[second, if present] = 1
        priority[all others] = 0

terminal = fresh MIP read with only the audited priority vector
official Work = root Work + sum(probe Work) + sum(terminal-attempt Work)
```

For a valid probe direction, infeasibility uses the full root gap `G0`; an optimal child bound is clipped to `[0,G0]`. A candidate requires two valid directions. Score ties retain deterministic pool order. General-integer child bounds use mathematical floor and ceiling, not binary assumptions.

The fallback is determined only from the current root/practical probe validity and exact attribute readback. No forbidden metadata or historical result participates.
