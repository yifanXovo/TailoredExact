# Tailored BC Source Attribution

Tailored-BC source classes are:

- `tailored_bc_certified`: true callback branch-and-cut proof with callback API available;
- `tailored_bc_assisted_noncertified`: true callback mode ran but did not certify;
- `static_fallback`: tailored preset requested but callback API is unavailable, so only static/root compact-BC strengthening can run;
- `relaxation_only`: the Gini-frontier ledger certified without compact/tailored subsolver evidence;
- `benchmark_only`: plain CPLEX comparison row;
- `diagnostic`: test-only row.

Certified `paper-gf-tailored-bc` rows may be relaxation-only, but static fallback must not be described as true tailored callback evidence.
