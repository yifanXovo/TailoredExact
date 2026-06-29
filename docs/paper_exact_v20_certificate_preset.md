# Paper Exact V20 Certificate Preset

`--algorithm-preset paper-exact-v20-certificate` is the sealed
paper-candidate exact portfolio for regenerated V12 rows and the V20/M3 hard
stress suite.

## Components

- Native HGA-TGBC generates the initial incumbent inside the run.
- Archive scanning is disabled.
- The full Gini-frontier ledger covers the improving Gini range.
- V20-safe relaxation evidence is used for lower bounds.
- Large compact-flow mip-light relaxation with connectivity is available for
  large rows.
- Automatic interval-oracle closure is enabled for unresolved final leaves.
- Automatic BPC fallback remains off unless explicitly requested; BPC lower
  bounds require exact pricing closure before they can certify a leaf.

## Sealed Command

```powershell
build\ExactEBRP.exe --method gcap-frontier `
  --algorithm-preset paper-exact-v20-certificate `
  --paper-run-sealed true `
  --input <instance> --lambda 0.15 --T 3600 `
  --time-limit <budget> --out <raw.json>
```

No known UB, archive result, external incumbent JSON, manual focused interval,
or instance-specific gamma range is passed to this command.

## Status

The preset is an exact portfolio candidate, not a pure BPC-only algorithm.
Successful certificates may be relaxation-only full-frontier certificates or
full-frontier certificates completed by exact interval cutoff MIP
infeasibility certificates. Noncertified rows must report the exact remaining
open leaves and oracle/BPC status.
