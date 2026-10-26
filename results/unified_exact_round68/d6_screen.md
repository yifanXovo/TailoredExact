# D6 development screen, common cap600

Original CitiBike V30/M3/Q30/T18000 shortage scenario; input
070c2c1413840a09a264d238bdfa320ef76d293a45cab919095851afdea8c01d.
Same frozen build/settings, serial whole-run costs. All four remain open.

| Arm | Paid wall(s) | Original UB | Global LB | Absolute gap |
|---|---:|---:|---:|---:|
| P-GRB | 597.062 | .1572411758522922 | .14498588325431813 | .01225529259797406 |
| K1-R | 597.078 | .15708313110317415 | .1432241498846412 | .013858981218532962 |
| VD-P | 597.063 | .15708313110317415 | .14482251277766844 | .012260618325505707 |
| VD-S | 597.063 | .15708313110317415 | .14568020676209595 | .011402924341078202 |

VD-S improves both UB and LB against P. Its gap reduction is6.95%, below the
predeclared .001/10% material threshold; this is a modest directional gain,
not a claim that the primary large-instance proof problem is solved. Against
K1-R the gap improves17.72% and.00245606, meeting the material threshold.
Against VD-P the gain is7.00% and.00085769, also below the material threshold.
No statistical-equivalence or stable long-window claim follows from this panel.
The fresh P and VD-P end-state bounds exactly reproduce Round67 values; the
strict current table still uses only this stage's same-build experiments.

K1-R/VD-P/VD-S acquire identical initial route signatures and objective. HGA
costs322.819/322.562/323.488s. All perform5 LPs and commit one split; K1 adds
two MIPs, while VD-P/VD-S each have one terminal MIP. The new Start changes
neither initial U nor pre-MIP LP model information. No old route is imported.

VD-S maps the actual8273 columns of the retained MIP, checks30485 rows and
reads back every value. Gurobi accepts the Start, and the complete vector is
observed in MIPSOL. Independent actual-vector residual is below2e-16; mapping
difference below8e-15. Submission/mapping/checking cost.01115s inside paid wall.
Terminal native time269.377s,884 nodes; original physical route/time/operation
semantics and full frontier support the reported bounds. K1/VD-P lack native
incumbents in their terminal MIPs despite their valid outer witnesses. Native
Start adoption is thus established at this size; substantial P superiority is not.

The completed K1 HGA event log reaches its final objective at generation71,
about12.484s, then finishes at322.819s. This is an objective-value observation;
it does not by itself prove a shortened run retains identical routes or total
solver performance. No elapsed-time stop is introduced. A future startup
hypothesis would need a uniform admissible criterion and its own experiment
plan. HGA/UB event ledgers are included in compact evidence for that analysis.

After micros/D3/D6:12 runs,57 experiment Optimize calls,3364.314s paid wall,
zero failures. Independent route, parameter, coverage and actual Start audits
pass. All4 VD-S MIP decisions so far are eligible, accepted and fully observed.
42 initial-witness model checks include17 incompatible intervals and25 valid
mappings, no failures.160 compact artifacts are packaged. Post-experiment
audit scan costs are separate from the fully paid internal algorithm costs.

Continue the already-declared C2 protection test. D3's certificate gain and
the absence of a D6 regression justify further qualification of the same frozen
candidate, without assuming all protections or unseen instances will benefit.
Overall goal unmet; no confirmation, extra repeat or3600/7200 comparison opened.
