$ErrorActionPreference = 'Stop'
$taskWork = [IO.Path]::GetFullPath('E:\codes\ExactEBRP-work')
$taskRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$taskOut = Join-Path $taskRoot 'results\unified_exact_round131'
$taskTemp = Join-Path $taskWork 'temp\round131'
$taskReceipt = Join-Path $taskOut 'cleanup_receipt.json'
if (Test-Path -LiteralPath $taskReceipt) { throw 'Preserve the existing cleanup receipt; no automatic repeated deletion' }
$taskRestore = Get-Content -LiteralPath (Join-Path $taskOut 'public_restore_receipt.json') -Raw | ConvertFrom-Json
if ($taskRestore.status -ne 'PASS' -or $taskRestore.Optimize -ne 0 -or $taskRestore.native_starts -ne 0) { throw 'A passed actual public recovery is required' }
if (Get-CimInstance Win32_Process -Filter "Name = 'ExactEBRP.exe' OR Name = 'gurobi_cl.exe' OR Name = 'g++.exe' OR Name = '7z.exe'") { throw 'Native/build/archive process remains active' }
$taskVolumeBefore = (Get-Volume -DriveLetter E).SizeRemaining
$taskStarted = [DateTime]::UtcNow
$taskActions = [System.Collections.Generic.List[object]]::new()
$taskRetained = [System.Collections.Generic.List[object]]::new()

function Get-TaskHash([string] $taskPath) {
    return (Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLower()
}
function Read-TaskGzipJson([string] $taskPath) {
    $taskStream = [IO.File]::OpenRead($taskPath)
    try {
        $taskGzip = [IO.Compression.GZipStream]::new($taskStream,[IO.Compression.CompressionMode]::Decompress)
        try {
            $taskReader = [IO.StreamReader]::new($taskGzip,[Text.Encoding]::UTF8)
            try { return ($taskReader.ReadToEnd() | ConvertFrom-Json) } finally { $taskReader.Dispose() }
        } finally { $taskGzip.Dispose() }
    } finally { $taskStream.Dispose() }
}
function Assert-TaskOwned([string] $taskPath, [string] $taskAllowed) {
    $taskResolved = [IO.Path]::GetFullPath($taskPath)
    $taskBoundary = [IO.Path]::GetFullPath($taskAllowed).TrimEnd('\') + '\'
    if (-not $taskResolved.StartsWith($taskBoundary,[StringComparison]::OrdinalIgnoreCase)) { throw "Deletion path outside allowed owned root: $taskResolved" }
    if ($taskResolved -eq $taskRoot -or $taskResolved -eq $taskWork) { throw 'Cannot delete a worktree or shared work root' }
    $taskCursor = Get-Item -LiteralPath $taskResolved -Force
    while ($null -ne $taskCursor) {
        if (($taskCursor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse-point path is not eligible: $($taskCursor.FullName)" }
        if ($taskCursor.PSIsContainer) { $taskCursor = $taskCursor.Parent } else { $taskCursor = $taskCursor.Directory }
    }
    return $taskResolved
}

$taskArchiveManifest = Get-Content -LiteralPath (Join-Path $taskOut 'raw_archive_manifest.json') -Raw | ConvertFrom-Json
foreach ($taskArchive in $taskArchiveManifest.archives) {
    foreach ($taskPart in $taskArchive.pieces) {
        $taskPublishedPart = Join-Path $taskRoot $taskPart.path
        if (-not (Test-Path -LiteralPath $taskPublishedPart) -or (Get-TaskHash $taskPublishedPart) -ne $taskPart.SHA256) { throw 'Retain duplicate ZIP: published local piece is missing or differs' }
    }
    $taskDuplicate = [IO.Path]::GetFullPath($taskArchive.temporary_complete_archive)
    if (Test-Path -LiteralPath $taskDuplicate) {
        $taskResolved = Assert-TaskOwned $taskDuplicate $taskTemp
        if ((Get-TaskHash $taskResolved) -ne $taskArchive.SHA256) { throw 'Temporary ZIP differs from published/recovered archive' }
        $taskBytes = (Get-Item -LiteralPath $taskResolved).Length
        Remove-Item -LiteralPath $taskResolved -Force
        $taskActions.Add([pscustomobject]@{path=$taskResolved;kind='byte-identical complete ZIP duplicate';bytes=$taskBytes;recursive=$false})
    }
}

$taskRestoredRoot = [IO.Path]::GetFullPath($taskRestore.destination)
if (Test-Path -LiteralPath $taskRestoredRoot) {
    $taskResolved = Assert-TaskOwned $taskRestoredRoot (Join-Path $taskWork 'restore')
    $taskState = Get-Content -LiteralPath (Join-Path $taskResolved 'restore_state.json') -Raw | ConvertFrom-Json
    if ($taskState.commit -ne $taskRestore.science_commit -or -not $taskState.initially_empty -or $taskState.owner -ne 'Round131 single science-commit recovery' -or -not (Split-Path -Leaf $taskResolved).StartsWith('round131')) { throw 'Recovery ownership or pinned commit does not match' }
    $taskCopies = @('restore_state.json','portable_stdout.log','portable_stderr.log','portable_check_receipt.json')
    $taskAttemptDirectories = @(Get-ChildItem -LiteralPath (Join-Path $taskOut 'review\public_recovery_attempts') -Directory | Sort-Object Name -Descending)
    if ($taskAttemptDirectories.Count -lt 1) { throw 'Retained recovery receipts are missing' }
    foreach ($taskName in $taskCopies) {
        $taskSource = Join-Path $taskResolved $taskName
        if (Test-Path -LiteralPath $taskSource) {
            $taskPreserved = Join-Path $taskAttemptDirectories[0].FullName $taskName
            if (-not (Test-Path -LiteralPath $taskPreserved) -or (Get-TaskHash $taskSource) -ne (Get-TaskHash $taskPreserved)) { throw 'Unique recovery receipt has not been retained outside deletion root' }
        }
    }
    $taskItems = @(Get-ChildItem -LiteralPath $taskResolved -Force -Recurse)
    if (@($taskItems | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count -ne 0) { throw 'Reparse point inside recovery root' }
    $taskExpected = [System.Collections.Generic.Dictionary[string,string]]::new([StringComparer]::OrdinalIgnoreCase)
    $taskPublicManifest = Get-Content -LiteralPath (Join-Path $taskResolved 'results\unified_exact_round131\export_manifest.json') -Raw | ConvertFrom-Json
    foreach ($taskMember in $taskPublicManifest.files) { $taskExpected[$taskMember.path.Replace('/','\')] = $taskMember.SHA256 }
    $taskExpected['results\unified_exact_round131\export_manifest.json'] = $taskRestore.export_manifest_SHA
    foreach ($taskArchive in $taskArchiveManifest.archives) {
        $taskExpected[('archive_transport\'+$taskArchive.name)] = $taskArchive.SHA256
        foreach ($taskMember in @(Read-TaskGzipJson (Join-Path $taskRoot $taskArchive.member_index.path))) {
            $taskExpected[$taskMember.path.Replace('/','\')] = $taskMember.SHA256
        }
    }
    foreach ($taskName in $taskCopies) {
        $taskPreserved = Join-Path $taskAttemptDirectories[0].FullName $taskName
        if (Test-Path -LiteralPath $taskPreserved) { $taskExpected[$taskName] = Get-TaskHash $taskPreserved }
    }
    $taskUnexpected = @()
    foreach ($taskItem in @($taskItems | Where-Object { -not $_.PSIsContainer })) {
        $taskRelative = [IO.Path]::GetRelativePath($taskResolved,$taskItem.FullName)
        if (-not $taskExpected.ContainsKey($taskRelative) -or (Get-TaskHash $taskItem.FullName) -ne $taskExpected[$taskRelative]) { $taskUnexpected += $taskRelative }
    }
    if ($taskUnexpected.Count -eq 0) {
        $taskBytes = ($taskItems | Where-Object { -not $_.PSIsContainer } | Measure-Object Length -Sum).Sum
        Remove-Item -LiteralPath $taskResolved -Recurse -Force
        $taskActions.Add([pscustomobject]@{path=$taskResolved;kind='successful reconstructible single public recovery expansion';bytes=$taskBytes;recursive=$true})
    } else {
        $taskRetained.Add([pscustomobject]@{path=$taskResolved;reason='unexpected or changed files; preserve entire recovery root';files=$taskUnexpected})
    }
}

$taskPDF = Join-Path $taskOut 'manuscript.pdf'
$taskPDFHash = Get-TaskHash $taskPDF
$taskRenderManifest = Join-Path $taskOut 'review\pdf_render_manifest.json'
if (Test-Path -LiteralPath $taskRenderManifest) {
    $taskRenders = Get-Content -LiteralPath $taskRenderManifest -Raw | ConvertFrom-Json
    if ($taskRenders.PDF_SHA -eq $taskPDFHash) {
        foreach ($taskPage in $taskRenders.pages) {
            if (Test-Path -LiteralPath $taskPage.path) {
                $taskResolved = Assert-TaskOwned $taskPage.path $taskTemp
                if ((Get-TaskHash $taskResolved) -eq $taskPage.SHA256) {
                    $taskBytes = (Get-Item -LiteralPath $taskResolved).Length
                    Remove-Item -LiteralPath $taskResolved -Force
                    $taskActions.Add([pscustomobject]@{path=$taskResolved;kind='inspected reproducible PDF page image';bytes=$taskBytes;recursive=$false})
                } else { $taskRetained.Add([pscustomobject]@{path=$taskResolved;reason='page image differs from inspected manifest'}) }
            }
        }
    }
}
$taskPDFRoot = Join-Path $taskTemp 'pdf'
if (Test-Path -LiteralPath $taskPDFRoot) {
    foreach ($taskFile in @(Get-ChildItem -LiteralPath $taskPDFRoot -Recurse -File -Filter '*.pdf')) {
        if ((Get-TaskHash $taskFile.FullName) -eq $taskPDFHash) {
            $taskResolved = Assert-TaskOwned $taskFile.FullName $taskTemp
            $taskBytes = $taskFile.Length
            Remove-Item -LiteralPath $taskResolved -Force
            $taskActions.Add([pscustomobject]@{path=$taskResolved;kind='byte-identical temporary PDF';bytes=$taskBytes;recursive=$false})
        } else { $taskRetained.Add([pscustomobject]@{path=$taskFile.FullName;reason='different PDF content, not removed'}) }
    }
}

$taskBaseline = @(Get-Content -LiteralPath (Join-Path $taskOut 'user_dirty_baseline.json') -Raw | ConvertFrom-Json)
$taskDirtyChecks = @($taskBaseline | ForEach-Object {
    $taskPath = Join-Path 'E:\codes\ExactEBRP' $_.path
    $taskCurrent = Get-TaskHash $taskPath
    [pscustomobject]@{path=$_.path;before=$_.sha256;after=$taskCurrent;unchanged=($taskCurrent -eq $_.sha256)}
})
$taskVolumeAfter = (Get-Volume -DriveLetter E).SizeRemaining
$taskResult = [ordered]@{
    status='PASS';started_UTC=$taskStarted.ToString('o');finished_UTC=[DateTime]::UtcNow.ToString('o')
    public_science_commit=$taskRestore.science_commit;actions=@($taskActions);retained_different_content=@($taskRetained)
    logical_removed_file_bytes=($taskActions | Measure-Object bytes -Sum).Sum
    E_free_bytes_before=$taskVolumeBefore;E_free_bytes_after=$taskVolumeAfter
    observed_E_free_byte_change=($taskVolumeAfter-$taskVolumeBefore)
    observed_space_delta_not_attributed_entirely_to_cleanup=$true
    directed_dirty_hash_checks=$taskDirtyChecks;all_directed_dirty_hashes_unchanged=(@($taskDirtyChecks | Where-Object {-not $_.unchanged}).Count -eq 0)
    unique_current_raw_retained=$true;failure_records_retained=$true;old_worktrees_untouched=$true
    user_unpushed_content_not_deleted=$true;PE_DLL_not_removed=$true;global_Git_or_app_configuration_changed=$false
    no_entire_user_files_integrity_claim=$true
}
$taskResult | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskReceipt -Encoding utf8
$taskResult | ConvertTo-Json -Depth 8
