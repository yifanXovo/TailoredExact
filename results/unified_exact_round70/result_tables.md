# Round70 result tables

Complete bounded stage. Overall research goal remains unmet.

All roles are exposed development data. No independent confirmation, extra repeat or long extension is included.

|Role|Arm|Cap|Certified|Paid wall|Verified UB|Global LB|Signed gap|Startup wall|
|---|---|---:|---|---:|---:|---:|---:|---:|
|E7|P-GRB|120|True|1.282|0.0203825038422|0.0203825038422|3.46944695195e-17|0.000|
|E7|VD-S|120|True|5.610|0.0203825038422|0.0203825038422|0|4.319|
|E7|DS|120|True|1.156|0.0203825038422|0.0203825038422|3.46944695195e-17|0.019|
|S12|P-GRB|120|True|5.187|0.0585639731258|0.0585639731258|4.16333634234e-17|0.000|
|S12|VD-S|120|True|39.187|0.0585639731258|0.0585639731258|2.70616862252e-16|37.911|
|S12|DS|120|True|2.094|0.0585639731258|0.0585639731258|5.55111512313e-17|0.341|
|N12|P-GRB|120|True|3.891|0.80462551972|0.80462551972|-1.11022302463e-16|0.000|
|N12|VD-S|120|True|3.640|0.80462551972|0.80462551972|7.77156117238e-16|1.739|
|N12|DS|120|True|1.453|0.80462551972|0.80462551972|1.88737914186e-15|0.016|
|D3|P-GRB|300|False|297.063|0.0450541615805|0.041578308421|0.00347585315956|0.000|
|D3|VD-S|300|True|84.187|0.0450015500556|0.0450015500556|7.6327832943e-17|2.060|
|D3|DS|300|False|297.063|0.0450015500556|0.0432201948457|0.00178135520996|0.018|
|D3|K1-R|300|False|297.063|0.0450541615805|0.0438938487828|0.00116031279775|2.059|
|C2|P-GRB|300|False|297.063|0.829963413172|0.771497142603|0.0584662705684|0.000|
|C2|VD-S|300|True|124.078|0.829963413172|0.829963396652|1.65193129176e-08|2.654|
|C2|DS|300|True|154.297|0.829963413172|0.829963413172|9.99200722163e-16|0.015|
|D4|P-GRB|300|False|297.078|0.506343307565|0.196200011066|0.310143296499|0.000|
|D4|VD-S|300|True|54.219|0.506343307565|0.506343307565|6.66133814775e-16|1.996|
|D4|DS|300|True|53.968|0.506343307565|0.506343307565|1.11022302463e-16|0.015|
|D6|P-GRB|600|False|597.313|0.157241175852|0.144985883254|0.012255292598|0.000|
|D6|VD-S|600|False|597.063|0.157083131103|0.145680206762|0.0114029243411|319.129|
|D6|DS|600|False|597.063|0.157083131103|0.150087063918|0.0069960671847|5.511|
|D6|K1-R|600|False|597.078|0.157083131103|0.143340966163|0.01374216494|318.508|
|D7|P-GRB|600|False|597.078|0.290186246296|0.196954926915|0.0932313193812|0.000|
|D7|VD-S|600|False|597.094|0.215644075316|0|0.215644075316|597.058|
|D7|DS|600|False|597.094|0.331965787612|0.204077158583|0.127888629028|2.799|
|D7|K1-R|600|False|597.204|0.215644075316|0|0.215644075316|597.163|

Signed gaps, including tiny negative numerical discrepancies, are preserved in the CSV. Zero requested gaps do not imply a rational certificate. Startup is never subtracted from formal total time.

|Role|DS reference|Classification|Wall delta|UB delta|LB delta|Gap delta|Bound relation|
|---|---|---|---:|---:|---:|---:|---|
|E7|P-GRB|below_practical_threshold|-0.126|0|0|0|aligned_or_unchanged|
|E7|VD-S|material_improvement|-4.454|0|-3.46944695195e-17|3.46944695195e-17|aligned_or_unchanged|
|S12|P-GRB|material_improvement|-3.093|-6.93889390391e-18|-2.08166817117e-17|1.38777878078e-17|aligned_or_unchanged|
|S12|VD-S|severe_improvement|-37.093|0|2.15105711021e-16|-2.15105711021e-16|aligned_or_unchanged|
|N12|P-GRB|material_improvement|-2.438|0|-1.99840144433e-15|1.99840144433e-15|aligned_or_unchanged|
|N12|VD-S|material_improvement|-2.187|0|-1.11022302463e-15|1.11022302463e-15|aligned_or_unchanged|
|D3|P-GRB|material_improvement|0.000|-5.26115249063e-05|0.00164188642469|-0.00169449794959|aligned_or_unchanged|
|D3|VD-S|certificate_loss|212.876|0|-0.00178135520996|0.00178135520996|aligned_or_unchanged|
|D3|K1-R|below_practical_threshold|0.000|-5.26115249063e-05|-0.000673653937121|0.000621042412215|mixed|
|C2|P-GRB|certificate_gain|-142.766|0|0.0584662705684|-0.0584662705684|aligned_or_unchanged|
|C2|VD-S|material_regression|30.219|0|1.65193119184e-08|-1.65193119184e-08|aligned_or_unchanged|
|D4|P-GRB|certificate_gain|-243.110|0|0.310143296499|-0.310143296499|aligned_or_unchanged|
|D4|VD-S|below_practical_threshold|-0.251|0|5.55111512313e-16|-5.55111512313e-16|aligned_or_unchanged|
|D6|P-GRB|material_improvement|-0.250|-0.000158044749118|0.00510118066416|-0.00525922541327|aligned_or_unchanged|
|D6|VD-S|material_improvement|0.000|0|0.00440685715638|-0.00440685715638|aligned_or_unchanged|
|D6|K1-R|material_improvement|-0.015|0|0.00674609775534|-0.00674609775534|aligned_or_unchanged|
|D7|P-GRB|material_regression|0.016|0.041779541316|0.00712223166866|0.0346573096473|mixed|
|D7|VD-S|material_improvement|0.000|0.116321712296|0.204077158583|-0.0877554462873|mixed|
|D7|K1-R|material_improvement|-0.110|0.116321712296|0.204077158583|-0.0877554462873|mixed|

Classifications use the predeclared absolute and relative practical thresholds. A missing certificate is explicit; mixed UB/LB changes must be read with the raw values. Micros do not enter performance pairs.

Revision2: 27 performance + 6 micro runs; 133 experiment Optimize calls; 6797.377s complete paid wall; zero validity failures.
Startup-only whole-run deadlines: 2; supervisor postcondition exceptions: 2. These retained runs use independently justified global LB0, without inventing a proof tree or certificate; no rerun or replacement.
Revision1: 6 superseded micros, including 2 DS configuration failures; 21 calls and 0.766s retained, never replaced or counted as valid candidate performance.
Both CTest batches together: 24 native calls, separate from experiments. See qualification_native_call_audit.json for the runtime fixture count and independently counted CLI ledger.
Initial-witness/model checks: 97, including 38 incompatible Gini intervals. Actual Start decisions: 22; eligible 22, native accepted 22, full submitted vectors observed 22.
Native MIPSOL equality is qualified C++ observer evidence. The independent replay checks the retained submitted/readback vectors, exported rows/types/objective and original physical routes; unretained full native event vectors cannot be replayed.

Frozen implementation commit: 86c35aa7fc055e784fecf7eb1a623483c6206dc8; executable SHA256: 2e841e23cdbc81f71b9373f35b7c82494223a7ecfbb670bcdc33f7ec2b66e6f3.
Gurobi13.0.2 / Threads1 / Seed0 / PresolveAuto / original numerical standards. All fresh arms inherit logical processor2/mask4. P-GRB remains original compact/default, without HGA, explicit external Start, added cuts or imported bounds.

Source, model, input, physical witness, full frontier, affinity and actual-Start evidence are under revision2/. Large raw models/logs and both binaries remain local. Read algorithm.md, small_screen.md, status.md and reproduce.md for scope.
