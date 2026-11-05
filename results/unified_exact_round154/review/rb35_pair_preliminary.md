# Preliminary actual-data review: RB35 B/E

Reviewer: independent nonimplementer under the adopted Round154 goal, section H.
Only small sealed endpoints, closeouts, control summaries, frozen identities
and producer/total/outer receipts were read. No Optimize, compilation, new
qualification, or large raw/audit/MPS I/O was performed. Seven registered
arms are complete; the NC20 pair and final finite audit remain outstanding.

## Identity and paid endpoint

This pair is `R-B35-S-T1`, with lambda `0.055125275219827186` and resource
time `T=4800`. These values match the frozen launches and corresponding
identity launches; the endpoints independently retain `T_seconds=4800`.
The process cap is separately 2400s. Both have input SHA
`64f9a5dfdfb09fcfbe705c1edfa16e94ea8bbf30281c5d25bb919c63c503a71a`,
the same frozen PE
`0d3a94183285cc2794676c717a23dc75a47c872ad48c26d2237dd8634f1a5a01`,
DLL/source/Seed0 and complete own-H. The small sealed closeouts qualify both
implementations, evidence and performance eligibility.

| Field | B, position 6 | E, position 7 | E minus B |
| --- | ---: | ---: | ---: |
| Own feasible U | 0.59151763477047 | 0.59151763477047 | 0 |
| Supported L | 0.45590389125187164 | 0.45590389125187164 | 0 |
| Absolute gap | 0.1356137435185984 | 0.1356137435185984 | 0 |
| T_produce | 2377.024685886223 | 2372.0503406876232 | -4.974345198599622 |
| T_verify | 2.8164852000772953 | 7.482151299947873 | 4.6656660998705775 |
| T_total | 2379.8411710863 | 2379.532491987571 | -0.3086790987290442 |
| Outer metered G1 | 2379.9143642000854 | 2379.6230840999633 | -0.2912801 |
| Certificate / T_cert | Open / null | Open / null | No closure gain |

The endpoints have identical U/L/gap, and neither supplies a final
certificate. The small net time difference does not establish a proof-speed
advantage; paid producer and verification components differ in opposite
directions. Both outer receipts have exit code zero.

## Terminal floor effect

E's own-root helper costs `9.8399299s` inside T_produce and the original
2400s cap. Its qualified scoped floor is `0.14243319962421927`, with root
interval/own cutoff `[0, 0.6351732034025019]`, root-once operation, node
limit 4096 and price target `1e-4`. It records no offline-data use, formal
new columns or extra root LP.

The final proof ledger has
`raw_search_L = proof_L = 0.45590389125187164`. The floor lies
`0.3134706916276524` below the raw bound, so it is inactive in the terminal
maximum and adds no endpoint lower. This does not assert it was never active
earlier. Source qualification, complete root and source-live flags are true;
`proof_stopped=false`, `native_floor_rows=0` and
`AM_uses_search_bounds=true` are retained.

The small E control summary records three actually called formal-model
identities, each with `base_SHA == model_SHA` and zero floor rows, plus five
passing Native floor audits. Original columns, bounds and objective remain
preserved. Thus this actual pair is a paid terminal null outcome for E's
additional proof source, not evidence of a hidden formal-model strengthening.

## Small binding checks

Frozen group identity hashes match the matrix and endpoint PE; small closeout,
producer and total receipt links agree, including the endpoint time tuples.
Endpoint audit SHA references match their closeouts. Large audit bodies and
actual MPSs were not reopened during the active queue and remain subject to
the final finite audit and existing full per-arm verification.

| Evidence | B SHA256 | E SHA256 |
| --- | --- | --- |
| Endpoint | `c500cc6ace561ac9df47e4b1c7ec857e3612f0ec5d543b1ef25184faa7814e85` | `d16d5e7a6f22c3f60b35b4d65c4055339949945ad16ac62278d5e616710d7acc` |
| R153 control summary | `18caf406b5a9c3280c22bd977386ab3f671a2a9bc6795241ec325776548afd17` | `2e2b199826e5c76b7a61839865f5cf55940ffd09482176eab5fe2f2aadde5f4f` |
| Closeout | `c1c59acb02a5ae5c5f2559f33d4b7d0265d357cde3456bdbc27c3ebcc90540ef` | `aa01ab5e8a4c5bf49f0a5e3dfeef291778ea2c8ed503f0d63fe0de02d2cce6eb` |
| Group identity | `46c3ad308dbc059e475f91c4ef0217cc1ad81d2b5d0fdfc3fa3c7190b4170fb9` | `cd054278f85dada19b921da9b494558101bfcf52d19dba08799da0d2102468c8` |

Disposition: retain the exact finite null endpoint result. Do not alter the
remaining registered NC20 arms or adopt E from this pair. Final panel and
scientific approval remain held.
