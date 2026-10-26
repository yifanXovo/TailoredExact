# Round 50 branching baseline audit

Stage 1 completed all 14 frozen development states with one executable (`e206264c9cac78fedc8c24c0a3b65029616aef8769ee54665dd91c071f4b043f`), one unchanged `interval-mip-v0` policy, and 300-second total-process caps. 10 rows certified and 4 capped honestly (D1, D9, D11, D14). Model fingerprints matched the reconstruction freeze; there were no false certificates or cap violations.

The dominant search signals are excessive node or simplex-iteration burden, delayed native incumbents, and weak post-root-cut bounds on several hard roles. D1 and the tight3102 group show particularly expensive proof trajectories; D13 is dominated by tree size and delayed incumbent despite a comparatively strong root-cut bound. D2 remains an easy negative control. This supports testing only the predeclared uniform semantic priority policies B1-B3. No branch direction, dynamic switching, or per-instance priority is opened.

The classification is derived from `interval_mip_bottleneck_map.csv`, not model size alone. The candidate comparison will use a same-executable 120-second v0 core baseline and all three candidates, followed by a 300-second D1-D14 qualification for only the best screen candidate.
