# Preliminary actual-data review: NB35 B versus E

Reviewer: independent nonimplementer for the adopted Round154 goal, section H.
Only the first two sealed endpoints, verification closeouts, small producer and
total receipts, frozen identities, and control summaries were read. No Native
solve, compilation, new qualification, raw-model scan or large audit read was
performed. The J arm and the remaining six arms were not complete at this
review. This record is not final nine-arm approval or adoption of E.

## Matched endpoint result

Both arms use NB35 input SHA
`80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98`,
the frozen same PE
`0d3a94183285cc2794676c717a23dc75a47c872ad48c26d2237dd8634f1a5a01`,
and cap 2400s. Their sealed closeouts qualify implementation, evidence and
performance eligibility; both endpoints record a complete own-H. Equal own-H
semantic/fleet hashes are consistent with the declared deterministic seed,
not evidence that one arm consumed the other arm's H.

| Field | B, position 1 | E, position 2 |
| --- | ---: | ---: |
| Own feasible U | 0.450291503262878 | 0.450291503262878 |
| Supported L | 0.38931060164210607 | 0.3959564087240911 |
| Absolute gap | 0.06098090162077191 | 0.05433509453878688 |
| T_produce | 2371.656277666334 | 2371.3379457800183 |
| T_verify | 2.8259734997991472 | 7.515714599983767 |
| T_total | 2374.482251166133 | 2378.853660380002 |
| Outer metered G1 | 2374.5538700998295 | 2378.9349014000036 |
| Certificate | Open; T_cert null | Open; T_cert null |

E has the same U and improves reported L by `0.0066458070819850334`,
reducing the absolute gap by the same amount. Its T_total is about 4.3714s
larger. Both metered processes have exit code zero. This single pair supports
a proof-bound improvement at the paid endpoint; it supplies neither a better
physical incumbent nor a closed certificate.

## Floor placement and retained raw information

The E ledger retains raw search L `0.3892936193183539`, which is
`1.6982323752190442e-5` below B's supported L. E's supported L is instead
the independently paid own-root floor `0.3959564087240911`. The control
summary records a qualified, live source and one complete root, original root
interval `[0, 0.5772179446388799]`, own cutoff `0.5772179446388799`, and
current root cutoff `0.4502915032628781`. Therefore the cutoff-complement
floor `min(own_cutoff, floor)` equals the stated floor and covers the current
root. The ledger reports `proof_stopped=false`; both runs remain open.

The unchanged own-floor helper costs `14.5403498s` inside E's T_produce and
2400s allowance. Its metadata records root-once execution, 4096 nodes,
price gap target `1e-4`, zero extra root LP, no offline-data use and no formal
new columns. The floor is not treated as a free historical/global floor.

The small E control audit records three actually called formal-model
identities, with `base_SHA == model_SHA` and zero floor rows for each, plus
five passing Native audits, also with zero floor rows. Its proof ledger
records `AM_uses_search_bounds=true`. Thus these actual qualified control
summaries support the intended placement distinction: E's endpoint consumes
the extra scoped floor in the proof ledger while retaining the raw search
bound and unmodified same-domain formal models. This step did not reopen the
MPS/raw call evidence; the final finite audit and already required full
verification retain that responsibility. No AM-only causal claim follows
from this pair.

## Small evidence bindings checked

The endpoint audit SHA references agree with their closeouts. I rehashed the
small closeouts, producer receipts, total receipts, frozen group identities and
E proof ledger; their stored bindings agree. Reported time tuples match the
producer/total receipts. Group identity hashes match the frozen matrix, and
each endpoint PE matches its group identity. The large `audit.json` bodies were
not read or rehashed during the active Native queue.

| Evidence | SHA256 |
| --- | --- |
| B endpoint | `474a1275fbe4720bbd9bddbd47084552cb3f90bcf1d7c8739a3b0ed628d2fa53` |
| E endpoint | `c44ef27c6235c496f9aab85ca13e9fc4c6b1008722c6b2afa07fec692b86b218` |
| B closeout | `2baaf183209461ec6111bf4fc91fcfed5e405972c58afbe0336df82f5f5635ea` |
| E closeout | `75f1557cec4641b45e4239d9bb06ff4ea339a3e6a50fad85066440993e24aa95` |
| E placement control audit | `e34ba189bf74965c1d14bd1cdc9de2b2bcbca9486c2a4e60d9df818d448d0f48` |
| E proof ledger | `c523300a4deb774689ade8a7889603226d8218ad4e20843971ef0005f9e03c03` |

Disposition: the preliminary NB35 pair has an interpretable paid proof-bound
gain with identical U. Keep E research-only/default OFF pending the remaining
registered arms, the actual zero-Optimize full audit and the final claim review.
