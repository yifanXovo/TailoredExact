# R95 G2 raw archive delivery

The original `runner_full_block_g2/` directory remains in place. One create-only packaging process produced [full_block_g2_raw.zip](full_block_g2_raw.zip) and its separate [per-file manifest](full_block_g2_raw_manifest.json). The ZIP contains exactly the 35 raw files under the `runner_full_block_g2/` prefix; it contains neither the ZIP nor the manifest. Uncompressed length is 23,140,787 bytes. The ZIP is 2,486,021 bytes, SHA-256 `97fec1e75289ce2dba408c64963e60066046ee07185228bbd80ffc009277c1b3`. Manifest SHA-256 is `54976747e96f610b99d8612ff66781fd6f2b0456cfba90a5713a71df27babf62`.

The packaging process enumerated original files in sorted relative-path order, recorded each length and SHA-256, created the ZIP without overwriting an existing path, then reopened the ZIP and streamed every entry to check its path, length and SHA-256 against the original-file manifest. All **35 of 35** entries matched; the process exited 0. Its [complete launch-to-exit receipt](full_block_g2_archive_receipt.json) records **0.5073221 seconds** for inventory, compression, ZIP-stream verification and manifest creation. The separate stdout is [here](full_block_g2_archive_stdout.txt); stderr is empty. A later read-only SHA check of ZIP and manifest matched the printed hashes. This is post-experiment delivery cost; it did not launch the diagnostic again.

To extract without touching the original raw directory, choose a new destination and run in PowerShell:

```powershell
$destination = 'E:\codes\ExactEBRP\results\unified_exact_round95\extracted_copy'
if (Test-Path -LiteralPath $destination) { throw 'Choose a new empty destination' }
Expand-Archive -LiteralPath 'E:\codes\ExactEBRP\results\unified_exact_round95\full_block_g2_raw.zip' -DestinationPath $destination
```

The extracted files will be under `$destination\runner_full_block_g2\`. To recheck them against the manifest without rerunning any diagnostic:

```powershell
$manifest = Get-Content -Raw -LiteralPath 'E:\codes\ExactEBRP\results\unified_exact_round95\full_block_g2_raw_manifest.json' | ConvertFrom-Json
foreach ($entry in $manifest.files) {
    $path = Join-Path (Join-Path $destination 'runner_full_block_g2') ($entry.relative_path.Replace('/', '\'))
    $file = Get-Item -LiteralPath $path
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    if ($file.Length -ne $entry.length_bytes -or $hash -ne $entry.sha256) { throw "Mismatch: $path" }
}
```

The [G2 result](g2_diagnostic_report.md) and [independent audit](g2_independent_review.md) remain separate from this raw package.
