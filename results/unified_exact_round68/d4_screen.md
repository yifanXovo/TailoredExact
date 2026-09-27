# D4 development protection, common cap300

Original V12/M3/Q30/T2400; input
7ee8a95ca3043f83b2e8c6b3663f8aa212678043d0c98b0153efbeb834d48823.
The conditional batch was opened under the original resource allowance after
D3/D6/C2 qualification; see conditional_d4_opened.json.

| Arm | Paid wall(s) | Certified | UB | LB |
|---|---:|---|---:|---:|
| P-GRB | 297.078 | no | .506343307565206 | .19587930751914068 |
| K1-R | 129.657 | yes | .506343307565206 | .5063433073265636 |
| VD-P | 40.062 | yes | .506343307565206 | .506343307565206 |
| VD-S | 54.453 | yes | .506343307565206 | .5063433075652053 |

VD-S is14.391s/35.92% slower than VD-P, a material regression under the frozen
small-certified rule. This negative component result is retained. It still
certifies75.204s/58.00% faster than K1-R and preserves the certificate gain over
P. The D3 repair therefore has a local cost against the one-hot ablation,
without losing the important K1/P protection. This is an acceptable current
development tradeoff, not a requirement to retain every historical fastest time.

All K1 variants have identical paid initial routes; HGA costs about1.96-1.97s.
All perform3 LPs. K1 uses one terminal MIP; VD-P/VD-S also perform a mathematical
target MIP. Both VD-S starts are accepted and observed as complete MIPSOL vectors,
with independent actual-vector checks. Its terminal MIP costs51.914s,10273 nodes.
Every original-route, parameter and coverage audit passes. Signed certificate
discrepancies remain visible rather than being silently clipped.

The final declared panel is complete:20 runs (16 performance+4 micros),
94 experiment Optimize calls,4735.860s paid wall, zero failures. All8 actual
VD-S MIP decisions are eligible, accepted and fully observed.66 retained
initial-witness model audits contain26 incompatible intervals and40 valid
mappings, no failures.278 compact evidence artifacts are packaged. No extra
repeat, independent confirmation or3600/7200 comparison is included.
