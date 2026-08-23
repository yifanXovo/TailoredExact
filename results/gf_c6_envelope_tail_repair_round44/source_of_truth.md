# Round 44 source of truth

- Base branch: `codex/round43-k1-k4-envelope-refinement`
- Base commit: `3b4b50da3292a834c5731fb2c00f056a22c77cff`
- Base tree: `280d711a005d28d54b543606c976f48ce53f5a84`
- Research branch: `codex/round44-c6-envelope-tail-repair`
- Validated tailored baseline: C6-HGA-FULL, K0=4, rho=0.01
- External comparator: canonical P-GRB
- Solver: Gurobi 13.0.2, Presolve Auto, Seed 0, Threads 1, zero gaps
- Certificate tolerance: 1e-7
- Small-run cap: 3600 seconds; paired extension: 7200 seconds
- V12 cap: 7200 seconds; V20 checkpoints: 300/1200/3600 seconds

Round 43's executable score is `D_R43`, not `P_profile`; see the erratum.
Round 44 raw runs live under `runs/`. Compact committed summaries and manifests
are derived only from completed, noninvalidated rows bound to one frozen
executable. Native logs and large model artifacts may remain local when their
hash, size, signature, generation command, and retention state are published.
