# Common-horizon timing and witness scope

No algorithm decisions use this post-experiment analysis. Original solver
options and whole-run deadlines remain frozen; all analysis calls optimize0.

For HGA, canonicalCandidateSerialization in src/Round60Candidates.cpp orders
vehicles, keeps the complete node sequences, and orders each route's integral
operations by station. The independent Python serialization must reproduce
the event SHA-256 and hga_retained_candidate_sha256 exactly. It then physically
checks the retained initial routes against the frozen input. An equal objective
without this full-content match is insufficient.

The HGA observer verifies and copies the candidate synchronously during
update_best, before the generation's elapsed timestamp is appended. If g is
the matched event generation, t_g its end time, t_last the final generation end,
and T_loop the process-clock phase after ga.run returns, then

    actual publication time <= T_loop - t_last + t_g.

This uses a conservative upper bound on the GA epoch and does not need a
guessed callback cost. Nonnegative external-minus-internal process wall is
charged before all trace events as an additional conservative overhead shift.
The provenance records retain the equation inputs, event identity and witness
hash. Seven completed Round69 HGA runs passed. A read-only check on the prior
Round68 D6 route also passed, including its empty vehicle, linking generation71
to a conservative12.522s publication bound. That check is historical QA, not a
new performance run or a claimed Round69 D6 result.

For P-GRB, intermediate full vectors/hashes were not retained. Its callback
incumbents remain explicitly native telemetry. Callback elapsed times start
before the optimize-launch phase; adding that phase time and the conservative
overhead shifts them later, never earlier. Synthetic solver_final rows are
excluded from intermediate checkpoints; full endpoints use completed-run
physical witnesses and the continuous objective bound. No future final native
route is assigned to a past event and no inconsistent bound is clipped away.

Before a qualified contemporaneous witness is available, UB remains absent
in this evidence table. Before exact search the mathematical nonnegative lower
bound is available. During exact search the complete-frontier trace is used;
restricted leaf bounds alone cannot stand in for a global bound.

The fixed-interval backend stores callback events in memory and returns them
after Optimize. PaperExternalGiniTree then writes their past timestamps; a live
tail before that return is incomplete, not evidence that its bound is stationary.
Source inspection also found that the printed callback process timestamp adds
callback-relative elapsed to an earlier solve-launch clock, omitting the
intervening setup. The offline extractor conservatively shifts each contiguous
native-bound group by (next actual process-clock event minus its last callback
timestamp). This upper-bounds the missing setup offset, also charging any tail
without a new bound improvement. It can therefore understate early progress,
but cannot place a bound too early. The exact adjustments are retained; no
rounded native log bounds, changed solver settings or new build are substituted.
Full-window endpoint values and paid times are unaffected.
