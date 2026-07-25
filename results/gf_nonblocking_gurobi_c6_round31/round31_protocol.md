# Round 31 frozen protocol

## Research question

Can one uniform, exact, paper-compatible, nonblocking external-Gurobi Gini
tree approach broad same-solver superiority over one-thread plain Gurobi
without time, Work, node, solution, attempt, retry, family, size, seed, path,
or historical-optimum dispatch?

## Order of work

1. Preserve and hash the starting dirty workspace.
2. Freeze and generate the six sealed held-out instances.
3. Complete failure-instance and leaf-structure forensics using only retained
   historical evidence.
4. Implement at most one primary C6 prototype and one fallback only for a
   correctness, API, or clear mechanical failure.
5. Select and document one uniform C6.
6. Freeze source, parameters, commands, executables, and official matrix.
7. Pass all clean-build and Stage 0 correctness gates.
8. Execute official Stages 1--5 serially.
9. Execute Stage 6 only if the frozen 300-second broad-nonregression gate
   passes.
10. Analyze, package, commit, push normally, and verify the live branch.

No official result may tune or change the frozen C6 candidate.

## Sealed held-out seed derivation

The derivation was frozen before instance generation, inspection, solver
execution, or C6 implementation.

For each `(family, V)` in
`{high_imbalance, moderate, tight_T} x {20, 50}`:

```
material = starting_commit + "|" + "round31-sealed-heldout"
           + "|" + family + "|V" + decimal(V)
digest = SHA256(UTF8(material))
seed = 1 + (integer(digest[0:16], base=16) mod 2147483646)
```

Frozen values:

| family | V | seed | derivation SHA-256 |
|---|---:|---:|---|
| high_imbalance | 20 | 1968399862 | `feb741b57a765f11165805ba9d5d0d4046d3880175471d2552467577befd7413` |
| high_imbalance | 50 | 802548647 | `adf8b6c977f310765df7d08ca3910fe4bd3b264a20632f1d05a6dbe76292fd5e` |
| moderate | 20 | 311185674 | `7a591a88a927e6dfeb1f99508743ad712f2ac455ef71d8e61655ead07a95ed24` |
| moderate | 50 | 1112848618 | `2eb71ea887783e45d8c76174d8eb35358229a30cf5567aa3a9ff2cb68245fcda` |
| tight_T | 20 | 2113109204 | `5b554cc6109e49b721372da7dc38c5d7e228c0101b613f2082d2037f8a7c410d` |
| tight_T | 50 | 1973327304 | `00098045f57894b1d1dcba9c99038516c31bc87c545b7ec77d48b4591790a678` |

The existing deterministic three-cluster generator is used with `M=3`,
`Q=30`, `lambda=0.15`, and the established family time parameter:
`T=3600` for high-imbalance and moderate, `T=2400` for tight-T. The generated
instances are official sealed tests only and cannot influence C6 design,
parameter selection, or development.

## Existing mathematical parameters

- Certificate tolerance: `1e-7`
- Initial intervals: `4`
- Interval geometry: binary midpoint
- Maximum depth: `8`
- Minimum interval width: `1e-4`
- Sole policy threshold: `rho=0.01`

No additional tunable strategy parameter is planned. Any native-bound
termination target must be an objective-defined mathematical milestone.

## Correctness invariants

C6 must preserve complete improving-range coverage, exact interval
representation, atomic replacement, valid inherited bounds, complete LP
statuses, independently verified incumbents, and the minimum-valid-open-leaf
global lower bound. A partial native bound changes an open leaf's state; it
never closes that leaf. Closure requires infeasibility, exact optimality, or
verified objective cutoff. Strict certification requires every relevant
coverage element to close.

## Official execution discipline

- One solver thread
- Gurobi Seed 0
- One process-entry deadline
- 300-second process cap
- Five-second engineering shutdown margin
- Serial execution only
- Common independently verified upper bounds
- Observed bound-progress AUC only from complete compatible traces

Stage 6 uses 1,200 seconds and is conditional on the frozen short-run gate.
