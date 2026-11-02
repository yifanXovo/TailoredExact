# Matched LP increment: one added common-S row

Five complete saved R146 LP domains on three physical instances were
reoptimized once each. K20 BASE/joint/STOCK are three carriers of one
instance. The original objective and constant, all old rows, support,
variable bounds, g interval and cutoff are exactly retained. No old LP
is reoptimized and no variable is fixed at its old fractional value.
Each new row is bound to the saved model/primal SHA. The old GD high
and low rows remain. All five actual Native readbacks equal the signed
compiled rows. Seed0, Threads1, affinity4, serial execution.

| Role | Carrier | Old objective | New objective / qualified numerical LP bound | Gain | g | Weighted penalty |
| --- | --- | --- | --- | --- | --- | --- |
| K-20-S | base | 0.236010302342 | 0.238279588751 | 0.002269286408 | 0.061061931719 | 0.177217657031 |
| K-20-S | joint | 0.239052184675 | 0.241511748078 | 0.002459563403 | 0.061972915276 | 0.179538832802 |
| K-20-S | stock | 0.251016109922 | 0.255570495817 | 0.004554385894 | 0.076057748783 | 0.179512747034 |
| K-35-U | base | 0.204187028164 | 0.209568159043 | 0.005381130879 | 0.048029680471 | 0.161538478571 |
| R-X20-S-T1 | base | 0.365004645621 | 0.381636295279 | 0.016631649658 | 0.160832394483 | 0.220803900796 |

| Role/carrier | Rows added | Row NZ | Construction/readback s | Native runtime s | Outer s | RHS box loss bound | Remaining violation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K-20-S/base | 1 | 450 | 0.742987 | 0.185000 | 1.536582 | 7.669e-16 | 0.041731590572 |
| K-20-S/joint | 1 | 450 | 0.669450 | 0.263000 | 1.347596 | 7.934e-16 | 0.046090430886 |
| K-20-S/stock | 1 | 450 | 0.620293 | 0.154000 | 1.169401 | 7.437e-16 | 0.049551078681 |
| K-35-U/base | 1 | 537 | 1.867377 | 1.055000 | 3.607366 | 3.013e-16 | 0.028004456515 |
| R-X20-S-T1/base | 1 | 144 | 0.490440 | 0.098000 | 0.915103 | 2.207e-16 | 0.033261183883 |

The final column is separation at the returned new point; it is not
another optimized increment. No optional closure rounds were entered:
one row already gives clear information on D carriers and beyond the
joint carrier. These LP diagnostic domains are not automatically the
current full algorithm's root domain.

The full objective matters. On K20 BASE, g decreases from about .065068
to .061062 while weighted penalty rises from about .170943 to .177218;
their sum increases by .002269. On K35 the weighted penalty remains
.161538478571 and g supplies the .005381 increase. Point activity cannot
substitute for either optimized comparison.

All results are numerical OPTIMAL values with every inherited quality
measure and independent full-matrix residual at most 1e-6. The numerical
dual objective/gap and any adverse reduced cost at an infinite bound are
reported separately in result.json. Neither the old floating-point
optimum nor these values are represented as exact rational optimality
certificates. The exact rational certificate here concerns the new row's
valid coefficient direction. Initial LP values, Native root-after-cuts
bounds and final external supported L are separate evidence layers.

The E1 decision is to implement one uniform, default-off own-root row
and one additional root LP on standalone D, then first test the K35
same-new-PE full pair. It is not an adoption decision. No STOCK/joint
combination grid, exact LP closure or second inequality family is opened.
