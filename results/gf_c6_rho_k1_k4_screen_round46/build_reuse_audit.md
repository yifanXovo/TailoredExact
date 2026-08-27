# Round 46 build-reuse audit

- Reusable development build: `build/dev-gurobi-release/`
- One clean official build: `build/official-round46-36033fab4/`
- Generator/compiler: MinGW Makefiles / GNU 15.2.0
- Gurobi: 13.0.2 at `D:/gurobi1302/win64`
- Clean configure time: 2.796 s
- Clean full build time: 312.670 s
- Initial full CTest time: 2.080 s; final full CTest time: 1.94 s
- Official executable SHA-256: `d574b38b2f44ae2aacf92bf685f439354b5a08dbe257b6c399045b98a157871b`
- Algorithmic source changes after executable freeze: none
- Post-freeze script changes: analysis/ranking/reporting only; no official executable invalidation
- Per-rho or per-instance builds: none
- Old `build_round*` directories deleted: none

The complete safe-to-delete inventory is in `build_inventory.csv` (41 directories). No build products are committed.
