# Round131 benchmark assessment

Execution: **COMPLETE**. Stage exit: **`FINAL_VERSION_BENCHMARK_COMPLETE`**. Scientific assessment: **`DIRECT_CERTIFICATION_SUPPORT_WITH_FINITE_LIMITS`**.

On the six known SC problems at two Seeds (12 matched observations), S2 and P certify 10 and 5 observations, respectively; the strict S2/P directions are 10 Win, 0 Lose, 0 Tie and 2 undetermined. The tiny layer records 9 strict Win, 3 strict Lose and 0 Tie across twelve matched observations, with 0 observed >=10-second delays and 0 P-only certification risks. At V35, S2 and P have 0 and 0 nonzero certificates across two Seed0 observations, with 0 P-only cases; both-open cases have unknown final certification-time ordering.

The adopted method remains the frozen S2/MS2. R129 selection and R130 adoption are settled. This study compares only full S2 and original cold P, using the same frozen E3/DLL, complete independently paid workflows and unchanged numerical/time policies. All ten inputs were already exposed. There is no fresh, blind or unseen validation claim, tuning, production compilation, algorithm change or instance-wise dispatch.

## A: primary final-version certification panel

Six original SC problems, two Seeds, 24 arms and 12 S2/P comparisons. The full six-problem set includes SC-C20-S. S2 truly certifies faster in the both-certified intersection on: **SC-C15-S / S0, SC-C15-S / S1, SC-B15-S / S0, SC-B15-S / S1, SC-C15-B / S0**. S2 alone certifies on: **SC-C15-B / S1, SC-B20-S / S0, SC-B20-S / S1, SC-B20-U / S0, SC-B20-U / S1**. Actual strict losses: **none**. Both-open observations: **SC-C20-S / S0, SC-C20-S / S1**. Every both-open pair is UNDETERMINED, regardless of its U/L advantage. The full endpoint/clock table in Supplement S and arms.csv gives the actual values.

| Known problem / Seed | P T_cert (s) | S2 T_cert (s) | Class | S2/P direction | S2 - P (s) | P / S2 |
| --- | --- | --- | --- | --- | --- | --- |
| SC-C15-S / S0 | 460.809 | 33.167 | BOTH_CERTIFIED | Win | -427.642 | 13.894 |
| SC-C15-S / S1 | 469.536 | 35.538 | BOTH_CERTIFIED | Win | -433.998 | 13.212 |
| SC-B15-S / S0 | 12.875 | 2.851 | BOTH_CERTIFIED | Win | -10.024 | 4.515 |
| SC-B15-S / S1 | 16.181 | 2.245 | BOTH_CERTIFIED | Win | -13.936 | 7.208 |
| SC-C15-B / S0 | 242.256 | 57.928 | BOTH_CERTIFIED | Win | -184.328 | 4.182 |
| SC-C15-B / S1 | open | 33.444 | S2_ONLY_CERTIFIED | Win | null | null |
| SC-B20-S / S0 | open | 982.279 | S2_ONLY_CERTIFIED | Win | null | null |
| SC-B20-S / S1 | open | 676.371 | S2_ONLY_CERTIFIED | Win | null | null |
| SC-C20-S / S0 | open | open | BOTH_OPEN | UNDETERMINED | null | null |
| SC-C20-S / S1 | open | open | BOTH_OPEN | UNDETERMINED | null | null |
| SC-B20-U / S0 | open | 26.893 | S2_ONLY_CERTIFIED | Win | null | null |
| SC-B20-U / S1 | open | 15.998 | S2_ONLY_CERTIFIED | Win | null | null |

Only the 5 explicitly both-certified observations enter the conditional geometric mean P/S2=7.578. It does not summarize the entire panel. Absolute seconds and ratios use the unrounded authorities; the table display is rounded. A/C materiality is symmetric, slower minus faster >= max(10 seconds, .1*faster), and does not change strict Win/Lose. Repeated material reverse roles: **none**. Single-sided certificates are never excused by a time threshold.

## B: final-S2 absolute tiny overhead

Two known problems, three Seeds and two opposite-order matched repeats per Seed: 24 arms, twelve observations. This layer is not pooled with A/C. Observed >=10-second S2 delays: **0**; P-only certification risks: **0**. At least two of six observations meet the delay threshold on: **none**. Within the same Seed, both valid repeats meet it at: **none**. These are observed repetitions, not a statistical noise theorem. A 0.1-second loss remains Lose. Fewer than two valid repeats never yield an estimated fluctuation range. SM-B10-B is a legal empty-fleet/structurally easy role and does not represent all tiny difficulty.

| Known problem / Seed / repeat | P T_cert (s) | S2 T_cert (s) | Class | S2/P direction | S2 - P (s) | P / S2 |
| --- | --- | --- | --- | --- | --- | --- |
| SM-C8-S / S0 / R1 | 5.568 | 2.645 | BOTH_CERTIFIED | Win | -2.923 | 2.105 |
| SM-C8-S / S0 / R2 | 5.143 | 2.865 | BOTH_CERTIFIED | Win | -2.278 | 1.795 |
| SM-C8-S / S1 / R1 | 3.904 | 3.227 | BOTH_CERTIFIED | Win | -0.677 | 1.210 |
| SM-C8-S / S1 / R2 | 4.197 | 2.845 | BOTH_CERTIFIED | Win | -1.352 | 1.475 |
| SM-C8-S / S2 / R1 | 4.611 | 3.781 | BOTH_CERTIFIED | Win | -0.830 | 1.220 |
| SM-C8-S / S2 / R2 | 4.307 | 4.126 | BOTH_CERTIFIED | Win | -0.180 | 1.044 |
| SM-B10-B / S0 / R1 | 0.778 | 0.792 | BOTH_CERTIFIED | Lose | 0.014 | 0.983 |
| SM-B10-B / S0 / R2 | 1.122 | 0.461 | BOTH_CERTIFIED | Win | -0.661 | 2.433 |
| SM-B10-B / S1 / R1 | 1.067 | 0.511 | BOTH_CERTIFIED | Win | -0.556 | 2.088 |
| SM-B10-B / S1 / R2 | 0.708 | 0.801 | BOTH_CERTIFIED | Lose | 0.093 | 0.883 |
| SM-B10-B / S2 / R1 | 0.794 | 0.800 | BOTH_CERTIFIED | Lose | 0.006 | 0.992 |
| SM-B10-B / S2 / R2 | 1.129 | 0.461 | BOTH_CERTIFIED | Win | -0.667 | 2.447 |

| Problem | Both-cert n / 6 | Median S2-P (s) | S2-P range (s) | P median [range] (s) | S2 median [range] (s) |
| --- | --- | --- | --- | --- | --- |
| SM-C8-S | 6 | -1.091 | -2.923 .. -0.180 | 4.459 [3.904, 5.568] | 3.046 [2.645, 4.126] |
| SM-B10-B | 6 | -0.275 | -0.667 .. 0.093 | 0.930 [0.708, 1.129] | 0.652 [0.461, 0.801] |

tiny_summary.json retains all six directions and each Seed's two repeats, with valid counts and exact ranges. These are six actual observations per known input, not six new inputs.

## C: finite V35 scope boundary

The two complete original R122 V35 roles use Seed0 only and fresh full 2400-second contracts. They are not continuations of old trees or merged short-window development clocks. Final S2 nonzero certifications: **0/2**. This does not expand the observed nonzero certification size to V35. For any both-open pair, **final certification-time ordering is unknown**. U/L/gap may describe the observed endpoints only. One Seed supplies no two-Seed robustness statement.

| Known problem / Seed | P T_cert (s) | S2 T_cert (s) | Class | S2/P direction | S2 - P (s) | P / S2 |
| --- | --- | --- | --- | --- | --- | --- |
| PB-C35-U / S0 | open | open | BOTH_OPEN | UNDETERMINED | null | null |
| PB-B35-B / S0 | open | open | BOTH_OPEN | UNDETERMINED | null | null |

## Open endpoints, without certification ordering

The following are the actual both-open endpoints. The relation is descriptive only: no certification Win, Tie, cap-based speedup or extrapolated final solve time is assigned.

| Layer / problem / Seed | S2 U | S2 L | P U | P L | Observed endpoint relation |
| --- | --- | --- | --- | --- | --- |
| A / SC-C20-S / S0 | 0.216430184034 | 0.208682789507 | 0.280579842119 | 0.161053464025 | S2 lower U; S2 higher L |
| A / SC-C20-S / S1 | 0.216733997978 | 0.208247979072 | 0.234721130013 | 0.162552496354 | S2 lower U; S2 higher L |
| C / PB-C35-U / S0 | 0.18370155687 | 0.0847282772542 | 0.174771887556 | 0.0597029031719 | P lower U; S2 higher L |
| C / PB-B35-B / S0 | 0.246504470413 | 0.121942123502 | 0.305555778217 | 0 | S2 lower U; S2 higher L |

## Version migration and limits

A is the principal final-version SC table. R126/R127 full three-station M-B tables remain historical and are not relabelled S2. B fills the final-S2 tiny-version gap. R129's four inputs retain their prospective-at-selection role and are now known; its protection input is separate. R130's complete PS and S2R attribution directions, including reversals/open cases, remain separate. R127/R128 MS2 development uses its original build and clocks. Earlier R122/R123 V50 and longer-window MB/ENS results remain predecessor evidence. This round measures a maximum V35 with one Seed in C and validates neither final S2 at V50/V60 nor universal dominance or statistical significance.

The ten known inputs come from two existing safe station tables. Inventories, targets, weights and fleets are constructed; geography retains original compact/regional Euclidean rules. Scenario means service-station total shortage/balance/surplus, excluding depot. A has four shortage, one balanced and one surplus role; B has one shortage and one easy balanced role; C has one surplus and one balanced role. Source, geography, size, fleet and physical T vary together, with station overlap. These are not a factorial design, IID city samples or independent unseen validation. Only lambda=.15 is tested. The finite denominators are A=6 inputs/12 observations, B=2/12, C=2/2; no weighted total Win or cross-round average speedup is supplied.

There is no new component or causal test. The paper may describe a tailored branch-and-cut framework with Gini-interval decomposition while distinguishing the custom representation/valid rows/H/controller from Gurobi's native branching and cuts. Decomposition exists; R130 did not show repeated material net outer-package gains. R127 tuned-P negative holdout, earlier mixed same-H outcomes, and R128/R129 reverse/open observations remain visible.

The final-version evidence gap is closed within this finite design. Deliver the limited paper statement for substantive review and end this round; no extra ablation or selection cycle follows.
