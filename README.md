# TailoredExact

Exact solvers for the Equity-aware Bike Repositioning Problem.

## Paper and author review

The current scientific manuscript is **Round172**, delivered in [PR #234](https://github.com/yifanXovo/TailoredExact/pull/234). Its maintained sources and PDFs live in `results/unified_exact_round137/`. The paper presents the shared inventory formulation, the frozen uniform GI-TBC/B method (historical S2/ms2, pair-only with AP off), and bounded transportation decisions.

- [Main PDF with Appendices A and B](results/unified_exact_round137/manuscript.pdf) · [Complete manuscript Markdown](results/unified_exact_round137/manuscript.md)
- [Supplement PDF](results/unified_exact_round137/supplement.pdf) · [Supplement source](results/unified_exact_round137/supplement.md)
- [Main text](results/unified_exact_round137/paper_body.md) · [Appendix source](results/unified_exact_round137/model_and_algorithm_appendices.md) · [Mathematical companion](results/unified_exact_round137/mathematical_analysis.md) · [Bibliography](results/unified_exact_round137/references.bib)
- [Author reading guide](docs/paper_review.md) · [R172 author decision memo](results/unified_exact_round172/author_decision_memo.md) · [Revision record](results/unified_exact_round172/revision_record.md) · [Technical review record](results/unified_exact_round172/review_record.md)
- [Authoritative benchmark CSV (132 records)](results/benchmark_tables/GI_TBC_vs_P_GRB_All_Tested_Instances.csv)

Use the [rebuild and historical run guide](docs/paper_s2_release.md) for a pinned R172 checkout and the [document build entry](scripts/round172_documents.py). The solver launcher in that guide retains the historical Round137 profile.

## Historical evidence and workspace

The six 50-station comparisons in R172 §4.4, Table 6, come from the [Round171 experiment report](results/unified_exact_round171/final_report.md). The [Round170 report](results/unified_exact_round170/final_report.md) records the paid-initialization confirmation and the decision to close C169. C166, D167 and C169 remain research variants outside B. The bare executable retains its **ENS-C compatibility default**. See the [research index](docs/unified_exact_research_index.md) for earlier evidence and the [Round165 contribution map](results/unified_exact_round165/contribution_positioning.md) for its historical framing.

Round136 was merged into Git `main` by ordinary merge commit in [PR #198](https://github.com/yifanXovo/TailoredExact/pull/198). Its local disposition is recorded in the [Round136 continuation record](results/unified_exact_round136/RESUME.md). The [former K1-AM-SF/R55–R58 entry](https://github.com/yifanXovo/TailoredExact/blob/25800aa6b51bf7607b51e5df14a10a5ca4571889/README.md) and the root [Manuscript directory](Manuscript/README.md) are historical.

New work belongs in isolated checkouts under `E:\codes\ExactEBRP-work`. The original `E:\codes\ExactEBRP` contains user changes and the shared Git store. [Workspace policy](WORKSPACE_POLICY.md)
