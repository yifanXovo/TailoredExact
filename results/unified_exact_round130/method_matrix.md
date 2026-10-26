# Round130 fixed method matrix

The sole proposed method is **GI-TBC (uniform pair-support implementation, MS2)**, table ID **S2**. The selected E2 `ms2` algorithm is unchanged in E3. Historical full M-B and ENS-C measurements keep their original identity. The repository default remains ENS-C; paper reproduction explicitly selects `ms2`.

| ID | Independently paid startup | Actual mathematical backend | Role |
| --- | --- | --- | --- |
| P | no H or external Start | original cold compact, one complete native MIP, defaults | sole primary benchmark |
| PS | full same H; own fully mapped and read-back Start | same original compact as P; normal nonzero path has one native MIP; no project cutoff, strengthening or root LP | same-start control |
| S2 | full same H | unchanged pair support, R, ordered supply, C_G, A/B, Gini interval control | sole paper method |
| S2R | full same H | inclusive `[0,min(U0,(n-1)/n)]`, `F_model<=U0`, pair-only strengthened root; complete LP then MIP, own full Start | outer-control package deletion control |

PS uses the existing `--round112-ens-start-compact` entry with research mode off. S2R uses exactly one `--round127-mode s2-root`; sequential conflicting old mode flags are forbidden by the frozen argv. Only the semantic interval-no-improver proof row is suppressed in S2R. Ordinary MS2 and full MD-R retain their old behavior.

All methods use one frozen E3, original DLL, original physical/numerical settings and complete 1200-second cap. H, mapping, validation, LP/MIP, output and shutdown share the deadline. P receives no other arm's solution. PS and S2R receive no extra budget. The fixed comparison types are S2/P, PS/P, S2/PS, S2/S2R and S2R/PS.

The original declared verified-zero startup scope is retained. A qualified startup-zero branch has no backend exposure and supplies no pure backend attribution. No new zero shortcut is added. Nonzero S2R requires its complete LP+MIP chain; all formal roles here have nonzero own H.

S2/PS measures the complete backend, representation and control increment after matched own H. S2/S2R measures the entire exposed outer control package only when actual H, initial scope, settings and effective root agree. S2R/PS also changes representation, preprocessing and cutoff domain; it is not a pure-cuts experiment. Splits alone do not prove a net benefit.
