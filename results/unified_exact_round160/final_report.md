# Round160 final research report

The parent-containing physical neighborhood yields original-J improvements
from both intended own-H inlets. The frozen complete algorithm comparison
does not support default activation: final U is worse on RX35 and NB35,
equal on K20 and RX20T1, and RX20T1 certification takes about 14.67s longer.
The stable GI-TBC/B entry and historical P-GRB comparison CSVs are unchanged.

## Mechanism and exactness interface

The C++ optimizer jointly opens legal quantity, eligible owner and local order
on b=min(8,releasable) stations. All outside inventories and served owners are
fixed. Maximal outside runs preserve original B holes, original car, internal
order and relative run order. At most g<=b extra true internal arcs are cut
by a deterministic round-robin insertion-increment rule. Free nonzero service
can use run boundaries and depot gaps, including empty cars; zero service has
no visit or owner. Uncut runs remain indivisible. The original supports,
necessary total-stock bounds and parent-inclusive J<=parentJ+1e-8 scope apply.

Run delta/min/max summaries propagate the new entry load exactly. Complete
boundary/internal travel, variable pickups/drops and final depot unloading
participate in the MIP; total handling is (tp+td)*P, with cumulative P allowed
above Q. Connected arc loads, MTZ order, mandatory runs and a depot bypass
give expansion/contraction at route/operation level and embed the complete
parent Start. Full original Gini uses fixed outside constants, cross unary
tables and only within-B variable pairs, retaining original n and weighted
penalty. A separate physical zero-stock branch avoids normalization at S=0.
See [the mathematical section](../../docs/round160_physical_neighborhood.md)
for propositions, pseudocode, literature attribution and actual complexity.

Every strict improvement is expanded and checked by the original Evaluator
under original T before consumption. Native OPTIMAL is a floating-point local
model status, not a transported exact-J optimum. No local bound, infeasibility
or no-improvement enters the global proof ledger. R133/R134 repairs remain.

## Two-source physical research and one revision

The source-identical historical pre-scope/RN own-H fleets are offline parents,
not late Native solutions. Formal arms generate their own fleets with own-H
seed20260626. Parent/source/processing hashes are in inputs and input_manifest.

|Parent|Parent J|v1 final J|Accepted events|Outer seconds|Native OPTIMAL / NODE_LIMIT|
|---|---:|---:|---:|---:|---:|
|RX35|0.4246498451636405|0.4016200111731245|12|40.9668595|12 / 23|
|NB35|0.5772179446388801|0.4900715637577154|22|65.6695970|16 / 19|

Both finish all 35 anchors, including unvisited/zero-gain anchors, without
reordering the remaining pass after improvement. RX/NB have 28/31 unique B
sets (20.0%/11.43% repeats), and 36/42 unique vehicle-arc cuts among 280 cuts
each (87.14%/85.0% repeated ports). This is one anchor pass, not all 8-subsets
or a neighborhood closure. Final route durations remain below original T.
Neither endpoint beats the old late physical U (.2996694007364017 /
.450291503262878). No new historical-best upper is claimed.

Every v1 event changes quantities. RX events include activation in 3, zeroing
in 2 and common-station order changes in 5; none changes an old served owner.
NB events include old served-owner changes in 5, activation in 6, zeroing in 4
and order changes in 5. No flip event occurs. Counts overlap. The complete
Y/owner/routes, operation quantities, prefixes, travel/handling, exact binary
coefficient J and previous-parent changes are in trajectory_analysis_v1 and
the raw event JSONs, including all intermediate strict improvements.

Since 42/70 v1 blocks reach NODE_LIMIT, the single evidence-based major
revision uses 2048 nodes uniformly, keeping parents, b/g/ports and one pass.
RX ends at .4186767011062194 (100.3456037s); NB at .4951307115747831
(148.8609335s). Local Native OPTIMAL counts increase to 18/22, yet both final
prices are worse and costs greater: deeper work changes accepted-parent
trajectories. v1 is retained for F; no further recipe/seed/capacity grid runs.

The matched NB event at B=[16,11,31,20,2,21,12,7] changes quantities
7,11,12,16, old owners 12,16 and common order on car0. Its block parent J is
.5749270842499868; joint J is .5596946598780417. Car net quantities change
by [1,-1,0], and car0 returns one unit: boundaries were not pinned to old load.
The owner-fixed control keeps only previously served owners fixed, preserving
unvisited activation/eligible owners, and reaches .573413506045513 at 512
nodes (0.8298238s outer). Its raw .5693066582827654 bound is untransported:
the contrast is observational/UNKNOWN, not an owner-necessity theorem.
A 512-node challenge from the stronger NB late parent finds no improvement;
it is not closure. The same-block semantic bridge reproduces the joint price.
Tiny enumeration and locked-arc uncompressed semantics support equivalence,
without a compression-speed claim or an old-closure-unreachability claim.

## Complete self-paid comparison

Fresh serial off/on arms use the SAME production PE, Seed0/Threads1 and
E+ RN16384/proof-only. The C++ inlet runs after this arm's complete H/R83,
before scope/RN. Returned routes go through the original incumbent consumer;
scope/cutoff and downstream state follow the new incumbent. No historical
fleet or local lower is loaded into production. All components, H, helpers,
local models, online verification, Native calls and return share one production
deadline. Postproduction verification is separate. All eight arms completed.

|Role|Arm|Physical U|Raw search L|Proof L|Absolute gap|Relative gap|T_total s|T_cert s|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|R-X35-S-T2|Eplus|0.299669400736|0.214205553889|0.236052102907|0.0636172978289|0.212291604257|7180.07577823|open|
|R-X35-S-T2|EplusR|0.375043475225|0.216070036022|0.236021308518|0.139022166708|0.370682803171|7179.94869785|open|
|N-B35-S|Eplus|0.450291503263|0.389293619318|0.395956408724|0.0543350945388|0.120666488586|2378.90678465|open|
|N-B35-S|EplusR|0.454059850109|0.387275870107|0.395943771336|0.0581160787729|0.127992111082|2378.63866694|open|
|K-20-S|Eplus|0.716806546278|0.70519127832|0.70519127832|0.0116152679576|0.0162041878912|1202.01076511|open|
|K-20-S|EplusR|0.716806546278|0.705130725828|0.705130725828|0.0116758204499|0.0162886632531|1201.20923324|open|
|R-X20-S-T1|Eplus|0.645325030386|0.645325030386|0.645325030386|2.22044604925e-16|3.44081810669e-16|23.8295065523|21.937043|
|R-X20-S-T1|EplusR|0.645325030386|0.645325030386|0.645325030386|1.11022302463e-16|1.72040905334e-16|38.4974488071|36.606473|

T_total=T_produce+T_verify. T_cert is production time to the actual complete
certificate and is empty for open runs. The inherited certificate_qualified
flag qualifies the reported certificate STATE, including an honestly open
state; reports/complete.csv separately identifies certified runs. RX20T1 is
the only certified role. Its E+/E+R T_total is 23.829507/38.497449s.

Online local component times/calls/accepted events are RX35 41.4654254s/35/12,
NB35 65.6103181s/35/22, K20 14.6207349s/20/0 and RX20T1 15.1338196s/20/5.
K20 retains its parent .7752127578025221; RX20T1 improves
.7530539180896819 to .6894954214298542. Online per-block build/solve and
nested callback validation costs remain in each round160 raw tree. Reports
separate engine, common RN and local Optimize calls; they are not inferred
solely from the legacy journal, which omits the new local calls.

These four roles and one frozen candidate/Seed show early physical capability
but no complete U gain and a certificate delay. They do not establish general
impossibility, P-GRB superiority, out-of-distribution behavior or independent
confirmation. Keep the component default off. No automatic full-fleet UNKNOWN
fallback or extra benchmark is warranted by this evidence.

## Qualification, identity and cost

Real parent lift residuals are at most 1.26e-15; 24 real objective-map samples
per source agree within 1.11e-16. Tiny enumeration includes unequal tp/td,
cumulative pickups above Q, empty car, zero-stock branch and locked-arc
uncompressed semantics. The final separate saved-evidence script rechecks
every accepted fleet's original T/J, outside stock/owner and indivisible runs,
the owner-control MPS/solution residual, all own-H->R->scope chains, input/PE/DLL
hashes, single deadlines and proof-source separation. This is the same agent's
separate script, not an independent person. Final_review.json records PASS.

The measured C++ source is d1da99b85219f4f0a1b5a703fc6ebf1c6dee4431;
candidate_manifest binds all actual source bytes and reused objects. Measured
off/on production PE SHA256 is
dd39a3671c114a9e60d1d169bf6ffb533595f1a632cdd5876fe03f08d0e4da08.
The v3 standalone core science uses PE SHA256
4616ea0d018a7f78989b3e5ad64a2e8dc3decba47f46ed4061b2c2c0b3381eb5;
its original measured bytes were recovered exactly after the v4 engineering
overwrite, with the recovered SHA checked and retained locally.
Gurobi13.0.2 DLL SHA256 is
9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88;
the actual production OS module path is captured in infra/runtime_binding_001.
GNU C++17 flags retain the original warning/optimization policy, no fast-math.
The later CMake-only import-library fix is separately clean-built and never
substituted into performance samples. Source, measured PE, final science
snapshot and delivery metadata are distinct identities.

Closed scientific cost is **22022.3569699s** of 129600s, including
all failed outer launches, core/revision/controls, fresh arms, online and
postproduction verification and final readback. The 24000s nominal panel and
31200s conservative admission reservation are not actual fees. Current
separate compilation/public/writing outer time is
217.0067088s; publication receipts record later
non-scientific I/O. Nested Runtime/Work/validation are decompositions, never
added again. Prior rounds add zero scientific cost. See cost_report.json for
every actual closed receipt and failed receipt, including compiler/include,
sparse-import and old-reader launch engineering corrections. The old on-arm
qualification reader was repaired and reverified against the sealed producer
without repeating Optimize. A final reporting correction separates qualified
open states from actual certificates and preserves both reporting fees.

## Evidence and delivery

The actual goal, history_dedup, plan/algorithm, source/input/build manifests,
qualifications, every model/log/event and failed fee are retained. A current-only
carrier excludes commercial binaries, licenses, credentials and protected user
dirty-file metadata; four old input blobs are fixed-commit/SHA references.
Publication pins a final science snapshot, performs one finite anonymous public
recovery with no Optimize or old carrier replay, and records a bounded post-PR
cleanup. See publication.json, public_restore_receipt.json and cleanup_record.json
in the delivery metadata commit for the observed outcome.
