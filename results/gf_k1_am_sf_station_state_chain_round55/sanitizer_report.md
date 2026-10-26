
# Sanitizer report

The normal GNU 14.2 warning-enabled Release build and both Round 54/55 suites
pass. A separate non-Gurobi AddressSanitizer/UndefinedBehaviorSanitizer
configuration was attempted before optimization. This Windows MSYS2 toolchain
does not ship `libasan` or `libubsan`; the compiler link probe failed with
`cannot find -lasan` and `cannot find -lubsan`, so a sanitizer executable could
not be produced on this host. This is recorded as an environment limitation,
not a passed sanitizer run.

Static audit covered signed shifts, overflow guards, finite-value gates,
solver return-code checks, initialized configuration fields, artifact paths,
incumbent epochs, and CRLF-independent binary SHA-256 hashing. Capacity is an
`int`, while bit construction uses `1LL << bits`; the maximum reachable shift
is safe for the represented capacity domain. The exact DP uses checked
addition and budget saturation.
