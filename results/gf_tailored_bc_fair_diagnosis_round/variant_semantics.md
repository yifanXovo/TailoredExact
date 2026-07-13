# Variant Semantics

- `tailored_static_no_callback`: safe compact rows, no callback, no dynamic root loop.
- `tailored_callback_telemetry_only`: same base model; callback samples telemetry but adds no rows, rejects no candidates, and creates no branches.
- `tailored_cheap_cuts`: callback permits only redundant Gini-interval and visit-inventory rows.
- `tailored_full_static_baseline`: no native callback; one static root separation round with the established safe families.
- `tailored_route_cutset_callback`: experimental audited route-cutset profile.
- The requested low-Gini-only route policy is not run because no existing audited generic activation rule is available; inventing one in a diagnosis round would confound causality.
