# Pre-freeze Stage 0 attempts

This directory is retained only to make early engineering attempts visible. None
of these rows is a fresh Round 21 numerical row, and none enters any summary
CSV. Official evidence is under `raw/`, `runs/`, and `commands/` and is stamped
with frozen executable SHA-256
`dfd67bcf4e4dd19cf7096bf5fa16c100d5a6ccefd3bb6df8a30547de39f7136a`.

- `plain_v8/` is the initial mixed-object ABI build. CPLEX completed, but the
  process then failed with Windows heap status `0xc0000374`; there is no usable
  result JSON.
- `plain_v8_gdb/` is the debugger reproduction of that same heap failure. Its
  stack reaches `SolveResult::~SolveResult`, identifying stale object files
  after the result-structure change.
- `plain_v8_retry/` is a successful full-rebuild smoke solve, but it predates
  the final signed-gap/inversion policy and frozen executable.
- `global_v8_f2/` is likewise a successful pre-freeze integration smoke solve;
  it predates the final certificate policy and authoritative model-dimension
  reporting.

The subsequent clean rebuild eliminated the ABI failure. The official Stage 0
runner then validated 10/10 rows. Its first audit pass reported a shared runner
schema mismatch (`native_mipopt_return_code` name and dynamically reserved
native deadline); the solver evidence itself was retained unchanged, the audit
was corrected, and all ten existing rows validated. No failed or pre-freeze
attempt is included in fresh performance or certificate counts.
