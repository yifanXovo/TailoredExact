# Preflight attempts

Initial configure passed in3.047s. Initial build failed in29.516s because the
backend's dynamic API wrapper had not loaded GRBsetintattr, needed to clear and
replace NumStart. The official Gurobi13.0.2 C header declares this function;
it is now explicitly resolved alongside the existing attribute functions.
This is an implementation wiring failure before tests/performance, not a
formulation or native solver failure. Source hashes before the attempt and
its full build log/receipt remain in build/round68/preflight_source_v1.json,
build_v1.log and build_v1.json. No performance/native micro has run.

NumStart and StartNumber=0 select the one complete supplied vector; they are
start bookkeeping, not search-policy tuning. The Start values are fully read
back. Clearing explicit starts does not claim to clear native previous-solution
reuse. That distinction is tested on the retained model.

The repaired build passed in42.938s (binary c291322fb78c08a2e587270a02e711d3302680070abb32a3854c7cde941fbbd4).
The first full CTest batch had44 passes and one new integration failure in4.578s:
the native model contained an unsupported column named `0`. Only its LP
qualification Optimize ran; the failed mapping prevented native MIP submission.
The LP writer serialized an empty left-hand expression as `0 <= 6` on the
zero-handling fixture. Gurobi interpreted `0` as a variable. The official
[LP constraints format](https://docs.gurobi.com/projects/optimizer/en/current/reference/fileformats/modelformats.html#constraints-section)
does not permit a constant on the left-hand side.

The shared writer now emits `0 G` for an empty expression, using the G variable
present in every compact model. This is an exact zero linear term, including
for impossible constant rows. No tolerance or intended constraint is changed.
Do not merely bless an arbitrary new column in the complete Start mapper.
All references will use the repaired build; model-byte changes where an empty
expression occurs will be identified separately from performance mechanisms.
The failed native artifact, log and rejection are copied to
build/round68/preflight_native_v2 before any retest; source/build/test receipts
remain separately versioned. No formal performance or native-micro launch yet.

Read-only inspection of all retained Round67 generated LPs found42 bare-zero
rows, all either tautologies or `0 <= negative` contradictions also infeasible
under the native column's nonnegative bound. No potentially relaxed false
constant row was found in that finite evidence. See round67_constant_row_audit.json;
this does not qualify uninspected historical models.

Build v3 passed in19.531s, binary ad6f29736c3f10a51339f07a3b7e2160964815e855b91ba8e60db27caeb49340.
The actual retained native Start then passed all258 rows, objective/readback,
was loaded by Gurobi and observed as the complete MIPSOL vector. Its MIP
certified5/24. The CTest assertion nevertheless failed because it expected an
empty success reason, while the established backend returns the string `none`.
That test-contract assertion was corrected; no solver change was required.
The full batch took3.719s (44 passes/one test failure). Two native qualification
Optimize calls ran in that attempt, before the assertion stopped the test.

Build v4 passed in2.453s with the same ad6f2973 binary; only the test assertion
changed. All45 CTests passed in1.859s. The new retained-model test performed
3 Optimize calls: LP, accepted complete MIP Start, and an ineligible replacement
with explicit Start cleared. Qualification evidence is in qualification_native_v4
with byte hashes. Across the failed and successful new-test attempts there were
6 native calls (1+2+3); these are separate from formal experiment calls. Total
configure/build wall was3.047/94.438s; failed CTest wall8.297s. See qualification.json.
The raw CTest detail retains its original Windows locale header bytes.

Offline audit tooling was repaired before performance: importing the reused
Round67 mapper reset shared ledger globals, and duplicate metadata keys broke
record construction. Explicit stage rebinding and record updates fixed both.
The corrected audit reads exactly four current micros and one actual Start.
These caused no optimizer rerun or solver/source change; no old-stage files
were written. Four micros certified5/24,21 calls,0.704s total process wall.
The submitted micro vector passed71 columns/167 rows and native adoption.
