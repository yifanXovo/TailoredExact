# Round127 finite packaging source review

Disposition: **PASS, source-only**. The two earlier source findings are resolved. Actual member-index compaction, public-manifest generation and anonymous public recovery remain **pending** at this review; this document is not an execution or recovery receipt. The original carrier pack is still the parent's active administrative operation. No compression, test, scan, network request, restore, model/carrier read, build or Optimize was performed by this reviewer.

Reviewed source bindings:

- `scripts/round127_member_indexes.py`: SHA256 `8cb99c46970d83a13caae22faca68b289bee9277ba1e1c9f9f19ebf10424cbb0`.
- `scripts/round127_public_restore.py`: SHA256 `df492432dc8722d57e9f9f15868b671bf3b82aa8d9e505d80838913ea36b0034`.
- `scripts/round127_release.py`: SHA256 `6c1d21093f4cec831647c7d67ab1819b26c7b63143788e55a75a268410865532`.

The compactor preserves the original plain manifest locally behind a non-overwrite guard, retains every member record and its order in a gzip JSON list, and records both compressed and decoded byte counts/SHA256 plus member count. It checks round-trip list equality and emits a representation receipt. Its explicit compression settings include mtime=0. It rewrites the public manifest representation only; the source contains no ZIP/raw rewrite or second carrier pack. This is source inspection, not an independent comparison of actual old/new indexes or carrier bytes.

The recovery source retains complete ZIP identity, member count/total size, duplicate-free exact member-name set and per-member size/SHA checks. Existing extracted files first pass size/CRC and are still included in the later full SHA loop; resume does not silently replace SHA verification with CRC. For v2 it also checks gzip size/SHA before decoding and decoded size/SHA before parsing. Original full-list v1 recovery remains supported.

The first finding was that a merely safe relative index path was being treated as canonical. The revised code now admits exactly the five planned archive basenames, requires a duplicate-free export-file declaration, and requires the literal per-archive path `results/unified_exact_round127/artifacts/member_hashes/<archive-name>.members.json.gz`. The corresponding export-manifest row must exist and agree with the index's compressed size/SHA. This closes both canonical-path and loose-export binding gaps without changing archive contents.

The second finding concerned future recovery failure receipts. The revised `manifest()` exclusion set now explicitly includes `public_restore_receipt_failure.json` alongside the normal recovery receipt, export manifest itself, resource accounting, runtime/resume state, cleanup, delivery/completion receipts and the post-manifest content scan. Raw stage/qualification/source_E0 trees and fees are excluded from loose enumeration because the finite carriers bind their selected contents. The pack source selects only already-closed fee directories, so its own live fee and later fees cannot enter that archive snapshot. The export manifest does not hash itself, and the later scan receipt is excluded. These exclusions avoid a self/future-receipt cycle; they do not delete retained evidence.

Only the later manifest exclusion function changed in the release module for these fixes; the reviewed pack function's archive construction remains the prior implementation. The already-running pack process is not being rerun or claimed to have loaded later source changes. No remaining issue was found in this bounded source review. Actual compaction equality, manifest closure, network retrieval and full member restoration must be established by their future metered receipts before any execution-success claim.
