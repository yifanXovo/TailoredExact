param([Parameter(Mandatory=$true)][string]$PlanPath,[Parameter(Mandatory=$true)][string]$ReceiptPath)
$ErrorActionPreference = 'Stop'
$taskStarted = [DateTimeOffset]::UtcNow
$taskTick = [Diagnostics.Stopwatch]::StartNew()
$taskActions = [Collections.Generic.List[object]]::new()
$taskBefore = ([IO.DriveInfo]::new('E:\')).AvailableFreeSpace
$taskFailure = $null

function Get-TaskHash([string]$Literal) {
    $stream = [IO.File]::OpenRead($Literal)
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $hasher.Dispose(); $stream.Dispose() }
}
function Assert-TaskContained([string]$Literal,[string]$Parent) {
    $absolute = [IO.Path]::GetFullPath($Literal).TrimEnd('\','/')
    $root = [IO.Path]::GetFullPath($Parent).TrimEnd('\','/')
    if (-not $absolute.StartsWith($root + '\',[StringComparison]::OrdinalIgnoreCase)) { throw "Target escapes the declared owned root: $absolute" }
    $cursor = $absolute
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            if (([IO.File]::GetAttributes($cursor) -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse point rejected: $cursor" }
        }
        $next = [IO.Path]::GetDirectoryName($cursor)
        if ($next -eq $cursor) { break }
        $cursor = $next
    }
    return $absolute
}
function Assert-TaskPlainTree([string]$Literal) {
    $stack = [Collections.Generic.Stack[string]]::new(); $stack.Push($Literal)
    while ($stack.Count -gt 0) {
        $directory = $stack.Pop()
        foreach ($entry in [IO.Directory]::EnumerateFileSystemEntries($directory)) {
            $attributes = [IO.File]::GetAttributes($entry)
            if (($attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse member rejected: $entry" }
            if (($attributes -band [IO.FileAttributes]::Directory) -ne 0) { $stack.Push($entry) }
        }
    }
}

$taskReceipt = Assert-TaskContained $ReceiptPath 'E:\codes\ExactEBRP-work\worktrees\round129\results\unified_exact_round129'
if (Test-Path -LiteralPath $taskReceipt) { throw 'Use a new cleanup receipt path; preserve previous attempts' }

try {
    $taskPlan = Get-Content -LiteralPath $PlanPath -Raw | ConvertFrom-Json
    if ($taskPlan.owner -ne 'Round129' -or $taskPlan.workspace.Replace('/','\') -ne 'E:\codes\ExactEBRP-work\worktrees\round129') { throw 'Unexpected cleanup owner/workspace' }
    if ($taskPlan.temporary_root.Replace('/','\') -ne 'E:\codes\ExactEBRP-work\temp\round129') { throw 'Unexpected temporary root' }
    if ($taskPlan.restore_parent.Replace('/','\') -ne 'E:\codes\ExactEBRP-work\restore') { throw 'Unexpected restore parent' }
    $taskLive = Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(ExactEBRP|gurobi_cl|cmake|ninja|g\+\+|cc1plus|MSBuild)\.exe$' }
    if ($taskLive) { throw 'Native/build task active; postpone owned cleanup' }
    foreach ($binding in @(@($taskPlan.public_recovery_receipt,$taskPlan.public_recovery_receipt_SHA),@($taskPlan.protection_receipt,$taskPlan.protection_receipt_SHA))) {
        if ((Get-TaskHash $binding[0]) -ne $binding[1]) { throw 'Required retained receipt changed' }
    }
    $taskRecovery = Get-Content -LiteralPath $taskPlan.public_recovery_receipt -Raw | ConvertFrom-Json
    if ($taskRecovery.status -ne 'PASS') { throw 'Public recovery did not pass' }
    $taskRestore = Assert-TaskContained $taskPlan.restore.path $taskPlan.restore_parent
    if ($taskRestore -ne [IO.Path]::GetFullPath($taskRecovery.destination)) { throw 'Recovery target mismatch' }
    if (Test-Path -LiteralPath $taskRestore) {
        if ((Get-TaskHash (Join-Path $taskRestore 'restore_state.json')) -ne $taskPlan.restore.state_SHA) { throw 'Restore owner state changed' }
        $taskState = Get-Content -LiteralPath (Join-Path $taskRestore 'restore_state.json') -Raw | ConvertFrom-Json
        if ($taskState.commit -ne $taskPlan.restore.science_commit -or $taskState.owner -notlike '*Round129*') { throw 'Restore owner/commit mismatch' }
        Assert-TaskPlainTree $taskRestore
    }
    $taskValidated = [Collections.Generic.List[object]]::new()
    foreach ($item in @($taskPlan.files)) {
        $absolute = Assert-TaskContained $item.path $taskPlan.temporary_root
        $extension = [IO.Path]::GetExtension($absolute).ToLowerInvariant()
        if (($item.kind -eq 'duplicate_archive' -and $extension -ne '.zip') -or
            ($item.kind -eq 'reconstructible_page_image' -and $extension -ne '.png') -or
            ($item.kind -eq 'identical_final_pdf' -and $extension -ne '.pdf') -or
            $item.kind -notin @('duplicate_archive','reconstructible_page_image','identical_final_pdf')) { throw 'Unexpected cleanup file kind' }
        if (Test-Path -LiteralPath $absolute) {
            if (-not [IO.File]::Exists($absolute) -or ([IO.FileInfo]::new($absolute)).Length -ne $item.bytes -or (Get-TaskHash $absolute) -ne $item.SHA) { throw "Owned duplicate changed: $absolute" }
        }
        $taskValidated.Add([pscustomobject]@{path=$absolute;kind=$item.kind;bytes=$item.bytes;SHA=$item.SHA})
    }
    # All guards and all hashes pass before the first mutation.
    foreach ($item in $taskValidated) {
        if (Test-Path -LiteralPath $item.path) {
            Remove-Item -LiteralPath $item.path -ErrorAction Stop
            $taskActions.Add([pscustomobject]@{path=$item.path;kind=$item.kind;action='removed';logical_bytes=$item.bytes;SHA=$item.SHA})
        } else { $taskActions.Add([pscustomobject]@{path=$item.path;kind=$item.kind;action='already_absent';logical_bytes=0}) }
    }
    if (Test-Path -LiteralPath $taskRestore) {
        Remove-Item -LiteralPath $taskRestore -Recurse -ErrorAction Stop
        $taskActions.Add([pscustomobject]@{path=$taskRestore;kind='verified_public_restore_expansion';action='removed'})
    } else { $taskActions.Add([pscustomobject]@{path=$taskRestore;kind='verified_public_restore_expansion';action='already_absent'}) }
} catch { $taskFailure = $_.Exception.Message }
finally {
    $taskAfter = ([IO.DriveInfo]::new('E:\')).AvailableFreeSpace
    $taskResult = [ordered]@{UTC=$taskStarted.ToString('o');status=$(if ($taskFailure) {'FAILED_PRESERVE_FACTS'} else {'PASS'});error=$taskFailure;
        actions=@($taskActions.ToArray());outer_seconds=$taskTick.Elapsed.TotalSeconds;
        free_bytes_before=$taskBefore;free_bytes_after=$taskAfter;observed_volume_delta_bytes=$taskAfter-$taskBefore;
        volume_delta_is_observation_not_exact_owned_reclaimed_bytes=$true;permission_denial_not_forced=$true;
        unique_raw_models_tables_failures_old_worktrees_and_user_files_not_targets=$true}
    $taskResult | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskReceipt -Encoding utf8
}
if ($taskFailure) { throw $taskFailure }
