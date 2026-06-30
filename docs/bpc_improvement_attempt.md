# BPC Improvement Attempt

Based on the leaf traces, `paper-gf-bpc-core` now enables the following
certificate-safe BPC settings:

- full generic warm start (`gcap_warmstart_level >= 2`);
- more pricing columns per call (`gcap_pricing_columns >= 8`);
- pricing completion lower-bound pruning;
- support-duration pruning;
- strong/reliability branching settings;
- final exact pricing required.

These changes do not relax certificate requirements.  Any BPC certificate still
requires exact pricing closure.

After the changes:

- V12 M2 diagnostic leaf generated more columns, but still did not close.
- moderate_seed3301 diagnostic leaf generated over 100k columns in the
  diagnostic budget and still did not close.

Current bottleneck: exact pricing / column-generation state explosion before
tree closure, not incumbent quality and not interval-oracle availability.
