# Round103 decisions (development in progress)

1. Stack on R102 PR164 delivery0b5640f0de5a29abf6545962dd776a2fab198f90,
   rather than main. The supplied measured source and PE were verified.
   ENS-C remains protected default; M-B, R101 and R102-J are not promoted.
2. Diagnose the actual declared conservative resource domain, with all
   original stations. Extend the DP with independently verified traceback;
   use full support upper bounds for cuts and explicit combinations for
   membership. Finite restricted distance alone never certifies OUTSIDE.
3. Eight full real raw/native points cover F2, C2, F5 and N2. C2/F5 zero
   hits in the historical finite direction family were not membership:
   full-domain dyadic pricing separates those points. N2's native point
   provides both actual OUTSIDE and explicit INSIDE examples by vehicle.
4. Base C2 convexification closes within1e-8 at the original objective
   0.16123605049876005. F5's original terminal classification includes an
   honest1.28465e-8 UNKNOWN. Preserve it. Separately paid feasible
   finite-column full-model witnesses bracket base and enhanced F5 hull
   objectives around0.244169448027537; these are numerical upper witnesses,
   not original BRP lower bounds or route UBs. Signed tiny bracket inversion
   is preserved and attributed to numerical LP precision, not clamped.
5. Investigate only the three-anchor mask strengthening. It excludes
   significant mass in actual mixtures and separates the original C2/F5
   points after remixing is allowed; one C2 vehicle does remix INSIDE.
   Enhanced C2 still closes at the unchanged objective. Enhanced F5 has
   the same numerical objective bracket. Reject anchors for production
   because the extra cost has no useful objective-capability evidence.
6. F2 base convexification closes within1e-8 at0.638005040404497, versus
   L0=0.528625649465355 and finite LJ=0.5286753357380306. The paid closure
   uses827 rows,456 outer LP/3188 master LP/3105 DP calls and134.6018s.
   It establishes substantial remaining domain capability; it does not
   license importing those historical rows into a production run.
7. Select one unified base-domain candidate: one self-paid standard LP
   and certified hull separation before each new qualified canonical MIP,
   at most one reliable global row per vehicle. No additional weights,
   callback Optimize, anchor dispatch, internal timers, Work dispatch or
   B&B restarts. Bind actual new canonical identity before journal/Start.
8. Short native shadow/submit runs are qualification only. Complete F2
   development uses1200s and contemporaneous P/ENS/H plus one R102-J
   attribution arm. C2/N2 development and known C3 regression protection
   follow. A worthwhile frozen candidate must retain two design-isolated
   confirmation roles and two common3600–7200s groups; none are yet
   executed or claimed. Default adoption remains undecided and OFF.

Failures and precision limitations stay in the evidence and fee records.
The initial C2-native NameError was billed and retried under a fresh label.
A rejected overlapping-launch preflight started no optimizer; a conservative
fee allowance will be retained. The F5 duplicate UNKNOWN results were not
overwritten or relabeled INSIDE. Initial bit30 diagnostics are historical;
later derived dyadic precision reduces the quantization envelope while
keeping the declared member tolerance and actual resource predicate fixed.
