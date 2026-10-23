# Round132 C preformal admission

Decision: **ACCEPT** for C execution binding SHA256 `3248070303dd4157ea0df766b859108b354dffffa7ee9909abe98352f9480135`.

This review was limited to light source reading, existing qualification records, saved S12 matrices and Start vectors, and the frozen 24-position C plan. It started while the authorized serial D campaign was running. This reviewer did not compile, build a native model, execute H, start Optimize, or replay native qualification. D adapters and frozen D files were not changed or redundantly re-audited.

## Implementation and mathematical scope

`Round132Expression.hpp` has one default-off, process-local expression selection. Geometry mode deletes exactly the three named factory families; it does not toggle their domain-generating options. SP mode normalizes every actual W row, classifies two MC lower planes and two MC upper planes plus the SP upper plane, appends both actual W box sides, and emits all 3 x 4 = 12 lower/upper combinations. This retains the compatibility/P-domain consequences and the actual box. It does not rely on the unsafe two-cutoff shortcut or a presumed tight physical penalty upper bound.

The generated CplexBaseline and main translation units are in the separate build cache. An in-memory comparison to frozen source showed only the header inclusion, expression parser option, qualified-emitter guards, the factory-row transformation, and omission of W from the SP Bounds section. Other production translation units are reused. The research program, exporter, implementation header and generated-source hashes agree with `research_build.json`; the actual program SHA is `eac4e778cacb316c61928d4a6f1e4c90c8397cc94e0dc528695773703e98cce2`. All C formal arms use that same research PE and the same original DLL. D continues to use original E3.

The ideal projection proofs in the earlier mathematical review remain applicable under their stated H-use and domain conditions. FM elimination itself handles zero or fixed domains without dividing by their width. Formal C uses positive lambda .15 and the qualified S2R entry; this admission does not broaden the mode to arbitrary presets, extra H usages, arbitrary native node cuts, zero-lambda runtime combinations, or every possible future floating matrix.

## Saved-matrix and numerical evidence

The saved matrix qualification has four fixture/interval records (S12 and R98-C2, each at alpha=0 and a positive lower endpoint), with 12 separate canonical all-continuous LP solves. Its old E3/default-off pairs have identical LP bytes. The stored LP values agree within 1e-7. Those are qualification observations rather than native MIP-root values or a general projection proof.

This reviewer additionally parsed the four actual S12 native roots and checked their saved hashes. Original E3 and research off are equal over the complete parsed matrix. Geometry mode removes precisely 66 H-spread, 132 fixed-centering and 132 variable-S-centering rows, adding none; all other rows, columns, types, bounds and objective are retained. SP removes W and its five rows, keeps every W-free row and every remaining column domain/objective, and adds exactly 12 projection rows.

An independent exact-rational reference formed from the parsed binary64 source coefficients and actual W box was matched to all 12 candidate rows with multiplicity preserved. The actual S12 native-root coefficient-domain rounding bound is 2.2106544245719703e-14; the largest separately reported qualification-fixture bound is 4.183533441835392e-13. Both are below the inherited 1e-7 numerical contract. The emitted binary64 coefficients are not thereby proved to be the exact rational FM coefficients or to define a universally identical strict rational polyhedron.

The potentially ambiguous `exact_native_binary64_rational_projection_proved` field is explicitly qualified by `C_matrix_wording_addendum.json`, bound to the original report SHA. It refers to the exact rational reference construction; emitted-row agreement and finite LP consistency retain their narrower numerical status. This interpretation must also be used in the manuscript and final tables.

## Native workflow and Start bridge

The four existing S12 full workflows (original E3, research off, geometry and SP) are independently qualified, each with its own H and a complete L0 LP-then-MIP chain. Their journal/ledger, verification closeout and actual `.round68.start.json` receipts were read. Each Start is mapped, all rows checked, objective checked, submitted once and read back. The stored maximum Start row violation is zero in each case, and the native logs record acceptance.

The complete E3/off/geometry Start vectors are equal. The SP vector equals the same off vector with only W removed. All remaining column values are preserved, including physical fleet decisions, state products, g and epigraph e. This supplies the required same-physical-Start mapping evidence; a qualified result is still distinct from its future formal performance.

The original and research off actual root hash is `c10d3aef0eac8d501b32be9a349cd9c7a45483debd545f2a6405ff9d42fae7f2`; geometry is `d9078e99b61cbcd05a58281e821e72dd12542f05d3db4e570318765e324bdf52`; SP is `a554c6da85981e78a2b4e80a7dd092c5e4c66e2078f1000982d1261d43ca7743`.

## Formal plan and review repairs

The eight groups contain exactly four known diagnostic roles, two Seeds and three separate expressions: 24 arms and 32400 nominal cap seconds. Role identities, input hashes, cap values 600/1200/1200/2400, full commands, the single `s2-root` mode, preset, m-binary, LP-G split false, own H and common deadline policy were checked. There is no combined geometry-plus-SP candidate. All formal destinations remained absent at admission.

The final C plan explicitly fixes S2R-GEOM/S2R and S2R-SP/S2R directions. Each has four problems x two Seeds = eight repeated comparisons, sharing eight baseline arms. Sixteen typed comparisons are not sixteen independent trials. Missing native diagnostic fields remain unknown, and the same inherited log/trajectory policy applies to all expressions. Qualification LPs do not fill missing formal native-root fields.

Two local review issues were repaired without native reruns:

- The imported D execution function would have written D/original-E3 recovery labels during C. C now clones the unchanged producer/verifier body with C/research-PE recovery wording. Only C metadata and the C runner/binding changed; the previous binding is preserved.
- Comparison direction and shared-baseline denominators were made explicit in the C plan and its binding.

The matrix-checker failures in attempts 01/02 are retained with their directories and costs. Their described cause was row-order matching in the checker, not a changed production algorithm. Successful qualification now matches coefficients/support with multiplicities. This reviewer found no basis to rerun healthy qualification or D work.

`research_build.json` still contains its build-stage `qualification_pending` field, and the matrix qualification's `remaining` string describes its earlier stage. Read these as dated stage records together with the later native qualification and this admission; the final current-method summary should point to the completed qualification chain rather than presenting the stale strings as current status.

Acceptance covers this frozen finite C plan and existing evidence. It does not authorize starting C concurrently with D, changing the formal matrices/parameters, substituting original-E3 timing as a same-build baseline, selecting a production replacement, or adding C3. Actual formal results and certificate/coverage/fee qualification remain required. This is internal review, not external reproduction.
