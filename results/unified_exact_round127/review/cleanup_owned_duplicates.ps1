$ErrorActionPreference = 'Stop'
$workspaceRoot = 'E:\codes\ExactEBRP-work'
$taskRoot = 'E:\codes\ExactEBRP-work\worktrees\round127'
$resultRoot = Join-Path $taskRoot 'results\unified_exact_round127'
$temporaryRoot = Join-Path $workspaceRoot 'temp\round127'
$restoreBase = Join-Path $workspaceRoot 'restore'
$actions = [System.Collections.Generic.List[object]]::new()
$cleanupErrors = [System.Collections.Generic.List[object]]::new()
$executedScriptText = Get-Content -LiteralPath $PSCommandPath -Raw -Encoding UTF8
$executedScriptSHA = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()

function Read-Record([string]$recordPath) {
    return Get-Content -LiteralPath $recordPath -Raw -Encoding UTF8 | ConvertFrom-Json
}
function Read-PublishedRecord([string]$relativePath) {
    $declarations = @($export.files | Where-Object { $_.path -eq $relativePath })
    if ($declarations.Count -ne 1) { throw "Missing/duplicate published cleanup basis: $relativePath" }
    $basisPath = Join-Path $taskRoot $relativePath
    $basis = Assert-Owned $basisPath $taskRoot
    if ($basis.PSIsContainer -or [long]$basis.Length -ne [long]$declarations[0].bytes) { throw "Published cleanup basis size mismatch: $relativePath" }
    if ((Get-FileHash -LiteralPath $basis.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $declarations[0].SHA256) { throw "Published cleanup basis SHA mismatch: $relativePath" }
    return Read-Record $basis.FullName
}
function Assert-Owned([string]$targetPath, [string]$allowedParent) {
    $absolute = [System.IO.Path]::GetFullPath($targetPath)
    $parentAbsolute = [System.IO.Path]::GetFullPath($allowedParent).TrimEnd('\') + '\'
    if (-not $absolute.StartsWith($parentAbsolute, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Target outside the expressly owned parent: $absolute"
    }
    $item = Get-Item -LiteralPath $absolute -Force
    $ancestor = $item
    while ($null -ne $ancestor) {
        if (($ancestor.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse target or ancestor retained: $($ancestor.FullName)"
        }
        if ($ancestor -is [System.IO.FileInfo]) { $ancestor = $ancestor.Directory }
        else { $ancestor = $ancestor.Parent }
    }
    return $item
}
function Remove-OwnedFile([string]$targetPath, [string]$expectedSHA, [string]$allowedParent, [string]$reason) {
    if (-not (Test-Path -LiteralPath $targetPath)) {
        $actions.Add([pscustomobject]@{path=$targetPath;status='ALREADY_ABSENT';logical_bytes=0;reason=$reason})
        return
    }
    $item = Assert-Owned $targetPath $allowedParent
    if ($item.PSIsContainer) { throw "File target is a directory: $targetPath" }
    $actualSHA = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualSHA -ne $expectedSHA) { throw "Changed file retained: $targetPath" }
    $bytes = [long]$item.Length
    Remove-Item -LiteralPath $item.FullName -Force
    if (Test-Path -LiteralPath $item.FullName) { throw "File still exists: $targetPath" }
    $actions.Add([pscustomobject]@{path=$item.FullName;status='REMOVED';logical_bytes=$bytes;SHA256=$actualSHA;reason=$reason})
}

$publicPath = Join-Path $resultRoot 'public_restore_receipt.json'
$public = Read-Record $publicPath
if ($public.status -ne 'PASS' -or $public.Optimize -ne 0 -or $public.native_solver_starts -ne 0) {
    throw 'Successful solver-free public recovery is required before any deletion.'
}
$live = Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(ExactEBRP|gurobi_cl|cmake|ninja|g\+\+|cc1plus|MSBuild)\.exe$' }
if ($live) { throw 'Native/build process active; retain all cleanup targets.' }
$export = Read-Record (Join-Path $resultRoot 'export_manifest.json')
if ((Get-FileHash -LiteralPath (Join-Path $resultRoot 'export_manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $public.manifest_SHA) {
    throw 'Local science-A export manifest differs from the recovered public manifest.'
}
$cleanupSourceDeclarations = @($export.files | Where-Object { $_.path -eq 'results/unified_exact_round127/review/cleanup_owned_duplicates.ps1' })
if ($cleanupSourceDeclarations.Count -ne 1 -or $cleanupSourceDeclarations[0].SHA256 -ne $executedScriptSHA) {
    throw 'Executed cleanup source differs from the science-A published source.'
}
# Read and bind every deletion-authorizing record before the first mutation.
$archives = Read-PublishedRecord 'results/unified_exact_round127/raw_archive_manifest.json'
if ((Get-FileHash -LiteralPath (Join-Path $resultRoot 'raw_archive_manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $export.raw_manifest_SHA) { throw 'Published raw-manifest binding differs.' }
$compaction = Read-PublishedRecord 'results/unified_exact_round127/review/member_index_compaction.json'
$validatedReviews = @{}
foreach ($reviewName in @('pdf_visual_review_attempt01.json','pdf_visual_review.json')) {
    $validatedReviews[$reviewName] = Read-PublishedRecord ('results/unified_exact_round127/review/' + $reviewName)
}
$retainedPortableRelative = 'results/unified_exact_round127/review/portable_local_receipt.json'
$retainedPortableRecord = Read-PublishedRecord $retainedPortableRelative
if ($retainedPortableRecord.status -ne 'PASS') { throw 'Retained portable-local result is not PASS.' }
$retainedPortableSHA = @($export.files | Where-Object { $_.path -eq $retainedPortableRelative })[0].SHA256

try {
    $destination = [System.IO.Path]::GetFullPath([string]$public.destination)
    $restoreItem = Assert-Owned $destination $restoreBase
    if (-not $restoreItem.PSIsContainer -or $restoreItem.Name -notlike 'round127-public-*') { throw 'Unexpected restore directory name.' }
    $state = Read-Record (Join-Path $destination 'restore_state.json')
    if ($state.commit -ne $public.commit -or $state.owner -ne 'Round127 public science-A recovery') { throw 'Restore ownership/commit mismatch.' }
    $expectedCount = [long]$public.files + 3 + [long]$public.archives.Count
    $expectedBytes = [long]($export.files | Measure-Object -Property bytes -Sum).Sum
    $expectedBytes += [long](Get-Item -LiteralPath (Join-Path $destination 'results\unified_exact_round127\export_manifest.json')).Length
    $expectedBytes += [long](Get-Item -LiteralPath (Join-Path $destination 'restore_state.json')).Length
    $expectedBytes += [long](Get-Item -LiteralPath (Join-Path $destination 'portable_check_receipt.json')).Length
    foreach ($archive in $archives.archives) {
        $expectedCount += [long]$archive.file_count
        $expectedBytes += [long]$archive.uncompressed_bytes + [long]$archive.compressed_bytes
    }
    $verifiedBefore = (Get-Item -LiteralPath $publicPath).LastWriteTimeUtc
    $directories = [System.Collections.Generic.Stack[System.IO.DirectoryInfo]]::new()
    $directories.Push($restoreItem)
    $actualCount = [long]0
    $actualBytes = [long]0
    while ($directories.Count -gt 0) {
        $directory = $directories.Pop()
        foreach ($child in Get-ChildItem -LiteralPath $directory.FullName -Force) {
            if (($child.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Restore reparse entry retained: $($child.FullName)" }
            if ($child.LastWriteTimeUtc -gt $verifiedBefore) { throw "Restore entry changed after recovery PASS: $($child.FullName)" }
            if ($child.PSIsContainer) { $directories.Push($child) }
            else {
                $actualCount++
                $actualBytes += [long]$child.Length
            }
        }
    }
    if ($actualCount -ne $expectedCount -or $actualBytes -ne $expectedBytes) { throw "Unexpected restore inventory retained: files $actualCount/$expectedCount, bytes $actualBytes/$expectedBytes" }
    Remove-Item -LiteralPath $restoreItem.FullName -Recurse -Force
    if (Test-Path -LiteralPath $destination) { throw 'Restore tree remains after removal.' }
    $actions.Add([pscustomobject]@{path=$destination;status='REMOVED';logical_bytes=$actualBytes;files=$actualCount;reason='Fresh owned public recovery duplicate; full per-member verification retained in the external PASS receipt.'})
} catch { $cleanupErrors.Add([pscustomobject]@{target='owned restore expansion';error=$_.Exception.Message}) }

foreach ($archive in $archives.archives) {
    try { Remove-OwnedFile ([string]$archive.temporary_complete_archive) ([string]$archive.SHA256) (Join-Path $temporaryRoot 'archives') 'Complete ZIP duplicate; identical public pieces, member indexes and authoritative raw retained.' }
    catch { $cleanupErrors.Add([pscustomobject]@{target=$archive.temporary_complete_archive;error=$_.Exception.Message}) }
}
try {
    Remove-OwnedFile ([string]$compaction.old_manifest_preserved_locally) ([string]$compaction.old_manifest_SHA256) (Join-Path $temporaryRoot 'archives') 'Plain member-index duplicate; exact complete values retained in verified public compressed indexes.'
} catch { $cleanupErrors.Add([pscustomobject]@{target='plain member-index duplicate';error=$_.Exception.Message}) }
foreach ($reviewName in @('pdf_visual_review_attempt01.json','pdf_visual_review.json')) {
    $review = $validatedReviews[$reviewName]
    foreach ($rendered in $review.render_receipt.rendered) {
        try { Remove-OwnedFile ([string]$rendered.path) ([string]$rendered.SHA256) (Join-Path $temporaryRoot 'pdf_review') 'Regenerable page PNG; PDF, source and actual visual/render receipts retained.' }
        catch { $cleanupErrors.Add([pscustomobject]@{target=$rendered.path;error=$_.Exception.Message}) }
    }
}
try {
    Remove-OwnedFile (Join-Path $taskRoot 'portable_check_receipt.json') $retainedPortableSHA $taskRoot 'Exact duplicate of retained portable-local PASS receipt.'
} catch { $cleanupErrors.Add([pscustomobject]@{target='portable-local duplicate';error=$_.Exception.Message}) }

$removedBytes = [long]($actions | Where-Object status -eq 'REMOVED' | Measure-Object -Property logical_bytes -Sum).Sum
$receipt = [ordered]@{
    status=$(if ($cleanupErrors.Count -eq 0) {'PASS'} else {'PARTIAL_WITH_RETAINED_TARGETS'})
    UTC=[datetime]::UtcNow.ToString('o');public_science_commit=$public.commit
    logical_bytes_removed=$removedBytes;volume_free_space_gain_measured=$false
    actions=$actions.ToArray();errors=$cleanupErrors.ToArray()
    script_SHA256=$executedScriptSHA
    executed_script=$executedScriptText
    preserved='Authoritative raw/models/tables; failed records; E0/E1 and original DLL; all old worktrees; user dirty; unpublished unique material.'
}
$receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $resultRoot 'cleanup_receipt.json') -Encoding UTF8
[pscustomobject]@{status=$receipt.status;logical_bytes_removed=$removedBytes;actions=$actions.Count;errors=$cleanupErrors.Count} | ConvertTo-Json -Compress
if ($cleanupErrors.Count -gt 0) { exit 1 }
