# Round 31 source of truth

## Repository state

- Repository: `yifanXovo/TailoredExact`
- Authoritative checkout: `E:\codes\ExactEBRP`
- Starting local branch: `codex/round30-c0-mechanism-transfer-c5`
- Starting local HEAD: `893656f85fa6394dac787fee78baad2a52cdd2d2`
- Observed live GitHub `main` before Round 31 work:
  `224e9bb333d08956dc37172d12544201bc48e5f5`
- Round 31 branch: `codex/round31-nonblocking-gurobi-c6`
- No pull, fetch, merge, rebase, reset, clean, restore, stash, force-push,
  or `main` mutation is permitted.

The local checkout is authoritative. Historical Round 22--30 result trees are
read-only inputs.

## Preserved starting workspace

At entry the checkout contained:

- zero staged paths;
- three unstaged tracked user files;
- 416 untracked files;
- 419 dirty-file manifest rows in total.

The complete path, byte-size, and SHA-256 ledger is retained at
`build_round31/starting_dirty_file_manifest.csv`. Byte-for-byte backup copies
of the three tracked edits are retained below
`build_round31/user_preservation_backup/`.

Round 31 commits may contain only intended source, tests, protocols, scripts,
generated sealed instances, and evidence under the isolated Round 31 paths.

## Stable and reference algorithms

- S0/F0-CPLEX remains the stable accepted paper mainline and is unchanged.
- P-GRB is the primary same-solver benchmark.
- P-GRB-HGA is an incumbent-value ablation only.
- C0-DIAG is exact but non-paper-compatible and is a diagnostic teacher only.
- C3, C4, and C5 are frozen references.
- C6 is the sole promotion-eligible Round 31 development candidate.

No Round 31 outcome automatically promotes C6 or replaces S0/F0-CPLEX.

## License handling

The Gurobi license file and its contents must never be opened, inspected,
copied, hashed, printed, serialized, or committed. Its location is supplied
ephemerally and may appear only in the environment of launched child
processes. Evidence records sanitized command arguments and environment-key
presence only.
