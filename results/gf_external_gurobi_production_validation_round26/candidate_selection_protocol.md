# Round 26 candidate selection protocol and decision

The quantitative protocol was frozen in `round26_evaluation_protocol.md`
before forensics or candidate execution: 5% V12 materiality, at least 50%
reduction of C0's V12_M2 excess Work as an alternative, and at most 0.02 loss
in normalized final LB or bound-AUC on every difficult development case.

Exactly one prototype was tested: P1 changes the uniform external-tree split
threshold from two unresolved attempts to one. No second prototype was used.
P1 reduced median V12_M2 Work from 341.716 to
299.967; relative to P-GRB it removed
70.0% of C0's excess Work. It also kept both V12 median
certificate times within 5% of P-GRB.

P1 nevertheless fails the difficult-case guard. On high3202, C0 strictly
certified in 404.537s,
whereas P1 timed out at the 600-second development horizon. P1's normalized
final-LB delta is -0.028835, below
the allowed -0.02. Earlier partitioning created more child models and discarded
the productive longer same-leaf search that C0 needed to close this case.

Therefore P1 is rejected without tuning, and **C1 is frozen equal to C0**. This
is the preregistered fail-safe outcome. The three initial C0 CLI failures are
retained separately and excluded because the old frozen binary rejected a new
harness flag before parsing an instance or starting optimization; their three
distinct repaired retries are the selection rows.
