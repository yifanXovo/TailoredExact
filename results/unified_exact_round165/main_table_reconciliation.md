# Main CSV reconciliation

No new instance/Seed performance data need appending. The task-specified exact 106-row UTF-8-BOM master was not supplied at the actual bounded Downloads/Desktop entries. The existing 103-row working copy is retained as incomplete, without replacing either user file.

| Actual file | Encoding / BOM | Rows × columns | Bytes | SHA256 |
|---|---|---|---|---|
| C:\Users\Administrator\Desktop\GI_TBC_vs_P_GRB_All_Tested_Instances.csv | gb18030 / False | 91 × 28 | 25180 | 2a0b80b9536bfbb278370f9b9dbf6947b9570d25ab7b158605e6a2012ad2b2f3 |
| C:\Users\Administrator\Desktop\Research\docs\tempfiles\GI_TBC_vs_P_GRB_All_Tested_Instances.csv | gb18030 / False | 91 × 28 | 25180 | 2a0b80b9536bfbb278370f9b9dbf6947b9570d25ab7b158605e6a2012ad2b2f3 |
| E:\codes\ExactEBRP-work\worktrees\round165\results\unified_exact_round164\reports\GI_TBC_vs_P_GRB_All_Tested_Instances.csv | gb18030 / False | 103 × 28 | 32685 | acca7225bb586f0955a4c453e59c199ba9e8c1835d538abcbfb156df528c772b |

The 12 R164 increment rows are already present exactly once in the 103-row working copy. The original 28-column schema, full numerical precision, old sources and existing byte stream are unchanged. This round adds 0 rows and does not infer a pooled statistical sample from this tracking table.

The absent original historical records are:

| Historical row | Seed / cap | Fixed inherited evidence |
|---|---|---|
| R138 R-B35-S-T2 | 1 /2400 | [R138 report](https://github.com/yifanXovo/TailoredExact/blob/de01e8fb27a954d031abac5fe99442d6c8d29d44/results/unified_exact_round138/final_report.md) |
| R155 N-B35-S | 0 /7200 | [R155 report](https://github.com/yifanXovo/TailoredExact/blob/de01e8fb27a954d031abac5fe99442d6c8d29d44/results/unified_exact_round155/final_report.md) |
| R156 R-X35-S-T2 | 0 /7200 | [R156 report](https://github.com/yifanXovo/TailoredExact/blob/de01e8fb27a954d031abac5fe99442d6c8d29d44/results/unified_exact_round156/final_report.md) |

Their original N/A-P descriptive/source fields are unavailable with the 94-row file. The known historical experiment results do not reconstruct every missing original CSV field; no fabricated union or 106-row-master update is claimed. See main_table_reconciliation.json for actual result keys and hashes. The endpoint figure uses its dedicated analysis/three_seed_endpoints.csv, not a reinterpretation of this master.
