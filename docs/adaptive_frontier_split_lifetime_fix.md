# Adaptive Frontier Split Lifetime Fix

The fair-diagnosis campaign observed one nondeterministic Windows access violation
while finalizing a V12 M2 frontier split. Windows Error Reporting recorded
`0xC0000005` at executable offset `0xBD883`. A symbolized `-O2 -g` build mapped
the fault to `src/main.cpp:13781`.

The split loop stored a reference to `interval_records[parent_idx]`, then appended
the first child to `interval_records`. A vector reallocation could invalidate the
parent reference. Building the second child subsequently read
`parent.lower_bound_source` through that invalid reference.

The fix copies `parent.lower_bound_source` before any child insertion and uses the
copy throughout the loop. The inherited lower-bound value, source label, child
coverage, and certificate logic are unchanged. Only the object lifetime is
corrected.

Validation consists of:

- the existing `adaptive-frontier-split-test`;
- repeated execution of the exact V12 M2 cheap-cut command that first faulted;
- the complete serial matched campaign, whose process return codes and final JSON
  status are audited.

The pre-fix crash artifact remains diagnostic evidence only. It is not selected as
a bound or certificate.
