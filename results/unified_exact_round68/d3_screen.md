# D3 development screen, common cap300

Original V12/M3/Q30/T2850, input29e0ca2c95ec2e061aa1cc524aaf6a41bf6c4a34355dca86df6966aa8a29b6b4.
All four arms use frozen binary ad6f2973... and the unchanged original settings.

| Arm | Paid wall(s) | Certified | Original UB | Global LB | Absolute gap |
|---|---:|---|---:|---:|---:|
| P-GRB | 297.062 | no | .04505416158053462 | .041582765758340995 | .003471395822193628 |
| K1-R | 297.063 | no | .04505416158053462 | .043903089074057794 | .001151072506476829 |
| VD-P | 297.047 | no | .04545145873146421 | .04226917585419155 | .003182282877272659 |
| VD-S | 84.172 | yes | .04500155005562836 | .04500155005562828 | 7.63e-17 |

VD-S gains the original-problem certificate against all three references. The
new unchanged VD-P control again loses most K1 protection, so the gain cannot
be credited to selecting a favorable old VD-P time. P's end-state bounds match
Round67; this table nevertheless uses only fresh same-build experiments.
The tiny signed final discrepancy is retained as numerical tolerance, not clipped.

K1-R/VD-P/VD-S acquire identical initial route witnesses with F=.049468682614419446;
HGA costs2.084/2.125/2.080s. Each performs3 LPs, one child-bound target MIP and
one terminal MIP, with zero committed splits. VD-P and VD-S use identical
actual model hashes and the same LP domain information. Start does not improve
the initial UB, alter the formulation, or avoid paying the HGA.

VD-S supplies the same complete1776-column witness in the retained parent model
for both MIPs. Each checks4199 rows, reads every Start value back, is accepted
in the native log and is observed as the complete MIPSOL vector. Independent
CSV/model checks have residual<2e-15 and mapping difference<3e-16. Total recorded
mapping/validation/submission cost is about0.005s inside paid wall. The target
MIP takes0.187s; terminal MIP81.550s,10805 nodes. No local time/Work stop is used.

Native telemetry shows K1's first printed search incumbents at44s and VD-P's
at241s. VD-S begins with the paid Start, improves to.0454515 at20s and reports
the final objective rounded as.0450016 at26s; it subsequently proves the bound.
Those intermediate printed values are native reports, not independently retained
full event vectors. The formal final witness is independently physically checked.
Search path and proof cost change substantially even though the projected LP
is unchanged. This is finite evidence for useful primal integration, not a
general claim that supplying Starts always improves dual bounds.

After the four micros and D3 panel:8 runs,37 experiment Optimize calls,
976.048s paid process wall, zero failures. Full-route/coverage/parameter audit
passes; all3 actual VD-S MIP Start decisions so far are eligible and accepted.
27 initial-witness model audits include11 incompatible Gini intervals and16
valid mappings, with no failures.94 compact evidence artifacts are packaged.

This is one exposed development role. It warrants the already-planned D6/C2
tests, but does not establish generalization, CitiBike startup repair or the
whole research goal. A large improvement needs a limited fresh repeat before
a stable-performance claim; no extra batch has yet been authorized by a new
resource revision. Continue the predeclared panel without changing the candidate.
