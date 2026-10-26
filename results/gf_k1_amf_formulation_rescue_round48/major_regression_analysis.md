# Major regression analysis

Instance: `round39_small_medium_V12_M3_Q30_slot08_seed1343324363`. Historical terminal Work/time may use longer caps; GI(300) is the common-horizon field where available.

| algorithm | certificate | work | time_seconds | gap | gi_300 |
|---|---|---|---|---|---|
| K1-AMF (300s) | False | 608.1906833850892 | 280.1459382 | 0.061236860738835275 | 0.19760149137693786 |
| K1-AM (historical) | True | 843.4563311103416 | 384.6042946 | 1.5419233104925857e-15 |  |
| K1-r015 (historical) | True | 843.4563311103416 | 385.4760476 | 1.5419233104925857e-15 | 0.2032792638378745 |
| K4-AMC (historical) | True | 1571.4256243238797 | 694.616193 | 1.3877309794433272e-14 |  |
| K4-r001 (historical) | True | 3898.1509266770327 | 1780.0433176 | 1.3877309794433272e-14 | 0.26022138147536894 |
| P-GRB (historical) | True | 1568.0170733870093 | 1009.0487443 | 0.0 | 0.12217803475016592 |
| K1-AM (historical) | False | 608.0716571725522 | 280.0422174 | 0.061236860738835275 | 0.19773781449217553 |
| K4-AMC (historical) | False | 599.1156114610512 | 280.0350646 | 0.17555035515550454 | 0.2554536700237098 |

AMF made no action change. The 300-second row did not certify, so the full-horizon historical K1-AM repair is not newly qualified by this bounded round.
