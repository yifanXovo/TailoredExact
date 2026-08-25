# Harmful negative-control analysis

Instance: `round39_small_hard_V10_M3_Q20_slot04_seed1145042375`. Historical terminal Work/time may use longer caps; GI(300) is the common-horizon field where available.

| algorithm | certificate | work | time_seconds | gap | gi_300 |
|---|---|---|---|---|---|
| K1-AMF (300s) | True | 8.991485297269257 | 6.8888414 | 4.400898038348613e-16 | 0.00945410539712101 |
| K1-AM (historical) | True | 8.991485297269257 | 6.8371267 | 4.400898038348613e-16 |  |
| K1-r015 (historical) | True | 8.991485297269257 | 6.9889521 | 4.400898038348613e-16 | 0.009797599889910344 |
| K4-AMC (historical) | True | 10.503884558425527 | 9.0619342 | 0 |  |
| K4-r001 (historical) | True | 10.503884558425527 | 9.3577064 | 0.0 | 0.011454996271531638 |
| P-GRB (historical) | True | 247.29863210454607 | 159.6051278 | 9.329888218111024e-09 | 0.23155178664399556 |
| K1-AM (historical) | True | 8.991485297269257 | 6.8933373 | 4.400898038348613e-16 | 0.009645113894413103 |
| K4-AMC (historical) | True | 10.503884558425527 | 9.2542616 | 0.0 | 0.011419629207557855 |

AMF retained the root, produced no rescue, and preserved the exact certificate and historical Work.
