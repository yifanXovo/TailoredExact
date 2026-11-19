# Round173 author review handoff

- The [README](../../README.md) identifies the R172 scientific manuscript and links directly to its PDFs, main and appendix sources, author memo, review history and authoritative benchmark table.
- The [author reading guide](../../docs/paper_review.md) follows the physical problem, complete method, measured comparisons and bounded decisions. It points to §4.4/Table 6 for the 50-station panel, §4.5 for the mechanism limits, and §5 for the decision bounds.
- The [rebuild and run guide](../../docs/paper_s2_release.md) pins the R172 content commit and shows a fresh checkout with its own PDF temporary directory. It retains the distinct R137 launcher profile, including the original clocks and budgets, and links the recorded R169–R171 executions.

Two independent internal readers checked the execution path and research wording, then confirmed the corrections. The targeted checks covered relative paths, heading anchors, PowerShell example syntax and the documented rebuild inputs. [Round173 review record](review_record.md)

The only document entry executed was `round172_documents.py paths`, once in `E:\codes\ExactEBRP-work\worktrees\round173`. It exited successfully and printed the checkout's R137 paper directory, R172 records directory, and `E:\codes\ExactEBRP-work\temp\round172\pdf`. The printed comparison base was R171 `e8c4a0d3ccbaf1c1a6e6f83242d9163fe29e74e4`. The separate reader rebuild root and all optional export stages were left for readers who need a local build.

Git object checks preserve the R172 paper sources, PDFs and review records, the solver source, configuration and launcher, and the historical panels. The benchmark CSV retains 132 data rows, 28 columns and 82,303 bytes with UTF-8 BOM and CRLF. Its SHA-256 is `0487ebaf90274f85a7cd94358215a701825f328c954a8de235fd5e58633989dc`. Round173 added zero CSV rows, solver runs, Optimize calls, H calls, C++ builds, PDF rebuilds, experiments, certificates and performance observations. [Benchmark CSV](../benchmark_tables/GI_TBC_vs_P_GRB_All_Tested_Instances.csv)

Local acceptance followed the two rechecks at 06:44:48 on 20 November 2026 (Asia/Shanghai), 778 seconds from goal registration at 06:31:50 against the 5,400-second limit. The delivery receipt records Git and public readback. The target is a stacked draft on the R172 branch because main lacks the R172 content commit.

The R172 manuscript is ready for author and peer technical review. Authorship and affiliation, funding and disclosures, the HGA-TGBC antecedent, recoverable capture metadata and the public code and data statement remain author decisions. [R172 author decision memo](../unified_exact_round172/author_decision_memo.md)
