# Round90 candidate ledger-gate revision (compile only)

This appends to `static_review_handoff.md`; its original source/binary snapshot and first configure/build receipts remain unchanged. Independent static review of that snapshot found one bounded evidence issue: if a flagged run had no eligible split and `round90_lp_g_split_choice.csv` could not be opened or its header written, the candidate might otherwise reach finalization without the candidate ledger. The sole source revision checks the stream immediately after candidate-only header flush and throws an explicit error if unavailable. It also checks each candidate row flush, so a later I/O failure cannot silently leave a partial split-choice record. No flag-off file is opened, and no point, cache, LP, AM, MIP, deadline or result parameter was changed.

Only `src/PaperExternalGiniTree.cpp` changed from the first handoff: old SHA-256 `d51adc6dcab78042d5e3453d4e40cabe98e85567bfafbb97a14d2de90d0cb436`, revised SHA-256 `3de879702ca6dd964a1273558fc5152eaa26fad9001860c0e298270bdb7975a9`. The other six source hashes in the first handoff remain current. `compile_build_002.{json,log}` records the affected core, `ExactEBRP` and Round90 pure target compiling/linking successfully in 6.5924511 s; `compile_build_002_legacy_links.{json,log}` records the three legacy test targets relinked against the revised core in 0.7807577 s. Both exits were zero. Total recorded external configure/build cost across the initial and revision commands is 41.0621198 s. The logs contain no Round90 compile warning or error.

| Current compiled artifact | Revised SHA-256 |
|---|---|
| `build/research/round90-lp-g-split/ExactEBRP.exe` | `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2` |
| `build/research/round90-lp-g-split/Round90LpGSplitTests.exe` | `6d234fda3a12ed54b6f0fa05654c26f500be83e6fc9359d89d5a745db78419d5` |
| `build/research/round90-lp-g-split/GlobalGiniTreeTests.exe` | `561f39167ccdfdcdc318abd420303a3eedd941700cd74064018cf36f10e44b19` |
| `build/research/round90-lp-g-split/Round47AdaptiveMassTests.exe` | `a40e2dd4ba94b67648ad1ca6ee788ec242b91af8396014d8abf0f9ab470d091f` |
| `build/research/round90-lp-g-split/Round83ExchangeDiagnostic.exe` | `36d361b662af80bcda8335bf0137f26434547b4f2b2ae4742c51b430541b1711` |

The independent reviewer found no other source blocker in the first snapshot. This revision still has **no executable test or Optimize result**. Pure fixtures alone do not certify actual native-target requeue or incumbent-epoch invalidation; those remain separate execution gates. Git remains root-owned.
