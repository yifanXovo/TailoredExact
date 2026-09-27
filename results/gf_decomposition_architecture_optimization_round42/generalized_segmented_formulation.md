# Generalized static segmented formulation

## Scope

Round 42 replaces the Round 41 midpoint-specific K2 construction with the
solver-neutral `StaticSegmentedBlockSpec`. A block is defined by a union
interval, an ordered list of exact child intervals, the complete interval row
factory result for every child, feasibility flags, the verified incumbent,
the formulation mode, and a deterministic identity.

The specification accepts K2, K4, fixed adjacent blocks, and unequal adaptive
sibling intervals. It rejects empty lists, reversed intervals, gaps, overlaps,
and endpoint mismatch. This validation occurs before the canonical LP writer
or native backend is called.

## Core formulation

For ordered segments `I_k=[L_k,U_k]`, the model contains one binary selector
`z_k` and enforces exactly one feasible selector. Infeasible segments have
`z_k=0`. Selected copies of `G`, inventory bits, bit activations, and G-bit
products preserve the Round 41 Core perspective block. Exact sum-back rows
recover the original-space variables. Selected domains use the interval-local
bounds of `I_k`; the global variables keep the union domain.

Every segment receives its complete deterministic interval row pack before
optimization. The native solver sees one immutable model and one final MIP
optimize for each block. Decoding returns original route variables, and the
original independent verifier recomputes feasibility and objective before a
strict certificate can be accepted.

## Determinism

The identity hashes the union endpoints, ordered segment endpoints, feasibility
flags, formulation mode, factoring/hierarchy controls, incumbent, and complete
ordered row-factory content. Canonical model SHA-256 values are recorded per
run. No callback creates segments, child models, or rows.

## Compatibility

An empty explicit segment list still selects the historical equal-midpoint K2
geometry, so Round 41 `ST-K2-P-Core` remains reproducible. All Round 42 controls
are default-off.
