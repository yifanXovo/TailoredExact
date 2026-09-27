# Direct parametric-LP split point

For split parameter s, v_L(s) is the continuous parent LP with G<=s and is
nonincreasing; v_R(s) uses the canonical transformed row -G<=-s and is
nondecreasing. PMM maximizes min(v_L,v_R). FPMM additionally clips each value
at the frozen frontier target. A complete maximizer interval is resolved by its
midpoint. Gurobi basis sensitivity is represented and unit-tested; the live
experiments use the permitted deterministic monotone-root fallback because the
shared model-builder interface does not expose stable basis sensitivity. An
uncertified point retains the parent rather than falling back to midpoint.
