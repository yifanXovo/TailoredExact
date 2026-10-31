# Round143 reciprocal-normalization study

The default-off [RN research entry](../scripts/paper_s2_rn.py) adds a compact
reciprocal-normalized Gini block to stable R137 GI-TBC, retaining integer
routes/inventory and the original penalty. Four matched continuous LPs show
real gains, including gains over TC+stock. Two same-PE Seed0 role pairs show
K35 incumbent/support-bound tradeoffs and no RX20-T1 proof-clock benefit.

The independently reviewed decision is **research-only; stop full expansion
this round**. Stable GI-TBC and previous entries/profiles remain available.
See the [report](../results/unified_exact_round143/final_report.md),
[mathematics](../results/unified_exact_round143/mathematical_analysis.md),
[decision](../results/unified_exact_round143/candidate_decision.json),
[research appendix](../results/unified_exact_round143/manuscript.pdf) and
[continuation/delivery record](../results/unified_exact_round143/RESUME.md).
The profile is `config/gi_tbc_rn_round143.json`; `--rn on|off` selects the
same-PE research/control mode. The launcher only expands unless `--run` is explicit.

All new build/raw/temp/restore assets stay under ExactEBRP-work. Post-PR
cleanup is bounded to this round after public recovery acceptance, retaining
unique raw/failures and necessary runtime dependencies. Old rounds and the
original user tree remain protected.
