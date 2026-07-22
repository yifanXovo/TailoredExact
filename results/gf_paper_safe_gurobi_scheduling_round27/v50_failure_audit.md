# V50 C2 failure audit

The official `stage3__moderate_seed6301__c2_paper__300s` process did not write
a final result JSON. The external harness terminated it at 308.032 seconds
after the declared 300-second process cap plus the fixed eight-second emergency
shutdown margin (`return_code=124`, `emergency_timeout=true`). The row is
retained and excluded; it was not retried.

The production HGA did finish. Its 3,325-generation trajectory ends with
exactly 2,000 consecutive non-improving generations and has restored SHA-256
`924ba64d5e8efa01c6be90067b76f58e4841cfefa6d4866c65b95f4d8423bf1d`,
byte-identical to the independently completed Stage 1 V50 trajectory. That
Stage 1 run independently verified objective `0.6075292832179728`.

No `external/` artifact directory or paper LP/MIP ledger was created before
termination, and the only generic progress row is the initial empty-incumbent
event. The evidence therefore establishes that termination occurred after HGA
but before the dedicated paper tree emitted its first event. It does not
establish which intervening preprocessing operation consumed the remaining
time. C2 consequently produced no final validity-gated V50 bound or resource
lifecycle record, and no claim is made from partial in-process state.

For comparison, official V50 P-GRB finalized at 294.281 seconds with verified
UB `1.0421330659912349`, valid LB `0.43346045610079509`, Work
`722.38249487455664`, and peak memory `0.463384793` GB.
