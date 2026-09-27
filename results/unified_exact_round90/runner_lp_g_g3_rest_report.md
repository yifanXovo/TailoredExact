# Round90 LP-G G3 rest: twelve-arm result

The single signed `run-rest` call completed all 12 preregistered arms in order (D3, C2, D7, U6, F5, F6; ENS-C and LP-G each). All process exits were 0, all offline audits passed, and all six new cross-arm contradiction checks passed. No identity, resource, process, or prespecified severe-regression stop fired. The frozen runner, preregistration, candidate executable, and seven source hashes still match the prepared identity. No arm was skipped or retried.

The table gives the physically audited upper bound U and same-arm global lower bound L. A `yes` certificate means a normally finalized original-problem proof; `open` means the full 1,200 s run ended at the external-tree time limit, with valid observed bounds but **no convergence certificate**. Full precision, per-arm prelaunch/end-to-end/audit costs, physical witness counts, and split counts are in `runner_lp_g_g3_rest_table.csv`.

| Role | Arm | Process wall (s) | U | L | Gap | Certificate |
|---|---|---:|---:|---:|---:|---|
| D3 | ENS-C | 153.984 | 0.04500155005562836 | 0.04500155005562838 | −2.08e−17 | yes |
| D3 | LP-G | 154.234 | 0.04500155005562836 | 0.04500155005562838 | −2.08e−17 | yes |
| C2 | LP-G | 112.141 | 0.8299634131717752 | 0.8299634131717752 | 0 | yes |
| C2 | ENS-C | 123.813 | 0.8299634131717752 | 0.8299634131717741 | 1.11e−15 | yes |
| D7 | ENS-C | 1197.172 | 0.23660241228050372 | 0.20335723151531615 | 0.033245180765187565 | open |
| D7 | LP-G | 1197.140 | 0.2366966782192034 | 0.20335723151531615 | 0.03333944670388725 | open |
| U6 | LP-G | 1197.125 | 0.153936747638459 | 0.12892489626165785 | 0.025011851376801147 | open |
| U6 | ENS-C | 1197.157 | 0.15232093301794666 | 0.12905844168500294 | 0.023262491332943724 | open |
| F5 | ENS-C | 1197.547 | 0.3295369905242713 | 0.281414298078084 | 0.04812269244618733 | open |
| F5 | LP-G | 1197.172 | 0.3247433832620608 | 0.2805875644544576 | 0.04415581880760322 | open |
| F6 | LP-G | 1197.157 | 0.29294130869051743 | 0.2761322758793161 | 0.01680903281120133 | open |
| F6 | ENS-C | 1197.172 | 0.29294130869051743 | 0.27680090872387575 | 0.016140399966641683 | open |

Among the two certified pairs, D3 certification time was effectively equal (+0.250 s, +0.16% for LP-G); C2 LP-G certified 11.672 s earlier (−9.43%). At the common censored deadline, the LP-G gap was 0.28% larger on D7, 7.52% larger on U6, 8.24% smaller on F5, and 4.14% larger on F6, relative to same-build ENS-C. U6 is the largest observed gap regression; it remains below the preregistered serious signal requiring both >50% relative and >0.01 absolute excess. The F5 improvement and C2 speed difference are single paired runs, not general performance claims. Historical Round88 P-GRB evidence is bound in preregistration as **unpaired historical context** and contributes no Round90 timed arm.

The six LP-G arms recorded 13 eligible proposals: 10 current-optimal-parent LP-G points and three midpoint fallbacks. Every proposed pair of child LPs completed, followed by the AM decision. D3, D7, U6, and F5 each observed a current-point proposal, native-target parent requeue, and same-epoch reuse, with no atomic split. D3 then completed the terminal parent path and certified the original problem. D7, U6, and F5 only entered/requested the terminal parent MIP path; their deadline-censored endpoints remain open, so the ledger's `proposed_exact_parent_closure` is **not** evidence of final proof closure. C2 adopted two atomic child transactions: its root used the current parent LP-G point, while its next adopted split used a midpoint fallback; the third proposal reached a certified closure. F6 adopted one atomic root split at the current LP-G point, then a midpoint-fallback proposal entered the terminal child path but remained open at the deadline. Thus **three** atomic splits were realized in rest, including two at actual LP-G points. All observed epochs were 0; incumbent-epoch invalidation remains unexposed. Current canonical LP bytes, optimize rows, and proof-ledger joins were audited; complete historical LP-byte archives are not present, so the receipts do not purport to prove every past model byte independently.

Editorial correction after root review: the earlier wording called D7/U6/F5's terminal-parent request an “exact parent closure.” Only D3's normally finalized certified endpoint supports that conclusion. This correction changes no raw data, bound, certificate, cost, or solver outcome.

The one outer `run-rest` launch-to-exit wall was **10,132.2608227 s**. Nested native process walls sum to **10,121.814 s**; prelaunch is **3.468 s**, yielding **10,125.282 s** fully observed per-arm end-to-end. The remaining **6.9788227 s** belongs to runner postexit audit, cross-arm checks, and wrapper work. Offline per-arm audit reports **6.4822515 s**, nested within that outer cost and not added twice. `runner_rest_completion.json` records 12/12 completion, `summary.jsonl` and each arm's `raw/` directory preserve endpoints and evidence, and `rest_outer_001.*` preserve the exact outer command and streams. No new solve, test, build, or archive was run for this report.
