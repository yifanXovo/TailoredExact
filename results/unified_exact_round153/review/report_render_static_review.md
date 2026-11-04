# Report and figure interface: independent static review

Reviewer: independent nonimplementer under goal I. This review covers the
new Work/node and own-H report fields and the unexecuted figure formatter.
Only small source files, source hashes, and the sealed own-root
qualification metadata were read. No report, renderer, source import,
Native call, Optimize, compilation, replay, or numerical validation was
run. The complete confirmation panel was still in progress when this
review was requested; no final panel data or figure appearance is certified
here.

## Source binding

SHA256 values at the initial static reading:

| File | SHA256 |
| --- | --- |
| `scripts/round153_reports.py` | `11617f0034a683f04fd4cb2b9704dc7abb286f371fa42ff3de766b70cb17f029` |
| `scripts/round153_figures.py` | `ee183762811bd4b4e90067d089cd5921f5918d58415041fdc9af3099a1d23ea4` |
| `scripts/round135_read.py` | `8ba64ca6a87e55ff2ea925c70620dfc4397d3ae49c58a77fe4074eac96c6b38c` |
| `scripts/round153_read.py` | `7daf2592f228a322db88fd1f447f4e6ea3d4b8d78338f3ec0ec9686830ab49ab` |
| `scripts/compare_round112_startup.py` | `9fb8ecf86c75239dc68ebb1983d9f26bb7a99c49ff8d21fe618dbd9ea6c2dbd2` |
| `scripts/round153_pricing.py` | `8ed325356a9171a3e1aaafbc4a5c0526a764f0c35148dd6de2ea15d0d925e558` |
| `scripts/round153_partitioned.py` | `d9e7c23e64dd2a96a5bf5fda58a881345c4ab31e6f34bf2a71b3a99632b90a9e` |
| `scripts/round153_graphcut.py` | `6cb2fa990c259e15d5faf696c4626f1c86165dbef55489de3ab9a72f3ca986c4` |
| `scripts/round153_primal_pool.py` | `ef8190f6b6aa12730d4f6ab82658345fbb44d1358f45cfed363b8b59afa95da5` |
| `qualification/own_root_v2/result.json` | `408d4040b5d827573e0fb3b790b56cdf1bede74be1ff6581ad7599729854879e` |

## Required presentation corrections

1. `same_own_H_fleet_bytes` compares the inherited `H_fleet_SHA`, which is
   a digest of compact canonical JSON of `H['fleet']`. The actual
   `fleet_key()` normalizes routes/operations and permutes vehicles within
   equal-capacity classes. This does not establish original file-byte
   equality. Rename it to `same_own_H_canonical_fleet`. Similarly,
   `H_semantic_SHA` hashes `semantic_traces`, with selected timing/path/hash
   metadata omitted; `same_own_H_semantic_trace` describes that comparison
   more precisely than `same_own_H_semantic_witness`. Preserve the explicit
   statement that equal hashes do not imply shared or unpaid H execution.

2. The initial figure computes both endpoints as
   `[coupled_L - direct_U, coupled_U - direct_U]`. This is an interval for
   the strengthened LP value relative to the fixed numerical reference
   upper, not an interval for its gain over the unknown exact reference
   optimum. The axis must explicitly identify that fixed baseline, for
   example `Offset from numerical reference LP upper`, with per-role
   `baseline = direct_U` annotations. Alternatively, a true value-gain
   interval uses `[coupled_L - direct_U, coupled_U - direct_L]` and requires
   corresponding width/label changes. The present absolute endpoint
   annotations can remain if their absolute-value meaning is explicit.

These are output-semantic corrections; neither requires any experiment,
model change, frozen-source change, or rerun of a producer.

## Accepted static interfaces

The Work/node fields match their actual writers. Ordinary completed price
records contain `calls[].Work` and `calls[].nodes` (`NodeCount`), as well as
Runtime. A partitioned parent's `calls` list contains each child call once;
the report collects full-domain parent results, not the conditional child
results again. Overlay reuse has an empty new-call list. Graph pricing has
an empty MIP-price call list and a separate `candidate_LP_calls` list whose
writer supplies Work/Runtime. The report separates these quantities and
adds only their call counts in `Native_calls_total`. This preserves the
distinction between no Native MIP pricing and nonzero Native candidate LP
selection.

The sets of full-price paths prevent the same collected path from being
listed twice. These new Work/node fields describe the completed calls in
those price records; they are not a comprehensive census of every RMP,
support LP, qualification, or interrupted pending call. The separate phase
directory artifact counters retain their already reviewed restricted
scope. A call artifact without a saved return is neither a completed
price certificate nor evidence of a currently live process.

No new Work/Runtime/node quantity is added to the outer fee ledger.
`costs()` continues to use each metered receipt once and explicitly
excludes nested H/LP/MIP Runtime and Work from additive charges. Helper
process seconds are already inside `T_produce`; the complete-arm table
states this instead of adding them again. The separate Native/primal
sweep statistics are diagnostic quantities, not another wall-clock bill.

The frozen panel uses own-H arms. The inherited reader writes
`H_complete`, `H_semantic_SHA`, and `H_fleet_SHA` together after H
reconstruction, and the sealed `own_root_v2` record contains these exact
keys. Thus the direct field access in the new pair comparison matches
this panel's schema. `both_own_H` remains distinct from equality of the
two H hashes. This is static schema confirmation, not a new audit of any
production arm or proof that its H traces will in fact match.

The complete-arm U is read from the independently sealed physical
endpoint; the research `coupled_U` remains a numerical primal upper on
the strengthened LP value. `science()` records that it is not physical,
and the figure legend/footnote explicitly calls its upper endpoints
numerical LP uppers, not routing incumbents. Outward eight-decimal labels
use `Decimal.from_float` with floor for the lower and ceiling for the
upper. This does not promote the inherited numerical primal policy to a
rational certificate. The displayed approximate width is a format of the
saved LP interval, not a new optimization result.

The trace and target logic retains the earlier accepted distinction:
intermediate rows are `recorded_controller_only`, shifted producer times
are descriptive, and `qualified_endpoint_producer_time` is available only
at the sealed endpoint's `T_produce` when that endpoint meets the target.
`T_cert` is separately inherited and remains null for open certificates.
Nothing in the new figure formatter uses a trajectory time as a
certificate time. The common targets remain explicitly post hoc.

No source-level runtime failure was found in these additions for the
specified three-role scientific table and frozen own-H panel schemas.
Actual execution, all eight endpoint/receipt qualifications, the final
finite audit, and visual inspection of SVG/PNG remain outstanding gates.
The figure's study-complete and closed-fee checks are preconditions, not
substitutes for those final evidence checks.

## Static gate

Initial disposition: `ACCEPT_STATIC_ACCOUNTING_AND_SCHEMA_WITH_TWO_OUTPUT_CORRECTIONS`.
The mathematical/reporting distinctions above are acceptable within the
stated scope. Final figure/own-H wording acceptance is conditional on the
two corrections above; this review does not claim that the study, final
processing, or rendered deliverables are complete.

## Correction readback and closed static gate

The changed source bytes and the matching reproducibility paragraph were
subsequently read, without executing either program:

| File | Corrected SHA256 |
| --- | --- |
| `scripts/round153_reports.py` | `340111b6e1af9f638eecb8fe1e33a029317bb732195f55c108c4410e39888e99` |
| `scripts/round153_figures.py` | `5fc7c5730decdaf46c20fda9be8300109d84cfc6054def0ec54bb9f64550aee3` |
| `reproducibility.md` | `efc8fa9ad1bece0d6465fefb89b7c8b683974413db40afa577487c3b5a2b1e1e` |

The own-H fields are now `same_own_H_semantic_trace` and
`same_own_H_canonical_fleet`. The figure axis now reads `LP value minus
the domain's numerical reference upper`. Its creation record explicitly
identifies fixed-reference offsets, disclaims complete value-gain
intervals, and saves each role's `direct_U` baseline. The reproducibility
text explains that the printed intervals are absolute coupled LP values,
and that matching normalized H hashes do not imply raw-byte equality or
shared/unpaid execution. These changes close both presentation findings.

Final static disposition: `ACCEPT_STATIC_REPORT_AND_FIGURE_INTERFACE` at
the corrected hashes above. This acceptance is limited to source/schema,
accounting separation, interval identities, and descriptive time labels.
It does not assert that final audit or rendering has run, that the final
eight-arm values have been independently reviewed, or that rendered
labels are visually unclipped. Those execution and visual checks remain
with the authorized serial finalization workflow.

## Later complete-panel source-field correction

The actual eight-arm component readback subsequently found that every
complete endpoint's source_commit equals the measured candidate commit,
whereas the earlier own_root_v2 sample used the legacy delivery base.
The corresponding original report assertion would fail on the real panel.
That assumption is superseded by [complete_panel_review.md](complete_panel_review.md),
which records the corrected measured-commit assertion, source SHA and
unchanged sealed data. This static acceptance never substituted for that
actual-data check.
