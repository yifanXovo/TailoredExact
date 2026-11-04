# Complete eight-arm panel: independent component review

Disposition: `ACCEPT_COMPLETE_PANEL_COMPONENT_READBACK`, with the report
source-commit correction below incorporated. This is an independent readback
of the eight sealed endpoints, verification closeouts, total receipts,
control-audit summaries, frozen matrix/identities, and eight small outer-fee
receipts. It is not another physical-route, Native model, journal or proof
replay. No Native, Optimize, compilation, report generation, plotting, or
heavy I/O was performed. The separate offline primal probes, including
their later execution or failure state, are not assessed here. Final
scientific audit, integrated claims and delivery
remain separate work.

## Frozen identity and own-H checks

The actual matrix SHA256 is
`d81767d4adfe9ec20a2f5bfcc6cd26450773f2f93fe3231459603c523210374e`.
All eight identity files hash to their registered matrix entries. Their
launch arm IDs and role/input hashes match their sealed endpoints. Each
pair uses the same PE, input, original resource parameters and seed. The
registered T values are 7200/10800/4800/5400 for NB35/K35/RB35-T1/NC20,
respectively; these are physical settings, distinct from the experiment
caps. RB35-T1 retains lambda 0.055125275219827186, while the other three
roles use 0.15. Threads and MIP threads are 1, Gurobi Seed is 0. The
matrix's independent H seed is 20260626. This review does not rerun H.

Shared measured identities:

| Item | Value |
| --- | --- |
| Measured candidate commit | `36d085cc7012690b8ab38d7ace70f487f54aec7e` |
| Delivery base commit | `ed058861e5eb094bc22d468a71a791bf558b51ac` |
| PE SHA256 | `44e593db8e3442925ce7dbd7bc16c077e79ab1646c7507b72541d8e697b996f7` |
| DLL SHA256 | `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88` |
| Candidate manifest SHA256 | `c967115083253e238cbb05a4a56740eab5cec046d1b94c0ce86c2ee53254edcc` |
| Helper manifest SHA256 | `24be18f4d03fae8ed8b21d14f2974b761a5e043dbf84f67715ed1ba632647504` |

| Pair | Matched input SHA256 |
| --- | --- |
| NB35 | `80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98` |
| K35 | `1b098a63a758e60ea22c257d559e3a27aef1fdf0cb4683b684761e72bb6ab4cb` |
| RB35-T1 | `64f9a5dfdfb09fcfbe705c1edfa16e94ea8bbf30281c5d25bb919c63c503a71a` |
| NC20 | `93b93b6abed55cf97f8ee21ddd85fb8501554b8e4c35bb997ae75782f1f98e16` |

Every endpoint has H_complete=true. Within each of the four pairs, both
H_semantic_SHA and H_fleet_SHA match. As established by the inherited
reader, these compare semantic traces and canonical capacity-assigned
fleets; they do not assert equality of raw files. Each arm has its own
producer/verification chain and paid outer receipt. Equal H hashes do not
mean shared or free H. The complete panel was fixed before its outcomes;
no role replacement or cross-arm inventory injection appears in these
registered identities/control summaries.

All eight closeouts report implementation qualification, complete
evidence, performance eligibility, necessary verification completion,
native-proof qualification, and no solution/certificate backfill. None
is a legacy-scope unevaluable disposition. Each endpoint's audit SHA
agrees with its closeout; actual closeout and total-receipt hashes match
the endpoint's references. The total receipt also matches the closeout's
producer hash and the actual closeout hash. This review relies on the
sealed inherited physical/proof audit and does not recompute that audit.

## Observed physical endpoints and times

The U/L below concern the complete physical problem, not the offline
strengthened-LP upper. Values are rounded here for readability; the
hash-bound raw endpoints retain full precision.

| Position / arm | U | L | U-L | T_produce (s) | T_verify (s) | T_total (s) | Certificate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 NB35 B | 0.450291503263 | 0.389310601642 | 0.060980901621 | 2371.497344 | 2.765726 | 2374.263070 | open |
| 2 NB35 J | 0.460394748354 | 0.395956408724 | 0.064438339630 | 2371.372241 | 6.677003 | 2378.049245 | open |
| 3 K35 B | 0.692854358631 | 0.565406336084 | 0.127448022548 | 2372.056156 | 2.754693 | 2374.810849 | open |
| 4 K35 J | 0.661326795081 | 0.539723389342 | 0.121603405739 | 2371.396882 | 5.125982 | 2376.522864 | open |
| 5 RB35-T1 B | 0.591517634770 | 0.455903891252 | 0.135613743519 | 2376.287360 | 2.813188 | 2379.100548 | open |
| 6 RB35-T1 J | 0.616049183898 | 0.461097372891 | 0.154951811007 | 2371.455771 | 5.091026 | 2376.546797 | open |
| 7 NC20 B | 0.245505069182 | 0.245505069182 | 4.61575e-14 | 266.702011 | 3.258861 | 269.960873 | closed |
| 8 NC20 J | 0.245505069182 | 0.245505069182 | 4.61575e-14 | 267.254185 | 3.998310 | 271.252495 | closed |

The six difficult-arm endpoints return normally at the overall method
deadline and retain T_cert=null. No cap, runtime, helper time, or trace
event is substituted for a certificate time. Their launch caps are 2400
seconds with the already frozen 30-second shutdown margin; the measured
times, not nominal caps, are reported.

Both NC20 endpoints have exactly the same stored U=0.24550506918249843
and L=0.24550506918245227. Their positive difference is
4.6157522248790883e-14, closed under the inherited numerical interval-cover
policy. This is not a newly asserted rational equality. Their T_cert
values equal their complete producer endpoints: 266.70201131957583 for B
and 267.25418481137604 for J. These are the inherited conservative
certificate-time observations, not exact first-witness timestamps.
T_verify remains separate, and T_total includes it.

The four comparisons have different tradeoffs:

- NB35 J raises L by about 0.00664581 but worsens U by about 0.01010325;
  its absolute gap is about 0.00345744 wider. Its T_total is also about
  3.79 seconds larger. This is a lower-bound improvement, not an overall
  endpoint improvement.
- K35 J improves U by about 0.03152756 but reduces L by about 0.02568295.
  Its absolute gap is about 0.00584462 smaller; relative gaps are nearly
  the same (0.18387794 J versus 0.18394634 B). Its T_total is about 1.71
  seconds larger. Better incumbent and weaker proof bound must both be
  reported.
- RB35-T1 J raises L by about 0.00519348 but worsens U by about 0.02453155;
  its gap is about 0.01933807 wider. Its approximately 2.55-second lower
  T_total does not reverse the endpoint tradeoff at this deadline.
- NC20 retains the same certificate values. J is about 0.55217 seconds
  later at T_cert and 1.29162 seconds later at T_total. This single pair
  is not evidence of a certificate-speed improvement.

Thus this fixed panel supports mixed behavior of the uniform candidate,
not uniform dominance or an added hard-instance certificate. It does not
establish broad statistical performance or identify the causal share of
each search-path difference. Any final adoption decision must preserve
the four outcomes rather than select roles after observing them.

## Own-helper scope and accounting

All four B controls are disabled, with null root and no embedded floor
models. Every J root is qualified, returns helper exit 0, has no global
deadline stop, declares its owned kill-on-close job, and records root_once,
NodeLimit=4096, and original price-gap target=1e-4. Each root's input and
helper-manifest hashes match its frozen own launch. Their current physical
cutoffs and hard resource intervals are retained. No offline data,
formal AP/GD/RN/NC/TS block, formal new column, or additional root LP is
declared. The completed control audits report original columns, bounds
and objective preserved and own-source scope verified.

| J role | Own hard-total range | Own cutoff | Qualified floor | Helper process seconds | Actual model summaries |
| --- | --- | ---: | ---: | ---: | --- |
| NB35 | [136,211] | 0.577217944639 | 0.3959564087240911 | 14.6320539 | 3 model summaries with a floor row; 4 formal Native audit events |
| K35 | [251,326] | 0.767456604725 | 0.23294169799100467 | 1.5181520 | 2 summaries with a floor row, 1 without; 4 audit events |
| RB35-T1 | [161,236] | 0.635173203403 | 0.14243319962421927 | 9.7448168 | 2 summaries with a floor row, 1 without; 4 audit events |
| NC20 | [211,271] | 0.379768306785 | 5.645715353552737e-17 | 1.1602574 | 3 summaries without an added floor row; 4 audit events |

These summary counts do not count helper pricing as a formal Optimize
or equate repeated Native audit events with distinct model files. Formal
endpoint Optimize counts are B/J=5/4, 4/4, 5/4, 4/4 by pair, with all
declared calls returned. NC20's tiny qualified floor is below the row-add
threshold; it is not an added useful positive constraint. In K35/RB35-T1,
final physical lower bounds are far above their own scalar floors, so the
full endpoint change cannot be attributed numerically to the floor alone.

The helper process seconds above are inside each arm's T_produce, which
is inside its total receipt and unique outer fee. They must not be added
again, nor should H time, solver Runtime/Work, or T_total be added to the
outer fee. The eight outer receipts are observed exit 0 with no timeout
or supervisor failure; their charges total 14801.14538730029 seconds,
consistent with the closed campaign record. They are slightly larger than
the arm totals because the outer wrappers encompass additional measured
overhead. The previously disclosed pre-outer setup/identity timing gap
remains; it is not zero-cost work or repaired by rerunning producers.

## Actual-data correction to the earlier static report assumption

All eight actual endpoints have source_commit equal to the **measured**
candidate commit 36d085..., not the delivery base ed058.... The earlier
own_root_v2 qualification had the latter legacy field meaning. Its schema
example did not justify extrapolating that meaning to the frozen complete
campaign. The previously accepted report assertion against delivery_base
would fail on these eight valid endpoints; its explanatory text was also
wrong for this panel. This readback supersedes that earlier static
assumption. It is not a defect in the sealed measured data.

The root changed only report/documentation handling. The reread
`round153_reports.py` now requires endpoint source_commit to equal
identity.measured_source_commit, exposes endpoint_source_commit, and
keeps delivery_base_commit separate. Its corrected SHA256 is
`d3f59159f59d49d7177335e742254caebfa92216ddb647567fa0af64cbba772f`.
The matching reproducibility text was read at SHA256
`712382befd38205bcbbdef4aac1bf75a5270e70019a6984aff04e47f55f88e58`.
No sealed endpoint, identity, frozen production source or measured outcome
was rewritten. Reports have not been executed in this review.

## Evidence bindings

Positions refer to the immutable matrix groups under
`campaign_confirmation/NNN/raw/<arm_id>/`. The endpoint SHA binds its
referenced closeout/total-receipt hashes, both of which were independently
hashed and matched in this component readback. Identity hashes were
independently matched to the matrix. The larger underlying audit bodies,
PE, physical input files and models were not rehashed or replayed here.

| Position | `round135_endpoint.json` SHA256 |
| --- | --- |
| 1 | `423ebb16163b1b1c00191704171a214b59c1f0850a5a70b793b19edea60b1d80` |
| 2 | `49372656adc35e8b732c486a7e7f07b6f4308557a2c5bd8fa7eca83ec6ab4ca6` |
| 3 | `457432e0a0d462e9f66ccc25624e4487e20bfc0876da4d922ceca81bf0d3fc65` |
| 4 | `bfa660a9c2c8185c5c82ddd5bfaac5fb20b734b4bc5650c94a0f4adaa0de1ab5` |
| 5 | `136f03155f928d439340613a72c182d89b78da164c19a9cf9f4f84a02b6029f0` |
| 6 | `8369fcbc16d6dbad6bbf7e6b892d24f383bb5809422b65834e7110f623368228` |
| 7 | `497edb254e9f626efa9a2b663652ec85824245f530247327386219bbed26c745` |
| 8 | `53a1e8712272d0333316bf34370fa56026e1e206b8342ff278ac56faa229280e` |

| Position(s) | `round153_control_audit.json` SHA256 |
| --- | --- |
| 1,3,5,7 (disabled) | `18caf406b5a9c3280c22bd977386ab3f671a2a9bc6795241ec325776548afd17` |
| 2 | `9dfaa9d726be8aaad36d012dca709bda930c78f2390fecee9aa00a7ebbd38a8e` |
| 4 | `128ce3213d560c5ae51c0d1c3fc8fa53f0c8c26a9a66a33ae845ee853e634166` |
| 6 | `a1042a85e80c67a118ba5dfd3531d52aeaa69288eb28a3c9e755d24d686420a0` |
| 8 | `ceabc243dc943b2fafc5aa5576ff83752529cd9c07b28c5029f89e3f573acdcc` |

| `fees/confirmation_NNN/receipt.json` | G1 seconds | SHA256 |
| --- | ---: | --- |
| 001 | 2374.3298696998972 | `c1a0a1bed6a33dba0f1fefb078a7639075400808d0a04d407051e7e95dccd8cd` |
| 002 | 2378.1284487000667 | `53646efd39435515c44f4a4424936396b53703bc1647578e4e3932c03a56ec3d` |
| 003 | 2374.9481723001227 | `57fc968aec40dc2edb3f1b1944627ffd5718ed2ffb6916c3a56b9b531d57b2b3` |
| 004 | 2376.5916002001613 | `c8086076901da37127ce166a8f321b86e51ae84fe4047412ff4a9615b00bc2ce` |
| 005 | 2379.1701336000115 | `65d3ad0def0a7afc18b8b329cf9a6eea750784958b6882f41f1461f3e9c6434b` |
| 006 | 2376.618468400091 | `6dadc6879d5b0184395fbb2ec4d31af5ff4f3ee89ec1d530457cce92fc778c47` |
| 007 | 270.0301557998173 | `2669967559ebd74032217834aff7f14fc7abba9a3a6d90dcbfab1a9b9e51474c` |
| 008 | 271.32853860012256 | `3740ca39bb26a04774bd73855f76e14aa4226d7f29a4c0d2f0f21fc826c47a7c` |

The closed queue/status records read here have SHA256
`b24f9becdeaed6010a42dc275ac20e1c25f18e800e8399933d23d4b5d1c850a5`
(`followthrough_status.json`, REGISTERED_QUEUE_CLOSED) and
`5445378c38ec93f71b9754b9419c39c0afce9169f9cb1dab2f295f303e6f6373`
(`confirmation_run_return.json`, stop_after=8). Their then-closed budget
snapshot is not a claim that later offline research has ended.
