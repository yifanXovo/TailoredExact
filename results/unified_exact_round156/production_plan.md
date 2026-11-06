# Prospective Round156 paid producer comparison

The prepared candidate uses the same original RN model and gap, with a
uniform 16384-node capacity from its own initial DP, and proof-only R154
consumption. It is not frozen/admitted until the matched oracle comparison,
actual evidence readback, fresh helper checks and complete smoke lifecycles
pass. Old E keeps RN4096 and its existing entry. Stable B stays default.

Preselected full panel: RX35 B/E/Eplus 7200 seconds each; NB35 E/Eplus 2400;
RB35 E/Eplus 2400; RX20 E/Eplus 1200. Physical horizons and original lambdas
are unchanged. All use one rebuilt PE, Seed0/Threads1, own-H20260626,
pair-only AM .08, depth8 and minimum width1e-4. Each complete arm performs
its own H and helper, with no offline or cross-arm injection. No mechanism
switch depends on elapsed seconds. The whole-method deadline remains.

The new flag --round156-rn-refinement on requires enabled proof-only E and
the separately hash-bound R156 helper response with node capacity16384.
Its parameter/root logs declare that capacity and rule. Default/off and
the original R153 helper protocol retain the old capacity and behavior.
All three translation units using Round153Controls must be rebuilt.
