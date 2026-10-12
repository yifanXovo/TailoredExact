# Round116 evidence: safe publication supersedes the original carrier

Use `results/unified_exact_round117/safe_evidence/manifest.json` and the numbered
parts it lists. The original R116 parts are removed from the current branch
because they duplicate web client credentials and response cookies. Historical
pack/export/restore receipts and original SHA256s remain historical identities;
they do not validate the new safe bytes and are not instructions to download an
old carrier. Git history and PR178 still require separate owner treatment.

The safe carrier preserves every scientific member of the original R116
payload, including its V100 history, failed pending arm, original negative
results, producer/verification clocks, routes, model records and paid fees.
Explicit exceptions are the two HTML runtime bodies, request header metadata,
nested snapshot receipts and publication engineering code/instructions. The
station-information response and mathematical input data are unchanged.
See the Round117 redaction manifest and scientific-integrity receipt.

From a checkout of the safe branch, run:

```text
python scripts/round117_release.py restore --root <safe-checkout> --destination <new-empty-directory> --out <receipt-path>
python <new-empty-directory>/scripts/round117_validate.py --root <new-empty-directory> --out <validation-directory>
python scripts/publication_security.py --root <safe-checkout> --paths results/unified_exact_round117/safe_evidence --out <scan-path>
```

Restore verifies the new manifest and part SHA256s, rejects unsafe archive paths,
and verifies every restored file. Validation reads only that restored root,
reconstructs four V20/V50 roles and their existing 16 observations/24 pairs,
and preserves their numerical qualifications. It uses no contaminated HTML,
old carrier, network, native solver, reference exporter or original-worktree
fallback. It neither reruns the production algorithm nor attempts full V100
model recovery. No new input files are generated.

The source text extraction preserves license/discovery provenance while removing
scripts and client configuration. Response headers use an explicit whitelist.
Original SHA256s prove historical byte identities, not recoverability of removed
secrets. The old R116 evaluation remains BLOCKED (18 starts,17 qualified arms,
24/36 evaluable pairs); the four-role layer is descriptive evidence already seen.
