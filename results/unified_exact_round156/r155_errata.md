# Two bounded R155 reporting corrections

The fixed R155 science commit 1a73c0fad8fd7298e04920efc482072d191dfb97
remains immutable. Its mathematical_analysis.md contains a preliminary
sentence saying the level selector had not been executed. The actual R155
study did execute the fixed-level adjustment, followed by substantive
feedback; zero levels resolved. The final K35/NC20 intervals are retained.
That sentence is superseded here by the executed-treatment description;
the failed or unresolved level calls are not retroactively successful.

R155 observations/effective_available_seconds are relative to the actual
process_start_marker. The complete cutoff uses producer.t0_unix. Therefore
the corrected elapsed time is the saved observation time plus exactly
marker.unix_seconds - producer.t0_unix. Child birth and other startup fields
are not substitutes. round156_errata.py reconstructs the chronological
last-available state, including floor availability and observation batches,
and writes new R156 correction tables without modifying the old evidence.
The executed reader confirms exactly one changed bound among all18 points:
RX35-B at4800 seconds changes from .2141444605048453 to
.21414084957658006; U is unchanged. All time labels, floor-availability
times and batch observations use the same producer origin. RX20-E's raw
crossing is observed in a batch at4.255399397108704 seconds; it is not an
exact Native crossing time. Endpoint U/L, T_cert and fees are unchanged.
See reports/r155_common_checkpoints.json and review/r155_clock_correction.json.
Checkpoints remain observations of long runs, not independent short-cutoff
trials. No performance run was repeated for these corrections.
