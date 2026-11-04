# Independent review of the conditional production floor candidate

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).

Verdict: **ACCEPT_MATHEMATICAL_DESIGN; FULL_ARM_ADMISSION_PENDING**.
The proposed single total-objective floor and its descendant reuse are valid
under the stated scope. The default-OFF integration is appropriate for the
finite transfer opportunity. Two execution-chain corrections identified below,
the actual Native/Start/exit qualifications, and a frozen source/PE/helper/panel
identity are required before any complete B/J pair. This report does not admit
a full arm or imply production adoption.

The two source corrections have subsequently been reviewed as implemented;
see the static-repair addendum below. Concrete compiled qualification and
the frozen full-arm gate remain pending.

This was static source review only. No compilation, Optimize, Native model
load, performance experiment, large read or independent verification process
was started. The ongoing offline K35 experiment was not disturbed.

## Material inspected

- `production_plan.md`.
- `include/Round153Research.hpp`.
- `scripts/round153_online.py` and the `node_limit` path in
  `scripts/round153_pricing.py`.
- The Round153 switch/argument checks in `src/main.cpp`, the root/descendant
  insertion and existing global-clock path in `src/PaperExternalGiniTree.cpp`,
  and `auditRound153Native` in `src/GurobiBaseline.cpp`.
- The inherited actual-model scope parser, row append/serialization helpers,
  Native runtime binding, and relevant import-time/accounting behavior.

The code was still being developed and had not yet been compiled, qualified
or frozen. The later source manifest and full-arm gate must identify the
final reviewed bytes rather than treating this initial source state as frozen.

## Mathematical and scope assessment

The helper reads only its own current canonical model, derives the actual
supported inventory states, actual ratio coefficients, objective weights,
G bounds and cutoff, and verifies the hard-total rows. Its pricing costs are
`beta=1,d=h`. The hard-resource/Gupper domain is a necessary inventory domain
for every physically feasible solution of that source. Thus a qualified lower
L on `max(gamma_L,G(Y))+H(Y)` yields the valid formal row

`G + sum_i omega_i e_i >= L`.

This is the correct APoff total row. The formal route model receives no
diagnostic AP/GD/RN/NC/TS block, no inventory columns, and no auxiliary route
variable fixing. The old-joint rows are used only inside the independently
paid inventory pricing relaxation; their construction cost and contribution
belong to the floor calculation. The already reviewed full-domain pricing,
true-stock upper checks and numerical transportation remain applicable.

A root floor remains valid in a descendant with the same input/resource
identity, ratios and objective weights, contained supports, a higher G lower
bound, a lower G upper bound and a nonincreasing cutoff. The descendant's
inventory domain is contained in the root domain, and its required G
completion is at least the root completion. The implementation checks these
directions. It also retains the original total row form rather than silently
substituting a direct-Gini rewrite.

The Python parser binds its scope to the actual source bytes. The C++ parent
checks the source SHA in the response, actual objective weights and descendant
supports; its ratios are recomputed from the unchanged instance targets.
Targeted qualification must therefore confirm that the canonical writer's
actual ratio/G coefficients agree with these parent metadata, and that the
first invocation is the intended initial root source after own H. The saved
source SHA alone is not a substitute for checking the claimed scope mapping.

The floor is appended only if it is above the current G lower bound by the
uniform relevance tolerance. Omitting a redundant or tiny floor is valid.
True inventory witnesses remain price uppers only; no routing incumbent is
created by this helper. The observed offline N-B35/K35 values motivate the
candidate but are absent from the online code path.

## Uniformity and ownership

The candidate has one current-root attempt and no role/name/size/winner
dispatch. It constructs its own DP and normalized oracle without loading
saved inventories, prices, potentials or another arm's incumbent. Importing
shared arithmetic modules does not itself load historical result files.
The NodeLimit=4096 and mathematical gap criteria are valid deterministic
internal stopping choices. No offline 20/120-second step is copied into the
online algorithm.

The C++ default is disabled. The switch checks require the isolated stable
GI-TBC path and exclude the listed prior research compositions. B and J must
use the same new PE; stable R137 entry/profile bytes remain unchanged. The
actual own-H seed, candidate arguments and matched input/cutoff provenance
still belong in the pre-panel freeze and Native qualification.

## Execution-chain issue 1: global deadline

The initially reviewed `hiddenHelper` used
`WaitForSingleObject(process.hProcess, INFINITE)`, while the online oracle set
Native TimeLimit to infinity. The deterministic node cap does not bound the
time spent in presolve, a node or the whole helper. Although the parent build
clock includes the synchronous call, that alone does not enforce the ordinary
whole-method deadline. A long helper could overrun a 2400/1200-second arm;
an external hard kill could also leave the helper alive.

This is a **full-arm admission blocker** in the initially reviewed code.
The parent accepted the following repair design: pass the current remaining
global deadline; create the hidden helper suspended, assign it to an owned
KILL_ON_JOB_CLOSE job, then resume it; wait only within that same whole-method
deadline; terminate the owned helper job at global exhaustion and immediately
enter the parent's ordinary deadline finalization with existing valid U/L.
If Native also receives a remaining global cap, its resulting TIME_LIMIT is
a whole-method stop, not a newly accepted normal NODE_LIMIT floor.

That repair preserves the intended rule: normal online pricing stops on
mathematical/deterministic criteria; the entire method can always stop at its
declared global budget. It is not an elapsed-k-seconds switch to another
algorithm. The actual implementation and one bounded deadline/child-reaping
qualification remain to be reviewed before full-arm admission.

## Execution-chain issue 2: frozen helper manifest

The initial parent checks the top-level helper SHA, and Python checks the
dependency hashes and interpreter/DLL hashes supplied by the manifest. The
manifest SHA itself, however, was only read into parameter/root logs; it was
not cached and required to remain equal across invocation. The response only
returned the source-model SHA. A changed manifest plus changed dependencies
could therefore self-consistently pass those local checks while departing
from the intended frozen candidate.

Before freezing, cache the expected manifest SHA in the parent, check it
before/after invocation, and bind the response to that same manifest identity.
The frozen manifest must cover the actual project-source import chain, not
only an arbitrary subset of files named by the caller. This can be established
by a complete frozen dependency inventory with a targeted loaded-source check;
there is no need for a broad new packaging framework.

The final PE, helper, manifest, interpreter, actual loaded Native DLL and
dependencies need one consistent execution identity. A mismatch may retain
existing legitimate information but must not admit a new floor. Qualification
should exercise an actual identity failure rather than merely inspect the
happy-path JSON fields.

## Numeric and stopping details

Normal online accepted price statuses are OPTIMAL and NODE_LIMIT with finite
qualified ObjBound. The fallback remains an independently valid hard-total
DP lower. Unsupported status/failure cannot supply a new Native bound. Source
or result rejection leaves no newly accepted floor. A complete-domain
infeasibility result also must not be converted into a fabricated finite lower.

The production source initially retained both `MIPGap=1e-7` and
`MIPGapAbs=1e-4/scale`. The freeze should either explicitly record both
mathematical stopping criteria or set the relative criterion to zero if the
stated rule is intended to be only the absolute gap or node limit. Further,
1e-4 is the Native gap target restored to original objective units; the
certified true-price interval also contains the numerical guard and coefficient
transport. The report must not claim that every returned true-price gap is
at most 1e-4.

The 17-digit response and row emission preserve the accepted binary64 floor.
The Native audit reads the actual appended row and checks its coefficient
map, sense and RHS against the expected original-objective row, rejecting
duplicates and extra Round153 columns. Original-variable and own-Start
preservation still need the concrete compiled qualification; static absence
of new columns does not alone establish successful Start mapping.

## Cost identity

The helper is synchronous inside canonical model construction. Existing
`build_seconds`, process elapsed time and remaining-deadline calculations
therefore include Python startup/imports, manifest and DLL checks, DP/model
construction, Native pricing, helper serialization, and C++ waiting. Its own
reported seconds and Native Runtime/Work are nested observations, not fees
to add again. The formal-row Native audit also belongs to the actual J cost.

After the deadline repair, the parent must check remaining global time again
before subsequent formal optimization. Failed helpers and deadline stops
retain their logs/status and actual outer charge. Qualification/build and
full-arm compute stay serial and are separately identified as required by
the goal. No old offline price can be booked as free online information.

## Required finite pre-panel gate

The scope of the next qualification is limited to actual new behavior:

1. The normal node/gap path, a genuine NODE_LIMIT or valid unresolved return,
   and a forced identity/unsupported-result failure that admits no new floor.
2. The same whole-method deadline, child/job cleanup, graceful existing-bound
   finalization and no unowned-process termination.
3. Actual source scope; byte-preserved original columns/rows/objective/cutoff;
   Native total-floor readback; own physical Start extension; a valid narrower
   descendant and a rejected scope expansion/mismatch.
4. One frozen source/PE/helper/manifest/runtime identity and a pre-result
   mechanism-based panel with its reserved complete windows.

These checks do not reopen old tiny-gap, baseline or historical-carrier
qualification. Once their concrete results and the repaired source are
reviewed, a separate independent gate can admit the full paired experiment.
At this stage the mathematical transfer is justified, while production
effectiveness and complete-cost performance remain untested.

## Static-repair addendum

The reviewer reread the repaired header, online helper, pricing status/limit
path, the three C++ integration points and the new AST dependency-manifest
generator. This was still static review only: no build, Native call or
experiment was started by the reviewer.

**The two source-level blockers are closed. Full-arm admission remains
pending the finite compiled qualifications and freeze above.**

`hiddenHelper` now creates an owned job with `KILL_ON_JOB_CLOSE`, starts its
hidden child suspended, assigns that process before resuming it, and waits
within the passed whole-method remaining time. Assignment failure terminates
only the newly created process. Timeout terminates only the owned job and
returns 124; closing the job also owns any remaining descendants. The parent
passes `globalDeadlineRemaining()` after accounting for preparation, records
the launch remainder, rejects a nonzero helper result and immediately calls
the existing `stopAtDeadline()` path on global exhaustion. Existing valid
information is retained by that ordinary method finalization.

The helper also passes its remaining whole-method deadline to Native. An
online TIME_LIMIT cannot qualify the Native ObjBound; the helper exits 124
and the parent admits no new floor. A mathematically safe DP lower may still
be present in the helper's diagnostic JSON, but that is distinct from parent
admission. Parent process waiting remains the authoritative outer deadline,
including interpreter launch, imports, construction and output. This closes
the previous infinite wait and orphan-helper risk; actual bounded exit and
cleanup remain required compiled qualification observations.

The parent now requires a fixed `--round153-manifest-sha`, preserves it
across reset, and verifies helper/model/manifest bytes before and after the
call. Response `R153-FLOOR-v2` binds source-model, manifest and helper SHAs.
The Python entry checks interpreter and actual loaded Native DLL identity,
all manifest dependency bytes and every loaded project module under
`scripts/`. The manifest generator follows the transitive project AST import
closure, including imports within functions; the loaded-source check rejects
an uncovered dynamic project import. These checks supply the requested
execution-chain identity. The final manifest must be regenerated after the
last source change and its hash pinned in the actual panel arguments.

Online pricing now sets `MIPGap=0`, `NodeLimit=4096` and the absolute target
`1e-4/scale`. Its TimeLimit is solely the whole-method remaining deadline;
there is no normal fixed-duration pricing step. The certified true-price
interval continues to include transport and guard, so an asserted 1e-4 bound
on every resulting true interval would still be incorrect.

One reporting detail was communicated to the primary agent: the early
deadline return initially preceded the ordinary `total_model_build_seconds`
increment. The later source, independently reread during the campaign review,
now adds `partial_build_seconds` and the applicable budget charge before
deadline finalization. Outer metered elapsed time and root helper seconds
already included this work, so the change repairs the nested field rather
than an uncharged experiment or invalid bound. The same reread confirmed
explicit owned-job cleanup on `ResumeThread` failure. These repairs do not
justify repeating historical qualification. The later source hashes and
finite saved qualification are recorded in `campaign_pipeline_review.md`.

Reviewed source SHA256 values at this addendum:

| File | SHA256 |
| --- | --- |
| `include/Round153Research.hpp` | `cf396be67d6de44b2565bcbf3e55ab50c09b5aa0e1ba1e1fb48b20a04061b9d1` |
| `scripts/round153_online.py` | `510d01a368e2f63532a42aff9d8150d68f28f7b43b0dff85c0b741345d88f665` |
| `scripts/round153_pricing.py` | `280d5a91a7875f248178c8ac85d041643e343748b5908e87ef91974a46df3350` |
| `scripts/round153_build.py` | `2c143361dabcab2a00bb8a002fa495d27856fefe798267e3cdc1be932ace8aa8` |
| `src/main.cpp` | `b1128045fb00f27dd1c180af1d24265f12e8935c53caf01485502146d8423f68` |
| `src/PaperExternalGiniTree.cpp` | `03b6e63b8bf2b1b0aca79199716fad7563f0206386b48778c6d695d54763e163` |
| `src/GurobiBaseline.cpp` | `6c09462142db6ca8ffeee378dace8518593283f144d2c0252913a2b31b5a9b61` |
