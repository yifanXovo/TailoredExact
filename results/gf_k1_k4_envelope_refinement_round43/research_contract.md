# Round 43 research contract

This round evaluates one exact, parameterized family `A(K0,d,rho)` at globally
fixed `K0` values 1 and 4. Both values use the same node operator and code path;
`K0` changes only the complete equal-width initial partition. Every Round 43
control is explicit and default-off.

The primary score is `D_d`. The only admissible secondary score is
`max(D_d,C_d)`, and only if the frozen structural atlas proves that `C_d` is
complete, stable, solver-independent, and adds information. Candidate behavior
may not inspect metadata, historical outcomes, hardware, time, Work, nodes,
iterations, or memory. The external 3600/7200 second caps interrupt the entire
algorithm but never choose an algorithmic action.

Development precedes validation. Validation remains closed until one globally
frozen candidate passes every development gate; the sealed holdout remains
closed until that same candidate passes validation. If no candidate passes,
all mathematically triggered Stage 4/5 branches must be completed or formally
ruled inadmissible before `bounded_systematic_negative_result` is assigned.
