# Post-primal continuation and research endpoint: independent review

This is a read-only goal E3/I assessment by the independent nonimplementer.
It uses the sealed research records named below, their plans, and small
closed outer receipts. No Native, Optimize, replay, enumeration, source
import, compilation, or experiment was executed. The conditional primal
probes and the complete eight-arm panel have not been read as final
outcomes. Their results must not be presumed. This review does not authorize
a new expensive run; any continuation is a root decision and remains
serial and fully charged. Frozen production and pricing sources stay fixed.

## Evidence available before the primal probes

| Role | Current strengthened-LP interval | Width | Latest near-optimal phase | Same-Q support transfer |
| --- | --- | --- | --- | --- |
| K35 | [0.2828596948801647, 0.2873261633063073] | 0.004466468426142567 | 11 complete 300-second prices; 1043 to 1114 columns; outer 3485.3559666 s | 81 supports; outer 12.9624733 s; L increased by about 0.00023604 |
| NC20 | [0.1833218484555365, 0.18995680056588546] | 0.006634952110348952 | 17 complete 300-second prices; 283 to 427 columns; outer 5203.6791515 s | 48 supports; outer 9.1190025 s; retained L |

All six examined long-price/near-optimal/support-transfer receipts have
observed exit 0 and no timeout or supervisor failure. Their outer seconds,
not inherited result seconds or nested solver Runtime, are the costs above.
In particular, the support-transfer result may retain the preceding phase's
seconds. It must not be treated as another fee of that size.

Relative to the current direct-Q numerical upper, the established lower
improvements are approximately 0.00399524 for K35 and 0.00855272 for NC20.
The intervals therefore establish meaningful positive full-hull value;
they do not locate its full value to the registered 1e-4/1e-5 targets.
The widths are about 45 and 663 target units, respectively. NC20's much
older approximately 2.68e-4 increment has not thereby become a precise
explanation of the present complete-hull effect.

The last K35 iteration, `near_optimal_zero_pool/iter00010`, has qualified
RMP upper 0.2873261633063416, D_K 0.28732605330672223, beta about 0.999957,
and price [0.06092685437735434, 0.08087030469130901]. It adds no column;
its only returned stock is already represented to price precision. The
lower correction remains 0.01994345031395467 and its individual corrected
lower is only 0.26738260299276756. This is not full pricing convergence.
The preceding two iterations added 2 and 3 columns without improving U.

NC20's `iter00016` has RMP upper 0.18995680056588546, D_K
0.18995669056587938, beta 1, and price
[0.0038673609493397416, 0.04327504345243518]. Eight columns were added,
seven negative at the selected dual. Its individual corrected lower is
0.14975960633294666; the inherited better L is correctly retained. The
final upper improved by about 0.00011368 from the preceding plateau, so
this phase was still discovering useful columns when its allowance ended.

Both RMP-minus-D_K differences are about 1.1e-7. The last prices have
guard sizes about 2.1e-6 but widths about 0.01994 and 0.03941. These scales
locate the immediate problem in extending/pricing the selected dual and
in useful column discovery, not in the tiny RMP residual. They do not
prove that either LP upper is the full-hull optimum. The conditional
primal probe addresses a different, still plausible explanation: missing
useful feasible inventory mixtures despite expensive directional pricing.

## Fixed-direction ceilings and their precise scope

For a saved, qualified C_Q and true a_K, and a full-domain price bracket
[l,u], define

`B_dir = C_Q + min(a_K,l)`,

`P_dir = C_Q + min(a_K,u)`.

P_dir is an upper bound on the lower certificate attainable by making
this same price exact while retaining this C_Q/a_K correction. It is not
an upper bound on the full-hull optimum. The numbers below are rounded
diagnostic arithmetic from saved certificates, not new exact certificates.

| Saved direction | Price width | P_dir, approximately | Implication at the current checkpoint |
| --- | --- | --- | --- |
| K35 old `price_deep/iter00003`, after 3600-second price | 0.00106151 | 0.2836851622 | At most about 0.00082547 additional direct-certificate gain above current L; at least about 0.00364100 of current hull width remains even at this ceiling |
| NC20 old `level_zero_continued/iter00008`, after long price | 0.00000110772 | 0.1833229562 | At most about 1.11e-6 additional direct gain, below the registered 1e-5 target |
| K35 latest near-optimal `iter00010` | 0.01994345 | 0.2873260533 | Almost the current RMP upper; potentially important, but not attained |
| NC20 latest near-optimal `iter00016` | 0.03940768 | 0.1891672888 | Potential direct gain about 0.00584544; still leaves about 0.00078951 against the current U even if attained |

The old NC20 price ended at Native status 2 after about 647.45 Runtime
seconds (648.6849454 outer), with its remaining width already close to
the declared approximately 1.02e-6 guard. Extending its time limit is not
a meaningful response to the present 0.00663 hull width. This does not
call for reopening the inherited tiny-gap policy. The K35 old direction
remains less tightly priced after 3600 seconds/621815 nodes, but its
ceiling rules it out as a one-direction route to closing the current hull.
It is not categorically useless: its remaining direct potential still
exceeds 1e-4, and must be judged against cost and better alternatives.

For comparison, the latest K35 price lower must rise from about 0.06093
to above 0.07640 merely to beat current L; the latest NC20 lower must
rise from about 0.00387 to above 0.03743. Large potential ceilings alone
do not predict that these substantial bound advances are affordable.
Neither latest beta-near-one direction has received the corresponding
fixed-direction long-price test. The old long prices used beta about
0.237 and 0.460, respectively. Their behavior cannot be transferred
without qualification to the new directions.

Two restrictions on using these ceilings are essential:

- After the primal probe, reevaluate saved directions on every new true
  legal column before ranking them. The updated feasible price upper is
  a minimum and can decrease; a previously attractive ceiling may vanish.
  This is finite candidate evaluation, not a full price lower. It must
  still be included in the next authorized computation's accounting.
- P_dir bounds only this fixed dual certificate. A tighter support row
  can interact with other supports when the complete free Q is solved
  again. The K35 support transfer already demonstrates such an advantage
  over the individual accumulated certificates. Therefore a ceiling at
  or below current L does not prove that the entire support family has
  no value. It only removes the advertised direct-certificate reason to
  extend that direction. Any separate complementarity hypothesis needs
  evidence; it is not an excuse to repeat a numerically closed price.

## Narrow conditional next step

First finish and seal the already registered primal probes. Retain the
previous lower, qualify any new complete-Q primal upper, and report
actual U reduction, final residuals, added columns/pairs, stop reason, and
outer fee. A heuristic no-new-column exit is not even a proof of exhaustive
local optimality, much less full pricing convergence.

If the resulting width meets the role's registered target, no continuation
is needed. Otherwise update the ceiling screen above using the new stocks
and new U. Do not automatically run both another level loop and another
long price in both domains.

The most informative narrowly different test, if its ceiling remains
material and verification/delivery reserves permit, is **one selected
new near-optimal fixed direction**, keeping the existing normalized full
oracle and all scope/certificate bindings. An initial roughly 1200-second
Native allowance is a reasonable fourfold diagnostic of the existing
300-second bottleneck, not an automatic adoption or a mathematical stop
rule. On present evidence K35 iter00010 has the cleaner potential to
approach its U; that preference must be reconsidered after the primal
columns update its price upper. Choose the direction from the documented
research evidence, not from full B/J performance. Retain old price bounds
and all legal stocks; apply C_Q/a_K correction once and reuse a newly
stronger support through the already reviewed same-Q transfer when useful.

A renewed `level_zero_pool` pass has a more specific role when:

- the primal probe materially changes U or active mixtures, making the
  old level/dual selection obsolete; or
- a well-priced near-optimal direction establishes substantial *true*
  negative reduced cost and a low direct ceiling, so changing to the
  updated midpoint level is more promising than extending its price; or
- observed bound-versus-cost progress confirms that beta-near-one pricing
  is the limiting step, while the earlier lower-beta level mechanism
  provides a concrete, updated and cheaper direction-selection hypothesis.

Such a pass must start from all current legal columns and accumulated
supports/bounds, keep Q and the full price domain, and compare its actual
gain/cost with the completed near-optimal phase. Merely adding more
columns, exhausting another fixed iteration count, or retaining a large
uncertain price upper does not establish progress. The fresh midpoint is
a candidate selector, not a lower certificate.

## Honest stage endpoint and continuation decision

Goal E3 permits a quantified unresolved endpoint after meaningful targeted
deepening; it does not require spending the capacity or achieving the same
micro-gap on every domain. A defensible endpoint after these probes must
include all of the following:

1. The final qualified interval and positive improvement over the same
   full-Q reference, with its remaining width and numerical policy.
2. Actual before/after L and U and unique outer costs for the long saved
   prices, changed dual selection, all-support free-Q replay, and primal
   column diagnostic. The finite partition/CDF/graph alternatives are
   reported only within their tested directions and allowances.
3. The remaining price brackets, corrections, RMP-minus-D_K scale, true
   stock ceilings, and observed column/upper response. This distinguishes
   an easy exhausted old direction from difficult new directions.
4. An explicit reason for stopping or continuing the *remaining claim*:
   either its relevant accuracy is met, a candidate's possible direct
   improvement is too small, or the targeted evidence locates an unresolved
   pricing/coupling cost barrier without another concretely justified step.

For an optional additional diagnostic, predeclare a material research gain
relative to the post-probe interval (for example, at least the registered
absolute target and roughly one tenth of that width). This is a decision
threshold, not a convergence tolerance or an eligibility rule for valid
bounds. Retain every smaller valid improvement. At the sealed return,
compare achieved L/U improvement and price-bound advance with this target
and with the still-possible ceiling. If useful progress is continuing and
a substantial reachable gap remains, E3 favors another specifically
justified step while resources allow. If the added test yields neither
material interval reduction nor a supported route to it, record the
quantified unresolved boundary rather than automatically extending caps.

The evidence already supports a positive value result and a large
direction-dependent pricing difficulty. The future primal result can
confirm or weaken the missing-primal-column explanation; it cannot by
itself certify full-hull optimality. No-new-column outcomes, time caps,
weak tested alternatives, and unfavorable full B/J outcomes are not proofs
that no further potential exists. Conversely, an unresolved interval is
not by itself a reason
to repeat indefinitely a direction whose stated purpose is exhausted.
The final stage conclusion must say which of these boundaries was actually
observed. It must not call the family negative, the targets met, or the
entire goal complete before final evidence qualification and delivery.

## Evidence binding

Paths below are relative to `results/unified_exact_round153`; SHA256 values
bind the read checkpoint, not a replayed proof.

| Record | SHA256 |
| --- | --- |
| `deepening_plan.md` | `f458c30aae38f9b44b10e532a0114f2a1dcb5188d2b914b7272d199ad5580fe7` |
| `primal_pool_plan.md` | `76a8de085400c3c035f65a717eb0fb80dcda0affd409c8513a968d3eefeec4ab` |
| `coupled/K-35-U_near_optimal_zero_pool/iter00010/result.json` | `82838b48064fa5e9e2ec9ab265aaf66b28d64389eaa94be3a80207debeafef73` |
| `coupled/K-35-U_near_optimal_zero_pool/iter00010/pricing/result.json` | `ed1be4f66ec365c5aab36939a7c186c225654df067827f4a8474362729b418ba` |
| `coupled/N-C20-U_near_optimal_zero_pool/iter00016/result.json` | `fbc7431d2f1cfe52a63a47d0eb5d73a3762ac1a64807cd4f905af6cb7d38895d` |
| `coupled/N-C20-U_near_optimal_zero_pool/iter00016/pricing/result.json` | `dcaa467816af976bed021ddbc32d50541bdb5f9cf89c5de22e89cdfe40cbadb0` |
| `coupled/K-35-U_saved_direction_long/result.json` | `7e8ea321fc01a4ed3c2797d78c1dc7e955a2a20e88f15096466675b745849a81` |
| `coupled/N-C20-U_saved_direction_long/result.json` | `bd76edc03081a40a62e165533995eef4b9b555ddbf0d8fb4453a243491a4b4cf` |
| `coupled/K-35-U_deepened_support_envelope/result.json` | `7ec7bdab10fb2dd0d27d598e05645071f58a527f40014a65828916e377b61616` |
| `coupled/N-C20-U_deepened_support_envelope/result.json` | `70ecd7408bd5e56f414810fca10b476e128881bfbd33f6ff6ca8ef689f39d7e7` |
| `support_LP/K-35-U_deepened_support_envelope/result.json` | `c6d1a6a07fb05f221796103449995cfcb8a3f94dea911b9af35ee618bfdedb57` |
| `support_LP/N-C20-U_deepened_support_envelope/result.json` | `7db3221f42982e1fbdb26ce222a6f70860ecf4663d26bc499a6c8b54cb57390a` |

Disposition: `ACCEPT_CONDITIONAL_RESEARCH_DESIGN`, with probe outcomes,
continuation selection, final audit, and stage conclusion still pending.
