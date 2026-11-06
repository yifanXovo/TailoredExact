# Scope of the initial workspace protection record

The saved initial_paper_status.txt lists44 old tracked paths reported
modified under rounds142,143 and149. They are excluded from Round155 edits,
staging and cleanup. The initial_original_status.txt separately preserves
the original project tree's reported modifications and untracked content.

The initial protected_tracked_bytes.json is empty, and initial_identity.json
correctly records protected_tracked_count=0. The preparation script used
git diff --name-only to select byte hashes. A later read-only check confirms
that git status still reports those44 old paths, while git diff reports no
content changes for them; Git also warns about LF/CRLF handling. The two
sampled files have LF in both index and working tree. No normalization,
reset, re-add or other change to these files was performed.

The earlier RESUME description of this empty file as a44-file byte snapshot
was incorrect and has been corrected. Both initial files are preserved as
actually written. An end-of-study readback will record the current bytes
of the originally listed paths and compare them with fixed Git blobs where
applicable. It will state its actual observation time. This later readback
cannot establish an unavailable pre-task byte-for-byte snapshot and will
not be labelled as one. The original project tree's unique modifications
remain protected regardless of any fixed-blob comparison.

Final staging must use explicit Round155 delivery paths, check that none of
these historical paths is staged, and retain their current bytes through
publication and bounded cleanup. No old path is a cleanup candidate.
