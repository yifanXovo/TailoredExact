# Future incremental-optimization notes

Round 28 intentionally implements no incremental optimization. Any future
work must be justified by the measured repeated-model, presolve, root, Work,
and runtime evidence produced here.

Potential later investigations, kept outside C3, are:

- retain an in-memory canonical parent model while preserving immutable
  mathematical fingerprints;
- express child creation as add-only interval bounds and local strengthening;
- transfer compatible LP VBasis/CBasis state and use dual-simplex
  reoptimization;
- test PStart/DStart only under a complete identity and validity audit;
- submit independently verified compatible MIP starts without using them for
  lower bounds or structural decisions;
- prove that any presolve reuse preserves the exact child formulation and
  status semantics.

None of these mechanisms is implemented, enabled, or implied by Round 28.
