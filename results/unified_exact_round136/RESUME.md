# Round136 consolidation and paper handoff

**Preparation branch:** `codex/round136-mainline-consolidation`, based directly
on R135 `25800aa6b51bf7607b51e5df14a10a5ca4571889`. The English consolidation
PR targets **main**. Its actual number, base/head and final checks are recorded
in [integration_status.json](integration_status.json).

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
  includes all 136 branch heads. No old PR state has been changed.
* [Local inventory](local_inventory.json) covers 39 registered worktrees at
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

New native solve time **0 seconds** (limit 600), Optimize **0**, compilation **0**,
new performance panels **0**, repeated raw/public restores **0**. Historical
R135 production clocks and earlier R132/R134 versions and denominators remain.
R135 is 32 positions / 16 pairs / 7 inputs and 10/16 certificates per method;
R134 S2 12/14 and historical R132 S2 17/24 are distinct panels/policies.

Stable refs and their actual targets/readbacks are recorded in
[stable_refs.json](stable_refs.json). Old main and independent R38 are archived;
`paper-s2-round136` names the verified entry snapshot. Later publication receipts
can be separate commits; no commit is claimed to attest its own future state.

## One final authorization batch

**Integration preparation is complete once the actual PR and final review are
read back. Main update and old-PR closure require the single final confirmation
specified by goal D2. They are not performed automatically.**

The concrete proposed batch is:

1. Refresh main/PR refs and merge this consolidation PR with an ordinary merge
   commit, preserving the R135 chain and all Round136 commits. Do not squash,
   rebase, replay/cherry-pick the chain, force push or include independent R38.
2. Read back main and verify it contains the actual integration head, R135
   metadata/science/source baselines and the accepted S2 entry.
3. Refresh old PR states. Close still-open #86-#197 only where the refreshed
   head is contained in main, as absorbed/superseded; adoption of each old
   candidate is not implied. Preserve discussions, reports and negative results.
4. Close #85 separately as completed/not adopted, retaining its independent
   stable ref. Keep remote old branches. Record actual counts and exceptions.

If refs have changed, reassess those concrete changes before applying this
batch. Existing GitHub permissions do not replace the user's merge approval.
No email, submission, additional experiment or next optimization round is part
of this batch.
