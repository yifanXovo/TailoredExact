# R94 full evidence archive handoff

The one authorized archive attempt succeeded. The local original `round94_full_evidence_v4.zip` is **113,905,614 bytes**, SHA256 `f16239464f23c80ec146743f6d4b3622022d3509afa304378b1bfe38e393fcb7`. It contains **136,691 unique members**, **431,133,063 uncompressed bytes**. The [member manifest](member_manifest.jsonl) SHA256 is `128dd941e64b6ac40a73bcc76418659f571b02fea2fca32b74e1cd102d399bc6`. The archiver reopened the ZIP and streamed **every member**, matching each path, uncompressed size and SHA256 to that pre-archive manifest; ZIP CRC was checked during each member read. [verification.json](verification.json) SHA256 `44651a19d37481e1eee21640e359349641af828f6b0f8a8be0032ab1fe60e846` records the pass. The original files remain in place; none were deleted or rewritten.

The archive covers all 12 paid formal raw directories (**136,512 members; 397,689,677 bytes**), all four qualification raw directories (63 members; 7,178,665 bytes), the other runner identity/lease/recovery/failure/summary/receipt files (47 members; 7,635,442 bytes), and top-level R94 plans, reports and outer/stdout/stderr records (54 members; 191,051 bytes). Another 15 members (18,438,228 bytes) preserve the frozen executable, key R94/R90/R88/R86 scripts, four original inputs, planning manifest and R87 reference identity. The 12 formal directories were individually checked for completion, native journal and the appropriate original `compact.lp` (P-GRB) or external LP models (ENS-C/LP-G). This includes both original paid F2 raw directories, all ten continuation raw directories, the failed original F2/ENS-C adapter audit, v2/v3/v4 recovery evidence and current split ledgers. No qualification search value entered the formal results.

The source-only archiver was `scripts/round94_archive_full_v4.py`, SHA256 `9bff870577fba9387fdcf4e224998c02b5597675f72ff24a1159c7bc00d3926c`. Its one complete Python command exited **0**, with external PowerShell launch-to-actual-exit wall **85.2064936 s**. [archive_outer_receipt.json](archive_outer_receipt.json) SHA256 `84ce54fc220d4827c0064b51bffec4d23a042b2e94e0d06877b98ab5ba9e2fb1` pins the real command, exit and stdout/stderr; stderr is empty. The archive itself, manifest, verification and outer receipt live in `archive_v4/` and were intentionally excluded from the ZIP to avoid self-reference. They must be retained together with the ZIP.

The archive cost is separate from the measured **10,190.2724150 s** formal outer wall, **4.4152170 s** qualification outer wall and **24.3734809 s** listed zero-Optimize prepare/check outer wall. Adding those known external measurements and this archive yields **10,304.2676065 s** of known instrumented wall across separate operations; the failed v3 read-only `require_prepared` check has no authoritative outer receipt, so its exact cost remains **unknown** and is excluded. Independent human/agent review time is also excluded. The archive is evidence preservation, not an additional experiment or a change to any U/L/certificate.

The ZIP is larger than GitHub's 100 MiB single-blob limit. For Git delivery, use the four **create-only binary parts** and [archive_parts_manifest.json](archive_parts_manifest.json), SHA256 `4e0cf2e1a889bbbfc552360560d8ebd5c1f87404c233cb1a33f3046392057eb2`. Parts 1–3 are each 33,554,432 bytes (32 MiB); part 4 is 13,242,318 bytes. Each is below the recorded 40 MiB maximum. The splitter streamed them in numeric order, independently re-read each part, and computed an ordered concatenation of **113,905,614 bytes** with SHA256 `f16239464f23c80ec146743f6d4b3622022d3509afa304378b1bfe38e393fcb7`, exactly the original verified ZIP. It did not re-run or re-compress the archive and did not revisit the 136,691 raw members. The original ZIP and all raw files remain local; **stage the parts and manifest for Git, not the over-limit original ZIP**.

| Git part | Bytes | SHA256 |
|---|---:|---|
| `round94_full_evidence_v4.zip.part0001` | 33,554,432 | `24e13a7926dd7da641253e91524142f6f30fb1e7dc1a2a79869c591c569d1b57` |
| `round94_full_evidence_v4.zip.part0002` | 33,554,432 | `67e38077b7d41788f2042548d6ac7accc6681a65665d218cf0d417caa4bf6b00` |
| `round94_full_evidence_v4.zip.part0003` | 33,554,432 | `eddc7e75421e32c969a2ef3bae80c340d75e78ec6cf6323ccd7bbf53d8830a24` |
| `round94_full_evidence_v4.zip.part0004` | 13,242,318 | `01294ef3605df0cc9a6c94e3618cd70fb4753b3bfbc9b0e8c7002df65e688791` |

PowerShell reconstruction at a **new** path, with per-part and final length/SHA verification:

```powershell
$base = 'E:\codes\ExactEBRP\results\unified_exact_round94\archive_v4'
$manifest = Get-Content -LiteralPath (Join-Path $base 'archive_parts_manifest.json') -Raw | ConvertFrom-Json
$output = Join-Path $base 'reconstructed_copy\round94_full_evidence_v4.zip'
[System.IO.Directory]::CreateDirectory((Split-Path -Parent $output)) | Out-Null
$destination = [System.IO.File]::Open($output, [System.IO.FileMode]::CreateNew)
try {
    foreach ($part in $manifest.parts) {
        $path = Join-Path $base $part.file
        if ((Get-Item -LiteralPath $path).Length -ne [long]$part.size_bytes) { throw "Part size mismatch: $path" }
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $part.sha256) { throw "Part SHA mismatch: $path" }
        $source = [System.IO.File]::OpenRead($path)
        try { $source.CopyTo($destination) } finally { $source.Dispose() }
    }
} finally { $destination.Dispose() }
if ((Get-Item -LiteralPath $output).Length -ne [long]$manifest.source_size_bytes) { throw 'Rebuilt ZIP size mismatch' }
if ((Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.source_sha256) { throw 'Rebuilt ZIP SHA mismatch' }
```

The sole split command exited 0 in **0.4002033 s** launch-to-actual-exit. [split_outer_receipt.json](split_outer_receipt.json) SHA256 `f19915e15265e36d663029d58f6405677aa4bb56a660909649f019ad9ca0012f` pins the command and empty stderr; `scripts/round94_split_archive_v4.py` SHA256 `6233b43eaf1be226796ab755f87f67848f480ab658b4ea2d1b195890a81caf09` pins the splitter. Known instrumented wall including formal, qualification, listed prepare/check, archive and split is **10,304.6678098 s**. The failed v3 read-only self-check remains exact-cost **unknown**.

The research conclusion and 12-arm table are [final_report.md](../final_report.md), [formal_results_v4_report.md](../formal_results_v4_report.md), and [formal_evidence_summary_v4.json](../formal_evidence_summary_v4.json). Independent result review is [independent_final_review.md](../independent_final_review.md). With this split handoff written, the R94 evidence tree and archive are closed to further writing pending root's Git/PR integration.
