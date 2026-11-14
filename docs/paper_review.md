# Current author/colleague review packet

Read the [current main PDF with complete Appendix A/B](../results/unified_exact_round137/manuscript.pdf),
[main component](../results/unified_exact_round137/paper_body.md),
[complete mathematical/algorithmic appendices](../results/unified_exact_round137/model_and_algorithm_appendices.md),
[mathematical companion](../results/unified_exact_round137/mathematical_analysis.md),
[supplement PDF](../results/unified_exact_round137/supplement.pdf) and
[bibliography](../results/unified_exact_round137/references.bib).
There is one maintained paper directory. Round166 holds research evidence,
[contribution positioning](../results/unified_exact_round166/contribution_positioning.md)
and the [internal author memo](../results/unified_exact_round166/author_decision_memo.md).

The new question is whether legal affine-piece support can compress the
joint inventory/movement/visit/product graph while preserving integer
physical points and common raw LP information. The paper gives the
constructive proof and its exact interface boundary. C166 implements that
change with a separate absolute-stock binary-product layer. Eight scoped
LP pairs agree to3.33e-16; all twelve fresh paired complete arms qualify.
B has3/6 certificates, C1662/6. Two n35 primal gains coexist with weaker
proof endpoints; X35 worsens on both sides and X20 costs substantially more.
Uniform B stays main. This is a finite same-build representation study on
exposed inputs, not new B/P or Seed evidence.

The revised decision analysis uses every complete fleet from all four
specified weight families and all four resource pairs. It distinguishes
feasible archive envelopes from an optimal frontier, and bounds quality
throughout continuous intervals. It also reports both sides of route-time
value, including broad n35 magnitude uncertainty. The private May30
antecedent's model/decoder attribution is retained; author/publication facts
remain internal rather than delaying the technical result.

The prior breadth/resource denominators, three-Seed six-input cohort,
C35 reversal and historical P witness, open n35/fixed-target outcomes,
E+'s proof gain and cost, and unresolved independent value of external
control all remain visible. No per-input portfolio or extra experiment is
used to improve the presentation.

Final independent mathematics, implementation/data, and research/manuscript
findings and their actual dispositions are in
[the review closeout](../results/unified_exact_round166/review/final_review_dispositions.json).
The [full report](../results/unified_exact_round166/final_report.md) links
new-only recovery, source/build/QA and CSV reconciliation.

Build the sole current components with:

```powershell
python -B scripts/round166_documents.py assemble
python -B scripts/round166_documents.py pdf
python -B scripts/round166_documents.py qa
```

The [build record](../results/unified_exact_round166/document_build.json)
and [page QA](../results/unified_exact_round166/document_qa.json) bind the
actual exports. The historical R137 generator remains excluded. Future
research navigation is not an executed query or an automatically started
Round167.
