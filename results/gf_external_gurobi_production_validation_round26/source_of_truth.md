# Round 26 source of truth

- Authoritative checkout: `E:\codes\ExactEBRP`
- Branch: `codex/round26-external-gurobi-production-validation`
- Round 25 base/current starting HEAD: `d8cba691424eb990fc22357f7a2911ec5d34f3df`
- Generator commit: `0573d21c39d7c8fa8edb29f9eacb4184faa26bde`
- Observed live `origin/main` before Round 26 work: `4a608eeae559cc69ca5c37b6eb4abab74fd3bc3b`
- Gurobi license policy: `GRB_LICENSE_FILE` is set only in child-process
  environments. Its file is never opened, copied, hashed, printed, or serialized.
- Dirty-tree policy: all pre-existing staged, unstaged, and untracked user paths
  are preserved and excluded from Round 26 commits.

The held-out seal was produced before any Round 26 solver execution. A solver
runner must verify every sealed hash and the protocol hash before launching a
held-out or V50 process. Round 22--25 evidence is immutable context only.
