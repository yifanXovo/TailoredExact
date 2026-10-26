# Actual master transformation

`variables.csv` in each run lists every native index/name, old type, new type
and relaxation flag. Only the constructed index set changes type. Bounds,
all objective coefficients, the objective constant and every old row remain.

| Actual block | Original type | Master type | Purpose |
|---|---|---|---|
| x_k_i_j, every original i!=j arc | binary | continuous [0,1] | Necessary fractional topology/time/capacity |
| load_k_i, every original station | integer [0,Qk] | continuous same bounds | Necessary prefix-load rows |
| ord_k_i | continuous | unchanged | Already continuous; no new relaxation |
| conn_k_i_j where the original F0 declares it | continuous | unchanged | Already continuous connectivity flow |
| z_k_i | binary | unchanged | Integer unique vehicle service assignment |
| mode_k_i | binary | unchanged | One-direction service |
| p_k_i,d_k_i | integer | unchanged | Original integer operations |
| Y_i | integer | unchanged | Final inventory |
| state_i_y in the actual root domain | binary | unchanged | One-hot inventory and exact integer G product |
| state_g_i_y,zprod_i | continuous | unchanged | Perspective/product representation |
| G,r_i,e_i,h_i_j and other original F0 auxiliaries | continuous | unchanged | Original objective epigraph/valid estimators |

Newly relaxed count is M*((V+1)*V+V). Order and connection counts are never
included in that count. All state columns in the original root domain must
remain binary; a selected state missing from the domain is an ERROR.

Every original route/connection/load/time/inventory/Gini/penalty/service row
is retained. F0 strengthening, movement reachability, transfer compatibility,
handling necessary rows and vehicle label symmetry remain valid for original
integer solutions in the declared metric domain. They need not be exact at
fractional topology points. Exhaustive historical V<=12 subset-duration rows
remain off, matching clean F0. R101/102/103/104 experimental pools are off.
No necessary-resource cut family is added by this round.

The root uses paid U0, gamma_L=0, gamma_U=min(1,U0), cutoff=U0, epsilon=0.
The complete original physical seed is independently checked and separately
mapped in the sparse representation required by the original mapper. Every
actual original linear row is audited against its complete mapped Start.
This non-strict domain contains the known seed and every original optimum.
It is neither P-GRB nor an AM leaf. Original P-GRB source/model construction
is not changed by the default-off R105 dispatch.
