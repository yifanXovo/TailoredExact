# Order/slack qualification (real-instance admission still pending)

The free-order model passed all 750 inventory/permutation mappings: 85 were
physically feasible, and model feasibility agreed for every mapping. The one
native micro returned the enumerated optimum 0.20833333333333331, status 2,
zero checked row/bound/integrality residual and an independently valid route.
Its entire Python process took 0.5430564 s; this is the second native micro of
the four allowed in this round. It is a restricted diagnostic certificate.

The C++ order mechanism micro passed. Initial F, complete two-station closure F
and original R83 closure F were all 0.31666666666666665. The new finite proposal
accepted one route-order move, followed by one original quantity move, reaching
F=0. Its entire test process took 0.2323946 s, with no native Optimize call.
Repeated invocation on the zero endpoint preserved it. This demonstrates a
physical mechanism, not real-instance benefit or global search efficiency.

The first incremental build succeeded with two misleading-indentation warnings;
the code was made unambiguous before any test or real diagnostic. The second
build completed without warnings. Both build logs and timings are retained;
neither is a performance run. `route_order_build_gate.json` binds the actual
second-build binaries, source files, cache and micro receipt.

The one F5-final free-order diagnostic is now the next paid contrast (300 s).
It remains restricted to original ownership and originally served nodes. Any
time-limit result must remain unknown unless a validated better witness is
returned. The six predeclared C++ cases follow serially and are the actual
incremental quality/cost admission test against unchanged R83 closure.
