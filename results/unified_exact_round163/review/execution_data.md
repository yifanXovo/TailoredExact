# Round163 independent execution and data review

Reviewer canonical identity: `/root/round163_execution_review`.
This is the separate agent assigned by `/root` under goal H. The checker below
is this reviewer's own program; it is not represented as an additional person.
No subagents were used. The reviewer read `goal.md` and `WORKSPACE_POLICY.md`,
inspected current-round files and source, and wrote only `review/` artifacts.
The reviewer did not run a solver, model builder, H, inventory helper, old
producer, old archive recovery, or the independent numerical checker.

## Current disposition

The final execution/data review is **PASS**, including science and the actual
six-pair master CSV append. Static inspection and the independently
computed readback find no conclusion-changing execution/data defect in the
frozen 18-arm panel. Root serially metered `review/check_execution.py` v3;
`review/execution_readback.json` reports PASS for six actual input parses and
all 18 complete raw fleet reconstructions, own startup fleets, execution
identities/counts, q0/cold P, raw/proof cover composition and expenses. Root
then completed the actual append to both masters and serially metered the
separate CSV-only checker. `review/csv_readback.json` is PASS. The reviewer
read that result, its actual observed-exit receipt, the append receipt,
immutable source binding, canonical increment and current actual-file hashes.
No fleet replay was repeated for this CSV follow-up.

The first root-metered checker attempt stopped before fleet arithmetic because
the program compared the raw launch object to the frozen launch as a whole.
The supervisor legitimately appends `prelaunch_seconds`, `prereg_sha256` and
`runner_sha256`. The review adapter now compares every frozen field, including
full argv, permits only those three additions and binds their hashes to the
own identity. The failed checker and JSON remain in
`review/check_execution_attempt1.py` and
`review/execution_readback_attempt1.json`; its nonzero-exit fee remains under
`fees/independent_execution_readback/`. This fixes only the reviewer adapter,
with no production change or producer rerun.

The second root-metered attempt reached X35 and stopped because the reviewer
adapter called the final exported E+ proof cover a raw search cover. R154
intentionally exports its proof copy at finalization while retaining the raw
scheduler in `external/round154_proof_ledger.json`; the last pre-final trace
still reads `.39492875817006656`, and final proof L is
`.42319954961578576`. The adapter now binds the actual ledger SHA to its
qualified audit, matches every scheduler leaf/scope, reconstructs raw and proof
complete covers separately, verifies the qualified floor merge leaf by leaf,
checks the raw cover against the last pre-final Native/search trace, and checks
the proof cover against the final trace/export/endpoint. No coverage test was
removed. Attempt2 source and JSON are retained as
`review/check_execution_attempt2.py` and
`review/execution_readback_attempt2.json`, with its nonzero-exit fee under
`fees/independent_execution_readback_v2/`. This is another reviewer-adapter
correction, not a change to any scientific endpoint.

The passing checker SHA256 is
`c00b3c938ef1f37111fd7a63050fdebc979aac0e93650075feaac68e46a8355b`.
Root's final attempt receipt at
`fees/independent_execution_readback_v3/receipt.json` has observed exit0,
no timeout and paid outer `.8381662000901997s`. The output's pending v3 fee
label reflects writing the JSON before its own process exit; that fee is now
closed. Root reports the closed scientific total after this review as
`24697.614487844054s`, including both retained failed reviewer-adapter attempts
(`.3091465001925826s` and `.7713310001417994s`) and the passing invocation.
Later CSV/delivery accounting must use its own final closeout rather than
freezing this intermediate total as a final resource claim.

The passing independent check supports the reported 3/6 B, 3/6 E+ and 1/6 P
certificates, all-six identical B/E+ physical U, and X35's raw/proof distinction.
The reviewed decision and human report retain P's better C35 U, the all-six
denominator, the real limited X35 proof benefit, paid E+ costs and the narrow
archived-source/single-Seed scope. There is no execution/data objection to
the stated uniform B-main, limited E+ proof-supplement tradeoff. The late
crosswalk disclosure remains a qualification on chronology, not a blocker
that warrants changing data or repeating production.

## Inspected contracts and evidence

The review read the actual `matrix_frozen.json` destinations, representative
raw result/fleet objects, committed identity/call events, producer seals,
producer/total/outer fee receipts, live OS bindings, `science_identity.json`,
method/source/helper freezes, six-input manifest, first-draw artifacts,
selection/source mappings, qualification/failure records, and completed
reports. The executable checker enumerates all 18 destinations rather than
relying on a representative arm for the final readback.

The three methods start from separate clean frozen templates. B is the R137
`ms2` M-B/VD-P pair-only profile, AM .08 with unchanged depth/width and fixed
own-H seed20260626. E+ adds the unchanged R154 proof-only placement and R156
RN16384 helper. P uses `--method gurobi --plain-baseline --round127-mode p`,
without a B preset or the P-S start flag. Source `Round127Research.hpp`
validates the isolated entries; `round137_parameters.json` reads back the
unchanged split threshold and no deletions. `--round138-stock-rlt` is a
one-way true switch and is absent, rather than counteracted by a later flag.
The source shows `--round162-physical-completion off` leaves both PC/stock
controls false. Other current candidate-external mechanisms are explicitly
off or remain default-off, consistent with the qualification inventory.

The common reused PE is SHA256
`fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93`;
Gurobi13.0.2 DLL is
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
Measured C++ commit is `e920b92e199e825ec89a2932f701861ff158e0d4`.
The manifest separately records the inherited, uncompiled no-Gurobi stub
difference. The reused PE is not mislabeled as built from later paper or
delivery commits. The runtime and helper dependency maps are checked against
actual files by the independent program.

The helper entry bytes and closure remain unchanged. Its source is each E+
arm's own canonical root LP, not input text or a historical role. The launcher
performs generic input/path bindings only. RN16384, original absolute price
gap1e-4, old_joint=True, exact DP/fallback, root-once and the whole-method
deadline remain visible in source and actual metadata. It is accurately a
mixed C++/Python implementation. The proof ledger and control audits retain
zero helper floor rows in formal Native models and use raw search bounds for
AM. Inventory upper bounds are not physical fleet upper bounds.

## Input timing and novelty limitation

The recipe/method commit, six-input seal and frozen matrix precede formal
production. All six first draws were retained, with no collision redraw or
performance screening. The six rows follow the specified source, n/M/Q,
inventory, geometry, replicate, original T and cap. The selection ID enters
the landscape identity. Within each archived source the two new selections
are disjoint; historical source-row overlap is allowed and is disclosed.
Weights and lambda are based on the serialized data, not unrounded landscape
weights. `Parser.cpp`'s legacy max10 downgrade convention was inspected; the
post-panel effective-key check explicitly includes it.

There is a real ordering departure that must remain in final reporting:
history-manifest mathematical keys were sealed before performance, and the
primary CSV was located and prospective IDs checked before the panel, but
the detailed historical master-row-to-input crosswalk was inspected after
the first arm began and completed post-panel. The effective-parser novelty
strengthening and retained R57 ephemeral-pilot metadata check were also
post-panel. These checks found no mathematical collision and caused no input
or producer change. They are not preregistered crosswalk evidence. R57 pilot
metadata supports n/M/Q separation and overlap disclosure; absent old pilot
input files are not claimed to have been reconstructed.

The proper scope is prospective new configurations on archived sources with
synthetic demand fields, now exposed. It is not a new-city or independent
population validation claim.

## Costs, failures and qualification

Each formal arm has its own producer, H where used, fresh helper where used,
raw journal and outer fee. P's actual readback requires NumStart=0, and the
actual call journals retain Threads1/Seed0/Presolve-1/MIPFocus0/Cuts-1 and zero
requested gaps. The paid outer clock includes startup, H/helper, model
construction, Native work, validation, cleanup and observed exit. Nominal caps
are not convergence times, and Native Runtime/Work are diagnostics rather
than an additional fee.

The completed analysis corrects two reporting fields without changing a
producer: actual `helper_process_seconds` is read from its real metadata,
and the reader trailer through observed outer exit is added to T_verify and
T_total. The small remaining wrapper-entry difference is still present in
the scientific outer fee, so it is not silently removed from total science.
The conservative initial-history enclosing charge includes the premature
generation attempt. Nonzero-exit qualification/tiny-reader attempts retain
their original fee receipts; they are not discarded from scientific cost.
Pure reader repair does not justify a second healthy producer.

The independent checker also reads unclipped signed gaps. CERT uses the
inherited tolerance and fully paid producer close, OPEN has no T_cert. Tiny
negative signed endpoint gaps remain disclosed. The near-zero C35 inventory
floor is not an exact-zero physical certificate. Native status2 at its allowed
absolute gap and the helper's retained legacy decision label are distinct
facts; status8 RN16384 prices remain intervals. In particular, the earlier
R156 narrow residual is not transferable to the new B35/X35 scopes.

## Independent executable readback

`review/check_execution.py` uses only the Python standard library and no
project imports. It parses the six actual text files, independently replays
all 18 final result fleets and their own startup fleet witnesses, explicitly
completes unused vehicles, and checks zero initial loads, station
disjointness, capacity, fleet stock conservation, travel at speed1.5,
pickup/drop handling and depot unloading. It computes satisfaction ratios
and decimal weights as exact fractions and uses the sorted-ratio Gini
identity, rather than calling or copying the inherited pairwise `full_fleet`
entry point. It compares these independently reconstructed endpoints to the
raw result, qualified endpoint and report.

It additionally checks actual frozen input/source/runtime hashes, order and
method/off flags, live OS binding, paid deadlines, committed call/identity
anchors, NumStart0, all returned/deadline-skipped call counts, final raw trace
and complete cover, proof-only floor composition, retained fees and aggregate
method expenses. It does not claim to independently re-prove the inherited
source-qualification theorem or replay every chronological Native callback.
Those remain explicit separate core audits.

Root must execute, serially under the shared meter:

```powershell
& 'E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe' -B results/unified_exact_round163/review/check_execution.py --root 'E:/codes/ExactEBRP-work/worktrees/round163'
```

The output is `review/execution_readback.json`. Its own metered invocation
cannot have a closed receipt until after its output is written; final cost
closeout must include the actual observed checker exit.

That invocation is now complete as recorded above; no repeat fleet check is
requested for publication or CSV authoring.

## Master-table contract and completed CSV signoff

Static inspection of `scripts/round163_tables.mjs`,
`scripts/round163_table_append.py`, and `main_table_schema_readback.json`
shows the intended append retains the original GB18030 bytes and all 85
historical records. Both current masters have 28 raw columns with two empty
trailing source-header cells; a DictReader view collapses those two names and
must not be mistaken for a 27-column source. New source URLs are positional
columns27/28. The separate increment uses the named 28-column header.

Only verified B/P pairs enter the six new master rows. E+ remains in the
18-arm comparison and is not relabeled as B. Actual lambda/.15 is computed,
convergence time is blank for OPEN, OPEN gap is a percentage, qualified L/U
come from the complete reports, and the unconfirmed comparison category is
left blank with explicit certificate/U/L facts in the note. Existing category
labels and historical source identities remain unchanged.

The root-metered follow-up inspected the actual two written master files,
their exact original byte prefixes, 91-row totals, 28-field widths, six unique
new keys, both source columns, and value correspondence to B and cold P.
It did not repeat the completed fleet reconstruction for CSV transport.

The independent CSV-only checker at `review/check_csv_transport.py` writes
only `review/csv_readback.json`, reads the completed independent fleet PASS,
and checks the actual master prefix/suffix, both named/unnamed schemas, all
six B/P value mappings, source identities, status/time/gap semantics and
actual write receipts. It contains no fleet replay or project/solver imports.
Root executed it; the reviewer did not execute it.

Final CSV readback identities:

| Artifact | Actual identity |
|---|---|
| Numeric results/input source commit | `4d09e6fc9ed1c34dacd11aa8c7b7d22ae9f8ebbc` |
| CSV-only checker SHA256 | `76c792aaecec59b8a99c24977e54ed4e1fb88b73635985b48b0756a39d0035dc` |
| Original 21230-byte master prefix SHA256 | `0648bdc3b297fbb1c34de3cbc9bede5718c0c8cdfa2656462bcff457b0ab8718` |
| Both updated master files and repository master copy SHA256 | `2a0b80b9536bfbb278370f9b9dbf6947b9570d25ab7b158605e6a2012ad2b2f3` |
| Named 28-column increment SHA256 | `65457e68400aaab27a0482db75baf3a6fa46395f9ae2aee2b96fd4d31a5c4893` |

The actual updated paths are
`C:/Users/Administrator/Desktop/GI_TBC_vs_P_GRB_All_Tested_Instances.csv`
and
`C:/Users/Administrator/Desktop/Research/docs/tempfiles/GI_TBC_vs_P_GRB_All_Tested_Instances.csv`.
Both are now 25180 bytes, byte-identical, GB18030, with 85 preserved historical
records plus six new records and the original 28-field header, including its
two unnamed source-header cells. `main_table_update.json` records the actual
append at `2026-11-12T01:31:30.924598+00:00`; the independent CSV-only PASS is
timestamped `2026-11-12T01:31:31.704292+00:00`.

The increment contains exactly R163-C20-S, R163-B20-B, R163-X20-S,
R163-C35-U, R163-B35-S and R163-X35-S, each once, from B and cold P only.
In particular X35's GI-TBC lower is B's `.3949882559151472`, not E+'s
`.42319954961578576`. C35 retains P's better physical U alongside B's stronger
L. The status labels, OPEN blank convergence times, percentage gaps, actual
lambda/.15 multipliers, blank new comparison categories and fixed-commit
source URLs in positional columns27/28 match the verified endpoint/input
sources. All historical labels and source identities remain unchanged.

`fees/independent_CSV_readback/receipt.json` records observed exit0, no timeout
and paid outer `.09534050012007356s`. Root reports closed science
`24697.709828344174s` after this CSV-only verification, with no pending fees.
Later publication/recovery/cleanup metadata must still receive its normal
final accounting. This final execution/data signoff requests no additional
scientific execution and has no remaining CSV or scientific blocker.
