# Finite historical impact of the Seed and source-qualification defects

This read-only investigation preserves R132 bytes and the original formal policy. It uses aggregate observation, arm, classification and source-loss tables and the needed X-15-B D15/D16 call/bound events, model hashes and receipts, plus C03's optimize ledger and native terminal log. It does not replay all 84 raw arms, read large full reconstructed files or rerun the checker. Native Optimize, compilation and archive extraction are zero.

## Confirmed affected fields

The frozen `evidenceParameterReadback` requires `seed==0` as one conjunct, even when the registered actual configuration requests Seed1. The four X-15-B controls isolate the defect: within each method the actual model bytes and scope/cover are exactly the same at both Seeds, and the nine-setting readback differs only in Seed.

| Method | Actual model SHA256 | Seed0 journal | Seed1 journal | Seed1 reason |
| --- | --- | --- | --- | --- |
| P | `53c5d24f277e81f80b1f73f0b3883fe51a39fb403eef89eb457f1c03281b37ea` | native_preconditions=1, global_available=1 | native_preconditions=0, global_available=0, global_bound null | `full_native_preconditions_unavailable` |
| S2 | `fa59ff6eae511f2b5f154c7cc7e6b29ff8da21ebe05b8b6c7ecffe892bbe3087` | native_preconditions=1, global_available=1 | native_preconditions=0, global_available=0, global_bound null | `native_scope_not_matching_frozen_live_leaf` |

P is full-original call1. S2 is terminal call4 on L0 with physical G interval [0,0.08166666666666667] and the same cutoff; both Seeds have identical cover fields. The three S2 LP calls have native_preconditions=0 at both Seeds because LP relaxation is a separate failed integer prerequisite. Those LP flags are not attributed solely to Seed.

The affected values are the producer journal's parameter prerequisite and global-attribution availability/reason. Raw finite native observations remain. A null passive-journal global bound does not alone disqualify every local bound, prove a physical-domain mismatch or establish online scheduler use. S2's reason conflates prerequisite failure with a real scope mismatch.

## Independent qualification retained

Both Seed1 arms already have `computed_seed_scope.json` receipts validating actual requested/read-back Seed, returned model/types/scope and linked call log. They record computed_native_prerequisites=true, successful_return=true, raw_flags_preserved=true and raw_global_available_and_global_bound_unchanged=true. Their qualification_role explicitly identifies an offline returned original-model scope proof, with no callback/global flag promotion. This report checks referenced observation/completion/result hashes, model bytes, producer receipts and verification-closeout links. It does not claim a new full matrix proof or alter raw event flags.

| X-15-B arm | Producer receipt SHA256 | Computed Seed scope SHA256 | Verification closeout SHA256 |
| --- | --- | --- | --- |
| P / Seed0 | `4b3bc3948838b0424873e56147cafba0b9a0c91eb483d76f5856557542d26eb1` | not needed at Seed0 | `2c36d0f7c2567929fc9be602c393d7374efe0e40fcba37a04a1623eceba7dcca` |
| S2 / Seed0 | `4c17447426d3dc14cd2938f1879374abcabb3d15834fce806cf533abf37ad069` | not needed at Seed0 | `60503b92c48bf47e56f925f82acd9ec03958e80a6740906a5af74cf114902d46` |
| P / Seed1 | `8dddcd998aa687b7f5c6954116c98439f5e230409b08587f5e75cb8e338dfc98` | `1ef37e72e59ebe30375d840fcda95a1a98bf052a407df9c6c7c9af23564bda94` | `17c8f747e366a3ac44d56d465c5f355991eeac6dc5c757470b4ea112064efff8` |
| S2 / Seed1 | `4bdc977cc7def0f02fcf16490ea217aa92342170859ad9ac666ad529a6845fa2` | `8a449a1875bc34c430a72fa0817605d5e8eed24cad17d92ab5cdb248569153f7` | `db375d472354ca2f8d3828e930f37c302e8579923b6e0a8c7f26204746d0c50d` |

The independent reader uses `round122_evidence.qualify_seed` and the actual-Seed projection from `round109_seed_scope`; the paid PS path has an actual-Seed adapter in `round130_evidence`. These check actual configuration and returned-call scope while preserving the on-disk callback flags. Their predicates serve a different purpose from the passive producer flags. The four directly checked X-15-B endpoints therefore remain eligible historical certificates. This finding neither repairs producer consumers nor proves native search numerically reliable.

## Population and other known numerical outcomes

The original population remains 84 produced arms (60 D and 24 C), 64 typed comparisons and 83 performance-eligible observations. Original-policy D certificates remain S2 17/24, P 9/24 and PS 4/12. The additional S2 own-zero proof is D24 X-35-U / Seed1: its already-refuted call4 stays REJECTED, formal T_cert remains null and its planned comparison stays UNEVALUABLE. Aggregate source_reduced, rejected_calls and eligibility fields identify only this known arm. No additional source contradiction or reason to revoke another historical certificate was found in this bounded check. Absence from the summary is not a new proof that all other native sources are valid.

C03 SC-B20-S / Seed0 / GEOM has a different numerical outcome. Its saved MIP ledger says OPTIMAL; the linked terminal log ends with native objective=bound approximately 0.3153886972242. Independent physical U=0.31538912105343897 gives signed gap 4.2382920323325024e-7. At actual production 707.4430182999931 seconds, it is qualified-open with null certificate time under the unchanged 1e-7 rule. It is not a 1200-second timeout or a D24-style positive lower bound refuted by a legal zero.

C03 producer receipt SHA256: `6d8eaa3bb560cc4a5bd3f859305ef69f1ba59bc655e4cd719099639636bad570`. Native terminal log SHA256: `6c2c83c741b393b24f917ed3ba61412b4ad3983ba4b6d551ac8799aef40aa814`.

K-35-B is already unknown_optimum_class with an empty positive-floor evidence list in the original classification file. It remains UNKNOWN. K-35-U's separate historical positive lower bounds do not change this class, and a positive current U does not prove a positive optimum.

## Three-way impact scope

- **Affected:** directly demonstrated Seed1 prerequisite/global-attribution flags and the conflated S2 reason; the known D24 rejected source; accurate native-versus-physical interpretation of C03.
- **Unaffected by this specific defect or inference:** Seed0 controls, the four independently qualified X-15-B endpoints, the frozen population/denominators and original-policy counts, and K-35-B's UNKNOWN classification. This is not a blanket reliability claim.
- **Pending:** other individual Seed1 producer journal and consumer effects have not been freshly replayed here. The summary registers 42 Seed1 native arms (30 D, 12 C); after the two directly checked Seed1 X-15-B arms, 40 remain listed explicitly in the JSON, including the separately known D24. Shared-source exposure is inferred from the predicate, while actual per-call effects and independent offline eligibility are kept distinct. Candidate online source handling belongs to B/C/D, not this historical annotation.

The companion JSON hash-binds 71 decisive files, the fixed source commit and exact call/bound identities. All old evidence remains unchanged. No later witness, other-arm solution or revised qualification is fed to an independent production arm. The recorded 0.3232658999040723-second figure meters the final checking process only, not all static reading or human time.

The selected raw dependencies are publicly held as archive members rather than individual loose files. Four original carriers (D15/D16/D24/C03) were hash-checked, and 62 selected members (1,630,344 bytes) were streamed and matched to local raw, without extraction. The JSON records each exact carrier SHA, member path and member SHA. This one bounded carrier check took 0.225517 seconds; no full campaign reconstruction was read or rerun.

## Additional inclusive-cutoff marker defect and bounded historical screen

The inherited shared interval factory and compact fallback could emit the artificial row `0<=-1` when the analytic no-improver floor reached `c-1e-9`. The shared branch also requires an active interval/cutoff, lambda>1e-12 and positive incumbent. The row is not valid on the required inclusive physical domain F<=c; a legal F=c boundary can be excluded. The replacement removes both emitters and keeps the legal penalty lower bound. This is a genuine candidate model-row change and belongs in the version identity and required adopted-version D3 bridge.

It is a distinct defect from the two numerical anomalies. D24 has a complete exact feasible extension in its actual matrix (transferred through the fresh same-DLL rational-model comparison), so that matrix cannot contain an inconsistent constant row. C03 GEOM actually uses s2-root and its inclusive mode already omitted the marker. Ordinary full compact P/PS does not activate this interval shortcut; other parameter/journal reliability questions are separate.

A bounded screen read only the existing small optimize ledgers and model-contract indices for the 24 registered R132 production ms2 S2 arms. Their 104 actual calls have 90 OPTIMAL, 8 INTERRUPTED and 6 TIME_LIMIT statuses, with no INFEASIBLE candidate to direct a further constant-row check. No model matrix was restored or parsed. The contract indices record source model SHA/row/column/types and physical-domain fields but contain no explicit marker/constant-row flag. Thus the finding is **no intentionally empty-model INFEASIBLE observation in this screen**, not proof that every saved matrix lacks the row or that every old certificate's inclusive dependencies have been checked.

If an intentionally inconsistent model were found, its correct native INFEASIBLE return would not by itself be a commercial numerical failure. Conversely, using that source as an inclusive physical infeasibility proof would require correction. Actual row presence and certificate dependencies for unparsed historical matrices remain PENDING. This source-level finding does not justify blanket revocation of all old S2 results, and the original 17/24 policy count is not protected against a future actual counterexample. No additional revocation is supported by this bounded evidence.

This final index/ledger check read 128,015 bytes across 48 small files and took 0.255971 seconds in its outer process, with zero Optimize, model parses, archive extraction or full reconstructed reads. Fixed paths/SHA and the per-arm result are in the companion JSON.
