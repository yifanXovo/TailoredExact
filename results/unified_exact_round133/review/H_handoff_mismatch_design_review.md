# D1 first-arm H handoff reader failure

Independent review of the sealed first arm, before any postverification
repair is accepted. Production raw, frozen helpers and matrices are unchanged.

The failing conjunction's count is satisfied: there is exactly one call-zero
startup witness, sequence2, source `same_run_verified_startup`. Its three
capacity-assigned routes equal `hga.csv.exchange/initial.json`, not the final
exchange fleet. Both exchange endpoints have `F=0.16038610038610038`,
`G=0.10038610038610038`, `P=.4` and the same inventory. Two neutral exchanges
changed routes and the assignment of service to vehicles0/2. The recorded
exchange result has two neutral moves and zero strict moves.

The production `main.cpp` consideration rule updates the accepted routes only
when `v.objective < out.verification.objective - 1e-10`. The exchange endpoint
is submitted to that same rule. Consequently this equal-objective final
fleet is fully processed and logged, but the accepted startup remains the
initial fleet. `PaperExternalGiniTree.cpp` journals that actual accepted
`verified_seed.routes`. The final-only comparison added in the Round133
reader is stronger than this production contract. The inherited Round90
reader already distinguished initial versus final exchange handoffs.

The minimal correction is a new explicitly bound postverification adapter.
Select a unique accepted H endpoint with the actual production expression:
the final endpoint if its recorded, independently physically checked objective
is strictly below the initial endpoint minus `1e-10`; otherwise the initial
endpoint. Do not accept an arbitrary objective-equal fleet, use the final
native result as a startup, or change a journal witness. Keep complete24+1
descent, the original full neutral/strict exchange replay, all physical
checks, capacity-aware fleet identity, Start mapping and the PS startup check.
PS has the same final-only assumption inside `startup.reconstruct` and must
be checked against the uniquely selected accepted endpoint too.

The H record should distinguish the accepted startup's physical/fleet data
from the actual final exchange endpoint. Its complete semantic trace must
continue to contain the real `exchange/final.json`, even when that final
fleet was not selected. A source clone may replace the one initial
assignment used to compute the accepted physical/fleet values; replacing
the entire read function for the final path could corrupt trace semantics.

The adapter's scientific work must run after producer seal and native exit.
The first native arm is not rerun. Preserve its original failed audit and
fee and its original `T_produce`; any further failure goes to a new repair
failure record rather than overwriting the first failure. Bind a new
wrapper/adapter identity and explicit repair admission, while retaining the
original four helper bytes, full matrices, production/source/PE/DLL and
native argv. Remaining native positions keep their original order and caps.

Controlled checks should cover different-fleet objective ties, strict final
improvement, improvements below the threshold, exact threshold equality,
rejection of an unrelated third fleet, accepted versus rejected PS startup,
unchanged actual final-trace semantics and incomplete H. Approval of this
design is not approval of the sealed arm's final evidence: its own physical
zero and failed postverification remain separate until the complete repaired
audit succeeds. The effective wrapper and fixture identities remain pending.
