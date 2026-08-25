# Round 50 clean official build and initial tests

- Build directory: `build/official-round50-fe793b20e`
- Source commit at configure/build: `fe793b20efe85f85761c5a7b938a7f3f168f424a`
- Source tree: `a893eec926240fb364795005f64294df84bcfd25`
- Configuration: clean Release, MinGW GCC 14.2.0, Gurobi 13.0.2 enabled
- Full build: passed (100%)
- CTests: 28 passed, 0 failed
- Historical Python protocol tests: 158 distinct tests passed after binding the Round 46--49 suites to their existing SHA-named official executables
- Round 50 fixed-state executable SHA-256: `85a6404acb015ea71e1b56a656f85665cda46b1f72a29a7174e6f48d96f8e81a`
- Round 50 full-solver executable SHA-256: `7cc8ecb324c69526b38f21a8d66cdc4ca6ab6de0cd03639f916f25340d097a2e`

The first broad protocol discovery attempt reported four class-setup errors solely because those historical suites defaulted to unsuffixed build paths. The expected official binaries existed in their SHA-named directories; rerunning the four suites with their documented environment overrides passed all 42 tests. No source or evidence assertion failed.

Final post-run evidence, default-off, certificate, coverage, source-scope, and storage audits are recorded separately and will be appended to the final test summary.
