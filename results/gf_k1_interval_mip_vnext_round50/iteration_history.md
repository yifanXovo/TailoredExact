# Round 50 bounded iteration history

| Iteration | Family | Entered candidates | Result | Active policy after iteration |
|---|---|---:|---|---|
| 1 | branching | B1, B2, B3 | rejected; corrected B1 qualification lost D3/D13 certificates and regressed D14 | Gurobi default |
| 2 | cut/formulation | C1 exact duplicate elimination | rejected; D12 failed the independent objective-residual certificate tolerance | original v0 pack |
| 3 | symmetry/numerical | S1 plus one S1-R1 revision | rejected; both lost D13's v0 certificate | v0 cardinality symmetry; no numerical change |
| 4 | model/basis reuse | none after audit | R1 not opened because no corresponding solved LP model exists | one-model rebuild; no reuse |

No candidate passed every frozen acceptance gate, so the cumulative backend contains zero accepted modifications. The final post-iteration D1--D14 v0 rerun is also the exact cumulative vNext rerun; copying its measurements under the frozen-backend label introduces no empirical substitution because the policy and executable path are identical.
