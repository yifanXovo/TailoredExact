# Large-V Stability Diagnostic Report

Large-V diagnostics used `paper-gf-bpc-core` with sealed mode and no route-mask
enumeration.

Summary file:

- `results/paper_core_realignment_round/large_v_summary.csv`

Rows produced in this round:

- V50/M3 average, short sealed diagnostic final JSON.
- V100/M5 average, short sealed diagnostic final JSON.

Both rows are noncertified and intentionally reported with honest LB/UB/gap.
The short diagnostics mainly verify that the unified preset does not fall back to
small-instance enumeration or interval-oracle certificate logic.  Longer V50/V100
runs should wait until the BPC/pricing bottleneck is addressed.
