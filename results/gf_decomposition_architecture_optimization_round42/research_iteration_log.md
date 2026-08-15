# Round 42 research iteration log

The split, gates, materiality rules, candidate definitions, and executable were
frozen before official candidate development runs. All rows use the 1,800-second
process-entry cap, one Gurobi thread, Seed 0, Auto presolve, and zero gaps.

| Order | Family | Iteration | Uniform mechanism | Development outcome |
|---:|---|---|---|---|
| 0 | reference | K1 | contemporary exact C6-K1-SINGLE | completed; witness repaired, positive control catastrophic |
| 0 | causal | fixed K2 | External-K2-Fixed versus ST-K2-P-Core | completed; static/external gmeans 1.026 Work, 1.029 shifted time |
| 1 | A | base | flat ST-K4-P-Core | rejected: 2 catastrophics; positive control 1.330 Work |
| 2 | A | required refinement | dyadic hierarchical K4 selectors | rejected: witness 0.426 Work but positive control 1.570 |
| 3 | B | base | adjacent paired K4 Core blocks | rejected: witness 1.060 Work; 1 catastrophic |
| 4 | B | required refinement | exact common-row factoring in both blocks | rejected: witness worsened to 1.134 Work |
| 5 | C | base | exact terminal sibling Core union | rejected: cap-bound certificate regression; control 1.489 Work |
| 6 | C | required refinement | exact common-row factoring in every sibling union | rejected: certificate regression persists; control 1.422 Work |

The lexicographically best exact family is paired-K4. Its already required
uniform factoring refinement worsens the major witness and aggregate shifted
time, so the optional second-refinement allowance is not used. Engineering
smokes remain separate from official development evidence, and invalidated raw
runs remain preserved locally.
