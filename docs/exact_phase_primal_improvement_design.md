# Exact-Phase Primal Improvement Design

Two certificate-safe UB-only mechanisms are now traced in paper-core runs.

1. Route-pool incumbent master
   - Uses verified elementary route-load columns already collected by the
     exact algorithm.
   - Reconstructs a complete route plan and re-runs the independent verifier.
   - Accepted incumbents update UB only.

2. Local re-decode repair
   - Runs the native HGA-TGBC decoder/local improvement path again with a
     deterministic alternate seed and a small exact-phase budget.
   - Candidate route plans pass through `acceptIncumbentRoutes`, the same
     verifier-gated incumbent acceptance path used by all other primal sources.
   - The mechanism is enabled by paper-core but can be disabled with
     `--exact-phase-local-redecode-repair false`.

Neither mechanism contributes lower-bound evidence. Certification remains based
on full frontier coverage and valid lower bounds.
