# Independent production-writer review

Reviewer: `/root/independent_math_review`, separate from the principal implementer. Date: 2 November 2026 (Asia/Shanghai). This is a bounded source/evidence review with zero Optimize, compile, commercial Native loading or historical raw replay by the reviewer. The mathematical scope and derivations are reviewed in `preliminary_math_review.md`.

**Disposition: PASS for the joint source mathematics, complete-block projection and inspected Native audit. Full-experiment admission remains conditional on the short complete lifecycle qualification and correction of the method-identity metadata noted below.** No mathematical or cutting-row validity blocker was found.

The reviewed production construction is commit `75834484f078b6f83b34c8866f751282a442e841`, compared against verified R144 head `68041d6a69e14ca7cfbff4e3262ab17331bf792e`. The following inspected file hashes bind this review; a pending metadata-only main/reader amendment is to receive a separate readback.

| File | SHA256 |
| --- | --- |
| `include/Round145Research.hpp` | `dae453750c9a054653329d6c29c322188100843fae55d2e96cff6e11bb81d687` |
| `include/Round144Research.hpp` | `e1dd872a5f4ce6e0b71f7cd1c4025f74dca6e255e08d64463180fe9548a44fcf` |
| `src/GurobiBaseline.cpp` | `1853291bfb09c50690b3841482002716974e934adc294cdb537cff60ecbeba38` |
| `src/PaperExternalGiniTree.cpp` | `46629cc18d4665e510cc569c6b9118842a68eb2b54ce52b71ca8465ac439b952` |
| `src/main.cpp` | `205dc57fc8fb8de51e33320a2d23d14eaa66250453f1a2eb171b9b66828d5ec7` |
| `scripts/round145_qualify.py` | `415ef2b85ece91df141a2055fdbccaa4f08230a88bdb866d9c8a3c5280164d39` |
| `scripts/round145_project.cpp` | `d56ed638a3297dadeddc9abb89cee2354a3465e17a9c3e775697e6c55060ca9f` |

## Production source and coefficient validity

`round145_detail::augment` receives the existing production-capped RN block and appends exactly two NC and four TS rows without adding columns. It preserves the RN applicability and finite denominator bounds. The NC rows use both R140 count aggregates; signed selector coefficients become the corresponding signed `rn_w` coefficients and the TC2 constant becomes `-constant*rn_t` on the left. R140's downward coefficients and constant are safe because t and w are nonnegative. The checked dyadic count arithmetic, actual ratio identity, supports and physical inventory budget remain the established ones.

TS uses `sum(rn_Y_i)`, original `sum(Y_i)`, the same RN `lt/ut`, and the physical budget intersected with supported extrema. The four coefficient/sense/RHS choices match the independently derived forms. Only the RHS budget-times-slope product needs new rounding, and the implementation moves it outward by one ULP in the correct direction. Positive power-of-two scaling preserves any small nonzero term through import. The production NC arithmetic is the reused R140-down formulation; the standalone diagnostic LPs used an exact-coefficient/signed-box-compensated formulation. These are separately identified actual matrices, not claimed byte-identical sources. Their tiny numerical transport differences do not affect integer validity.

The finite RN hhat caps are correctly described in the new header as integer-valid. The invalid shortcut of reducing every hhat to its absolute-difference minimum in the presence of NC is not used to justify joint-model redundancy.

## Complete block and source isolation

The `rn` object selected by `PaperExternalGiniTree.cpp` is the augmented RN/NC/TS block when RN-JP is enabled. The very same `rn.rows` list supplies source serialization and the call to `round144_detail::project`; the source additions are therefore not truncated to the historical RN prefix. The projection evidence now explicitly records every source row. There are no stock/TC/TC2 additions in this production candidate, so no such rows are silently treated as part of formal stable BASE.

The generalized projection keeps the established sign repair, equality multipliers, complete finite new-column boxes and outward compensation. Its only algorithmic generalization is the legitimate original `Y_*` terms and a distinct `r145_PC` name. The signed/mixed exact oracle check verifies the <= row against the negated exact >= projection, including the correct maximum original-box conversion error. Zero projection remains uniformly omitted.

The initial-root guard, own-H cutoff/domain construction, once-attempted state, temporary `source_running`/RN flags, source integer-type restoration and explicit backend discard remain intact. A source failure does not install a row, point or bound as formal control. Native evidence must remain usable before narrower-domain inheritance. Reset clears the shared per-run source/projection state while retaining the selected method switch. This inspection supports the inherited mechanism; an actual short complete run is still required to demonstrate its lifecycle under the new source.

## Native auditing and inheritance

During the disposable source call, `auditRound143Native` detects RN-JP through `round145().enabled && round144().source_running`, reconstructs the augmented block and collects both `rn_*` and `r145_*` rows. It checks complete row count, coefficients, senses and RHS against the expected list, actual old ratio equalities, continuous new-column types, exact finite bounds and zero new-column objective. The six new rows cannot evade the audit by their prefix.

Formal `auditRound144Native` rejects persistent `rn_*` columns and rows, rejects `r145_NC*`/`r145_TS*`, and requires the single expected `r145_PC` with actual transported coefficients. In the zero-projection case it rejects any `r145_*` row as well. The source audit and formal audit have distinct paths, consistent with source disposal.

Embedding retains the original input hash, narrower G interval, nonincreasing cutoff and support-subset guards. A removed selector is identically zero; only its coefficient is removed. Y coefficients remain because Y stays an original variable with its station identity and supported bounds. The candidate's projected original terms are G, selectors and Y, so these guards also retain the finite-box validity scope. No repeated leaf source solve is introduced.

With RN-JP disabled, the new block-selection branch is inactive. R144 RN-P still calls the same historical RN generator and default projection arguments, with `r144_PC` and no Y allowance. The generalized audit matches that expected row name. The arithmetic library and stable BASE factory are unchanged. These are source-level compatibility findings; they do not relabel an unrun OFF equivalence test as a measured experiment.

## Qualification evidence inspected

`qualification_exact_writer.json` records compiled C++ block equality against an independent Fraction oracle on the binary four-station case, a heterogeneous holey-support case, and K35/RX20/K20 scopes. It covers exact physical extensions and finite caps for the two small cases; signed/equality/mixed-direction projection, Y retention, wrong-sign multiplier repair, zero projection and run reset are separately checked. The reviewer inspected both checker implementations and this saved output rather than rerunning them.

The two actual serialized/reimported compact LPs retain all prior BASE semantics and read back the projected coefficient/sense/RHS exactly, with no RN columns:

| Domain | Joint source objective | Compact objective | Source-minus-compact loss | Complete source rows / PC NZ |
| --- | --- | --- | --- | --- |
| K35 | 0.2345081978937098 | 0.23450819789368227 | 2.7533531010703882e-14 | 2346 / 366 |
| RX20-T1 | 0.3963391037508019 | 0.3963391037507846 | 1.7263968032921184e-14 | 714 / 49 |

Both pass the existing 1e-6 maximum quality/residual policy. K35's compact DualVio is about 4.78e-7; this is accepted numerical LP evidence, not an exact primal/dual certificate. Retention fractions of the new NC/TS increment are approximately 0.9999999999957 and 0.9999999999974. Same-root preservation applies to these matched actual sources and original objective only.

The strong K35 old carrier O has objective 0.2292221974605569, while O+joint is 0.23450819789370975, agreeing with joint alone to numerical precision. O's saved point violates NC2 and TS4 materially. The reoptimized objective increment, approximately 0.00528600043315, therefore exceeds numerical noise and is more informative than saved-point violation alone. O's reported DualVio is approximately 9.97e-7, within the inherited threshold; no global dominance is inferred from the numerical comparison of nonnested O and joint. The nested O-to-O+joint comparison supplies the relevant actual nonduplication result.

## Required identity correction and remaining gate

The inspected main sets the shared R144 lifecycle flag when RN-JP is enabled and then writes a `round144_parameters.json` declaring `RN_P:true`, alongside the distinct JP parameters. Although the actual source/row names and method launch distinguish RN-JP, this reused parameter declaration is ambiguous for raw consumers. The principal implementer accepted the finding and plans to make the Round145 parameter file the sole method identity for JP, while retaining the old R144 reader and RN-P behavior unchanged. This is a reporting/identity correction; it does not change the six source rows or projection arithmetic.

Before an expensive full run, independently inspect that amended main/reader, bind the resulting source and PE, and complete the planned short own-H/source/formal health qualification with actual complete Start, Native all-six-row readback, type restoration/discard and source/formal proof separation. No extra grid or broad audit system is requested. On passing that gate, the inspected evidence supports route B and one frozen unified RN-JP candidate; it does not yet establish full algorithm benefit or stable-method promotion.

## Identity correction and actual writer readback

The correction is now independently inspected at production source `3510d7c15bd0712ff0c57c298721ff111c60cdec`. The only further production C++ change is a guard preventing the reused R144 lifecycle path from writing old RN-P method parameters during RN-JP. The sole JP method parameter file is `round145_parameters.json`. The original R144 reader remains byte-identical to the verified R144 version. The copied Round145 reader retains its entire physical/proof/quality/lifecycle logic, substitutes the complete joint-source and Y-aware exact checks, and checks distinct JP method identity. Its internal R144 lifecycle alias remains an implementation detail; the authoritative method and Round145 control audit identify RN-JP.

The amended `src/main.cpp` SHA256 is `37fa1e516d9e47a647514f3537cbbda0eb24929e1052b805e2a7ae8ee8fa2576`; `scripts/round145_read.py` is `e873135212408b601540e94798106d72925e03175b52f256752c6a143de3c868`; unchanged `scripts/round144_read.py` is `e9c5a37b3923be3f30b7902251854675e7c87a9c8f8b712e6cfd5b306d34ed77`. The actual measured PE path is `E:/codes/ExactEBRP-work/build-cache/round145/ExactEBRP-jp.exe`, with independently read SHA256 `044bff47f944c4df09c092aafe3fbb8112a5db708a8bc8a6e26e08f8949558d6`, matching the candidate manifest. This is a new identity distinct from the preliminary build.

`qualification_native_writer.json` additionally passes the actual canonical append/embed writer, complete physical Start, original Y terms, a narrower child, G/cutoff/support scope rejection, all submitted Native row coefficients/senses/RHS/bounds/types, zero RN columns and one PC. Its K35 OFF canonical matrix equals the sealed historical stable BASE. This is a zero-Optimize writer qualification, not a timing comparison. The separate short complete own-H/source/formal health run remains pending at this addendum; no full pilot ACCEPT has yet been recorded by this reviewer.

## Short health completion and pilot admission

The subsequent sealed K20 short complete qualifier passes `necessary_verification_complete`, `implementation_qualified` and `evidence_complete`; its distinct Round145 control audit identifies RN-JP. The actual source is optimal at 0.22280893966110182, has all 1330 expected rows including the six NC/TS rows checked by the Native audit, and is restored/discarded. Its once-source preparation costs 0.7886135 seconds; its formal models contain one 387-NZ PC and zero RN columns. The exact online projection check has a nonnegative validity margin. Full outer qualification cost is 64.5663562999107 seconds, including verification, and is charged once. This short qualifier is not a full-cap performance comparison.

The independent reviewer read the frozen pilot matrix and all four identity files. Both K35 positions use cap2400, both RX20-T1 positions cap1200, each compares stable OFF with RN-JP using the identical verified PE. Seed0, one thread for each solver, H seed20260626 and serial own-H execution are explicit. Frozen input paths, physical T, original objective coefficient, fleet-capacity vector and initial-stock total match the R137 authority. The nominal pilot allocation is 7200 seconds; unused nominal time from early certificates is not a reason to expand the experiment. The recorded experimental fee total at admission is 109.35887480038218 seconds, leaving ample room under the 28800-second total ceiling for this pilot and its required verification.

**Pilot admission: ACCEPT**, limited to the four positions bound by `pilot_admission.json` and its actual matrix SHA. The prior method-identity issue is resolved. This is an engineering/scientific admission to measure full outcomes, not an adoption recommendation, outcome prediction, all-tree root-retention claim or authorization for a second complete panel. All entered hard-role windows and adverse endpoints remain part of the report.
