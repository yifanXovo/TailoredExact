# Part 1 iterative research log

1. Frozen the 10-instance diagnostic panel before K1 results: easy P-GRB wins, the major medium regression, both hard P-GRB wins, the numerical endpoint, the strongest C6 control, and additional medium/hard C6 wins.
2. K1-single reduced independent proof jobs on the major witness from 8 to 1 and reduced Work from 4373.078 to 3052.420. Runtime fell from 1911.466 to 1414.160 seconds, but remained above P-GRB's 934.687 seconds.
3. Original adaptive split the major root and recreated 4 integer proof jobs, increasing runtime to 1644.581 seconds. This falsified nondecisive `rho` refinement as the recovery mechanism.
4. The decisive revision retained one terminal job on the major witness and completed in 1332.262 seconds with 3053.145 Work.
5. The strong C6 control falsified K1 as a universal replacement. K4 took 82.518 seconds/133.735 Work; K1-single took 432.400 seconds/739.784 Work. The single coarse MIP was genuinely weaker even though it eliminated independent jobs.
6. Final panel result: K1-single, original adaptive, and decisive each win 8/10 against K4. Decisive has the lowest panel total (1917.676 vs 2187.960 seconds), but its 5.24x strong-control slowdown prevents promotion.

Negative results are retained in `k1_vs_k4_comparison.csv`; no candidate was silently replaced.
