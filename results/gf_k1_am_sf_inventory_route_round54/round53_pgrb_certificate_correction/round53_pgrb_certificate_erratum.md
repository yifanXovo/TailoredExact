# Round 53 P-GRB certificate-chain erratum

Round 53 reported **0/12** P-GRB strict certificates because its new sealed
commands omitted the pre-frozen expected-model-fingerprint binding.  The
models and solutions were retained; the rejection reason on otherwise closed
rows was `model_fingerprint_mismatch`.

Round 54 first reconstructed all 12 complete plain-Gurobi models with the
original Round 53 executable and committed their expected fingerprints before
this correction.  Every expected fingerprint, canonical LP SHA-256, objective
fingerprint, and variable/row/domain identity matches the immutable Round 53
artifact.  A separate standard-library verifier re-parsed each input and
independently checked its retained routes and objective.

The corrected count is **9/12**.  Certificate status changes
on 9 rows:

- `round53_sealed_v12_tight_T_2400_V12_M2_Q20_seed19430436`
- `round53_sealed_v12_high_imbalance_3600_V12_M2_Q20_seed15988921`
- `round53_sealed_v12_moderate_3600_V12_M2_Q20_seed1498709331`
- `round53_sealed_v12_tight_T_2400_V12_M2_Q30_seed1826205989`
- `round53_sealed_v12_high_imbalance_3600_V12_M2_Q30_seed527237204`
- `round53_sealed_v12_moderate_3600_V12_M2_Q30_seed1230493897`
- `round53_sealed_v12_tight_T_2400_V12_M3_Q20_seed1388001936`
- `round53_sealed_v12_moderate_3600_V12_M3_Q20_seed587061832`
- `round53_sealed_v12_tight_T_2400_V12_M3_Q30_seed169390111`

The remaining rows retain honest noncertified native statuses.  Work,
process-time, bound, gap, and GI values are unchanged for all 12 rows; no raw
Round 53 result, command, completion marker, report, decision, or sealed
manifest was overwritten.  This is a post-hoc strict evidence correction, not
a replayed performance experiment.

The correction does **not** change the Round 53 F0-CLEAN fixed-interval
promotion, K1-AM-F0 support, or sealed candidate-over-v0 conclusion.  It does
change only contextual comparisons that previously counted fingerprint-
rejected optimal P-GRB rows as uncertified.  Round 54 algorithm selection is
forbidden from using this repair.
