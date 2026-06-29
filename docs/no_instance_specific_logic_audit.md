# No Instance-Specific Logic Audit

The sealed paper pipeline must not select algorithmic behavior by instance
filename, seed name, known objective value, or hard-coded Gini interval.

`scripts/audit_no_instance_special_cases.py` scans production C++ sources and
paper-run scripts for hard-coded V20 stress instance identifiers and known
objective constants. It allows those identifiers only in deterministic data
generators, result summaries, reports, and the audit script itself.

The current audit output is:

```text
results/sealed_paper_pipeline_round/no_instance_special_case_audit.txt
```

Passing this audit is a necessary but not sufficient condition for paper
certification. It verifies that the solver decision logic does not branch on
`high_imbalance_seed3202`, `tight_T_seed3101`, `moderate_seed3301`, or related
stress-row names. The algorithm may branch only on generic structural
properties such as `V`, `M`, route-mask completeness, solver status, unresolved
leaf count, and configured time budget.
