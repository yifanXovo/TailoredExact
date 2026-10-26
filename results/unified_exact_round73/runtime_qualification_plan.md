# Read-only evidence qualification (prospective, v5)

The algorithm remains the qualified v4 constructor plus 24+1 finite descent.
This shared instrumentation change requires one fresh isolated v5 build and
the complete serial CTest suite, including existing native fixtures. No prior
build, fixture or startup diagnosis is overwritten. Unit tests will exercise
scope, corrupt/incomplete receipts and inconsistent physical bounds without
an optimizer. If v5 fails, retain it and declare the repair before another build.

Implement an opt-in `--native-evidence-dir` journal. P publishes full original
compact bounds; interval calls publish local bounds and an immutable outer
coverage snapshot. Complete coverage must include cutoff-excluded objective
values, G-excluded ranges and explicitly verified contraction halves. Missing
coverage never becomes an inferred global bound. An analytical F>=0 record
is separately labelled and cannot masquerade as a recovered native bound.
Callback physical witnesses are independently verified and retained by original
F; observing them never changes the mathematical algorithm or native settings.

Data files are closed before hash receipts are written. Receipt timestamps
are taken after the data close; a reader must also record when the complete
receipt was first observed. Checkpoint availability uses the later time, never
backdates to a native callback runtime, and rejects partial or corrupt files.
This establishes process-kill persistence, not power-loss durability.

After successful qualification, the originally reserved six native diagnoses
are allocated in this order, all fresh, serial, at most30s whole-process each:

1. tiny T3, zero handling, P-GRB, normal completion.
2. same tiny, JDS-X, normal completion and scoped-bound receipts.
3. D6, P-GRB, terminate the owned diagnostic child after a committed native
   physical witness and bound have both been observed (otherwise whole-run stop).
4. D6, JDS-X, same forced termination criterion; preserve initial and callback
   witnesses, local scope and frozen complete coverage separately.
5. D3, P-GRB, normal whole-run deadline path.
6. D3, JDS-X, normal whole-run deadline path.

Forced termination is a reliability diagnosis only; it is not a candidate
strategy or a formal performance comparison. Commands and exact input/build/
script hashes must be frozen in the launch ledger before dispatch. Use the
same logical2/mask4 affinity and readback as prior experiments. At most180s
of fresh diagnostic process allowance is opened; any overrun is still failed.
The supervisor terminates the entire owned child with a declared cleanup
reserve inside30s; it does not launch another algorithm within that run.
All setup, callback verification, writes, polling, kill and exit wall is paid.
Offline replay cost is recorded separately. No formal/long panel is opened.
