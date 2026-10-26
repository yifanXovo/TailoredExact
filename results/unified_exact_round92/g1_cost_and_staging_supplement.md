# Round92 G1 cost and staging supplement

This supplements, without changing, `qualification_001/report.md` and
`qualification_002/report.md`. Times below were parsed from the retained UTC
strings with Python `datetime.fromisoformat`; values are reported to the
microsecond because that parser does not retain the seventh fractional digit.

| Attempt | Known start | Known postflight/release marker | Elapsed interval | Nested stage walls |
| --- | --- | --- | ---: | ---: |
| 001 | first configure, `2026-09-27T10:19:11.0641738+00:00` | no-process postflight, `2026-09-27T10:21:24.9665094+00:00` | 133.902336 s | 36.0171588 s |
| 002 | preserve-old-exe, `2026-09-27T10:24:41.0822928+00:00` | no-process postflight/release, `2026-09-27T10:25:21.7033108+00:00` | 40.621018 s | 4.5426408 s |

These are elapsed windows, including intermediate inspection, receipt/report
work, and waiting. They are not CPU time and must not be added to nested
command walls. The 002 release-message delivery instant was not recorded;
the postflight marker is the known endpoint.

For 001, the retained tool-call outputs reported complete `exec_command`
observation walls of 3.1787676 s (configure), 1.4379187 s (CTest), and
0.7167205 s (failed exporter). The build's first tool call observed
30.0027319 s and returned a live session; a later poll reported
0.0000071 s, which does not measure the intervening wait. Thus a complete
external launch-to-exit wall for that build, and a four-command external-wall
sum, cannot be recovered from the retained observations. The four nested
PowerShell command walls in the original report are complete for their stated
scope. For 002, `outer_invocations.json` retains all four separately observed
outer walls totaling 5.9066357 s. None of these measurements is a standalone
whole-attempt CPU cost.

The following are the exact existing files in the two qualification directories
for Git staging (24 files/346,271 bytes in 001; 26 files/204,744 bytes in 002).
Keep zero-byte stderr/stdout files and the failed prefix. Ignored `.log` files
may require explicit forced staging. The old and repaired test executables
reside under `build/` and are intentionally excluded. Stage this supplement
itself as an additional file.

```text
results/unified_exact_round92/qualification_001/artifact_index.json
results/unified_exact_round92/qualification_001/build.receipt.json
results/unified_exact_round92/qualification_001/build.started.json
results/unified_exact_round92/qualification_001/build.stderr.log
results/unified_exact_round92/qualification_001/build.stdout.log
results/unified_exact_round92/qualification_001/canonical_export/five_station_input.txt
results/unified_exact_round92/qualification_001/canonical_export/invalidated.lp
results/unified_exact_round92/qualification_001/canonical_export/off.lp
results/unified_exact_round92/qualification_001/canonical_export/on.lp
results/unified_exact_round92/qualification_001/canonical_export/reused.lp
results/unified_exact_round92/qualification_001/configure.receipt.json
results/unified_exact_round92/qualification_001/configure.started.json
results/unified_exact_round92/qualification_001/configure.stderr.log
results/unified_exact_round92/qualification_001/configure.stdout.log
results/unified_exact_round92/qualification_001/ctest.receipt.json
results/unified_exact_round92/qualification_001/ctest.started.json
results/unified_exact_round92/qualification_001/ctest.stderr.log
results/unified_exact_round92/qualification_001/ctest.stdout.log
results/unified_exact_round92/qualification_001/export.receipt.json
results/unified_exact_round92/qualification_001/export.started.json
results/unified_exact_round92/qualification_001/export.stderr.log
results/unified_exact_round92/qualification_001/export.stdout.log
results/unified_exact_round92/qualification_001/g1_step.ps1
results/unified_exact_round92/qualification_001/report.md
results/unified_exact_round92/qualification_002/artifact_index.json
results/unified_exact_round92/qualification_002/build.receipt.json
results/unified_exact_round92/qualification_002/build.started.json
results/unified_exact_round92/qualification_002/build.stderr.log
results/unified_exact_round92/qualification_002/build.stdout.log
results/unified_exact_round92/qualification_002/canonical_export/five_station_input.txt
results/unified_exact_round92/qualification_002/canonical_export/invalidated.lp
results/unified_exact_round92/qualification_002/canonical_export/off.lp
results/unified_exact_round92/qualification_002/canonical_export/on.lp
results/unified_exact_round92/qualification_002/canonical_export/reused.lp
results/unified_exact_round92/qualification_002/canonical_export/zero_handling.lp
results/unified_exact_round92/qualification_002/export.receipt.json
results/unified_exact_round92/qualification_002/export.started.json
results/unified_exact_round92/qualification_002/export.stderr.log
results/unified_exact_round92/qualification_002/export.stdout.log
results/unified_exact_round92/qualification_002/g1_repair_step.ps1
results/unified_exact_round92/qualification_002/outer_invocations.json
results/unified_exact_round92/qualification_002/preserve.receipt.json
results/unified_exact_round92/qualification_002/preserve.started.json
results/unified_exact_round92/qualification_002/preserve.stderr.log
results/unified_exact_round92/qualification_002/preserve.stdout.log
results/unified_exact_round92/qualification_002/readback.receipt.json
results/unified_exact_round92/qualification_002/readback.started.json
results/unified_exact_round92/qualification_002/readback.stderr.log
results/unified_exact_round92/qualification_002/readback.stdout.log
results/unified_exact_round92/qualification_002/report.md
results/unified_exact_round92/g1_cost_and_staging_supplement.md
```
