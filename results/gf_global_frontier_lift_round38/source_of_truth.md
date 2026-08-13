# Round 38 source of truth

Round 38 starts from remote main merge commit
1459308492a5eceed523dee53b5f9d79141b5242. This is the two-parent merge of
Round 37 pull request 84; its second parent is the Round 37 research commit
f312f2dc2436efb04cecbebece4ebb005f3cae67, and the two trees have no content
difference. The working branch was created as
`agent/round38-global-frontier-lift` and renamed to
`codex/round38-global-frontier-lift` before publication.

The validated solver mainline is **C6-HGA-FULL** with K=4, rho=0.01,
single-threaded Gurobi seed 0, proof normalization, and the existing exact
coverage/lifecycle/certificate contract. Round 37's G1 policy remains
default-off and was not promoted.

This round asks whether a midpoint refinement advances the global proof
frontier, rather than merely strengthening one Gini cell locally. Candidate
mechanisms remain explicit, default-off, deterministic, structural,
instance-independent, hardware-independent, and absent from certificate
semantics except through already-valid complete LP bounds and exact atomic
parent/child coverage.

The three pre-existing tracked worktree changes below are user work, excluded
from Round 38 staging, and hash-guarded:

| Path | SHA-256 at branch creation |
|---|---|
| results/gf_compact_bc_round/handling_convention_test/handling_convention.json | 9a5cd06f8a4163cfcbb57147a0b21c0a5e4aec91973ab93faa921baa0553f35b |
| results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv | 4af39fe81263cd8c15ca457f4d4f6473a959630b6ab68a9280bc0a0e0a6b8acb |
| results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json | b11e84e2442c0c7b5ac5aa638b44945de28426fe31753083bff13ad401644202 |

Other pre-existing untracked builds, manuscript products, caches, and raw
records remain outside Round 38 scope.
