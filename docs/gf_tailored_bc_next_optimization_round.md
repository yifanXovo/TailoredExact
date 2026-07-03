# GF Tailored BC Next Optimization Round

This round keeps `paper-gf-tailored-bc` as the paper-facing exact line: Gini-frontier decomposition, valid relaxation/frontier bounds, CPLEX-managed tailored fixed-interval branch-and-cut, and audited full-ledger aggregation.

The work focused on hard-leaf observability and finalization rather than promoting new certificate sources.

## Implemented Changes

- Callback heartbeat progress CSVs for in-process CPLEX tailored BC solves.
- Explicit best-bound availability and fail-reason fields in final JSON.
- Timeout and plateau metadata in result JSON.
- Gini subset-envelope callback de-duplication and later-node separation up to the configured global cap.
- Wrapper finalization for callback hard leaves that exceed wall-clock limits before CPLEX exposes a valid final best bound.

## Evidence Boundary

The round does not use BPC, route-mask enumeration, archive scanning, known UB injection, external incumbents, focus-only rows, or plain CPLEX benchmark bounds as paper-core evidence.

Rows marked `wrapper_timeout_noncertified` or `no_valid_bound_emitted` are diagnostic only. They may explain a hard-leaf bottleneck but cannot close an interval.

## Main Finding

Moderate low-Gini fixed-interval leaves still fail to emit a valid CPLEX best bound before wrapper termination in callback mode. Heartbeat logs show callback activity and some user-cut separation, so the problem is not missing execution. The immediate bottleneck is reliable native callback finalization and hard-leaf bound extraction, followed by low-Gini bound strength.

The next technical step is to isolate hard-leaf callback solves in a dedicated worker or use the static command-file tailored path when strict wall-clock finalization is more important than callback separation.
