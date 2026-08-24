# Round 50 tailored branching policy audit

All four core policies used one executable (`a268506844fa28de3509e44fa0e9b36db7325004be8fb21cd7d0181b06af2f49`), identical canonical model fingerprints, and nine frozen states at 120 seconds. B1, B2, and B3 assigned priorities to every integer variable through the semantic registry; assignment status was `applied` on every candidate row. Priority tiers were deterministic by semantic family and ordinal only. Default v0 assigned no priorities.

B2 was rejected in the core screen after losing D4 and D10 certificates. B3 was rejected because D4 Work rose from 129.528 to 195.896 (ratio 1.512, delta 66.368), a frozen severe regression. B1 alone qualified, but on the full 300-second D1-D14 panel it lost D3's v0 certificate (10 versus 9 total certificates) and severely worsened D14 capped proof progress. Its aggregate Work ratio was 1.046774. B1 did materially improve D10 and D12, demonstrating a local semantic effect, but it failed the no-lost-certificate and no-severe-regression gates.

No tailored branching policy is accepted. `interval-mip-v0` default Gurobi branching is restored as the cumulative backend. Candidate modes remain default-off solely to reproduce the rejected ablations; they are not selected by any preset or instance/time/size dispatch.
