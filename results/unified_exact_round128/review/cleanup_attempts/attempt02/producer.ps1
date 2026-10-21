param([string]$RoundRoot = 'E:\codes\ExactEBRP-work\worktrees\round128')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$expectedRoot = [IO.Path]::GetFullPath('E:\codes\ExactEBRP-work\worktrees\round128')
$actualRoot = (Resolve-Path -LiteralPath $RoundRoot).Path
if ($actualRoot -ne $expectedRoot) { throw 'Unexpected round workspace' }
$out = Join-Path $actualRoot 'results\unified_exact_round128'
$public = Get-Content -LiteralPath (Join-Path $out 'public_restore_receipt.json') -Raw | ConvertFrom-Json
if ($public.status -ne 'PASS' -or $public.Optimize -ne 0) { throw 'Successful finite public recovery is required' }
$archives = Get-Content -LiteralPath (Join-Path $out 'raw_archive_manifest.json') -Raw | ConvertFrom-Json
$native = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(ExactEBRP|Round128ExportE2)\.exe$' -and $_.ExecutablePath -like 'E:\codes\ExactEBRP-work\build-cache\round128\*' })
if ($native.Count) { throw 'Owned native processes are still active' }
$tempRoot = [IO.Path]::GetFullPath('E:\codes\ExactEBRP-work\temp\round128')
$restoreBase = [IO.Path]::GetFullPath('E:\codes\ExactEBRP-work\restore')
$actions = [Collections.Generic.List[object]]::new()
$errors = [Collections.Generic.List[object]]::new()
$retained = [Collections.Generic.List[object]]::new()

function Assert-NoLinkedParents([string]$Path) {
    $checked = Get-Item -LiteralPath $Path -Force
    while ($null -ne $checked) {
        if ($checked.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked cleanup ancestor; retain target' }
        $checked = $checked.Parent
    }
}
Assert-NoLinkedParents $actualRoot
Assert-NoLinkedParents $tempRoot
Assert-NoLinkedParents $restoreBase

function Get-Round128SHA256([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $digest = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($digest.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $digest.Dispose(); $stream.Dispose() }
}
$pdf = Join-Path $out 'manuscript.pdf'
if (-not (Test-Path -LiteralPath $pdf)) { throw 'Final PDF is required before cleanup' }
$hash = Get-Round128SHA256 $pdf
$before = (Get-Volume -DriveLetter E).SizeRemaining

function Remove-VerifiedDuplicate([string]$Path, [string]$Hash) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    if (-not $resolved.StartsWith($tempRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Duplicate outside owned temp root' }
    $item = Get-Item -LiteralPath $resolved -Force
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Unexpected duplicate type/link' }
    Assert-NoLinkedParents $item.Directory.FullName
    if ((Get-Round128SHA256 $resolved) -ne $Hash.ToLowerInvariant()) { throw 'Duplicate byte identity failed' }
    $size = $item.Length
    Remove-Item -LiteralPath $resolved -Force
    $actions.Add([ordered]@{ path=$resolved; logical_bytes=$size; kind='verified duplicate/reconstructible file' })
}

foreach ($archive in $archives.archives) {
    try {
        foreach ($piece in $archive.pieces) {
            $piecePath = Join-Path $actualRoot $piece.path
            if ((Get-Round128SHA256 $piecePath) -ne $piece.SHA256) { throw 'Authoritative carrier piece mismatch' }
        }
        Remove-VerifiedDuplicate $archive.temporary_complete_archive $archive.SHA256
    } catch { $errors.Add([ordered]@{ action=$archive.name; error=$_.Exception.Message }) }
}

$restore = [IO.Path]::GetFullPath([string]$public.destination)
try {
    if (-not $restore.StartsWith($restoreBase + '\round128-', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected recovery target' }
    if (Test-Path -LiteralPath $restore) {
        $resolved = (Resolve-Path -LiteralPath $restore).Path
        if ($resolved -ne $restore -or $resolved -eq $restoreBase) { throw 'Recovery resolution mismatch' }
        Assert-NoLinkedParents $resolved
        $state = Get-Content -LiteralPath (Join-Path $resolved 'restore_state.json') -Raw | ConvertFrom-Json
        if ($state.owner -ne 'Round128 single science-commit recovery' -or $state.commit -ne $public.science_commit) { throw 'Recovery ownership/commit mismatch' }
        $items = @(Get-Item -LiteralPath $resolved -Force) + @(Get-ChildItem -LiteralPath $resolved -Recurse -Force)
        if (@($items | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw 'Recovery contains a link; retain it' }
        $size = ($items | Where-Object { -not $_.PSIsContainer } | Measure-Object -Property Length -Sum).Sum
        Remove-Item -LiteralPath $resolved -Recurse -Force
        $actions.Add([ordered]@{ path=$resolved; logical_bytes=$size; kind='verified successful duplicate recovery expansion and transport' })
    }
} catch { $errors.Add([ordered]@{ action=$restore; error=$_.Exception.Message }) }

$pageRoot = Join-Path $tempRoot 'pdf_review'
if (Test-Path -LiteralPath $pageRoot) {
    foreach ($receipt in Get-ChildItem -LiteralPath $pageRoot -Filter render_receipt.json -Recurse -File) {
        $render = Get-Content -LiteralPath $receipt.FullName -Raw | ConvertFrom-Json
        foreach ($page in $render.rendered) {
            try { Remove-VerifiedDuplicate $page.path $page.SHA256 }
            catch { $errors.Add([ordered]@{ action=$page.path; error=$_.Exception.Message }) }
        }
    }
}
if (Test-Path -LiteralPath $pdf) {
    $pdfRoot = Join-Path $tempRoot 'pdf'
    if (Test-Path -LiteralPath $pdfRoot) {
        foreach ($copy in Get-ChildItem -LiteralPath $pdfRoot -Filter reading.pdf -Recurse -File) {
            if ((Get-Round128SHA256 $copy.FullName) -ne $hash) {
                $retained.Add([ordered]@{ path=$copy.FullName; reason='Distinct prior document-export evidence; retained with its source and logs' })
                continue
            }
            try { Remove-VerifiedDuplicate $copy.FullName $hash }
            catch { $errors.Add([ordered]@{ action=$copy.FullName; error=$_.Exception.Message }) }
        }
    }
}
$after = (Get-Volume -DriveLetter E).SizeRemaining
$receipt = [ordered]@{
    status = $(if ($errors.Count) { 'PARTIAL_RETAINED_ERRORS' } else { 'PASS' })
    UTC = [DateTime]::UtcNow.ToString('o')
    actions = @($actions.ToArray())
    failures_retained = @($errors.ToArray())
    distinct_prior_export_evidence_retained = @($retained.ToArray())
    removed_logical_bytes = ($actions | Measure-Object -Property logical_bytes -Sum).Sum
    E_free_before_bytes = $before
    E_free_after_bytes = $after
    observed_volume_free_delta_bytes = $after - $before
    volume_delta_is_observed_not_inferred_or_fully_attributed = $true
    authoritative_raw_models_tables_failures_final_PE_original_E0_E1_DLL_retained = $true
    old_worktrees_and_user_files_untouched = $true
    git_gc_prune_repack_or_force_push = $false
}
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'cleanup_receipt.json') -Encoding utf8
$receipt | Select-Object status,removed_logical_bytes,E_free_before_bytes,E_free_after_bytes,observed_volume_free_delta_bytes | ConvertTo-Json -Compress
