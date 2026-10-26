# Independent final-reader manifest binding correction

Closeout: the corrected metered `final02` invocation **PASSED** with source SHA `29f45ab15299cd848181bbe94e97a272858826fe55f29e0077e27dbb2f20e5a6`, receipt SHA `ecc9bf590846460915c07679d99da4f729028087c5cc2bebd6e1aea0c632ef70` and outer verification fee 15.516931800055318 seconds. No substantive rerun followed this PASS. The exact failed-source bytes are now preserved in `final01/audit_source.py`, verified SHA `a4159a14c5c481e85eebb8dd6e0607cd11a39420e6427eedb870359eaf89d54d`. The preparation/pending wording below is retained as the correction history; the completed finite numerical disposition is in `review/final_independent_review.md`.

The metered `final01` attempt (script SHA `a4159a14c5c481e85eebb8dd6e0607cd11a39420e6427eedb870359eaf89d54d`) stopped in its first selection-byte guard with `selection-era bytes changed: experiment_manifest.json`. Its receipt and 0.301002-second outer fee remain preserved. No formal endpoint, matrix, physical or proof-chain stage ran in that attempt.

Light source/metadata inspection finds only a line-ending mismatch. The actual manifest has 47,407 bytes and 1,872 CRLF pairs, SHA256 `4d9b4851d152eacf64f2241c9099049e29961f0c645d5e4fb1dba3536b9efd3d`. Selection commit `44ffd46367478dd784cc6a9595bfd3df174be8a7` contains the same text with LF: 45,535 bytes, SHA256 `74c0b57b37a62bd1141fa03d5ebb3a30d9906e8295ef14906a0dd6626c8af7f9`. Replacing only CRLF with LF gives exact byte equality, with no remaining carriage returns and identical parsed JSON. Git reports `i/lf w/crlf`; no content diff is present. The selected tuning file, PRM, input manifest and prior independent review/script/receipt are already byte-identical to that commit.

The admitted raw manifest is independently anchored before selection: `training/01_S12_S2_q0/identity.json` has SHA256 `7a2627b7d74a84d04030e742637b8d61a40524e92632467f917376a3d6994963`, exactly the first training identity SHA in the byte-exact committed `tuning_selection.json`. That identity's `prereg_sha256` is the current raw manifest SHA `4d9b...efd3d`. Thus the working manifest is the exact preselection admitted object, not a post-outcome replacement.

The reviewer script now permits only this explicit manifest case. It requires both the exact preselection raw-byte anchor and exact CRLF/LF-only committed-text/JSON equality, and reports actual, Git-blob and canonical hashes separately. It does not normalize arbitrary whitespace, accept a JSON-only semantic substitution, bypass any selected-parameter binding, or rewrite the manifest, raw files, sources or clocks. Other selection-era files retain strict raw-byte equality. This is an audit-reader correction; all experimental methods, parameters, positions, fixed samples and numerical requirements remain unchanged.

The corrected next attempt must use a fresh outer verification label and new attempt directory, for example:

```
python -B results/unified_exact_round127/review/final_independent_audit.py --formal-idle-confirmed --attempt final02 --fee-label final_independent_review_02
```

Only the source, compact identity/line-ending metadata and AST syntax were inspected while preparing this correction. The substantive corrected audit remains pending its metered invocation.
