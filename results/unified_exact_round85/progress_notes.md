# R85 progress through the first four roles

Twelve original runs returned normally and passed their per-run audits. Final campaign, mechanism and replication audits remain pending; C6/C8/D6 are unfinished. This is development/protection, not confirmation.

|Role|Arm|Paid seconds|Physical U|Global L|Signed gap|Certificate|
|---|---|---:|---:|---:|---:|---|
|E7|P-GRB|1.469|0.0203825038422|0.0203825038422|3.46944695195e-17|True|
|E7|ENS-C|1.329|0.0203825038422|0.0203825038422|0|True|
|E7|K1-R|5.656|0.0203825038422|0.0203825038422|2.08166817117e-17|True|
|S12|P-GRB|5.656|0.0585639731258|0.0585639731258|4.16333634234e-17|True|
|S12|ENS-C|1.766|0.0585639731258|0.0585639731258|2.70616862252e-16|True|
|S12|K1-R|40.781|0.0585639731258|0.0585639731258|1.87350135405e-16|True|
|D3|P-GRB|297.078|0.0450541615805|0.0415401200124|0.00351404156814|False|
|D3|ENS-C|139.047|0.0450015500556|0.0450015500556|-2.08166817117e-17|True|
|D3|K1-R|297.062|0.0450541615805|0.0438467487043|0.00120741287621|False|
|C2|P-GRB|297.063|0.829963413172|0.770943500725|0.0590199124463|False|
|C2|ENS-C|113.766|0.829963413172|0.829963413172|1.11022302463e-15|True|
|C2|K1-R|297.078|0.829963413172|0.797088381296|0.0328750318758|False|

Completed paid cost 1497.751000s; 45 Optimize starts / 45 returns. No prior qualification is charged again.

E7 ENS/P is near under the frozen practical rule. S12 ENS retains the nonzero small-role repair. D3 and C2 ENS certify while current P and K1 remain open at300s. K1 still improves P gaps on both, so ENS preserves those advantages by obtaining a certificate. The exact classification tables await the frozen final audit.

All four ENS starts finish25 decoded paths. E7 accepts one equal-net exchange and one subsequent quantity move; S12/D3/C2 accept no neutral moves. Their full-method gains cannot be causally assigned to the added exchange. Actual Start mapping/readback/native acceptance awaits the closed-campaign mechanism audit.

Original driver session22846 / PID49028 continues serially. Never restart it or rerun completed producers. Current state is in runtime_checkpoint.json and the live campaign summary.

## C6 complete; final stage audits still pending

All three C6 arms return normally and pass per-run audits at the common600s cap; all remain open.

|Arm|Paid seconds|Physical U|Global L|Signed gap|
|---|---:|---:|---:|---:|
|P-GRB|597.109|1.68910073221|1.37508782921|0.314012903008|
|ENS-C|597.156|1.68604175628|1.53661450055|0.149427255735|
|K1-R|597.125|1.68915723795|1.49847984643|0.190677391518|

ENS improves P gap52.413657% and K1 gap21.633470%, with both better U and stronger L against each. Unclipped K1/P advantage retention is1.334454654. This600s exposed protection does not establish long-window generalization.

All15 completed runs are normal/valid, 56 Optimize starts/returns and3289.141000s paid. C8 and the D6 repeat remain. ENS C6 accepts no neutral move, performs one quantity move and exhausts its controller; do not attribute the full-method gain to an accepted exchange.

## C8 complete; D6 repeat active

All three C8 arms return normally and pass per-run audits at600s; all remain open.

|Arm|Paid seconds|Physical U|Global L|Signed gap|
|---|---:|---:|---:|---:|
|P-GRB|597.063|0.806818916787|0.576956749593|0.229862167194|
|ENS-C|597.062|0.806689827932|0.668942064172|0.13774776376|
|K1-R|597.110|0.801649961457|0.629319151851|0.172330809606|

ENS improves P gap40.073756% with both bounds better. Against K1, U is worse by0.00503986647479 but L is stronger by0.039622912321; gap improves20.067825%. Unclipped K1/P advantage retention is1.601116457. This mixed U/L direction is retained.

All18 completed runs are normal/valid, 67 Optimize starts/returns and5080.376000s paid. Original D6 P/ENS/K1 repeat now runs at3600s each; session22846 remains the same original driver. Latest ordinary weekly availability54%; no reset. Final audits remain pending.
## Completed D3/C2 cost attribution before final campaign audit

These fields are read from the four original normal `result.json` files in
`campaign/local_raw/08_D3_ENS-C`, `09_D3_K1-R`, `11_C2_ENS-C` and
`12_C2_K1-R`. Their per-run audits have passed; full mechanism review remains
pending. Reported native totals explain the completed runs and are never
subtracted from formal paid time or used to create a counterfactual endpoint.

|Role / arm|Paid whole seconds|Startup seconds|Exact-phase start|Native solver seconds|Startup physical F|Outcome|
|---|---:|---:|---:|---:|---:|---|
|D3 ENS|139.047|0.0298273|0.0342756|138.738999844|0.0781153026105612|nonzero certificate|
|D3 K1|297.062|2.0891961|2.0928606|294.717999697|0.049468682614419446|open|
|C2 ENS|113.766|0.0420530|0.0468946|112.969000101|0.837091467554702|nonzero certificate|
|C2 K1|297.078|2.7168636|2.7229749|293.636000156|0.8299634131717752|open|

K1 starts with a better physical objective on both roles, and spends almost
the entire common cap in the native proof core. The observed complete-method
certificate gains therefore cannot be described solely as saved HGA seconds
or zero-objective termination. This does not isolate the causal effects of
the startup witness, Start submission, formulation and downstream AM path.
Neither ENS trace accepts a neutral relocation/exchange here, so these gains
are not evidence that an accepted equal-net exchange caused the repair.
