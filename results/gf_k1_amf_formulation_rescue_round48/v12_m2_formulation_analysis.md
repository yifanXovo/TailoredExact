# V12 M2 formulation analysis

Instance: `round39_small_hard_V12_M2_Q20_slot06_seed258908503`. Historical terminal Work/time may use longer caps; GI(300) is the common-horizon field where available.

| algorithm | certificate | work | time_seconds | gap | gi_300 |
|---|---|---|---|---|---|
| K1-AMF (300s) | True | 38.80867136188028 | 24.4513781 | 1.886388367463341e-15 | 0.013005771775391726 |
| K1-AM (historical) | True | 38.80867136188028 | 24.3114296 | 1.886388367463341e-15 |  |
| K1-r015 (historical) | True | 38.80867136188028 | 24.4948463 | 1.886388367463341e-15 | 0.013328019394555003 |
| K4-AMC (historical) | True | 12.770682545305828 | 11.3940177 | 0 |  |
| K4-r001 (historical) | True | 12.770682545305828 | 11.6839557 | 0.0 | 0.010373199219834173 |
| P-GRB (historical) | True | 66.468393110745 | 41.6932403 | 0.0 | 0.038441743021260355 |

The matched root MIDPOINT replay was exact with Work 9.6512 versus RETAIN Work 38.8087, but AMF retained and exactly reproduced Work 38.8087. The beneficial split was missed.
