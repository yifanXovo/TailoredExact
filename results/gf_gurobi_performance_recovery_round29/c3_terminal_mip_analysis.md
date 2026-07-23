# C3 terminal-MIP analysis

Completed official C3 rows launched 1657 exact terminal MIPs. They used
10850.066827 Gurobi Work, 80.4%
of combined LP-plus-terminal Work. Only about 372 terminal completions
produced an immediately observable strict global-LB increase, and about
0 produced an independently verified incumbent improvement.

The remainder are not mathematically useless: exact closure is required for a
strict certificate. They are, however, low-value performance events at a
short deadline when unconditional refinement has created many terminal
subproblems. Reusing an in-memory model can remove a reread, but it cannot
remove this terminal Work. A split strategy that retains the exact parent MIP
when complete child LPs certify no one-level benefit directly targets the
larger mechanism.

Native presolve and root times are unavailable and remain explicitly
unavailable. Counts from native logs, solver runtime, Work, iterations, and
model lifecycle are used; no phase time is inferred from Work.
