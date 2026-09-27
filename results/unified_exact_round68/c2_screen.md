# C2 development protection, common cap300

Original V20/M2/Q30/T1800; input
1bb4898eef8e5b2535a6d1d609637528875581fa81acf120636941f285f23b60.
The inherited historical role name says confirmation; this stage explicitly
uses it as exposed development data. It is not an independent confirmation.

| Arm | Paid wall(s) | Certified | UB | LB |
|---|---:|---|---:|---:|
| P-GRB | 297.063 | no | .8299634131717752 | .7714391643536709 |
| K1-R | 297.062 | no | .8299634131717752 | .797752204848004 |
| VD-P | 132.531 | yes | .8299634131717752 | .8299634128939517 |
| VD-S | 123.640 | yes | .8299634131717752 | .8299633966524623 |

VD-S preserves the certificate gain over P and K1. Its8.891s/6.71% reduction
against VD-P is below the frozen10s/15% material threshold, so this is preserved
protection with a small observed time difference, not a major new speedup.
The fresh VD-P control reproduces the previous132.656s certificate closely.
No old timing is substituted for a current paired reference.

All K1 variants acquire the same initial physical route witness, with full HGA
costs2.698/2.717/2.686s. Each uses5 LPs, one mathematical target MIP and one
terminal MIP, and commits one split. VD-S supplies the already-paid witness
to both actual retained MIPs. Both Starts pass the independent complete-point
checks and are accepted in the native logs. Full route, parameter and frontier
checks pass. The final signed discrepancy1.65e-8 is retained explicitly within
the existing numerical certificate tolerance; this is not a rational certificate.

After micros/D3/D6/C2:16 runs,79 experiment Optimize calls,4214.610s paid wall,
zero failures.57 initial-witness model audits include23 incompatible intervals
and34 valid mappings. All6 actual VD-S MIP decisions are eligible and accepted.
219 compact evidence artifacts are packaged, including actual Start vectors,
acceptance logs and HGA/UB event ledgers. This is still a development screen.

The predeclared D4 condition is now met: there is a useful candidate (D3
certificate gain, no D6 regression, C2 protection retained) with no unresolved
implementation failure. Open the four-arm D4 cap300 batch within the existing
maximum16 performance+4 micros; no extra resource allowance is introduced.
