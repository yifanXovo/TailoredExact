param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$studyRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../results/unified_exact_round141')).Path
$workRoot = (Resolve-Path -LiteralPath 'E:/codes/ExactEBRP-work').Path.TrimEnd('\')
if (-not $studyRoot.StartsWith($workRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Study root outside authorized workspace' }
$recordPath = Join-Path $studyRoot 'cleanup_record.json'
if (Test-Path -LiteralPath $recordPath) { throw 'Cleanup already recorded; inspect instead of repeating' }
$intentPath = Join-Path $studyRoot 'cleanup_intent.json'
if (Test-Path -LiteralPath $intentPath) { throw 'Prior cleanup intent exists; inspect it without overwriting or automatic repeat' }
$public = Get-Content -Raw -LiteralPath (Join-Path $studyRoot 'public_restore_receipt.json') | ConvertFrom-Json
$pr = Get-Content -Raw -LiteralPath (Join-Path $studyRoot 'PR_delivery.json') | ConvertFrom-Json
$render = Get-Content -Raw -LiteralPath (Join-Path $studyRoot 'pdf_render_manifest.json') | ConvertFrom-Json
$visual = Get-Content -Raw -LiteralPath (Join-Path $studyRoot 'pdf_visual_review.json') | ConvertFrom-Json
$manifest = Get-Content -Raw -LiteralPath (Join-Path $studyRoot 'carrier_manifest.json') | ConvertFrom-Json
$pin = Get-Content -Raw -LiteralPath (Join-Path $studyRoot 'publication_pin.json') | ConvertFrom-Json
$candidate = Get-Content -Raw -LiteralPath (Join-Path $studyRoot 'candidate_manifest.json') | ConvertFrom-Json
if (-not $public.passed -or -not $pr.Draft -or $pr.state -ne 'OPEN' -or -not $visual.PASS) { throw 'Delivery/public/visual acceptance incomplete' }
$manifestSHA = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $studyRoot 'carrier_manifest.json')).Hash.ToLowerInvariant()
if ($manifestSHA -ne $public.manifest_SHA -or $manifestSHA -ne $pin.manifest_SHA -or $public.commit -ne $pin.commit -or $pr.science_commit -ne $public.commit) { throw 'Public/PR acceptance is for a different manifest/commit' }
$pdfSHA = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $studyRoot 'manuscript.pdf')).Hash.ToLowerInvariant()
if ($pdfSHA -ne $render.PDF_SHA -or $pdfSHA -ne $visual.PDF_SHA) { throw 'Final PDF identity mismatch' }
$renderSHA = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $studyRoot 'pdf_render_manifest.json')).Hash.ToLowerInvariant()
if ($visual.render_manifest_SHA -ne $renderSHA) { throw 'Visual review is for a different render manifest' }
$paperCarrier = @($manifest.carriers | Where-Object { $_.path.EndsWith('/science_and_paper.zip') })
if ($paperCarrier.Count -ne 1) { throw 'Missing unique paper carrier' }
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$paperPath = Join-Path $repoRoot $paperCarrier[0].path
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $paperPath).Hash.ToLowerInvariant() -ne $paperCarrier[0].SHA256) { throw 'Paper carrier changed' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($paperPath)
try {
    $stream = [IO.StreamReader]::new($zip.GetEntry($paperCarrier[0].member_index).Open())
    try { $index = $stream.ReadToEnd() | ConvertFrom-Json } finally { $stream.Dispose() }
    if ($index.PSObject.Properties['results/unified_exact_round141/manuscript.pdf'].Value.SHA256 -ne $pdfSHA) { throw 'Published carrier contains a different PDF' }
} finally { $zip.Dispose() }
$qaPath = Join-Path $studyRoot 'qa_pages'
$targets = @()
if (Test-Path -LiteralPath $qaPath) {
    $qaItem = Get-Item -LiteralPath $qaPath
    if ($qaItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refuse reparse directory' }
    $qaRoot = (Resolve-Path -LiteralPath $qaPath).Path.TrimEnd('\')
    if (-not $qaRoot.StartsWith($studyRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Preview root escaped study' }
    foreach ($file in Get-ChildItem -LiteralPath $qaRoot -File -Filter 'page-*.png') {
        $resolved = (Resolve-Path -LiteralPath $file.FullName).Path
        if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refuse reparse file' }
        if ([IO.Path]::GetDirectoryName($resolved) -ne $qaRoot -or $file.Name -notmatch '^page-[0-9]+\.png$') { throw 'Unexpected cleanup target' }
        $expected = @($render.pages | Where-Object { [IO.Path]::GetFileName($_.preview) -eq $file.Name })
        $digest = (Get-FileHash -Algorithm SHA256 -LiteralPath $resolved).Hash.ToLowerInvariant()
        if ($expected.Count -ne 1 -or $digest -ne $expected[0].PNG_SHA) { throw 'Preview hash not accepted by render manifest' }
        $targets += [pscustomobject]@{ path = $resolved; bytes = [long]$file.Length; SHA256 = $digest }
    }
}
$retained = @()
foreach ($path in @($candidate.production_PE, 'D:/gurobi1302/win64/bin/gurobi130.dll')) {
    $asset = Get-Item -LiteralPath $path
    $retained += [pscustomobject]@{ path = $asset.FullName; bytes = [long]$asset.Length; SHA256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $asset.FullName).Hash.ToLowerInvariant(); reason = 'Necessary verified runtime retained' }
}
$freeBefore = [long](Get-PSDrive -Name E).Free
$intent = [ordered]@{
    UTC = [DateTime]::UtcNow.ToString('o'); round = 141; apply = [bool]$Apply
    scope = 'Only accepted final-page PNG previews, reconstructible from the published final PDF'
    targets = $targets; public_commit = $public.commit; public_manifest_SHA = $public.manifest_SHA
    PR = $pr.url; old_round_deletions = 0; recursive_delete = $false
}
$utf8 = [Text.UTF8Encoding]::new($false)
if (-not $Apply) { $intent | ConvertTo-Json -Depth 12; exit 0 }
[IO.File]::WriteAllText($intentPath, ($intent | ConvertTo-Json -Depth 12) + "`n", $utf8)
$attempted = @(); $failure = $null
try {
    foreach ($target in $targets) {
        # Resolved, direct-child, non-reparse targets were checked before mutation.
        $attempted += $target
        Remove-Item -LiteralPath $target.path -Force
    }
} catch {
    $failure = $_.Exception.Message
} finally {
    $deleted = @($attempted | Where-Object { -not (Test-Path -LiteralPath $_.path) })
    $remaining = @($targets | Where-Object { Test-Path -LiteralPath $_.path })
    $deletedBytes = [long](($deleted | Measure-Object -Property bytes -Sum).Sum)
    try { $freeAfter = [long](Get-PSDrive -Name E).Free } catch { $freeAfter = $null }
    $record = [ordered]@{
    UTC = [DateTime]::UtcNow.ToString('o'); round = 141; completed = ($null -eq $failure -and $remaining.Count -eq 0)
    metadata_scope = 'Current-round page previews and explicit runtime/carrier metadata only'
    deleted = $deleted; deleted_files = $deleted.Count; deleted_file_bytes = $deletedBytes
    attempted = $attempted; remaining_previews = $remaining; error = $failure
    E_free_bytes_before = $freeBefore; E_free_bytes_after = $freeAfter
    free_space_scope = 'Observed volume free space; concurrent filesystem changes need not equal deleted logical bytes'
    retained_runtime = $retained
    retained_carrier_bytes = [long](($manifest.carriers | Measure-Object -Property bytes -Sum).Sum)
    retained = @('unique raw and failures', 'all current-round scientific carriers and paper source/PDF', 'all build/qualification failure records', 'active worktree', 'public owner/attempt/member receipts', 'original user content and every old round')
    unique_raw_deleted = $false; old_round_deletions = 0; public_commit = $public.commit; PR = $pr.url
    }
    [IO.File]::WriteAllText($recordPath, ($record | ConvertTo-Json -Depth 12) + "`n", $utf8)
}
$record | ConvertTo-Json -Depth 12
if ($null -ne $failure) { throw $failure }
