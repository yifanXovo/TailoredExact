# BPC RMP Seeding

`--bpc-seed-columns none|incumbent|incumbent-plus-local|pool` and `--bpc-seed-column-max` are now JSON-visible. The paper-core preset records incumbent seeding as the intended default, but seed columns remain UB/RMP-start aids only.

Certificate rule:

Seed columns do not prove a lower bound. A BPC leaf closes only after exact pricing closure proves no missing negative reduced-cost column.

Round outcome:

RMP seeding did not produce a nontrivial exact BPC closure in the tested leaves. Pricing closure, not the initial RMP column set, remains the limiting step.

