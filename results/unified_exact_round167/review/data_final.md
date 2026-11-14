# Independent implementation and data review

Reviewer: `/root/data_review`, an actual independent child agent. Date:
2026-11-15, Asia/Shanghai. Scope: the Round167 C++ implementation, frozen
diagnostic inputs/matrices, calls, numerical evidence, Starts, tiny physical
solutions, sizes and CSV reconciliation. No solver library was imported and
no Optimize or full method was run by this reviewer. Public delivery and
manuscript argument are separate reviews.

**Decision: PASS for the implemented offline representation and the finite
diagnostic/data claims, with the reporting corrections below incorporated.**
No mathematical-performance implication is inferred from the agreement of
two models alone. The independent raw-file checks are retained in
`data_checks.py`, `data_checks.json`, `data_primal_dual_checks.json`,
`data_start_checks.json` and `data_graph_checks.json`.

## Actual checks and findings

1. **All 88 calls and every position are accounted for.** I independently
   joined the frozen manifest, complete positions and all 88 raw
   `Optimize.jsonl` files. Each has exactly one flushed begin and one end,
   return code zero; the driver ledger advances consecutively from 0 to 88.
   There are 72 canonical raw LPs, 12 local raw LPs and four tiny MIPs,
   with no reused, failed, infeasible or unexecuted matrix position and no
   reserved call consumed. Every completed native status is OPTIMAL.
   The first Optimize follows the manifest timestamp. The manifest reserved
   more than 10800 seconds for paper/review and binds actual inputs, original
   R166 argv, parent fleets, cutoffs and intervals, source hashes, PE and DLL.
   These hashes were read back independently, including the separately
   archived solver-free preparation-v1 source/PE. That preparation executable
   is not relabelled as the final 88-call executable.

2. **Numerical qualification is supported by raw primal/dual evidence.** I
   wrote a solver-free LP parser and re-evaluated every serialized row,
   bound and original objective at all 88 returned solutions. For the 84 LPs
   I additionally reconstructed the dual objective from the saved Pi and
   bound reduced costs, checked dual signs and stationarity against the
   actual matrix, and compared primal/dual values. Maximum solution-row
   violation is 6.7302607931e-11, bound violation 1.5543122345e-15,
   primal/dual difference 1.9151347175e-15 and stationarity residual
   3.0392355299e-15. This supports the stated numerical qualification;
   it is not an exact rational certificate or a general reliability theorem.

3. **Actual Native settings and raw-LP types agree with the protocol.** All
   88 parameter files report Threads=1, Seed=0, requested gaps zero,
   NodeLimit=1e100 (Gurobi infinity), and the prescribed 20/5/60-second limits.
   Method/Presolve/Cuts remain -1, MIPFocus=0, with unchanged feasibility,
   optimality and integrality tolerances. In `src/round167_research.cpp:228`,
   every original type is captured, all are relaxed, and NumIntVars=0 is
   checked before a raw LP Optimize. The original types are restored after
   LPs and before the tiny MIPs. Tiny native logs confirm the original 20
   integer variables, including 16 binaries, rather than a cut LP passed off
   as a raw relaxation. Each actual model SHA agrees with both the frozen
   request and the solve receipt. No opaque backend state is reused.

4. **R_abs uses the requested enhanced reference.** I checked the actual
   `rabs_delta` and `rabs_w` equations against absolute binary digits of
   every declared state. Its state and state-product columns are continuous,
   including in tiny MIPs, while each absolute digit is binary in the
   exported integer model. The reference therefore is not old B with its
   one-hot binaries accidentally left active, nor old offset-code LOG.

5. **D167's actual emitted graph retains the common information.** Rather
   than duplicate the C++ graph builder, I recovered edge incidence from
   the actual mass-flow rows and checked the same incidence for q. Only the
   sink equations are omitted. I checked the source-g equation, paired
   edge bounds, Y/M/V/Z costs, digit/w links, complete MSB-to-LSB path costs,
   and the unique legal stock spelled by every successful path. Across the
   24 canonical D167 models and two tiny models, this recovers 619 station
   graphs and 10827 paths, including repeated prescribed masks. These are
   implementation checks, not 619 independent domains or new test instances.
   There are no state/r166 columns in D167 and no old independent product
   inequalities; bit/prod columns occur only in the common graph link and
   the prescribed fixed-digit equations. The per-station row and nonzero
   formulas in the theory match every one of these emitted graphs.

   The interval graph builder is direct O(d) and never enumerates stocks.
   **The complete offline preparation pipeline is not a logarithmic-time
   writer:** `prepare()` first obtains the unchanged B canonical carrier,
   which enumerates its full state columns, then deletes that block and adds
   D167. Thus temporary carrier/file/import/deletion cost and peak storage
   still depend on |D|. The final representation-size theorem and measured
   matrices remain valid; end-to-end logarithmic construction or memory is
   neither established nor an appropriate description of this prototype.

6. **The unchanged physical block is retained, with a degenerate hashing
   boundary explicitly identified.** The before/after common exports agree
   for every transformation; R_abs and D167 share their raw common hash on
   all eight frames. Across C166 as well, six raw frame hashes match. On B20
   root/child, C166 has ten extra raw-filtered equations `sum_k z_ki=0`.
   Each is its V link at a station whose legal domain is the singleton b;
   B's equivalent `V+s_b=1` touches a state column and is removed by the
   generic auxiliary filter. I checked all ten station domains and exact
   coefficients. Removing only these representation-degenerate equalities
   makes the common row/domain/objective multisets identical, 8/8 frames.
   Thus the raw hash discrepancy is explained, not hidden as a matrix
   failure or falsely described as byte equality. The standalone B export
   exactly matches the old R166 model SHA
   `c41bf1e44af89b37904ee10bf1659c020c26fb91426b9737fd61408ace6869d7`.
   The four frozen production writer/backend/mapper/factory source files
   also have no diff from the R166 base.

7. **All 45 complete Starts pass independent actual-matrix checks.** The
   solver-free parser checks the whole column set, every bound, all original
   integer types, every serialized row and the original objective against
   `start.csv`. Maximum Start-row violation is 2.3536728122e-13 and bound
   violation zero. The exports include internal stock, loaded return,
   fixed positive g and a narrow positive interval. The D167 mapping puts
   f=1 and q=g on the same unique path, without endpoint-weight division.
   Tiny native logs confirm the submitted .15/.30 Starts were loaded.

8. **Tiny correctness has a separate physical argument.** Independently
   reconstructed routes in both nonzero MIPs are 0-1-2-0, final stock (1,1),
   pickup 2, delivery 1, prefix loads (2,1), return 1 and total handling
   240 seconds. They give true G=0, P=1 and F=.15. This is optimal without
   appealing to equal solver outputs: total final stock cannot exceed 3;
   target (2,2) is impossible. Equal nonzero ratios permit only (1,1),
   whose objective is .15, while every asymmetric stock with total at most
   3 has G at least 1/6>.15. The fixed-S0 MIPs instead have stock (0,0),
   route 0-1-0, loaded return 3, handling 360 and objective .30. That is the
   optimum of the fixed-stock diagnostic, not the unfixed instance optimum.
   The saved C++ oracle agrees. The independent exact-zero controller proof
   remains inherited and is not claimed to have been exercised by these
   four model MIPs.

9. **The objective findings retain their denominator and costs.** R_abs and
   D167 differ by at most 2.23e-16 in the 24 canonical frame/mask comparisons.
   D167 exceeds C166 beyond the numerical scale on exactly three of the 16
   conditioned comparisons: X20 root F2, B35 root F1 and B35 root F2.
   The other conditioned comparisons, all F0 comparisons, and all four
   strict local separations remain visible. All complete D167 root models
   have more columns and rows than R_abs in these small-capacity inputs;
   no complete GI-TBC speed advantage is supported by the diagnostic.

10. **CSV reconciliation is honest about available data.** I verified the
    byte hashes, 28-column widths and 91/103 record counts of the two files
    actually located. Neither is the requested 112-record master, and the
    reconciliation explicitly says so. No user CSV was rewritten, no missing
    rows were invented, and no prototype/local/tiny result was appended as a
    complete GI-TBC/P observation. The stated main-table increment is zero.

## Specific review corrections and disposition

| Location | Finding and effect | Disposition |
|---|---|---|
| `scripts/round167_diagnostics.py:139`, `positions.csv` | Local `prepare.id=L1` overwrote frozen `L1_R_abs` etc in the CSV merge. Raw models, solves and nested JSON were healthy. | The owner now restores `merged['id']=p['id']`; I read back unique local position IDs. No solver rerun. |
| `scripts/round167_diagnostics.py:129`, expense labels | 126.2616566s is the sum of recorded C++ subprocess outer durations, excluding wrapper/freeze/summary/reader handling; it must not be called the complete diagnostic outer cost. | Owner accepted and changed the manuscript wording to C++ subprocess wall time; final cost policy uses an enclosing diagnostic window plus independent offline checks. Record the final receipt separately. |
| `src/round167_research.cpp:61`, B20 common hashes | A generic auxiliary-name filter treats a singleton C166 V link as common and B's equivalent as representation. Raw hashes therefore need a qualified interpretation. | Verified all ten exact equations and legal domains on root/child. Normalized outside block matches on all eight frames; no model mutation or solve is needed. |
| `src/round167_research.cpp:167`, preparation pipeline | The final D167 block is logarithmic, but its current offline wrapper creates a temporary enumerated B carrier before replacement. | Disclose temporary O(|D|) preparation/storage and refrain from claiming end-to-end log construction; this is an explicit integration limit, not a failure of the final matrix or a reason to repeat healthy solves. |

The reviewer's first raw-common-hash equality assertion was too strong. Its
failure is retained in `data_reader_attempt1.json` and corrected by the
independent degeneracy check. It caused zero Optimize or producer reruns.
The successful complete check took 54.402567 seconds. The first reader
attempt lies within a conservative 294.348392-second enclosing interval;
its exact CPU time was not retained and is not invented. A rounded
360-second conservative independent offline calculation allowance covers
both these windows and small focal readbacks. Shared science wall time
still counts parallel review once; this allowance is separately reported
calculation cost, not an additional full-method time sample.

The implementation/data conclusion applies to this offline driver, these
fixed inputs/scopes and numerical checks. It does not verify an unimplemented
controller/target/terminal lifecycle, every Native branch row, full BRP
ideality, an algorithmic speedup or a broadly robust adoption claim.
