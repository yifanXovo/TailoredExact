# Pending execution prerequisite: evidence survives a native non-return

This is a prospective implementation design, not a completed repair or new
performance allocation. No source/runtime change described here has executed.
The original six native qualification diagnoses of at most30s each remain
available; record exact roles and commands before dispatch. Do not reopen
Round72, repeat its failed long baseline, or promote its log values.

R72 proves that synchronous Optimize can remain inside the native engine
past the process allowance. Existing MIP progress is buffered until return;
P's physical route is also extracted only afterward. Gurobi documents soft
TimeLimit completion and non-immediate GRBterminate. Its C callback API supplies
MIPSOL_SOL as a full user-model vector and MIP_OBJBND as the current bound.
MIPSOL can also present a non-improving solution or a MIP Start, so an event
is not automatically an improving physical UB. The qualified code already
uses this vector interface for Start observation; new persistence must be
separately tested.
[Callback codes](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/callbacks.html),
[official C example](https://docs.gurobi.com/projects/examples/en/current/examples/c/callback_c.html).
Direct page fetches returned429 during this check; the official search result
and previously inspected TimeLimit/terminate documentation were available.

Required observer behavior:

* Opt-in measurement path, default off. Record identities/settings/domain scope
  before native launch. Do not set a new heuristic, Start, cut or imported bound
  on P-GRB. Do not use snapshot progress to select a mathematical subproblem.
* At MIPSOL, read original-model values through the cached variable-name map,
  reconstruct original route/operations, verify original F and hard constraints,
  then durably publish an immutable witness. Verification and writing stay
  inside the paid process. Never treat native ObjVal alone as physical UB.
* Publish complete immutable data plus a final checked commit record. The
  commit records process-monotonic time after writing and a content hash.
  Ignore incomplete files, missing commits and records outside the observation
  cutoff; retain their failure evidence. Process-kill persistence is the scope,
  not power-loss durability. Callback failures cannot escape the C boundary.
* Record successful native MIP bound reads with their actual scope. A P bound
  applies to the full original compact model. An interval bound alone is never
  a global bound. Candidate recovery requires a frozen complete frontier and
  valid excluded-domain/closed-branch evidence from the same run. During a
  synchronous call, only its matching active leaf's bound may be strengthened.
  Prospective child probes or mismatched ranges cannot replace a parent.
* Excluded G ranges and cutoff-pruned regions require explicit mathematical
  lower-bound justification. Taking the minimum over those regions is coverage
  aggregation, not permission to clip a contradictory numerical bound. Any
  global LB exceeding a verified original UB beyond original tolerance rejects
  the recovered endpoint and is retained for investigation.

The single whole-run stop remains external to algorithmic choices. A shutdown
reserve may support orderly output and an owned-child hard stop; all launch,
verification, persistence, stop and exit cost must fit the declared process
cap. If measured wall exceeds it, the attempt remains over-budget. A hard-stop
endpoint is explicitly interrupted and has no native-finalization certificate;
it is never rewritten as an optimal Gurobi termination or strict rational proof.
Without enough committed physical/full-domain evidence, reject the endpoint.
Do not silently import an old witness or run another algorithm after a slice.

Qualification should cover normal P/candidate completion, forced termination
of owned diagnostic children after committed evidence, missing/partial/corrupt
records, interval-to-global scope rejection and bound inconsistency rejection.
Use native callbacks/official interfaces only. Shared instrumentation requires
a new isolated build and fresh matched controls for any subsequent performance
panel. The current constructor/seed evidence remains at its frozen builds.
