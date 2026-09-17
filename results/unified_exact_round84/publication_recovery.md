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
