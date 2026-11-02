# Round148: shared-S low-deviation affine rows (research only)

Statewise GD independently minimizes over conditional denominator intervals.
The new affine family retains the same total S as a first moment in each
station's mixture. It is valid on the original integer epigraph, including
nonminimal g, needs only endpoint/kink minima, and adds no variables.
It does not restore a common atomic distribution or the full routing hull.

Five saved full-domain LPs on three instances improve with one appended row:
K20 BASE/joint/STOCK by .002269286408/.002459563403/.004554385894;
K35 BASE by .005381130879; RX20 BASE by .016631649658. These are qualified
numerical reoptimization gains, distinct from the strictly larger saved-point
violations. No old LP is reoptimized and no optional closure iteration is run.

The same-new-PE complete own-H pairs expose the practical tradeoff:

| Role | D U / supported L | D + shared S U / supported L | Relative gap D → candidate |
|---|---|---|---|
| K35, cap2400 | .676798845196 / .545729444783 | .679917519727 / .558283855657 | 19.366079% → 17.889473% |
| RB35-T2, cap2400 | .335883588950 / .219663876370 | .371420783400 / .220898439927 | 34.601188% → 40.526096% |

All are open. K35 raises L 2.3005% with .4608% worse U. RB35 instead loses
10.5802% in U for only .5620% higher L; its signed-gap loss satisfies the
inherited serious double-open criterion. Thus the uniform one-row/one-added-
own-root-LP mechanism remains **research only**, with no further K20/RX20,
seed, high-deviation, RN/STOCK or AM rescue grid. R147 standalone D remains
its limited paper candidate and R137 remains stable. The result does not
declare the whole common-S family useless or claim broad robustness.

Production source is `d5868014c8868cdc305e6ed798bf0d5c86a1bda9`; new PE SHA256
is `4beb12f8a3de992691fc4ae229fdaff43e35ef00ce29f9f2bd3cb139af792ac2`.
The research entry is `scripts/paper_s2_shared_s.py`, profile
`config/gi_tbc_shared_s_round148.json`; bare `--round148-shared-s` defaults
off and `--shared-s off` selects the same-new-PE D control through the new
entry. Prior entries/profiles and historical results preserve their bytes.

[Final report](../results/unified_exact_round148/final_report.md),
[mathematics](../results/unified_exact_round148/mathematical_analysis.md),
[LP report](../results/unified_exact_round148/LP_report.md),
[decision](../results/unified_exact_round148/candidate_decision.json),
[paper-ready section](../results/unified_exact_round148/manuscript.tex),
[results/costs](../results/unified_exact_round148/cost_report.json) and
[delivery record](../results/unified_exact_round148/RESUME.md) retain all
new failures, identities, independent review and actual publication status.
The stronger historical TC/STOCK/RN results remain visible in the report.
