# Round 50 K1-AM action-mapping erratum

Round 50's pair interpretation inferred K1-AM actions from comparison labels.
The authoritative adaptive-mass ledger instead records lifecycle actions:
`split` means MIDPOINT, while `native-target` and `exact-close` both retain the
parent rather than creating a midpoint split. Historical raw evidence is not
modified.

The corrected mapping changes 5 of seven pair labels. Major root,
strong-control root, tight3102 L0.0, and the high-imbalance root are verified as
RETAIN, RETAIN, RETAIN, and MIDPOINT respectively. The high-imbalance Round 50
pair target is the distinct child L0.1.0 and is RETAIN.

Under the frozen ratio-plus-absolute rule the corrected audit has
0 severe false split(s) and 3 severe false
retain(s), 3 total. The major root is not
a K1-AM false split; strong-control root, tight3102 L0.0, and high-imbalance
L0.1.0 are severe false retains. This additive erratum supersedes only the
mapping/count interpretation in Round 50, not its native logs, exact results,
or production-v0 decision.
