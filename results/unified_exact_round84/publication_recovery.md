# Preliminary branch preservation

The original queue remains active. This is preparation preservation, not a
completed R84 result or a draft PR. Target5ad3564c2f338737bcb2e65ca31b512c1da14507
contains the original frozen-plan commit and later reader/recovery preparation.

Two ordinary non-force Git pushes failed to connect. The first full wall time
was not independently captured; its reported21.069s connection timeout is not
substituted for total cost. The second measured21.232463099993765s, exit128.
The initial exact remote R84 ref returned404.

The R84 exact-object API publisher created the new branch at the verified R83
base131d09280a1563243d0201e68367b26baf5079c3. Its first attempt failed after
16.075721899978817s/20 requests: a newly uploaded blob, whose returned SHA
matched locally, was rejected as invalid by detached tree creation (HTTP422).
A finite retry failed the same way after5.988464800175279s. The offending blob
subsequently read back with the correct actual Git SHA; a tree previously
returned as created was not found by a later GET. The cause is not established.
These exact receipts remain under publication_api/; no remote head advance
was claimed on the failed attempts.

The official Git tree API permits nested file paths and UTF-8 content together
with a base_tree. The preparation-only v2 publisher uses those documented
fields and requires exact round-trip UTF-8 bytes, resulting root-tree SHA and
original commit SHA before a non-force update. It does not normalize line
endings, rewrite authors/committers/messages or create substitute commits.
Source: https://docs.github.com/en/rest/git/trees#create-a-tree (read2026-09-17).

The first v2 attempt encountered a local reader error: object_readback.json is
a list, while the inherited ledger scan assumed every JSON file was a dict.
The failed script bytes and receipt are retained. Skipping non-ledger lists
resolved that metadata error; no optimizer or measured artifact was changed.

The corrected v2 attempt succeeded in16.57180509995669s and verified these
original commits and their exact root trees:

- 3dae75c03952f7e2194f184d4939216e0be4ca78
- 8f7ed3eee1068caee250ad6f209db2d51ab2ce29
- 5ad3564c2f338737bcb2e65ca31b512c1da14507

Final API readback reached5ad3564c2f338737bcb2e65ca31b512c1da14507. No force,
main merge, native restart or performance selection occurred. The v2 helper
is deliberately limited to UTF-8-only commits; it is not yet a transport for
later binary evidence bundles. The original publisher remains unchanged as
historical code. Stage publication will require fresh transport validation.

## Final evidence publication

The original evidence commit is3189c5ae0834a7e023ae281ed6151aac67131b4d.
The final ordinary non-force push failed with a connection reset after
42.279054400045425s; final_push_attempt.json retains the actual result.

The prepared binary v3 publisher first failed after224.56860460015014s/26
requests. Seven complete binary readbacks passed; a later GET failed with
"stream error: stream ID 1; CANCEL; received from peer". The affected blob's
POST had returned the expected Git SHA. Independent remote readback still
showed the preceding eight-run prefixbaf19b2d5, not the evidence head.

One bounded transport retry requested GODEBUG=http2client=0 only for the
publisher and children, preserving other existing GODEBUG options. The Go
HTTP documentation supports disabling client HTTP/2 through this setting:
[Go net/http](https://pkg.go.dev/net/http#hdr-HTTP_2). This is a transport
diagnostic, not a proved explanation of the first failure. Nine full binary
readbacks then passed, but the next large GET failed with "unexpected EOF"
after60.4216712s. Total publisher time226.70805450016633s; launcher time
226.81837770016864s contains it and is not added again. No ref advance occurred.
Both failures and original v3 code remain unchanged.

The separate v4 recovery uses Git content addresses for publication. GitHub
documents the blob's computed SHA and a creation response containing that SHA;
tree entries reference object SHA values, and a supplied base_tree retains the
existing tree. Sources: [Git blobs](https://docs.github.com/en/rest/git/blobs),
[Git trees](https://docs.github.com/en/rest/git/trees). The publisher recomputes
each local Git blob SHA, binds the two original receipts to the same target,
branch and v3 implementation, and preserves successful byte-readback evidence.
It distinguishes creation-SHA acknowledgment from a complete downloaded body.

All14 binary content addresses validate:9 prior complete byte readbacks,
1 prior successful creation-SHA acknowledgment and4 new creation-SHA
acknowledgments. The remaining five objects are not claimed as downloaded
byte-for-byte. All20726 local packaged members were independently verified
twice before publication. V4 requires the exact original root tree
0484255f39ea86703c2d9841c67997cfaba3c715 and original commit SHA, checks that
the remote has not changed concurrently, and performs a non-force update.
It succeeds in11 requests/31.014140299987048s; the31.124133700039238s launcher
measurement contains that duration. No artifact, author, timestamp, message,
tree or existing commit history is rewritten.

Fresh independent GitHub readback confirms the exact evidence head. Draft
PR145 is created against the exact R83 branch/base and independently verified
open/draft/unmerged: https://github.com/yifanXovo/TailoredExact/pull/145 .
Final text-only publication metadata follows in a separate original commit.
Its last transport receipt remains local after that commit to avoid a
self-referential evidence revision. No native process or audit is rerun.
