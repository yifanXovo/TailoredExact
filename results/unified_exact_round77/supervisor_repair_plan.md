# Correct the offline snapshot adapter; do not rerun completed solves

The frozen driver finishes P and JDS-C normally at1197.093/1197.094s, then
exits1 after JDS-C's offline closure replay raises TypeError. K1-R has not
launched. Original summary.json, per-run audit.json, driver_completion.json,
all raw witnesses, native logs and observations remain immutable.

The wrapper passes the closure's JSON snapshot as the replay function's
CLI-result argument. Snapshot operations are arrays; CLI-result operations
are dictionaries. replay_closure normalizes its initial/final snapshots but
expects that third result argument already has the CLI schema. route_hash
therefore indexes a list with a string. R76's original startup screen passes
the actual CLI result and is unaffected. No C++ algorithm/source or solver
configuration changed, and this is not a physical or bound rejection.

Admit one offline scope correction<=30s, zero Optimize. Reproduce the exact
adapter TypeError with retained data and save its traceback/cost; normalize
only the wrapper's snapshot-backed result, then repeat all original receipt,
physical, bound/coverage, endpoint, startup-path and closure checks. Also
independently check the actual submitted Start vector against the retained
native model before restoring the pending control. Any remaining failure
keeps the third launch closed. Store a separate correction document with
hash links to the unchanged raw failure and fully validated audit.

If those checks pass, execute only the originally frozen third K1-R command
under its original1200s cap, with all original observer/affinity/acceptance
rules and source/binary hashes. This is the unlaunched allocated control,
not a rerun or a new fourth arm. Freeze a small continuation driver first.
Write separate continuation process/summary/completion files; do not replace
the original stopped summary or doctor its failure. Combined analysis must
explicitly validate the correction's linkage and preserve the raw exception.
No new Optimize allocation beyond the original three arms/<=60 campaign
calls; no compilation, retest, seed change, long run or confirmation.

All elapsed native and failed offline work stays charged. The mathematical
criteria and overall research goal remain unchanged. This repair is part of
the current substantive stage, not a separate optimization achievement.
