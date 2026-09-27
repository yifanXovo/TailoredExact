# Round 87 user-authorized early closure

The original frozen protocol planned 18 serial runs (nine pairs). On 2026-09-26,
the user reduced this round's execution scope to the first 10 completed runs
(five complete pairs), citing the available time budget. The frozen protocol,
original driver, analyzer, solver binary, model, inputs, and completed data are
not rewritten to conceal the original plan.

The five formal pairs are D6, D7, U6, F2, and F5. Their first 10 run records
are in `campaign/summary.json`; each completed run has a passing run audit.
The original 18-run `driver_completion.json` does not exist and must not be
fabricated. A separate partial-scope offline analysis independently replays
only these 10 runs and explicitly reports the revised scope.

Before the scope-change message arrived, the detached serial driver had
already completed run 10, F5/ENS-C, and automatically launched run 11,
F6/ENS-C. At the first read after the message, run 11 showed approximately
2,400.531 process seconds. The identified continuation driver (PID 3836) and
run-11 solver (PID 39044) were then stopped; both were confirmed absent.
Run 11 has no completed formal record, is not one of the five pairs, and is
not used in any performance result. Its raw directory remains at
`E:\codes\ExactEBRP-round87-runtime\campaign\local_raw\11_F6_ENS-C`
as evidence of the attempted launch and user-directed stop. No run-12
directory existed at closure; runs 12–18 were not launched.

F6 and the remaining original panel roles were omitted solely because this
round's time budget ended. Their omission is not a failure or adverse
algorithm result; the same instances remain eligible for a future,
separately declared test. The F2/P-GRB quota interruption and its
conservative timing reconstruction are documented separately in
`interruption_report_2026-09-24.md`.
