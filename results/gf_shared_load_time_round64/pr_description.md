Round63's independent time flow and node-aggregate B4 did not test arc-wise load/time sharing. This adds opt-in Q, T, SEP and JOINT formulations, integer route embeddings and warm-state support on the unchanged complete K1 controller. Stable defaults and the official compact P-GRB remain unchanged; no resource callback, hidden restart or instance-specific selector is added.

Base: `codex/round63-cumulative-time-resource` at `f734d6781fd7125703489245cdb4dc27fb74625c` (PR #124). This PR contains the Round64 delta only.

The bounded study establishes actual SEP-to-JOINT projection exclusions after free auxiliary re-completion, with independently checked D4/D7 numerical Farkas evidence. A smaller QCAP projection is implemented and tested, then stopped after its declared D4 certificate-loss gate. The Farkas tool is diagnostic; no production separator or full projection closure is claimed.

Complete results are mixed:

- D4 warm JOINT certifies in 53.390 seconds versus SEP's 263.968, isolating a real arc-sharing gain. C2 JOINT improves over actual stable K1-H, while SEP is faster still.
- D7 warm JOINT regresses 8.3% against actual K1-H; C5 cold zero discovery slows from 59.453 to 208.000 seconds. D3 warm also regresses.
- Independent C6 cold JOINT reduces gap 52.6% versus cold OFF and beats both actual references, while warm JOINT regresses 36.1% against K1-H after expensive LP lookahead. The unchanged cutoff/domain-dependent paths are documented; no per-role startup choice follows.
- C7 is an actual zero-objective confirmation. All six arms certify, with below-gate isolated OFF/JOINT time differences. Identical HGA generation traces explain why its separate startup timing variation is not attributed to resource rows.

Validation closes at **62/72 charged launches, 4/4 native micros, 262 optimizer calls**, all serial and within physical caps. All 41 solver-free CTests pass. Independent audits cover 42 LP/combination records, four auxiliary records, 84 original witnesses, 18 warm pairs, four cold pairs, and both unchanged confirmation freezes. All negative results are retained. The final full matrix uses retained v3 source `438e9a286957370df2f962893f43a1026902839f`; current source additionally retains the stopped v4 QCAP facility, with separate frozen identities.

No uniform stable upgrade is proposed. Large raw models/logs and binaries remain local, with paths and hashes; 3,091 raw files are indexed.

[Final report](https://github.com/yifanXovo/TailoredExact/blob/codex/round64-shared-load-time/results/gf_shared_load_time_round64/final_report.md) · [Reproduction](https://github.com/yifanXovo/TailoredExact/blob/codex/round64-shared-load-time/results/gf_shared_load_time_round64/reproduction.md) · [Validation receipt](https://github.com/yifanXovo/TailoredExact/blob/codex/round64-shared-load-time/results/gf_shared_load_time_round64/validation_receipt.json)
