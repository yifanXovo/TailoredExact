# Round137 carrier I/O amendment: limited independent review

Review UTC: 2026-10-28T08:27:24.584001+00:00

**PASS for the bounded source amendment and small in-memory format/read check.** This does not assert that pack02, local120-position replay or the future public recovery has completed. Those require their actual output/semantic receipts. Only this new review file was written; no producer, build, recovery or archive mutation was invoked by the reviewer. Frozen scientific/document reviews remain unchanged.

## Scope and source identity

Read both current scripts, the preserved prechange copies, the inherited `round134_release.archive`/scan and `carrier_transport_change.json`. Actual old/new file SHAs agree with the amendment receipt. AST comparison confirms the old release `idle/source_capsule/pack/manifest/restore_script` functions are unchanged; new code replaces the rebound archive function and adds the bounded reader/forward ZIP sink. In the recovery class only initialization (parent-cache/lock) and `expand` change. Fetch, deadline accounting, state/receipt and semantic-run methods remain unchanged.

Both modified scripts are outside the219 frozen production sources and93 execution helpers, and are absent from the already completed exact source capsule. They are delivered separately through the current export-manifest script loop; the capsule is not being silently rebuilt. No scientific endpoint, model, parameter, native clock or source qualification changes follow from this transport amendment. The interruption receipt names only the ordinary pack PID56592/parent63236 and preserves the old partial/log; it does not request or implement a producer retry.

## Archive construction and reuse

- The sorted, duplicate-free source path collection and `pack` enumeration/filtering are unchanged, so concurrency does not select fewer positions/files or alter which failure/cost artifacts are carried.
- `bounded_member_reads` submits at most32 members per batch with8 read/scan workers. Ordered `pool.map` consumption preserves the sorted ZIP/member-index sequence. All current-member bytes pass the existing path/credential scan; SHA and byte count are computed from exactly the raw buffer passed to `writestr`. Compression/ZIP writing remains in one thread. The bound is on member count, not a claim of a universal byte-memory cap.
- `ForwardZipSink` supplies write/tell/flush and explicitly rejects seek. Standard `zipfile` therefore uses bit3 data descriptors instead of rewriting every member's local header. DEFLATE and central-directory/member names remain standard ZIP, including normal ZIP64 support; altered archive-level layout/hash is expected and explicitly reattested. The original per-member bytes/hash authority is unchanged.
- A completed target/index pair is reused only after unique index names/exact input membership, fresh original-file hashes and full ZIP names/count/CRC-read/bytes/SHA checks agree. This is at least as strict as the inherited reuse gate. No obsolete archive is relabelled as revalidated without reading it.
- A target without a completed index is moved to the bounded current repair path with checked resolved source/destination containment and no overwrite. Index/target inconsistency fails rather than silently repairing or discarding evidence. Split pieces retain exact chunk comparisons, sizes and hashes. Raw-manifest publication remains after all archives finish; this source review is not completion acceptance for an active pack.

## Concurrent expansion and owned-root boundary

The archive/pieces/full-compressed hash, unique member count/name set and index identity gates remain before member extraction. Every member still passes `safe`, rejects a directory entry, and is read through `ZipFile.read` (which checks CRC) with expected decompressed size/SHA before a new exclusive-create write. Worker batches are32 and pool size8; archives themselves expand serially, avoiding concurrent cross-archive writes to a shared path. `ZipFile`'s shared reader supports concurrent read handles, as also checked below.

The complete parent ancestry is validated before and after first creation, under a lock, then cached only inside the same exclusively owned restore object. Archive writes never create symlinks or replace directories, so caching an admitted parent is defensible under that existing exclusive-root contract. Every pre-existing target is separately checked with `lstat`: Windows reparse attributes and nonregular targets fail before SHA reuse. Missing targets use `xb`; an unexpectedly existing target cannot be overwritten. Duplicate members are rejected before scheduling; overlapping identical paths between carriers are verified, not rewritten.

If a worker fails, the batch raises and no later batch is admitted. Other already submitted independent writes may finish during executor shutdown; completed verified files remain for the existing failed-root resume policy. The method does not declare partial extraction complete. Same-owned-root/commit, FAILED_PRESERVE-only resume and no rerun of PASS/RUNNING roots remain. Every member checks the cumulative remaining allowance, and the inherited7200s recovery/at-most3600s semantic subprocess rules and fixed anonymous HTTPS/no-Git/no-native policy are unchanged. This is not a new claim of hard interruption inside a stalled single filesystem call.

## Actual bounded pure check

Used the already completed `campaign_004.zip` (207339 compressed bytes,73 members,927837 raw bytes) solely as a read-only fixture. In memory, reconstructed its exact name/byte sequence through the new forward-only sink. Reopening with standard `ZipFile` gave all bit3 descriptors, identical ordered membership/bytes, and `testzip() is None`. An8-worker/32-member-batch read of that in-memory result also matched every original member. No disk carrier or recovery root was created or changed, and no large current tree/history scan was performed.

## Result and remaining gate

No concrete member-loss, ordering, concurrent-write, standard-format or owned-root regression was found in this delta. Continue the current ordinary pack/local replay, then verify the completed immutable manifest and one actual public semantic receipt. A source PASS here must not be substituted for those later measured delivery outcomes. Do not repeat the accepted R135 recovery or rerun healthy native positions.

`final_science_review.md` remains SHA `d90064f778e5152ed849af1854c4a550b6593631f79a7caeaf4aabe6a9e83fe2`; `final_document_review.md` remains SHA `f28f917ef02d745c3d422a392e035f1b41b5dd5e86f729f42be4f29c77060c32`.

## Reviewed byte identities

| File | SHA256 |
|---|---|
| `E:/codes/ExactEBRP-work/worktrees/paper-current/scripts/round137_release.py` | `0015d0e0c014e39fa1f3620925cb9f73a263a1d48005f01afdee1157315bb581` |
| `E:/codes/ExactEBRP-work/worktrees/paper-current/scripts/round137_public_restore.py` | `c1dd2a335b46369b11b57eb7b1f3113c5d2bdc3046b1d98d9bd970522b4bc7be` |
| `E:/codes/ExactEBRP-work/temp/round137/drafts/round137_release_serial_pack.py` | `1f72c82a16ad3000876f7a6bf2045c7692b1e046e6cdd32c23fce42858389a45` |
| `E:/codes/ExactEBRP-work/temp/round137/drafts/round137_public_restore_serial_expand.py` | `ca42f85177b8f970aaed8474cabf5a937f6894970c960c36a3d6d692b0e5a783` |
| `E:/codes/ExactEBRP-work/worktrees/paper-current/results/unified_exact_round137/review/carrier_transport_change.json` | `91ae1f90f5a40a4677deaff307513e6a08fa9c40228b51ce3d1bb28fe908fa25` |
| `E:/codes/ExactEBRP-work/worktrees/paper-current/results/unified_exact_round137/source_publication.json` | `cee3499bb3a119002253edf3759608b58c00b4143b64fbd6c6b32498fabc8f9c` |
