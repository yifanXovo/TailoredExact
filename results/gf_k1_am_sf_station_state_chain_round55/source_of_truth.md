# Round 55 source of truth

- Base: `324646af2e253618218812717a53e3e9e9cf1d9c` / `137c7071757957648cc9a9fd2873d35e26ff1231`; draft PR [#112](https://github.com/yifanXovo/TailoredExact/pull/112) remains untouched.
- Branch: `codex/round55-k1-am-sf-station-state-chain`; evidence root: `results/gf_k1_am_sf_station_state_chain_round55/`.
- Stable comparator: K1-AM-SF / `paper-k1-am-sf` / F0-CLEAN.
- Direct development comparator: F0-CLEAN; final benchmark: P-GRB.
- Fixed states: inherited hashed D1-D14 and C1-C9 freezes from Round 53.
- Sealed panels: the unopened 12-row primary and 10-row expansion manifests.
- Candidate menu: conditionally SF-MC4, mandatory VD-P/VD-J, and at most two
  independently proved sparse removals. PC1/PC2 and combinations are gated.

The compact CSV/JSON decisions and hash inventories are authoritative. Raw
native logs may remain local only when inventoried and represented compactly.
Unopened conditional stages are reported as unopened, never as missing rows.
