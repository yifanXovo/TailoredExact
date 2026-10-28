# Independent compact-reader amendment review

Disposition: **ACCEPT** for matrix
`26f295da36097cd662b9c2ca049ab2452f0b295dfcdb12dd4b726ff25190c894`.
Separate internal reviewer `/root/independent_review`, 2026-10-27
(Asia/Shanghai). This is a narrow pure-reader amendment after the first sealed
P run; it does not repeat that native run or change the admitted experiment.

The R134-to-R135 reader diff adds a state/AP contract to the shared verifier,
alongside its common-module and endpoint-filename changes. That additional
contract assumes state selectors and fails on original compact P/PS, whose
ratio columns exist without state selectors. The saved original failure is
consistent with that mismatch. This was a reader applicability error, not a
native physical/model/proof failure or an ordinary numerical negative result.

The Round137 wrapper now marks only the added AP contract inapplicable for
P-GRB/P-S after asserting AP is disabled and no state columns exist. It retains
the inherited verifier's actual canonical-model equality, integer type,
physical, parameter, lifecycle, source-bound and PS Start checks. M-B retains
the unchanged AP-off state contract. The namespace adapter changes only this
AP contract; it does not replace the native proof/physical checks or create a
new incumbent/certificate. This scope is appropriate.

The independent saved-file check in `compact_reader_amendment_check.py` passed:

- Current and previous matrix JSON differ only in the reader helper SHA. All
  launches, identities, physical inputs, argv, source snapshot, PE, method order,
  caps, Seeds and plan/candidate/input hashes are unchanged. All current source
  and helper hashes match their bindings.
- The first P producer is normal-return, sealed, within its 600-second cap and
  stopped with no native reentry. All six primary raw hashes in the repair
  receipt still match. Only one native fee and one entered raw destination
  exist; no second native run was started.
- The actual returned fleet was independently replayed against the physical
  input. The saved compact model has the exact declared canonical hash, integer
  quantities and no state selectors. Its original type/model contract passes.
- The native-quality event's direct file and NEJ1 commitment match its hash and
  length; its supported ObjBoundC equals the reported L. The physically replayed
  U is .5922648822560825 and qualified L is .527662772138667. The run remains
  open with null certificate time and is eligible under the inherited policy.
- Original T_produce is 571.702276962 seconds. The raw T_verify of
  142.568012900 and T_total of 714.270289862 retain the real repair delay; they
  were not shortened. The actual pure repair replay is separately measured as
  2.509066500 seconds. The failed first wrapper's native cost remains charged:
  571.744445800/216,000 seconds. Nested native time is not added again.

The old admission and original reader failure are retained. Reissuing the gate
admits the remaining queue and pure interpretation of that existing sealed
P result; it grants no permission to rerun healthy native work. The reviewer
performed zero Optimize calls, compilation or commercial native-library loads.
No broader qualification or full-matrix rerun is warranted by this reader-only
applicability repair.
