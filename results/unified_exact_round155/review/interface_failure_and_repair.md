# Actual initial interface failure and bounded repair

The serial dispatcher first waited for NB35 B's successful outer receipt and
qualified complete verification. Its first new child, `interfaces_v1`, then
exited 1 after 0.667145499959588 outer seconds. The original stderr, source-byte
snapshot and partial base model are retained. No matched loop had started.

The failure occurred in `semantic_hash` while serializing legitimate infinite
variable bounds with JSON's non-finite-value rejection enabled. It preceded
the first Native Optimize; the oracle construction and model readback had
already occurred and remain charged. This was evidence encoding, not a failed
mathematical inequality or a rejected Native bound.

The repair gives positive/negative infinite bounds explicit canonical hash
tokens, rejects NaN, and normalizes signed zero, whose sign an MPS round-trip
can erase without changing the model. No finite replacement bound, row,
objective, stopping rule, tolerance or price conversion changed. The stored
base and delta identify the encoding, and reconstruction applies the same
encoding to the actual read-back matrix.

`interfaces_v2` passed in 0.528896699892357 outer seconds. It includes four
actual inherited pricing calls (both first and bounded, beta=0 and positive),
complete incremental-matrix reconstruction, independent finite enumeration,
old/new exact C_Q comparison, strict negative-column feedback, duplicate
handling, later weight/marginal checks and a support valid over the complete
micro domain. First calls returned Status11 under the inherited goal-stop
contract; bounded calls returned Status2. Reconstruction made zero Optimize
calls. `loop_admission_v2` bound the accepted loop/oracle source hashes and the
actual v2 result. Existing R154 oracle qualifications remain inherited.

The old dispatcher is terminal `FAILED_STOPPED`, not resumed or silently
rewritten. A new frozen dispatcher starts only the four original-pool screens
after checking the current admission. This review uses independent arithmetic
and matrix reconstruction; it is not labelled a nonimplementer-agent review.

A separate lightweight status query tried to index `raw_search_L` on a B
endpoint, where the inherited schema omits that E-specific field. The query
failed with KeyError and was corrected to use B's ordinary L. The report
reader already used this fallback, subsequently passed, and neither evidence
nor endpoint was altered. This query was not a solver or a fee-bearing retry.

The later optional fixed-level checker had a separate actual failure:
level_interfaces_v1 (0.5594974001869559s) compared the Gurobi1e100 infinity
sentinel to IEEE infinite bounds on MPS readback. Two selector calls had run;
this was not a pre-Optimize failure. The checker now canonicalizes infinite
bound representations; no selector formulation or finite coefficient changed.
level_interfaces_v2 passed in0.4143294000532478s. Its actual matrices, finite
enumeration, original-Q residual, persistent column feedback and complete
primal exits are detailed in review/level_adjustment.md. The zero-iteration
call really returned Status7/SolCount0 and was rejected. The old failure is
preserved, and neither a nonoptimal feasible result nor a large-domain gain
is inferred from this micro check.
