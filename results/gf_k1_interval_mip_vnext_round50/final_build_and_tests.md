# Round 50 clean official build and final tests

- Build directory: `build/official-round50-fe793b20e`
- Source commit at configure/build: `fe793b20efe85f85761c5a7b938a7f3f168f424a`
- Source tree: `a893eec926240fb364795005f64294df84bcfd25`
- Configuration: clean Release, MinGW GCC 14.2.0, Gurobi 13.0.2 enabled
- Full build: passed (100%)
- CTests: 28 passed, 0 failed
- Historical Python protocol tests: 162 passed, 0 failed, after binding the Round 46--49 suites to their existing SHA-named official executables
- Round 50 Python protocol tests: 22 passed, 0 failed
- Combined protocol discovery: 184 passed, 0 failed
- Round 50 fixed-state executable SHA-256: `85a6404acb015ea71e1b56a656f85665cda46b1f72a29a7174e6f48d96f8e81a`
- Round 50 full-solver executable SHA-256: `7cc8ecb324c69526b38f21a8d66cdc4ca6ab6de0cd03639f916f25340d097a2e`

The first broad protocol discovery attempt reported four class-setup errors solely because those historical suites defaulted to unsuffixed build paths. The expected official binaries existed in their SHA-named directories. The final combined run supplied the documented Round 46--49 overrides and passed all 184 tests. No source or evidence assertion failed.

Final audits also pass: 23/23 default-off fixed-state comparisons; 37/37 physical completion-marker and artifact-manifest checks; 0 false certificates; no V50; no cap above 1,800 seconds; no hidden runtime dispatch; source scope, secret/license, numerical quality, compact storage, and pre-existing-file preservation all verified.
