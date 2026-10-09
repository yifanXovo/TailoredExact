# Actual V100 entry failure and resource boundary

Round109 is BLOCKED by an actual native entry failure, not by an adverse
performance classification. Normal native execution stops at arm25,
G100-C1/Seed0/M-B. Its original command, input, PE, DLL, source, single-core
affinity and 3600-second cap remain frozen. The normal-return arms1–24 are
retained without reruns; arms26–42 never started. No formal Seed1 comparison
has been measured.

## What actually happened

Arm25 returned Windows status3221225725 (`0xC00000FD`, stack overflow), after
3.109 process seconds and3.327999999979511 legacy supervisor seconds. Its
phase ledger contains only `process_entry` and `instance_parsing_start`.
There is no parsing-complete phase, final result, native solver log, journal
commit or valid physical endpoint. The empty observations array and sampler's
provisional L=0 are not optimization evidence. Its exact full comparison
clock is absent; the aborted legacy clock is disclosed only as failure timing.

Independent actual Windows Application Error1000 and WER1001 records match
the original executable, PID38764, exceptionc00000fd and offset4e2693.
Independent disassembly maps that offset into the executable's instantiated
`std::regex` character matcher. Its PE header reserves2MiB stack and initially
commits4096bytes. `Parser.cpp` uses a bracket-payload expression containing
`[\s\S]*?`. These facts support a regex-stack explanation for the parsing
failure. There is no crash dump with a complete call stack, so the exact
named vector/points substage and full recursion chain are not asserted.

The actual separate `main09_stack_frame01` disassembly supplements this:
`main` probes and allocates0x159490=1,414,288bytes of fixed frame before
parsing, leaving a theoretical682,864bytes of the2MiB reservation even before
other pushes, calls and guard pages. The parser's explicit frame is1712bytes;
the compiled recursive DFS allocates32bytes per own frame and calls its
matcher. This is static-byte evidence for a large-main-frame plus recursive
matching explanation. It does not measure recursion depth or attribute the
main frame to particular local objects. The actual supplement SHA is
9b382567f4abf176916f7238d43a70119cfe46a9d5ab6c96cfb81ea9410d551b;
three disassembly commands/stdout/stderr/exits and an engineering receipt
are retained. The original diagnostic03 and frozen identity are unchanged.

The executable also imports libstdc++; the relevant matcher/executor
instances are compiled into this PE. An earlier diagnostic's description as
purely static is superseded by the actual successful diagnostic03. Original
diagnostic01 and02 source/stdout/stderr/exits remain, including the XML PID
representation correction. No diagnostic invoked a native solver or changed
the production or signed recovery sources.

One pre-exit sample reports13,284,835,328 available memory bytes and
64,784,240,640 free disk bytes. The actual status is stack overflow; it is not
reported as OOM. The public-generated input remains valid under its original
syntax, inventory and physical empty-fleet checks. The batch exporter had
already built its original cold reference with zero Optimize, but that
different exporter does not establish that the measured PE's V100 entry can
complete. H100 qualification was V20, not a V100 performance qualification.

## Why the campaign cannot be repaired inside this frozen round

[Windows thread-stack documentation](https://learn.microsoft.com/en-us/windows/win32/procthread/thread-stack-size)
identifies the executable header as the default reservation source and gives
explicit stack-size options for newly created threads. Increasing the Python
parent's stack or using an ordinary environment variable is not a verified
way to enlarge this `CreateProcess` child's main-thread reservation. No
qualified ordinary environment-only same-PE/same-entry repair was found.
Injected stacks, custom entry execution, changed input bytes or new runtime
dispatch are not substituted for the frozen native entry.

Editing the PE stack header changes its SHA. A parser/build change likewise
requires a new final PE. The task requires all42 performance arms on that
one final PE, even if a repair appears small; previous24 endpoints cannot be
spliced into a different-PE panel.

All13 fee wrappers are closed:51 conservative starts and
18618.079987913487 outer seconds. Main09 declares four paid starts but actually
launches only arm25;26/27 are never-started paid slots, with no refund.
Only21 conservative starts remain. Even ignoring every new wrapper,42 new
native arms require at least93 cumulative starts. Reserving all88200 formal
nominal seconds yields106818.07998791349 cumulative seconds before new
overhead. Both violate the72/100000 limits, without crediting unknown early
stops. There is no performance recovery admission and no further native run.

## Actual independent diagnosis and publication

`review/main09_stack_diagnosis03/audit.json` is
`ACCEPT_DIAGNOSIS_BLOCKED`, with stageBLOCKED and resumption_allowedfalse;
SHA7663f064e05f6d4f0d54f1cfe8420ba5baf87e2b497e3fda109eda047495545a.
Its actual engineering execution exited0 in3.123396199895069seconds with zero
Optimize/native environments. Actual Windows XML, PE-header/disassembly
evidence, input/production/raw/fee bindings, source snapshots, commands,
stdout/stderr and receipts are public evidence. The engine is excluded from
the public carrier; PE bytes were actually inspected locally.

`round109_finalize_blocked.py` calls the unchanged admitted raw reader over
all present evidence, then the unchanged frozen stage function with these
explicit unresolved faults. It adds the complete failure/missing inventory
and source-bound BLOCKED bookkeeping. The original raw-reader summary is
preserved. Incomplete-panel gate placeholders such as `SEED_SENSITIVITY` do
not describe an observed Seed result: all six formal Seed1 arms are unstarted.
The12-main/3-Seed denominators remain fixed. This round cannot support or
reject broader candidate performance from the partial panel.
