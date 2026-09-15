# Round71 result tables

Audited prefix; stage in progress. Overall research goal remains unmet.

All roles are exposed development data. No independent confirmation or extra repeat is included. D7 is one fresh1200s run per arm, not a continuation of Round70.

|Role|Arm|Cap|Certified|Paid wall|Verified UB|Global LB|Signed gap|Startup wall|
|---|---|---:|---|---:|---:|---:|---:|---:|
|E7|P-GRB|120|True|1.313|0.0203825038422|0.0203825038422|3.46944695195e-17|0.000|
|E7|DS|120|True|1.172|0.0203825038422|0.0203825038422|3.46944695195e-17|0.019|
|E7|DS-X|120|True|1.172|0.0203825038422|0.0203825038422|3.46944695195e-17|0.019|
|S12|P-GRB|120|True|5.140|0.0585639731258|0.0585639731258|4.16333634234e-17|0.000|
|S12|DS|120|True|2.156|0.0585639731258|0.0585639731258|5.55111512313e-17|0.342|
|S12|DS-X|120|True|2.125|0.0585639731258|0.0585639731258|5.55111512313e-17|0.346|
|N12|P-GRB|120|True|3.891|0.80462551972|0.80462551972|-1.11022302463e-16|0.000|
|N12|DS|120|True|1.437|0.80462551972|0.80462551972|1.88737914186e-15|0.016|
|N12|DS-X|120|True|1.422|0.80462551972|0.80462551972|1.88737914186e-15|0.016|
|D7|P-GRB|1200|False|1197.078|0.277320865934|0.197286478715|0.0800343872194|0.000|
|D7|DS|1200|False|1197.109|0.318958799087|0.204077158583|0.114881640504|2.829|
|D7|DS-X|1200|False|1197.109|0.278335266779|0.204146294626|0.0741889721534|9.380|
|D7|K1-R|1200|False|1197.125|0.215644075316|0.197357479228|0.0182865960875|612.421|

Signed gaps preserve tiny numerical discrepancies. Requested gaps0 do not imply a rational certificate. Startup remains part of formal paid time.

|Role|DS-X reference|Classification|Wall delta|UB delta|LB delta|Gap delta|Bound relation|
|---|---|---|---:|---:|---:|---:|---|
|E7|P-GRB|below_practical_threshold|-0.141|0|0|0|aligned_or_unchanged|
|E7|DS|below_practical_threshold|-0.000|0|0|0|aligned_or_unchanged|
|S12|P-GRB|material_improvement|-3.015|-6.93889390391e-18|-2.08166817117e-17|1.38777878078e-17|aligned_or_unchanged|
|S12|DS|below_practical_threshold|-0.031|0|0|0|aligned_or_unchanged|
|N12|P-GRB|material_improvement|-2.469|0|-1.99840144433e-15|1.99840144433e-15|aligned_or_unchanged|
|N12|DS|below_practical_threshold|-0.015|0|0|0|aligned_or_unchanged|
|D7|P-GRB|below_practical_threshold|0.031|0.00101440084517|0.00685981591119|-0.00584541506601|mixed|
|D7|DS|material_improvement|-0.000|-0.0406235323077|6.91360424403e-05|-0.0406926683502|aligned_or_unchanged|
|D7|K1-R|severe_regression|-0.016|0.0626911914634|0.00678881539741|0.055902376066|mixed|

Classifications use the frozen absolute and relative thresholds. Missing certificates and mixed UB/LB changes remain explicit. All DS diagnostic pairs are retained in pairs.csv; micros are excluded.

13 performance + 6 micro runs; 82 experiment Optimize calls; 4808.951s paid process wall; zero validity failures.
Valid startup-only whole-run deadlines: 0; supervisor exceptions: 0. Such deadlines use independently justified global LB0, without a fabricated tree/certificate or replacement run.
Qualification: 49/49 new CTests, 39 native calls and 95.131s configure/build/test. Ten no-opt reference exports cost 0.797s.
Initial-witness/model checks: 65, including 26 incompatible Gini intervals. Actual Start decisions: 10; eligible 10, accepted 10, full submitted vectors observed 10.
Native MIPSOL equality is qualified C++ observer evidence; independent replay checks retained submitted/readback vectors, rows, domains, objective and physical routes. Unretained full native event vectors cannot be replayed.

Source freeze: 3867214f480d0a4fef4d77f03404f9fd89fb8b42; binary SHA256: 4f60ed8cd6f65c695947e8ac3bd525b77d28d94733faf2c9ef25d057a69023af.
Gurobi13.0.2, Threads1, Seed0, PresolveAuto, original numerical standards; uniform logical processor2/mask4. P-GRB remains original compact/default without HGA, explicit external Start, new cuts or imported bounds.
Source, model, input, route, coverage, affinity and actual-Start evidence are retained in this stage. Large models/logs/binary remain local at manifest paths.
