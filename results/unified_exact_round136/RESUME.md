# Round136 consolidation and paper handoff

**Authorized D2/D3 closeout complete.** PR #198 was made Ready and merged into
`main` by ordinary merge commit `053b38a1bd66ad918e3c28932ebcd8f786704aeb`.
Its parents are old main `1459308492a5eceed523dee53b5f9d79141b5242` and PR head
`3fed6fb6776e3f86414c81e0de636707211b2084`; the merged tree equals that PR head.
Actual outcomes are in [closeout.json](closeout.json) and
[integration_status.json](integration_status.json).

The actual PR is [#198](https://github.com/yifanXovo/TailoredExact/pull/198),
closed and merged. The original consolidation branch is retained at its merged
head `3fed6fb6776e3f86414c81e0de636707211b2084`. The verified entry snapshot is
`715d487674d56bc89358cf098599bc78f29d878f` (`paper-s2-round136`). Review the
[Round136-only incremental changes](https://github.com/yifanXovo/TailoredExact/compare/25800aa6b51bf7607b51e5df14a10a5ca4571889...715d487674d56bc89358cf098599bc78f29d878f)
separately from the full 735-commit historical integration. Later receipt
commits carry publication metadata; final remote readback is kept outside the
commit it observes. The final authorized closeout readback is
`E:\codes\ExactEBRP-work\evidence\round136\closeout\final_readback.json`.

The authoritative algorithm/run entry is
[paper-S2 release](../../docs/paper_s2_release.md). The current
[review packet](../../docs/paper_review.md) links the sole R135 source set,
unchanged complete manuscript/PDF, supplement, primary tables and three concrete
author-fact gaps. S2 remains accepted; AP remains research-only/off; bare CLI
ENS-C, physical model, complete own H and proof/numerical policies are unchanged.

## Completed maintenance

* Metadata: 113 old open PRs, 97 distinct heads, 16 duplicate-head groups;
  #86-#197 are ancestors of R135. Independent #85 retains the non-adopted G2-A
  negative result and is not merged into the algorithm. Main is the R135 merge
  base, with R135 ahead 735 / behind 0 before Round136.
* [PR disposition](pr_disposition.csv) lists every base/head, containment,
  duplicates, proposed reason and actual state. [Full metadata](pr_inventory.json)
  preserves the initial 136-branch graph and appends the refreshed final states.
  Of #86-#197, 17 were marked merged by GitHub after the main merge, and 95 were
  closed by this execution after an additional per-PR state/head check. #85 was
  already closed and unmerged at readback; it is separately archived as completed
  research/not adopted. All 113 old PRs are closed, with no unhandled exceptions.
* [Local inventory](local_inventory.json) covers 39 registered worktrees (including paper-current) at
  entry, tracked changes, untracked/ignored counts and samples, actual file
  sizes, protected identities and temporary/restore roots. The full path
  inventory is retained locally under the recorded evidence path/size/SHA.
* [Specific cleanup plan](cleanup_plan.json) and [actual result](cleanup_result.json)
  record removal of clean reconstructible R124/R125 worktrees by normal Git
  worktree operations and five derived R135 PNG/text render directories. Exact
  source PDFs, renderer and review/failed-edit receipts remain. No force removal
  or broad round wildcard was used.
* Removed logical file bytes: **503,405,825**; observed E free-byte increase:
  **556,449,792**. The measures differ, including Git worktree metadata and
  filesystem allocation. Remaining directory size is not an acceptance goal.
* Original shared Git root/HEAD, three dirty-file hashes, protected R130/R132/
  R133/R134/R135 PE/DLL, R120 core, historical driver/qualification dependencies,
  unique raw/failures, other dirty/untracked/ignored trees and the locked
  initializing checkout are retained. The R135 passed public restore remains
  read-only at `E:\codes\ExactEBRP-work\restore\round135-public-2b27711484d8`.

The active checkout is `E:\codes\ExactEBRP-work\worktrees\paper-current`.
It is now on local `main`, tracking `origin/main`. After the minimal status-record
commit and normal push, final readback verifies `HEAD = main = origin/main =
remote main`. This checkout uses the same S2 code/config as `paper-s2-round136`;
the final commit changes only closeout records and current-status pointers.
No reset, switch, move or deletion was applied to `E:\codes\ExactEBRP`.
New assets stay under `E:\codes\ExactEBRP-work` per
[workspace policy](../../WORKSPACE_POLICY.md). This round's explicit B/E scope
authorizes the seven specific old-round cleanup objects; it does not authorize
deleting arbitrary old evidence. No global configuration was changed.

## Validation and historical boundaries

[Entry verification](entry_verification.json) runs the complete launcher in
dry-run mode for all 16 frozen S2 launches, compares whole argv vectors and
actual physical/data/cap/Seed settings, checks output/parameter refusal guards,
all 218 production source hashes, default PE/DLL and original dirty identities.
Manuscript, PDF, components, supplement, bibliography, frozen matrices and
candidate decision retain their R135 Git bytes.

Independent review is [recorded separately](independent_review.json). It covers
scientific interpretation, PR/branch classification, the complete launcher,
specific cleanup safety and final handoff/entry links. It is a different agent's
saved-data/source review, not independent third-party native reproduction.
The separate [authorized closeout review](closeout_review.json) covers the
ordinary merge, refreshed PR states, preserved refs/user changes and the minimal
record update; it does not repeat the scientific checks or experiments.

New native solve time **0 seconds** (limit 600), Optimize **0**, compilation **0**,
new performance panels **0**, repeated raw/public restores **0**. Historical
R135 production clocks and earlier R132/R134 versions and denominators remain.
R135 is 32 positions / 16 pairs / 7 inputs and 10/16 certificates per method;
R134 S2 12/14 and historical R132 S2 17/24 are distinct panels/policies.

Stable refs and their actual targets/readbacks are recorded in
[stable_refs.json](stable_refs.json). Old main and independent R38 are archived;
`paper-s2-round136` names the verified entry snapshot. Later publication receipts
can be separate commits; no commit is claimed to attest its own future state.

## Authorized D2/D3 outcome

The user explicitly approved the Ready transition, ordinary merge, refreshed
absorbed-PR closure batch, separate non-adopted R38 disposition and necessary
minimal status updates. That batch is complete; no confirmation remains pending.

All 112 refreshed heads of #86-#197 are contained in the merged main. Their
merged/closed state records history absorption, not adoption of every historical
candidate. The independent #85 head is not contained in main and its archive
tag remains. No redundant reopen/close was performed on the already closed #85.

Repository open PRs after the batch: **0**. Remote branches retained: **137**;
stable tags retained: **3**. All preexisting non-main branch heads and tag
objects/targets match their retained identities. Original R105 HEAD, three
tracked dirty statuses and their file hashes match the pre-authorization record.

The final metadata commit is pushed normally to main under the same approval.
Its actual final SHA and local/remote equality are recorded outside the commit
in `closeout/final_readback.json`, avoiding self-attestation of future Git state.
No squash, rebase, force push, branch deletion, algorithm experiment, email or
submission was added.
