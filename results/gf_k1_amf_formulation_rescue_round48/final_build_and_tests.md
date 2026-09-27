# Final build and tests

- Algorithmic source: `4c08f36452eaf90c3c0a974a9782abfa37eff16b` / tree `cb554bf511a35c417354e5ce3cf5f5dbb8190e40`.
- Clean build: `build/official-round48-4c08f3645`, Release, GNU 14.2.0, Gurobi 13.0.2.
- Official executable SHA-256: `bff4943b82d10c4fc082e5ae9add1970d46a1277ab1b398dc77410d94b4cbe34`.
- Full build: pass (all targets).
- CTest: 26/26 pass; dedicated Round48K1AMFTests: 42 checks.
- Historical Python protocol inventory: 135/135 pass after binding the frozen Round 46/47 executable paths.
- Round 48 Python protocol inventory: 14/14 pass after final-decision generation.
- K1-AM default-off sentinel: 20/20 comparisons pass.
- Official candidate executable hashes: one (`bff4943b82d10c4fc082e5ae9add1970d46a1277ab1b398dc77410d94b4cbe34`).
- Stage 3 artifact hashes: pass; failures: [].
