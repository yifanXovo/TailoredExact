# Round92 G3 zero-Optimize preparation

The root-admitted command `D:/msys64/ucrt64/bin/python.exe -B scripts/round92_handling_g3.py prepare` ran **once** and exited 0. Its complete external launch-to-exit wall was **0.3234094 s**. Raw stdout/stderr, exact argv, UTC timestamps and real child exit are in `g3_prepare_outer_001.*`. Stdout reports `optimizer_calls: 0`; stderr is empty.

`runner_handling_g3/identity.json` SHA256 is `576c88fa38f08201ec7cfa6be8dc720341f87f9a4a620ab423aa38687929035a`; `preflight.json` SHA256 is `0ca6763c6cd144e90f16147377d68dc20915521888790c10e28f4c2ef23deb04`. Preflight reports candidate binary, 15 source pins, nine harness/input-audit pins and eight actual input identities verified. It created exactly 16 fixed launches in the registered alternating order from E8/ENS-C through F6/ENS-C, with total complete-process cap 12,480 s and four smoke arms. No raw arm directory, model export or Optimize was created. The existing root gate SHA256 was `475672d318d4cfd1e6ebf37f3f6f77bcbe5ef0b89fdae2364221d244f4b088dd`.

A postflight process check found no solver, build or preparation child; the exclusive compute slot was released. This receipt does **not** authorize `run-smoke` or `run-rest`. Each needs the separately signed stage lease, and rest also needs accepted smoke evidence.
