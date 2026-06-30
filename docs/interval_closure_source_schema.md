# Interval Closure Source Schema

Every final frontier interval now records a closure source:

- `relaxation_bound`: a valid interval lower bound reaches the incumbent cutoff.
- `bpc_exact_tree`: a route-load BPC tree closes the interval, with exact pricing closure.
- `interval_oracle`: an auxiliary compact interval oracle closes or strengthens the interval.
- `empty`: the interval is outside the improving Gini range or empty.
- `unresolved`: no valid certificate closes the interval.

Result JSON also includes aggregate fields:

- `intervals_closed_by_relaxation_count`
- `intervals_closed_by_bpc_count`
- `intervals_closed_by_oracle_count`
- `intervals_unresolved_count`
- `certificate_uses_interval_oracle`
- `certificate_uses_bpc_tree`
- `certificate_uses_relaxation_only`
- `bpc_core_certificate_valid`
- `exact_portfolio_certificate_valid`

Audit policy:

- `paper-gf-bpc-core` optimal rows may use only `relaxation_bound`,
  `bpc_exact_tree`, or `empty`.
- `paper-gf-bpc-core` optimal rows fail audit if any interval oracle evidence is
  used as certificate evidence.
- Any BPC interval certificate requires exact pricing closure.
- `paper-exact-portfolio` rows may use interval-oracle evidence, but only when
  explicitly labelled as portfolio evidence.
