# R86 audited result tables

|Role|Arm|Cap|Paid seconds|Physical U|Global L|Signed gap|Relative gap|Certificate / stop|
|---|---|---:|---:|---:|---:|---:|---:|---|
|F1|P-GRB|120|49.953|0.195558533871|0.195558533871|5.13200593133e-14|2.62428124702e-13|yes; normal_return|
|F1|ENS-C|120|11.891|0.195558533871|0.195558533871|5.55111512313e-17|2.83859518337e-16|yes; normal_return|
|F1|K1-R|120|43.203|0.195558533871|0.195558533871|-3.88578058619e-16|-1.98701662836e-15|yes; normal_return|
|F2|P-GRB|300|297.078|0.865943520323|0.729109801423|0.1368337189|0.158016909519|open; normal_return|
|F2|ENS-C|300|297.078|0.865943520323|0.832902911374|0.0330406089492|0.038155616589|open; normal_return|
|F2|K1-R|300|297.063|0.865943520323|0.782062874142|0.0838806461809|0.0968661860875|open; normal_return|
|F5|P-GRB|3600|3597.125|0.434235836764|0.268250596924|0.16598523984|0.382246755764|open; normal_return|
|F5|ENS-C|3600|3597.172|0.329323694641|0.281453806344|0.0478698882966|0.145358166071|open; normal_return|
|F5|K1-R|3600|3597.203|0.316133367575|0.276147052028|0.0399863155476|0.126485590099|open; normal_return|
|F6|P-GRB|3600|3597.187|0.305585444373|0.265294704234|0.0402907401398|0.131847707022|open; normal_return|
|F6|ENS-C|3600|3597.313|0.292941308691|0.278026253182|0.0149150555086|0.050914825141|open; normal_return|
|F6|K1-R|3600|3597.188|0.288411162135|0.268087572328|0.0203235898075|0.0704674176167|open; normal_return|

|Role|Reference|Candidate|Frozen classification|Material gain|Material loss|Severe loss|Metric change %|
|---|---|---|---|---|---|---|---:|
|F1|P-GRB|ENS-C|both_certified_small|true|false|false|-76.195623886|
|F1|P-GRB|K1-R|both_certified_small|false|false|false|-13.5127019398|
|F1|K1-R|ENS-C|both_certified_small|true|false|false|-72.4764483942|
|F2|P-GRB|ENS-C|both_open|true|false|false|-75.8534597943|
|F2|P-GRB|K1-R|both_open|true|false|false|-38.6988478752|
|F2|K1-R|ENS-C|both_open|true|false|false|-60.6099732733|
|F5|P-GRB|ENS-C|both_open|true|false|false|-71.1601535517|
|F5|P-GRB|K1-R|both_open|true|false|false|-75.909716077|
|F5|K1-R|ENS-C|both_open|false|true|false|19.7156768285|
|F6|P-GRB|ENS-C|both_open|true|false|false|-62.981430828|
|F6|P-GRB|K1-R|both_open|true|false|false|-49.5576657639|
|F6|K1-R|ENS-C|both_open|true|false|false|-26.6121012585|

Positive metric change is slower certification or larger gap; no percentage is assigned across certificate gain/loss. The exact U/L direction and all checkpoints remain in the machine-readable evidence.
