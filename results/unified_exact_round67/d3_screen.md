# D3: loss of most of the existing K1 advantage

All four300-second whole runs completed and passed the same original-route,
native-parameter, model and full-coverage checks. The three K1 variants paid
the same initial routes; HGA took about2.1s, so startup is not the main issue.

| Arm | Process wall | UB | LB | Signed absolute gap |
|---|---:|---:|---:|---:|
| P-GRB |297.062|0.04505416158053462|0.041582765758340995|0.003471395822193628|
| K1-R |297.047|0.04505416158053462|0.04389637164220094|0.001157789938333681|
| VD-P |297.063|0.04545145873146421|0.042261711123146736|0.003189747608317473|
| LOG |297.062|0.04500155005562836|0.042367116468609856|0.002634433587018502|

None certifies. VD-P/LOG have somewhat smaller gaps than P, but only retain
12.2%/36.2% of K1-R's gap improvement over P. Their losses against K1-R both
meet the frozen material criterion. This is a substantial loss of an existing
advantage, not a harmless isolated timing difference. VD-P versus P is mixed
(worse UB, better LB); LOG has slightly better UB and better LB than P but a
much weaker LB than K1-R. Better UB must not be described as better proof.

LP strength did improve: initial K1-R0.02097749561 versus VD-P/LOG0.03000187371.
Thus a rule that selects solely on positive root-LP gain is not supported by
this role. Both alternative encodings spent much of the native search without
an incumbent, though the outer HGA UB remained valid. Full original witness
mapping into compatible models passed after the queue. No native starts were
submitted. This motivates an integration question, not a promised start gain.

The300-second results do not settle the old certification-time tail; all runs
are open. They do establish a current material loss of K1 protection. That
loss must be considered with D4/C2 and the primary D6 objective, not used as an
automatic per-point veto or hidden by a mean. C2 is still running. No rule,
input, threshold or source binary was changed after these results.
