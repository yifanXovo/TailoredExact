# Measured identity and inheritance

This is a new stacked R105 experiment on R104/PR166, delivery
`aa1d0e5b268cf95442b3713b2af8fc505974f6c2`, measured R104 source
`339835c46c37f353c7cf9813ef749782098fff5d`, measured R104 PE
`c469e9c9fcd0da968e02b6eb6d534d24473ef7c33975742c4aaab3b178284c4d`.
The specific R104 necessary-resource STOP is retained. Its cancelled
confirmations are not R105 experiments.

R105 numerical implementation was committed at
`732820c2c2a4f0d775833b4684dbcee3259c6ddd`; metadata/readback correction
at `91ff7da1b319577bf2fe703417bdd7d994a790a3` is the production source
used by diagnostic03/04 and all control01 arms. Actual ExactEBRP PE SHA256:
`8b17e33c612d9768edec0047df5ca9efdc088ee8fc5a67acfbf0dd1b5f5e19c9`.
Diagnostic02 F2 used the earlier commit/PE and remains explicitly separate.
Later tests, reports and evidence commits do not represent a rebuilt measured
production executable. Per-launch source hashes resolve that distinction.

Gurobi13.0.2 DLL `D:/gurobi1302/win64/bin/gurobi130.dll`, SHA256:
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
Threads=1, Seed=0, Presolve=-1, FeasibilityTol=1e-6,
IntFeasTol=1e-5, OptimalityTol=1e-6, both requested MIP gaps zero.
Affinity mask4 is the inherited serial measurement contract.
Every formal native call uses remaining global work time. The common
30-second exit reserve is inside the stated outer cap, identical across
all arms, with mathematical T and startup unchanged.

| Role | Input | SHA256 | V / capacity vector | T / pickup / drop / lambda |
|---|---|---|---|---|
| F2 | reference/round86_unadapted_confirmation/F2.txt | ebdf99e77dc9dcc57946970fa6d7e1cdf2defdcd277562a454d4889c716b645e | 20 / [30,30] | 3600 / 60 / 60 / .15 |
| R98-C2 | reference/round98_confirmation/C2.txt | 07d0964c87b534254e6bf2957911859a6a2bd73e377211728b7e65f44294fc76 | 30 / [20, 25, 30] | 7200 / 60 / 60 / 0.15 |
| F5 | reference/round86_unadapted_confirmation/F5.txt | 5145b134f52dc573900b0b271325639fb04dc5eed37bf996f6b984f74efacc8a | 50 / [30, 30, 30, 30] | 7200 / 60 / 60 / 0.15 |

`control01/identity.json` is a prelaunch freeze, not a retrospective claim.
`qualification_identity.json` explicitly consolidates test hashes after their
separate executions; production bindings historically omit tests. Native04
and native-added are separately identified rather than relabelled as one run.

No DLL/executable/license/credential is published. Compact evidence preserves
model/solution/quality/parameter/witness/call/fee/input bytes and SHA256s.
Failed receipts and never-started preparations remain distinct.
The three original user-modified files and unrelated historical outputs are
outside this change. No proxy, permission or default-algorithm setting changed.
