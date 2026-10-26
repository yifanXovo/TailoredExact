# Round120 fixed native proof experiment

**ADVANCE_NATIVE_PROOF_DISJUNCTION_TO_CONFIRMATION**. Full core admission and all fixed N40 follow-up obligations completed with preserved finite complete-method and conditional-information signals.

MB-D1 uses one binary root selector and three static pre-Optimize rows from this run's paid complete root-child LPs. MB-D0 removes only conditionality while retaining the common floor and identical added column/row count. Cold P-GRB is primary; frozen M-B is the direct complete-method control. ENS-C remains default and R119 MB-PC remains stopped.

F2 retains the same nonzero original-problem certificate with lower D1 T_produce than M-B and D0. C2 D1/M-B is a severe LOSS and D1/P a nonsevere LOSS; the fixed admission gate still holds. All N40 methods remain open: D1 improves own U and gap, while its lower bound is weaker than M-B and D0. This supports only the stated finite confirmation stage, not a V40 proof closure or a default change.

All 12 current formal positions use PE `5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba` and the pinned Gurobi13.0.2 DLL. No historical incumbent, bound or diagnostic Start entered a formal run.

| Role | Method | own U | qualified L | signed gap | Original certificate | T_produce | T_verify | T_total |
|---|---|---:|---:|---:|---|---:|---:|---:|
| F2 | P-GRB | 0.8659435203 | 0.7621151437 | 0.1038283766 | False | 1172.03135 | 1.6428501 | 1173.6742 |
| F2 | M-B | 0.8659435203 | 0.8659435175 | 2.862223125e-09 | True | 774.409291 | 4.9569598 | 779.366251 |
| F2 | MB-D0 | 0.8659435203 | 0.8659434978 | 2.254410592e-08 | True | 476.407599 | 4.571606 | 480.979205 |
| F2 | MB-D1 | 0.8659435203 | 0.8659435203 | 1.776356839e-15 | True | 208.144945 | 3.4013215 | 211.546267 |
| R98-C2 | MB-D1 | 0.2073016379 | 0.1895141275 | 0.01778751048 | False | 1771.83686 | 8.6712112 | 1780.50807 |
| R98-C2 | MB-D0 | 0.215940483 | 0.1900472132 | 0.02589326988 | False | 1770.58625 | 8.5832497 | 1779.1695 |
| R98-C2 | M-B | 0.1946348157 | 0.1906619659 | 0.003972849784 | False | 1770.75891 | 6.4602589 | 1777.21917 |
| R98-C2 | P-GRB | 0.1983028486 | 0.1866225684 | 0.01168028023 | False | 1770.55118 | 0.7130726 | 1771.26425 |
| N40-R1-S | M-B | 0.7822196776 | 0.573644234 | 0.2085754435 | False | 5371.87058 | 14.6074009 | 5386.47798 |
| N40-R1-S | MB-D1 | 0.75516598 | 0.5693519797 | 0.1858140003 | False | 5370.61724 | 19.5761559 | 5390.1934 |
| N40-R1-S | P-GRB | 0.8837281542 | 0.3511463954 | 0.5325817588 | False | 5370.72619 | 0.9581865 | 5371.68438 |
| N40-R1-S | MB-D0 | 0.7884056617 | 0.5698623843 | 0.2185432774 | False | 5370.68949 | 21.2070895 | 5391.89658 |

| Role | Pair | Classification | Severe regression | Basis |
|---|---|---|---|---|
| F2 | MB-D1/M-B | WIN | False | both_complete_certificate_time |
| F2 | MB-D1/P-GRB | WIN | False | candidate_only_complete_certificate |
| F2 | MB-D1/MB-D0 | WIN | False | both_complete_certificate_time |
| F2 | MB-D0/M-B | WIN | False | both_complete_certificate_time |
| F2 | MB-D0/P-GRB | WIN | False | candidate_only_complete_certificate |
| F2 | M-B/P-GRB | WIN | False | candidate_only_complete_certificate |
| R98-C2 | MB-D1/M-B | LOSS | True | both_uncertified_absolute_materiality |
| R98-C2 | MB-D1/P-GRB | LOSS | False | both_uncertified_absolute_materiality |
| R98-C2 | MB-D1/MB-D0 | WIN | False | both_uncertified_absolute_materiality |
| R98-C2 | MB-D0/M-B | LOSS | True | both_uncertified_absolute_materiality |
| R98-C2 | MB-D0/P-GRB | LOSS | True | both_uncertified_absolute_materiality |
| R98-C2 | M-B/P-GRB | WIN | False | both_uncertified_absolute_materiality |
| N40-R1-S | MB-D1/M-B | WIN | False | both_uncertified_absolute_materiality |
| N40-R1-S | MB-D1/P-GRB | WIN | False | both_uncertified_absolute_materiality |
| N40-R1-S | MB-D1/MB-D0 | WIN | False | both_uncertified_absolute_materiality |
| N40-R1-S | MB-D0/M-B | TIE | False | both_uncertified_absolute_materiality |
| N40-R1-S | MB-D0/P-GRB | WIN | False | both_uncertified_absolute_materiality |
| N40-R1-S | M-B/P-GRB | WIN | False | both_uncertified_absolute_materiality |

| Role | Method | LP / MIP calls | H seconds | LP native seconds | MIP native seconds | Recorded rows / columns / nonzeros |
|---|---|---:|---:|---:|---:|---|
| F2 | P-GRB | 0 / 1 | 0 | 0 | 1169.887 | 3689/1591/16490 |
| F2 | M-B | 3 / 2 | 0.2609697 | 0.533999681 | 771.309 | 9309/3488/53646, 9309/3488/54313 |
| F2 | MB-D0 | 3 / 2 | 0.2954681 | 0.521999836 | 473.09 | 9309/3488/53646, 9309/3488/54313, 9312/3489/53671 |
| F2 | MB-D1 | 3 / 2 | 0.2811102 | 0.522000074 | 205.083 | 9309/3488/53646, 9309/3488/54313, 9312/3489/53672 |
| R98-C2 | MB-D1 | 3 / 2 | 3.8812933 | 2.829 | 1757.613 | 31141/8871/194152, 31141/8871/195278, 31144/8872/194188 |
| R98-C2 | MB-D0 | 3 / 2 | 3.79032 | 2.8829999 | 1757.423 | 31141/8871/194152, 31141/8871/195278, 31144/8872/194187 |
| R98-C2 | M-B | 3 / 2 | 3.749822 | 2.79099989 | 1758.343 | 31141/8871/194152, 31141/8871/195278 |
| R98-C2 | P-GRB | 0 / 1 | 0 | 0 | 1769.703 | 10627/4242/50577 |
| N40-R1-S | M-B | 3 / 2 | 1.5323379 | 5.02499986 | 5353.163 | 77498/16132/434348, 77498/16132/434942 |
| N40-R1-S | MB-D1 | 3 / 2 | 1.4998209 | 4.95600033 | 5351.979 | 77498/16132/434348, 77498/16132/434942, 77501/16133/434394 |
| N40-R1-S | P-GRB | 0 / 1 | 0 | 0 | 5369.367 | 23158/8795/114075 |
| N40-R1-S | MB-D0 | 3 / 2 | 1.4781572 | 5.00700021 | 5351.87 | 77498/16132/434348, 77498/16132/434942, 77501/16133/434393 |

Native times are nested inside T_produce. Model construction, installation, online checks, callbacks, output and cleanup remain charged in T_produce; source event clocks and the full residual/closeout partitions are retained. These values are not added to T_produce again.

| Role | Extension | beta0 | beta1 | Root installation seconds | Completed extended calls |
|---|---|---:|---:|---:|---:|
| F2 | MB-D0 | 0.61054726084882072 | 0.88263898591401602 | 0.0821783 | 2 |
| F2 | MB-D1 | 0.61054726084882072 | 0.88263898591401602 | 0.0821125 | 2 |
| R98-C2 | MB-D1 | 0.16200538216771196 | 0.31701608437476442 | 0.2858436 | 2 |
| R98-C2 | MB-D0 | 0.16200538216771196 | 0.31701608437476442 | 0.2942383 | 2 |
| N40-R1-S | MB-D1 | 0.47897456977717712 | 0.78754719368799719 | 0.6413341 | 2 |
| N40-R1-S | MB-D0 | 0.47897456977717712 | 0.78754719368799719 | 0.6333349 | 2 |

All six fixed pairs per role are shown. Complete certificates have priority and original materiality/severe rules were replayed on all nine R119 published pairs. Signed gaps are retained; two open endpoints do not predict a final certification-time ratio.

The complete diagnostic LPs have equal D0/D1 original objectives (.6105472608488204 on F2 and approximately .162005382167712 on C2), but full feasible D0 primal points violate the actual D1 row by .10368547236475856 and .03176182992417159. Every original route/resource/inventory row and bound was checked. This proves nonredundancy in the extended (original variables, h) LP; it alone establishes neither a stronger original-objective minimum nor an integer-search or complete-method gain.

Static installation, complete-LP nonredundancy, sampled native row activity, actual native objective/physical F, and h fixing/branching are distinct. Actual native samples and model/Start/size/call/epoch identities are retained in mechanism_account.json and reconstructed tables. h fixing/branching is unknown; an incumbent h value or numeric crossing is not its observation. The original target/terminal requests and necessary epoch/domain artifacts remain; no entire-tree preservation or single-Optimize complete method is claimed.

D1/D0 is the finite conditional-information comparison. D0/M-B mixes the common floor and selector effects. D0 is an ablation and is not promoted after results. 
The four fixed N40 positions completed in their predeclared order; N40 is a known difficult follow-up, not an independent sample.

The original-core R119 tail supplement passed in R120 with zero Optimize and preserves the old R119 failed test. The first new zero-Optimize native qualification failed a synthetic LP-text objective-offset expectation. Its raw files/cost are retained; actual ObjCon/API/MPS qualification then passed without changing the production PE. Complete independent physical enumeration/actual matrix embeddings, all-column types/Starts, one real C++ chain and six H100 CLI positions passed. The chain certified nonzero1.2 using three original LPs and one extended MIP. H100 D0/D1 each submitted binary-h complete Starts and used the same extended SHA for original target and terminal. All full H comparisons agree.

Budget: 31/40 conservative starts, 32358.098362/48000 outer seconds; qualification 16/16 and 817.811069/3600. Failed starts and necessary supervision/verification are charged; native nested times are not added again. Pure compilation, mathematics, packing/export/recovery are separately recorded engineering work. Human time is unknown, not zero.

These are finite known-role numerical results. Standard disjunction/convexification is not new general theory. No default promotion, merge, parameter grid, automated next research or broad stability claim follows this exit. Scientific payload, export/recovery, separate extra review and remote receipts are separate artifacts.
