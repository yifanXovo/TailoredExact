# Consolidated terminal interpretation of Round 36

This record resolves the naming and lifecycle ambiguity in the frozen Round 36
package without rewriting historical evidence.

## Evidence chronology

1. **Stage B checkpoint.** `final_report.md` and
   `final_audit_decision.json` classified the isolated mechanism as
   `decomposition_geometry_dominant` and authorized a separately frozen Stage C
   validation candidate. These are intermediate decision artifacts despite
   their historical filenames.
2. **Stage C terminal decision.** `stage_c_final_report.md` and
   `stage_c_final_audit.json` recorded 47/47 completed rows, 18 strict
   certificates, 29 valid noncertificates, and zero false certificates. BW-P
   failed the frozen performance gate (qualification 9-9-17; independent V50
   2-6-4), so C6-HGA-FULL remained the validated mainline.
3. **Repository lifecycle.** Round 36 head
   `4eb8e36515bbb2dd36ba49c5605c7c1b12a7ae32` was merged through PR 83 as
   `414c01216bb3aa30eb1f27f390b6f23bf06cb2eb` at
   `2026-08-12T14:37:45Z`. The historical `github_pr_record.json` and
   `completion_requirements_audit.*` captured the earlier open-draft state and
   are now stale as live-state descriptions.

## Current conclusion

Round 36 supplied evidence that incumbent-dependent decomposition geometry can
causally alter the downstream exact search. It did **not** establish that the
tested wider-anchor policy is a generally better exact algorithm. The only
valid terminal algorithm decision is: keep C6-HGA-FULL unchanged and study a
structural geometry mechanism rather than promoting BW-P or conducting a
generic K/rho sweep.

## Immutability decision

The ambiguous Stage B filenames and pre-merge PR records are retained byte for
byte because the Stage C frozen manifest anchors the Stage B decision SHA-256
and the package is historical provenance. This consolidation layer supersedes
them for present-tense reporting.
