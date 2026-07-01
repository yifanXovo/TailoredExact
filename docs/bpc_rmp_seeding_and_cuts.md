# BPC RMP Seeding And Cuts

The BPC repair round keeps RMP seeding certificate-safe:

- incumbent and local-repair route-load columns may seed the RMP only when they
  are original-feasible columns;
- seed columns may improve primal feasibility or dual stabilization, but never
  certify a lower bound by themselves;
- exact pricing closure remains required for any BPC lower-bound certificate.

Relevant options:

- `--bpc-seed-columns none|incumbent|incumbent-plus-local|pool`
- `--bpc-seed-column-max <N>`
- `--bpc-cut-family station-operation,inventory-domain,gini-interval,duration-cover,transfer-compat,subset-row`
- `--bpc-cut-separation-rounds <N>`

The validation tables record columns inserted, cuts added, RMP/master time, and
pricing reduced costs.  If cut counts remain zero, the final report treats that
as a BPC implementation bottleneck rather than evidence that cuts are
mathematically irrelevant.
