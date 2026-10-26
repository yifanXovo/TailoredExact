# Strong-control rescue analysis

Instance: `round39_small_hard_V12_M3_Q30_slot08_seed1288546114`. Historical terminal Work/time may use longer caps; GI(300) is the common-horizon field where available.

| algorithm | certificate | work | time_seconds | gap | gi_300 |
|---|---|---|---|---|---|
| K1-AMF (300s) | False | 501.2736815547833 | 280.1429555 | 0.16025130118073339 | 0.21099855378069396 |
| K1-AM (historical) | True | 740.6340681077912 | 408.9598331 | 4.0828682536125e-08 |  |
| K1-r015 (historical) | True | 740.6340681077912 | 417.0651251 | 4.0828682536125e-08 | 0.21129863314544492 |
| K4-AMC (historical) | True | 133.73490192498448 | 76.7515995 | 3.0696806124470356e-15 |  |
| K4-r001 (historical) | True | 133.73490192498448 | 78.8809124 | 3.0696806124470356e-15 | 0.07099692172749544 |
| P-GRB (historical) | True | 3152.2339036687963 | 1739.1272517 | 5.701105555009818e-09 | 0.6509596068347505 |
| K1-AM (historical) | False | 501.34679704778335 | 280.0504799 | 0.16025130118073339 | 0.21114161523865324 |
| K4-AMC (historical) | True | 133.73490192498448 | 78.8355763 | 3.0696806124470356e-15 | 0.071174922644545 |

The root and every observed decision were unchanged from AM; the row did not certify. Classification: strong_control_not_rescued.
