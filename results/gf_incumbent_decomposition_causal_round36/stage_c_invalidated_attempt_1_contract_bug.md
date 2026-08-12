# Round 36 Stage C invalidated attempt 1

The first Stage C attempt is invalidated in full. Its 18 completed rows and
the preserved row-19 failure were moved, without deletion, to
`stage_c_invalidated_attempt_1_contract_bug/`.

Row 19 exposed a Round36-only contract defect. The independently verified
current proof incumbent improved from the startup-pair value
8.778082265416142 to 8.773853723068965 while the frozen decomposition anchor
remained 8.833146456637262. The old equality check rejected this safe
monotone improvement before the external tree began.

The archived attempt contains 19 run directories: 18 valid completion markers
(9 strict certificates and 9 valid noncertificates, with zero false
certificates) plus the fail-closed row-19 state. None of these rows may be
reused. Stage C must be re-frozen and all 47 rows rerun from serial order 1
under one isolated contract-fix executable. No candidate is promoted by this
diagnostic evidence.
