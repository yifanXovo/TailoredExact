# Dynamic Root Cuts On Hard Leaves

The current root separation loop is a real LP-probe loop: build a fixed-interval
compact model, solve a root LP probe, separate valid cuts, add them, and rebuild
for the final interval MIP.

Implemented dynamic families:

- support-duration incompatibility cuts;
- transfer-compatibility cuts;
- visit-inventory linking cuts;
- objective lower-estimator cuts;
- singleton receiver-source-cover cuts.

In this round, hard V20 top-level rows did not show decisive dynamic-cut bound
improvement. The high-imbalance 300s dynamic row remained open, while the static
1200s high-imbalance recovery row certified. This indicates the current dynamic
separators are not yet the controlling hard-leaf mechanism.
