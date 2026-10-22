# Saved R129 B20 coverage example

This is the original E2 MS2 Seed0 diagnostic, not a Round130 formal observation. Its own H already attains F=0.5773330699702928; that feasible witness alone proves no optimality. Three subsequent natural splits and their actual closure sources provide the coverage. No old solution or bound enters a Round130 producer.

The root is `[0,0.5773330699702928]` with the same-run linear cutoff `F_model<=0.5773330699702928`. Its complete LP lower bound is 0.4790764218520756.

| Natural split parent | Split point | Actual trigger |
| --- | ---: | --- |
| L0 | 0.28866653498514638 | adaptive_mass_preserve_child_infeasibility_split |
| L0.0 | 0.14433326749257319 | adaptive_mass_preserve_child_infeasibility_split |
| L0.0.1 | 0.21649990123885979 | adaptive_mass_preserve_child_infeasibility_split |

| Final coverage member | True-G interval | Actual disposition/source | Proof-closure row |
| --- | --- | --- | ---: |
| L0.1 | [0.28866653498514638, 0.57733306997029277] | empty: complete_child_lp_infeasible | 1 |
| L0.0.0 | [0, 0.14433326749257319] | empty: complete_child_lp_infeasible | 0 |
| L0.0.1.0 | [0.14433326749257319, 0.21649990123885979] | closed: native_terminal_mip_optimal | 0 |
| L0.0.1.1 | [0.21649990123885979, 0.28866653498514638] | empty: complete_child_lp_infeasible | 1 |

The two models containing the semantic closure row must be interpreted through their retained interval penalty lower bound and cutoff, rather than as inclusive physical infeasibility. Exact `L_a>c` excludes `F<=c`; exact equality excludes strict improvement only; a bound slightly below c retains that bound under the original numerical policy. The actual binary64 premises are L0.1: penalty floor 2.4700000000000006, L_a-c=0.081833465014853779; L0.0.1.1: penalty floor 2.4700000000000006, L_a-c=0.0096668312685671554. Both differences are positive here. The JSON preserves their full values. The other empty side has no such row. The remaining terminal MIP returns OPTIMAL with bound 0.5773330699702926; the tiny signed gap is retained.

The detailed immutable tree events, LP dispositions, root scope, all closed-side reasons and final terminal are indexed in R129_B20_coverage_example.json. Infeasibility of a model containing a semantic proof-closure row is interpreted only on its stated improving domain and original numerical policy; it is not inclusive-root physical infeasibility. Split exposure does not establish its net computational contribution.
