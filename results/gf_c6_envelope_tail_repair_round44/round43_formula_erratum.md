# Round 43 formula erratum

Round 43's official executable computed the split diagnostic recorded in the
historical `D_d` ledger column as

`D_R43(I) = V_residual(I) / (|I| * max(U - L_I, epsilon_cert))`.

The original mathematical mechanism note incorrectly described that value as
`V_residual / V_local`. Those quantities are not equal. The latter is the
separate profile diagnostic

`P_profile(I) = V_residual(I) / max(V_local(I), epsilon_volume)`,

which equals `1 - tau_d(I)` when `V_local` is positive.

All official Round 43 decisions and numerical outcomes used the executable
formula. The sealed raw results are therefore internally consistent and require
no rerun. In particular, the selected threshold `rho=0.10` must be interpreted
against `D_R43`, not against `P_profile`. Historical raw result and decision
ledgers have not been rewritten.

Round 43 also did not establish that lifted cuts were unnecessary. The accurate
statement is: the predeclared lifted-cut entry condition was not triggered, so
lifted cuts were not tested in Round 43.

## Documentation hash audit

Hashes are SHA-256 over LF-normalized repository text.

| Path | Before | After |
|---|---|---|
| `results/gf_k1_k4_envelope_refinement_round43/mathematical_mechanism_note.md` | `4a192f74357a14c1df9494cc765ab6cc1948a5c274ace6a758bbaa0a38c032cd` | `aa2493fdf4cbd8d16478febd6fd9b221ff8f44ce823eb9e94bb340796e9bec8f` |
| `results/gf_k1_k4_envelope_refinement_round43/final_report.md` | `65c9809496390a628fd764546366d34a4d8df3d45c54083bfdd9357ca2d8b910` | `43319c1f0442cba546311a3272b372ca6907be49e42cd150a945633849fbd740` |
| `scripts/finalize_round43.py` | `6fbb7b6c3185a70fe54a88cc9f6177b742f3b95440a3c0e6d38cc96947e80865` | `da1eb185a1b56ce39058be2b74ed1ac2a03e45069bce04edcbd0504ecc82f23f` |

The implementation source was already correct; only documentation and the
report-generation template changed.
