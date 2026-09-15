# First completed development role: D4

The frozen300-second four-arm queue completed before opening D6. All witnesses,
native settings, interval union and actual model encodings passed independent
checks. Paid initial routes are identical across K1-R/VD-P/LOG.

| Arm | Full wall seconds | Certificate | UB | LB |
|---|---:|---|---:|---:|
| P-GRB |297.062|no|0.506343307565206|0.19593794460085592|
| K1-R |128.938|yes|0.506343307565206|0.5063433073265636|
| VD-P |39.891|yes|0.506343307565206|0.506343307565206|
| LOG |89.313|yes|0.506343307565206|0.5063433075652056|

LOG is30.7% faster than K1-R, but49.422s/123.9% slower than VD-P. Both retain
the major P-GRB protection. This is not repair of a K1-vs-P deficit and not a
reason to accept/reject the whole direction. D6, D3 and C2 remain unmeasured.

Native root LP logs report K1-R0.09394825539, VD-P/LOG0.1140663222. Initial
model rows/columns are4136/1404,4119/1698,4174/1753 respectively. On this domain
LOG replaces214 one-hot selector binaries with55 code binaries and adds55
rows/columns. The common VD-P/LOG LP projection is proved algebraically; this
single logged agreement is supporting numerical evidence.

All three keep the parent, with zero interval splits. VD-P and LOG each use
one mathematical child-bound target MIP then terminal MIP; K1-R directly uses
terminal MIP after three LP probes. Terminal native costs: K1-R126.579s,
VD-P37.362s, LOG86.805s, with24983/7703/22214 nodes. HGA costs are1.976/1.962/
1.956s. Thus the observed LOG-vs-VD-P penalty is principally native search
under the alternative representation, not a startup difference or lost cover.
Binary count reduction alone did not deliver the fastest formulation.

No rule/parameter was changed after this observation. Continue the declared
four-arm D6 comparison at600, then remaining development roles. No confirmation
or long-run expansion is inferred from this one positive protection result.
