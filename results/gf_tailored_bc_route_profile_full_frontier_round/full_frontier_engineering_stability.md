# Full-Frontier Engineering Stability

- Fresh root rows: 35.
- Wrapper/error rows: 7; none is treated as a certificate.
- Package-local progress points: 285.
- Open ledger rows: 27.
- Long-run monitoring: five-minute frontier snapshots and process-tree memory samples are stored under `progress_traces/`.

The campaign runner survived every native exit and retained final JSON, stdout, solver logs, progress, and monitor data. During the simultaneous moderate plain 14400 s runs, CPLEX memory exceeded 18 GB and free physical memory fell below 0.3 GB. The lower-priority moderate-3302 plain row was stopped and recorded as resource-limited; no partial bound from it is used. All other selected long rows completed or produced audited noncertified wrapper artifacts. Failures, time limits, and the moderate-3302 regression remain visible in the package summaries.
