# v2 development runner — independent static review

The user-requested third perspective `/root/independent_review` read the
proposed `scripts/round97_development_v2.py` while qualification03 arm1 was
active. No compiler, optimizer, matrix audit or script execution was used.

One real freeze-boundary omission was found: the new preparer originally
checked qualified source/binary but replaced runner/helper hashes with
current values without first comparing them with the qualification freeze.
`qualified()` now verifies the original runner and every original helper,
plus research plan, revision plan and build identity, before admitting the
new development script to the new identity. The independent reviewer
confirmed this repair on a second static pass.

The reviewer verified D7 input d7dbd018…/T18000 and matched zero-Optimize
original compact reference; V1 dd841e57…/T7200; F2 ebdf99e7…/T3600;
same-v2-binary F5 feedback+r83/r96; OFF observe; plain original P-GRB;
13arms/33300s; no loading of historical solutions or reuse of old timings.
The existing non-P audit accepts the explicit OLD-FEEDBACK label.

The separate finite qualification continuation script was also checked. It
requires normally completed/audited arm1 and never-created arm2/3
destinations; then audits arm1 vectors, runs/audits arm2, and runs/audits
arm3. Mutable status uses a temporary file plus replacement, avoiding the
earlier immutable-write queue failure. Any failure exits without a restart.
The reviewer suggested additionally comparing summary (number,id,arm)
against the frozen launches; this small hardening was applied. Final queue
status explicitly requires a subsequent root qualification decision.

These are harness static findings, not passed real v2 qualification or a
complete stage review. The real gate is deliberately absent until the
actual production evidence and independent matrices are checked. The
development/confirmation campaigns were not started by this review.
