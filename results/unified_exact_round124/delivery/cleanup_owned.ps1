$ErrorActionPreference = 'Stop'
$timer = [Diagnostics.Stopwatch]::StartNew()
$base = 'E:\codes\ExactEBRP-work\worktrees\round124\results\unified_exact_round124'
$remote = Get-Content -LiteralPath "$base\delivery\remote_before_cleanup.json" -Raw | ConvertFrom-Json
$receipt = Get-Content -LiteralPath "$base\delivery\public_reconstruction.json" -Raw | ConvertFrom-Json
if (-not $remote.observed_PR.draft -or -not $receipt.arithmetic_typed_equal_except_measured_elapsed) {
    throw 'Completed public restore and remote readback are required'
}
$initial = Get-Content -LiteralPath "$base\initialization.json" -Raw | ConvertFrom-Json -AsHashtable
foreach ($entry in $initial.tracked_dirty_SHA256.GetEnumerator()) {
    $digest = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path 'E:\codes\ExactEBRP' $entry.Key)).Hash.ToLowerInvariant()
    if ($digest -ne $entry.Value) { throw 'User file changed' }
}
$active = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^(python|curl|ExactEBRP|gurobi|cplex)' -and
    ($_.CommandLine -like '*round124-public-A*' -or $_.CommandLine -like '*ExactEBRP-work\temp\round124*')
})
if ($active.Count) { throw 'An associated process remains active' }

$roots = @('E:\codes\ExactEBRP-work\restore\round124-public-A',
           'E:\codes\ExactEBRP-work\temp\round124')
$expectedRelative = @($receipt.transfers | ForEach-Object { $_.path })
$total = 0L
$removed = @()
$before = (Get-PSDrive E).Free
foreach ($root in $roots) {
    $resolvedRoot = (Resolve-Path -LiteralPath $root).Path
    if ($resolvedRoot -ne $root -or -not $resolvedRoot.StartsWith('E:\codes\ExactEBRP-work\',[StringComparison]::OrdinalIgnoreCase)) {
        throw 'Target must equal the recorded owned absolute path'
    }
    foreach ($p in @('E:\codes\ExactEBRP-work',(Split-Path -Parent $root),$root)) {
        if ((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw 'Reparse ancestor rejected'
        }
    }
    $items = @(Get-ChildItem -LiteralPath $root -Recurse -Force)
    if (@($items | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) {
        throw 'Reparse descendant rejected'
    }
    $files = @($items | Where-Object { -not $_.PSIsContainer })
    $allowed = if ($root -like '*\restore\*') { $expectedRelative } else { @('pr_body.md') }
    foreach ($f in $files) {
        $relative = [IO.Path]::GetRelativePath($root,$f.FullName).Replace('\','/')
        if ($relative -notin $allowed) { throw "Unexpected file: $relative" }
    }
    # Remove only the enumerated allowlisted files. No recursive removal.
    foreach ($f in $files) {
        $total += $f.Length
        Remove-Item -LiteralPath $f.FullName -Force
    }
    # Remove only empty owned directories, deepest first.
    foreach ($dir in @($items | Where-Object { $_.PSIsContainer } | Sort-Object { $_.FullName.Length } -Descending)) {
        if (@(Get-ChildItem -LiteralPath $dir.FullName -Force).Count) { throw 'Directory is not empty' }
        Remove-Item -LiteralPath $dir.FullName -Force
    }
    if (@(Get-ChildItem -LiteralPath $root -Force).Count) { throw 'Owned root is not empty' }
    Remove-Item -LiteralPath $root -Force
    $removed += [ordered]@{Resolved=$root;Files=$files.Count;AbsentAfter=(-not (Test-Path -LiteralPath $root))}
}
$after = (Get-PSDrive E).Free
$summary = [ordered]@{
    Completed_UTC=[DateTime]::UtcNow.ToString('o')
    Deleted=$removed
    DeletedLogicalBytes=$total
    EFreeBefore=$before
    EFreeAfter=$after
    ObservedFreeDelta=$after-$before
    ElapsedSeconds=$timer.Elapsed.TotalSeconds
    Method='allowlisted individual files followed by verified empty directories; no recursive remove'
    PriorRejectedAttempt='Automatic approval review blocked a recursive removal command before execution; only stated reason: blocked by policy'
    Retained='authoritative draft, sources, evidence receipts, all earlier worktrees/user/native/runtime/license assets'
    AutomaticGitMaintenanceSeparate=$true
}
$json = $summary | ConvertTo-Json -Depth 5
$json | Set-Content -LiteralPath "$base\delivery\cleanup_summary.json" -Encoding utf8
$json | Set-Content -LiteralPath 'E:\codes\ExactEBRP-work\evidence\round124\cleanup_summary.json' -Encoding utf8
$json
