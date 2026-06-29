# `moderate_seed3301` Certificate Attempt

`moderate_seed3301` is the priority noncertified V20/M3 stress row for the
sealed pipeline round.

The sealed run uses the same command template as every other row:

```powershell
build\ExactEBRP.exe --method gcap-frontier `
  --algorithm-preset paper-exact-v20-certificate `
  --paper-run-sealed true `
  --input reference\hard_stress\V20_M3\moderate_seed3301.txt `
  --lambda 0.15 --T 3600 --time-limit 7200 `
  --out results\sealed_paper_pipeline_round\raw\moderate_seed3301.json
```

The final restored sealed-row attempt did not produce a final JSON before it
was externally stopped after exceeding its intended sealed-row evidence budget.
Its progress log is preserved in:

```text
results/sealed_paper_pipeline_round/raw/moderate_seed3301.progress.csv
```

The last progress checkpoint was still in adaptive splitting:

- last event: `adaptive_split_child_19`;
- incumbent UB: `0.0491525526647`;
- current LB: `0.00921610362464`;
- reported gap: `0.8125`;
- unresolved intervals: `10`.

An earlier pre-restore diagnostic attempt did reach automatic interval-oracle
closure. That evidence was moved out of `raw/` so the paper audit cannot mistake
it for the final sealed row. It remains diagnostic only:

- blocking leaf id: `1`;
- gamma range: `[0.0122881381662, 0.0245762763324]`;
- oracle basis: `interval_exact_cutoff_mip_timeout`;
- solver status: time limit exceeded;
- best oracle bound: about `0.048285646403`;
- incumbent UB: `0.0491525526647`.

Because neither the final sealed run nor the earlier diagnostic oracle closed
the blocking leaf, no focused oracle evidence is merged into a full certificate.
The row is useful interval-level evidence, but it is not a paper certificate.
