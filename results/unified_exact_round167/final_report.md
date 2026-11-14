# Round167: conditional stock information and one consolidated manuscript

**Retain uniform GI-TBC/B. Keep C166 and D167 default off.** The new joint
conditional representation is mathematically valid and implemented by one
offline C++ prototype. It has measurable but limited conditional LP gains
and larger actual matrices. It does not currently justify complete-method
integration/comparison, and this round runs no new complete B/P/PS/E+ or
Seed panel. The one current English paper is substantially reorganized.

## Scientific finding and actual implementation

The new object retains stock Y, movement |b-Y|, nonzero visits, g, gY,
absolute stock digits delta and their products w=g*delta in one common
mixture. C166 preserves the unconditioned physical H(D), but its disjoint
bit layer can lose conditional service information: on D=0..4,b=2,
g in [0,1/2], fixing the low digit to one leaves legal stocks {1,3} and
requires M=V=1, while the fully checked C166 witness has Y=2,M=V=0.
This does not invalidate C166 integer correctness or prove a historical
Native branch caused its X20 slowdown.

One fixed MSB-first lower/upper-tightness DAG, separated into donor,
initial and receiver pieces, has O(1+log(C+1)) final size. Both mass flow f
and G-weighted flow q conserve on the same graph. Endpoint-flow
decomposition proves its enhanced projection is exactly E(D), equal to
the full-state same-absolute-code reference R_abs. Every partial absolute
digit fixing preserves E(D(F)); all integer digits recover one legal stock,
correct service and product. The fixed-g case needs no division. Conditional
physical hulls still use at most five legal donor/initial/receiver supports,
including holed conditions, but that is not a five-point E representation.
Full-model inclusion requires the declared outside interface. No full BRP
ideality or arbitrary-Native-branch guarantee is claimed.

These proofs specialize established network, disjunctive and binary-code
tools. Behle, Balas, Huchette-Vielma and the actual bounded-code literature
retain attribution and precise reading scopes. The project increment is the
specific joint object, its conditional relation, implementation and fixed
real-frame diagnostic. The direct graph compiler uses only bounds and
tightness flags; no state enumeration constructs the graph. The standalone
driver nevertheless obtains its common physical block from a temporary
one-hot B canonical carrier before replacement. Its end-to-end preparation
and temporary storage still have linear state-count costs. Full writer time
and peak memory are not claimed logarithmic.

`src/round167_research.cpp` and `include/Round167ConditionalState.hpp` own
all new modeling, Optimize and exact oracle work. R_abs s/q are continuous,
with integer absolute delta in tiny MIP. D167 uses no independent legacy
product layer. Original physical types/rows/objective and scope/cutoff
identity remain. Complete actual-column Starts use f=1,q=g on the legal
path, including loaded return and fixed/narrow positive g, and all integer
types are restored after LP. Unsupported extension combinations are not
accepted by the isolated entry. B/C166 production writer/backend/Start/
factory sources are unchanged. Sixteen old canonical base exports match
actual R166 files byte-for-byte with zero new solver calls.

Full proof: [conditional state theory](conditional_state_theory.md).
Actual source/build/PE/DLL: [candidate manifest](candidate_manifest.json),
[frozen diagnostics](diagnostic_manifest.json) and [reproduction](reproducibility.md).
The new final diagnostic PE SHA256 is
`26fe2d74d92e0d998966f73085b3a321007e39ea674ff4e2b8655f8414515f12`.
It is not the R166 performance executable. The first solver-free preparation
source/PE and its pre-Optimize boundary repair are separately preserved.

## Fixed diagnostic result and cost

All **88 actual Optimize calls** are completed and numerically qualified:
72 canonical raw LPs, twelve local LPs and four tiny physical MIPs. All are
serial, with the frozen one-thread/Seed0/zero-gap/unlimited-node policy and
20s/5s/60s caps, respectively. The eight repair slots remain unused. The
frozen manifest precedes the first Optimize, includes every actual input,
matrix, mask, original argv/domain/cutoff/objective and source/PE identity,
and is not changed after observing objectives. Every canonical level is
nondegenerate; none is infeasible, failed, reused or unexecuted.

Across the 24 frame/condition triples, max |L_D167-L_R_abs| is
**2.220446049250313e-16**. F0 objectives agree with C166. Among the sixteen
bit-conditioned triples, three have a strict increment above 1e-7:

| Frame and condition | L_D167-L_C166 |
|---|---:|
| X20 root F2 | 0.0003584890002124863 |
| B35 root F1 | 0.0000069290393767684755 |
| B35 root F2 | 0.00002081111748741815 |

The other thirteen conditioned triples agree at the registered scale.
These are subdomain LP bounds, not original whole-domain certificates. In
all four local positions, R_abs/D167 attain one while C166 attains zero.
That includes fixed g, visits and the second holed mask, with no objective
or mask search.

D167 has more columns and rows than R_abs in every frame, despite its
asymptotic graph bound. For example C20 root R_abs/C166/D167 columns are
3344/2596/4216 and rows 6885/6682/8991. X35 root has 9639/9381/10565
columns and 23244/23541/25174 rows. All full dimensions, graph sizes,
file bytes, build and per-call Runtime/Work are in the
[complete 88-position table](positions.csv) and [full records](positions.json).
The current constants and temporary carrier limit immediate integration
motivation; small LP times do not predict complete GI-TBC speed.

The independent C++ physical oracle gives optimum .15 at stock (1,1),
with a loaded unit returned and 240s handling. Both tiny representations
obtain it. The actual S=0 fixed-inventory path obtains .3 with stock (0,0)
and three returned units; it is distinct from the unchanged controller's
independent exact-zero proof. No unchanged controller is rerun for coverage.

The [cost report](cost_report.json) separates **126.261657s recorded C++
subprocess outer fees**, nested **31.346999s Native Runtime**, and a
**2434.394s conservative diagnostic total** under the 3600s limit. The latter
includes a broad 1910.031s enclosing window through the later CSV-reader
repair, with interleaved review/build/management, plus independently recorded
offline checks: mathematics 164.182s, implementation/data 360s and a small
manuscript numerical readback allowance. These conservative fees are not
added to the shared scientific wall window again. Actual final science
window and ordinary Git/public-transfer I/O are separately closed in the
delivery receipt, below the 36000s capacity.

Two healthy-producer summary-reader errors were repaired read-only: a
canonical-only mask requested on a local row, and local prepare IDs
overwriting frozen CSV position IDs. There were no producer failures or
solver reruns. Independent review also explains why C166's B20 root/child
raw common hash includes ten degenerate singleton V=0 links; all are
verified and the eight normalized physical interfaces agree. Raw and
normalized identities are not conflated.

## Current paper and retained evidence

The same whitespace count falls from **13,505 to 9,003 words** (33.34%
reduction). The six sections now connect the operational question, shared
states, complete GI-TBC, computational evidence and certified decisions.
Detailed role trajectories, mechanism/Seed interpretation and administrative
identity material move to navigable supplement sections. New conditional
content is a compact proposition/diagnosis in the body and full A.11 proof,
not another experimental-history chapter. Bibliographic reading logs are
internal. Three existing figures, including the continuous parameter figure,
are unchanged.

The main B/P/PS panels, C35's historical reversal, every relevant n35 OPEN,
E+'s X35 lower gain and C20 paid cost, and the full six-row C166 comparison
remain. B's historical 3/6 versus C166's 2/6, lost C20 certificate and
X20's 4.35-fold cost increase remain historical evidence, not new runs.
Four two-sided resource intervals and four whole-range parameter quality
bounds use the unchanged full-precision R166 authorities. Positive n35
resource lowers still leave broad magnitude uncertainty; B35/X35 loaded
return directions differ. Archive envelopes are not the full Pareto
frontier and do not backfill old incumbents or proof clocks.

The current [assembled paper](../unified_exact_round137/manuscript.md),
[main plus appendices PDF](../unified_exact_round137/manuscript.pdf) and
[supplement PDF](../unified_exact_round137/supplement.pdf) have **53/55 pages**.
Actual automated bounds/text and contact/targeted high-resolution inspection
find no clipped content, overlaps, replacement glyphs or abnormal blank
pages. The new supplementary introduction follows its landscape table;
metadata moves are read back. The inherited sub-point table-width warnings
are not clipped/out-of-page text. `document_qa.json` and actual reviewer
readbacks bind the final sources and exports.

The [restructure map](manuscript_restructure.md) links each claim to its
table/proof/full evidence. The [author memo](author_decision_memo.md)
distinguishes EJOR's integrated methods evidence, TRE's bounded transportation
decisions and the narrow OR representation increment. HGA-TGBC's actual
problem/decoder source attribution is retained without asserting an unread
later author version is available or published.

## CSV, independent review and delivery

**主表无新增运行数据：新增 0 条。** The bounded search did not find the exact
112-row, 28-column, UTF8-BOM master with expected SHA
b728f85512741779a8b066ae9c974ec60892360c3fe15fbf7b946fb0ab0a4878,
nor its specified 106-row predecessor. It found the 91-row user Desktop
file and 103-row historical working copy; both remain unchanged. No
missing rows are fabricated and neither old copy replaces the authoritative
112-row identity. [Reconciliation](CSV_reconciliation.json) retains every
actual location/hash and the R166 six-row unpaired increment reference.
The 88 prototype diagnostics are separate from GI-TBC/P performance records.

Three actual independent reviews pass: mathematics/model, implementation/
data and contribution/manuscript. They inspect the actual C++/LP/Start/
KKT/physical data and current manuscript/PDF, not just paired objective
agreement. The coefficient-bit-length wording, explicit D(F), run-count
labels, CSV identity and cost interpretation are corrected and read back.
[Dispositions](review/final_review_dispositions.json) retains exact findings,
including the honest temporary-carrier limitation. No general OR breakthrough,
complete acceleration or Native causal attribution is inferred.

The English Open Draft stacks on verified R166 while main lacks its
dependencies. Normal commit/push, actual PR head/base/Open/Draft readback,
new-only source/raw carriers and one public byte recovery are recorded in
the subsequent delivery receipt. Commercial DLLs, credentials, licenses,
private antecedents and historical carrier collections are excluded.
Protected original/dirty trees remain read only and cleanup deletes nothing.

This answers the prescribed conditional-information question and completes
the manuscript consolidation. The structural result is retained; full
integration requires acceptable implementation costs and separately frozen,
independently paid complete-method evidence. No further round or complete
run is started by this decision.
