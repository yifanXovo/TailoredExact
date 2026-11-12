# Independent research-contribution and manuscript review

Reviewer: actual separately spawned agent `/root/contribution_review`.
Review completed: 2026-11-12 20:24:42 UTC (13 November 2026, Asia/Shanghai).
This is an independent agent review, not a human peer review or licensed
performance replication. No subagent, solver, Optimize, production build or
external message was used. Only this report was written.

The reviewed initial current snapshot has paper-body SHA256
`1576ee8e717c4459d0b665ba4961e4d384f5cd28337acb127c4e07d6e1246ead`,
manuscript-PDF SHA256
`36e42223ab2ee6e45e2ff9d612dd7dfcd38ef438c331ed2a901ccaf03adb1fd0`,
and bibliography SHA256
`5587b21ed4823f63124f0d6707f082fba7943bd722cc53b7837414eebe308b55`.
Later corrections must be identified separately, rather than treating this
review as automatically covering changed bytes.

## Findings requiring bounded corrections

1. **P2: Köppe source locations mix versions.** At the reviewed
   `literature_review.md:10` and `references.bib:128`, the newly checked
   arXiv v1 is described as §2, Definitions 3–4 and Theorem 8. Direct reading
   of [arXiv math/0603311v1](https://arxiv.org/pdf/math/0603311) shows
   Definition 3 at printed p.5 (both linking and aggregated polyhedra),
   Example 4, and Structure Theorem 5 at printed pp.7–9. Theorem 8 is the
   polynomial separation result in §3, printed p.14. Correct the new arXiv
   locations; retain any older postprint numbering only under its own
   version. The main §1.1 generic attribution is sound, so this correction
   changes source precision, not the stated contribution or results.

2. **P2: the equivalent B20 endpoints receive an uninformative numerical
   scale in the new figure.** Actual initial manuscript PDF p.18, top-centre
   panel of `three_seed_endpoints.png`, uses an axis offset around .42323218
   and a 1e-10 range. It magnifies tiny residual differences that are
   equivalent under the declared 1e-7 scale. Use a sensible minimum y-range
   and disable the offset, or explicitly collapse only the displayed
   equivalent values. Keep the exact analysis CSV unchanged. This improves
   scientific readability and does not alter a result.

3. **P3: Table 1's study map omits a named initial cohort row.** At initial
   `paper_body.md:257–267`, the later cohort row lists 24 added B/P arms plus
   12 historical B/P observations, but the initial six-input B/E+/P study's
   18 observations (including six E+) have no separate row. §5.5 states
   the denominator correctly. Add the initial cohort row for a complete
   study map without counting those twelve historical B/P observations
   twice. This is a presentation gap, not a conflicting performance claim.

The parent was notified of the first two findings promptly and accepted
them. This report records them before their correction; final disposition
belongs in the integration review.

## Contribution assessment

The manuscript is a substantive exact-method paper. Its current main text
defines the physical model and objective, presents linked stock products,
service and visit information, gives an explicit complete controller, reports
complete-method/resource/weight/cohort results, and interprets mechanism and
structural evidence. The full model and algorithm appendices are assembled
with it. It is not another submission-readiness report. Actual PDF p.7 has a
readable main algorithm with inputs, outputs, region selection, targets,
splits, continuation, bound qualification and finalization; it is not an
empty instruction to follow unspecified rules.

The most defensible value is the problem-specific integration and the
checked distinction between inventory representation, valid lower-bound
information and physical/paid complete-method benefit. Integer service
follows from the stated unique one-way integer-stock premises. Shared stock
states then link movement and visits to objective mixtures. The integrated
method has finite certification and endpoint advantages over the specified
compact controls. The account correctly avoids inferring the value of each
component from the value of the entire package.

I directly checked the relevant primary passages of
[Gupte et al.'s formal §2.1](https://www.pure.ed.ac.uk/ws/files/137476899/110836183.pdf)
and Köppe's arXiv §2. The current §1.1 identifies product expansion and value
disjunction as established tools. The single-block McCormick projection in
§3.1 is retained; no route-hull or new general product theory is claimed.
The service/visit linkage is the precise additional connection being
evaluated, not a relabelled priority claim. McCormick/Jensen background is
treated as standard. The HGA-TGBC operational model and decoder retain direct
available-draft attribution, without calling the May file the latest version.

The current 2026 comparison is appropriately bounded. The
[official Caggiani record](https://research.unipd.it/handle/11577/3596099)
supports availability/state-of-charge and zonal electric-micromobility equity.
Qiao's available publisher abstract/highlights support task-duration fairness
and coordinated echelons. Neither accessible abstract is used to establish
equivalence, strict model separation, dominance or firstness. I did not read
the unavailable complete formulations or repeat the failed Caggiani download.
Older BRP model comparisons rely on the inherited version-specific access
notes; this is not an independent exhaustive priority search.

## Adverse evidence and current scientific limits

Main §§5.1–5.5 and 6.2 preserve the important opposing evidence: paid-start
reversals; all n35 cohort outcomes OPEN; C35's changed within-Seed primal
ranking alongside the better historical P fleet than every B incumbent;
unreached X35 absolute targets in the added Seeds; root-only's slightly
higher final L on hard roles; and all three K15 deletion-time directions
reversing at Seed1. These are not hidden by a combined gap or a pooled
success denominator. E+ is separate, has its one final-proof gain and paid
cost, and inherits no B/P Seed-robustness claim.

The important OR-level gap is specific. The article has not established a
distinct general algorithmic advantage of the outer interval controller over
the same strengthened root formulation; the tested controls give no
substantive full-over-root certificate-time gain. The stock-service links
have valid and interpretable effects, but the present small root increments
and mixed complete costs also do not establish a broad characterization or
general performance consequence of that cross-module information. Correct
coverage and standard reformulation tools alone do not fill that gap. This
does not imply that the integrated method has no research value, nor does
it create a requirement to win every input or invent another theorem.

## Stage judgment

Retaining frozen B as the finite main method is reasonable; proof-priority
readers may rationally value the separately labelled E+. The current稿 has
enough mathematical and computational substance for a serious author/coauthor
or internal peer discussion after the bounded corrections and final visual
QA. It is not evidence of journal acceptance or a newly demonstrated speed
improvement in R165.

Recommend reviewing this completed稿 first. If that review identifies a real
architecture choice, the sole useful follow-up candidate is whether the
outer controller earns retention over the same complete, strengthened
root-only continuation under a predeclared full-cost/endpoints criterion.
Retention would need a meaningful and reproducible certification or
two-sided endpoint benefit that offsets added work; parity/adverse results
would support simplification and narrower claims. This is an architecture
decision, not a search for a convenient outer-controller win, and no such
study is executed or automatically authorized here. The already studied
C35 fixed-route, route-feedback, larger-price and routine extra-Seed objects
are not proposed again.

Conclusion: no conclusion-changing originality or manuscript omission was
found within this review's scope. The two precise source/figure fixes and
the study-map clarification are local, reviewable corrections; genuine
scientific limits should remain explicit in the author decision memo.

## Targeted correction closure

At the parent's request, a bounded readback completed at
2026-11-12 20:45:04 UTC (13 November, Asia/Shanghai). This did not repeat the
whole review, historical studies or any solver work.

- Finding 1 is **closed**. The current literature table and bibliography now
  identify arXiv v1 Definition 3 and Structure Theorem 5, and give printed
  p.5 and pp.7–9. The earlier postprint remains a separate historical read.
- Finding 2 is **closed**. I inspected actual current manuscript PDF p.18
  again. Its B20 panel now spans .400–.440 with ordinary objective labels,
  shows the equivalent endpoints together, and has no 1e-10 offset axis.
  The plotting code specifies a .04 minimum span and disables the offset.
- Finding 3 is **closed**. Current Table 1 includes a separate six-input,
  18-observation Seed0 B/E+/P row. The following row identifies the added
  B/P observations and historical B/P views rather than new independent
  inputs; the main denominator explanation remains explicit.
- I read the final author decision memo. Its integrated-method assessment,
  finite B/E+ choice, specific outer-versus-root and cross-module-value
  gaps, review-current稿-first recommendation, and sole conditional
  architecture-simplification question are consistent with this review.
  The memo preserves C35's absolute primal deficit and the X35 target
  censoring; it does not turn administrative unknowns into technical blockers.

Actual identities at this targeted closure:

| Artifact | SHA256 |
|---|---|
| Current paper body | `eaed6620eafb6e85619480e556562a9dfd58447dec0bc0224c884500a54e1dbf` |
| Current bibliography | `44c246fc403db4667029a6d44ff521ab23a28739dc70287c564d41fa26094937` |
| Three-Seed figure | `d13d9b41d03fd291ba9e2b307115ab7a126456ac15513faafab3f661291f4fa6` |
| Targeted literature review | `c7dde2fe557afb017a1e38ddd55119985d85d1dab0b33e867e3271e6409e6c67` |
| Author decision memo | `94e55555aeb7b432708e345448ab3f7dd1e65139e3195f7432f70e56096915ce` |
| Main PDF, 52 pages | `3b24cdd828e666cb491dcb7a421889fdc4623eb05a2fe6b7a9087d290957dc71` |
| Supplement PDF, 39 pages, identity/page-count read only | `5bebe69ae5d7b090ebe4dc0de8114e276ad5d1a9a1e72c234575cfde89cebbeb` |

Targeted closure status: **PASS**. No unresolved corrective finding remains
from this reviewer. This is not a new whole-document visual acceptance claim;
the final build, data and PDF QA receipts retain their own scopes.
