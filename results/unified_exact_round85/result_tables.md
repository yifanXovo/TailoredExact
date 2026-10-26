# R85 audited result tables

|Role|Arm|Cap|Paid seconds|Physical U|Global L|Signed gap|Relative gap|Certificate / stop|
|---|---|---:|---:|---:|---:|---:|---:|---|
|E7|P-GRB|120|1.469|0.0203825038422|0.0203825038422|3.46944695195e-17|1.70216916372e-15|yes; normal_return|
|E7|ENS-C|120|1.329|0.0203825038422|0.0203825038422|0|0|yes; normal_return|
|E7|K1-R|120|5.656|0.0203825038422|0.0203825038422|2.08166817117e-17|1.02130149823e-15|yes; normal_return|
|S12|P-GRB|120|5.656|0.0585639731258|0.0585639731258|4.16333634234e-17|7.10904011482e-16|yes; normal_return|
|S12|ENS-C|120|1.766|0.0585639731258|0.0585639731258|2.70616862252e-16|4.62087607463e-15|yes; normal_return|
|S12|K1-R|120|40.781|0.0585639731258|0.0585639731258|1.87350135405e-16|3.19906805167e-15|yes; normal_return|
|D3|P-GRB|300|297.078|0.0450541615805|0.0415401200124|0.00351404156814|0.0779959374422|open; normal_return|
|D3|ENS-C|300|139.047|0.0450015500556|0.0450015500556|-2.08166817117e-17|-4.62576993148e-16|yes; normal_return|
|D3|K1-R|300|297.062|0.0450541615805|0.0438467487043|0.00120741287621|0.0267991420515|open; normal_return|
|C2|P-GRB|300|297.063|0.829963413172|0.770943500725|0.0590199124463|0.0711114628785|open; normal_return|
|C2|ENS-C|300|113.766|0.829963413172|0.829963413172|1.11022302463e-15|1.33767706745e-15|yes; normal_return|
|C2|K1-R|300|297.078|0.829963413172|0.797088381296|0.0328750318758|0.0396102181784|open; normal_return|
|C6|P-GRB|600|597.109|1.68910073221|1.37508782921|0.314012903008|0.1859053738|open; normal_return|
|C6|ENS-C|600|597.156|1.68604175628|1.53661450055|0.149427255735|0.0886260706048|open; normal_return|
|C6|K1-R|600|597.125|1.68915723795|1.49847984643|0.190677391518|0.112883150979|open; normal_return|
|C8|P-GRB|600|597.063|0.806818916787|0.576956749593|0.229862167194|0.284899327979|open; normal_return|
|C8|ENS-C|600|597.062|0.806689827932|0.668942064172|0.13774776376|0.170756787789|open; normal_return|
|C8|K1-R|600|597.110|0.801649961457|0.629319151851|0.172330809606|0.214970146437|open; normal_return|
|D6|P-GRB|3600|3597.188|0.157241175852|0.150802687078|0.00643848877467|0.0409465824697|open; normal_return|
|D6|ENS-C|3600|3181.735|0.157083131103|0.157083131103|4.19109191796e-15|2.66807256039e-14|yes; normal_return|
|D6|K1-R|3600|3597.141|0.157083131103|0.148313237483|0.00876989362009|0.0558296333827|open; normal_return|

|Role|Reference|Candidate|Frozen classification|Material gain|Material loss|Severe loss|Metric change %|
|---|---|---|---|---|---|---|---:|
|E7|P-GRB|ENS-C|both_certified_small|false|false|false|-9.53029272474|
|E7|P-GRB|K1-R|both_certified_small|false|true|false|285.023825718|
|E7|K1-R|ENS-C|both_certified_small|true|false|false|-76.5028288557|
|S12|P-GRB|ENS-C|both_certified_small|true|false|false|-68.776520512|
|S12|P-GRB|K1-R|both_certified_small|false|true|true|621.021923625|
|S12|K1-R|ENS-C|both_certified_small|true|false|false|-95.6695519977|
|D3|P-GRB|ENS-C|certificate_gain|n/a|n/a|n/a|unavailable|
|D3|P-GRB|K1-R|both_open|true|false|false|-65.6403359837|
|D3|K1-R|ENS-C|certificate_gain|n/a|n/a|n/a|unavailable|
|C2|P-GRB|ENS-C|certificate_gain|n/a|n/a|n/a|unavailable|
|C2|P-GRB|K1-R|both_open|true|false|false|-44.2984062274|
|C2|K1-R|ENS-C|certificate_gain|n/a|n/a|n/a|unavailable|
|C6|P-GRB|ENS-C|both_open|true|false|false|-52.4136574314|
|C6|P-GRB|K1-R|both_open|true|false|false|-39.277211321|
|C6|K1-R|ENS-C|both_open|true|false|false|-21.6334697338|
|C8|P-GRB|ENS-C|both_open|true|false|false|-40.0737557462|
|C8|P-GRB|K1-R|both_open|true|false|false|-25.0286327195|
|C8|K1-R|ENS-C|both_open|true|false|false|-20.0678253211|
|D6|P-GRB|ENS-C|certificate_gain|n/a|n/a|n/a|unavailable|
|D6|P-GRB|K1-R|both_open|false|true|false|36.2104358184|
|D6|K1-R|ENS-C|certificate_gain|n/a|n/a|n/a|unavailable|

Positive metric change is slower certification or larger gap; no percentage is assigned across certificate gain/loss. The exact U/L direction and all checkpoints remain in the machine-readable evidence.
