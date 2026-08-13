# Round 38 persistence analysis

Every one of the 19 evaluated midpoint pairs failed `b+ >= t`; no candidate split entered the live tree. Refined-descendant persistence is therefore not applicable. What persists is a rejected-lookahead path effect: G2-A completes the initial census, discards its child models, then targets the unchanged parent at `t`.

| Stage | Row | Cap | Outcome | Gap change | AUC change | Accepted |
|---|---:|---:|---|---:|---:|---:|
| smoke | 8 | 180 | g2a_improves | 0.0799122 | 0.061046 | False |
| smoke | 10 | 180 | tie | 0 | -0.0045387 | False |
| diagnostic | 8 | 480 | g2a_improves | 0.100224 | 0.0800375 | False |
| diagnostic | 10 | 480 | tie | 0 | -0.00137203 | False |
| diagnostic | 11 | 480 | g2a_regresses | -0.00932019 | -0.0121246 | False |
| confirmation | 8 | 900 | g2a_improves | 0.112251 | 0.0945276 | False |
| confirmation | 10 | 900 | tie | 0 | -0.00078866 | False |
| confirmation | 11 | 900 | g2a_regresses | -0.00900788 | -0.0108887 | False |

The stable V20 positive persists from 180 through 900 seconds and the original adversarial V50 remains a final-gap tie. The V50 tight-T regression persists from 480 through 900 seconds after common-UB normalization. Hence rejected-pilot target/split reordering is bidirectional and is not a stable structural rule.
