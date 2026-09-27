# Existing-witness Start API review

Read-only follow-up research, 2026-09-15. No Start is enabled in Round67.

Gurobi 13's [Start attribute](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/variable.html#start)
is modifiable and affects MIP solves. The solver attempts to construct an
initial solution from its values; the attribute is not a certificate of
acceptance. The [C attribute API](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/attribute.html#c.GRBsetdblattrarray)
documents setting a contiguous array of Start values using GRBsetdblattrarray.
The [model update API](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/model.html#c.GRBupdatemodel)
processes pending model modifications. These are actual interfaces already
loaded by this project's backend.

The [warm-start guide](https://docs.gurobi.com/projects/optimizer/en/current/features/warmstart.html)
distinguishes a supplied Start from reuse of a previous model solution. It
also explains that failure to produce a new incumbent need not mean the Start
was infeasible. Log evidence of loading a solution and subsequent incumbent
vectors must therefore be distinguished from a zero API return code.

Implementation inference: restoring the required MIP variable types and
current bounds, processing updates, then setting a verified complete Start on
the retained model is a plausible supported sequence. The documentation does
not impose the project's old `!retained` condition. This is not yet a tested
claim about this backend: a future stage must exercise the actual LP-to-MIP
transition, read back the Start, check current linear rows and objective, and
observe native use. Retaining a model object is not retaining a branch tree.

No new native parameter, partial-start repair budget, reset, or forced model
reload is implied. Any future supplied witness must be acquired within that
same paid run and satisfy the current interval/cutoff; an incompatible witness
is skipped without changing proof coverage. P-GRB keeps all external starts
off. General MIP-start reuse was already studied in Round44; see
provisional_integration_question.md for the narrower unresolved question.
