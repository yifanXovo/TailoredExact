$ErrorActionPreference = 'Stop'
$taskWork = 'E:\codes\ExactEBRP-work'
$taskRoot = Join-Path $taskWork 'worktrees\round122'
$taskOut = Join-Path $taskRoot 'results\unified_exact_round122'
$taskEvidence = Join-Path $taskWork 'evidence\round122'
$taskRestore = Join-Path $taskWork 'restore\round122-9ed88cf9da87'
$taskTargets = @(
    (Join-Path $taskWork 'temp\round122\public-export'),
    (Join-Path $taskWork 'temp\round122\public-export-attempt01-tls'),
    $taskRestore,
    (Join-Path $taskWork 'build-cache\round122-reference')
)
$taskStarted = [Diagnostics.Stopwatch]::StartNew()
function Assert-TaskPath([string]$taskPath) {
    $taskAbsolute = [IO.Path]::GetFullPath($taskPath).TrimEnd('\')
    if (-not $taskAbsolute.StartsWith($taskWork + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Cleanup path outside fixed work root' }
    if ($taskTargets -notcontains $taskAbsolute) { throw 'Cleanup path not in the four exact owned targets' }
    $taskParent = $taskAbsolute
    while ($taskParent) {
        if (Test-Path -LiteralPath $taskParent) {
            $taskItem = Get-Item -LiteralPath $taskParent -Force
            if (($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Cleanup parent is a reparse point' }
        }
        $taskParent = [IO.Path]::GetDirectoryName($taskParent)
    }
    return $taskAbsolute
}
function Measure-OwnedTree([string]$taskPath) {
    $taskAbsolute = Assert-TaskPath $taskPath
    $taskStack = [Collections.Generic.Stack[string]]::new()
    $taskStack.Push($taskAbsolute)
    [long]$taskBytes = 0; [long]$taskFiles = 0; [long]$taskDirectories = 0
    while ($taskStack.Count -gt 0) {
        $taskDirectory = $taskStack.Pop(); $taskDirectories++
        foreach ($taskEntry in [IO.Directory]::EnumerateFileSystemEntries($taskDirectory)) {
            $taskInfo = Get-Item -LiteralPath $taskEntry -Force
            if (($taskInfo.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse entry in cleanup tree' }
            if ($taskInfo.PSIsContainer) { $taskStack.Push($taskInfo.FullName) }
            else { $taskFiles++; $taskBytes += $taskInfo.Length }
        }
    }
    return [pscustomobject]@{path=$taskAbsolute; files=$taskFiles; directories=$taskDirectories; logical_bytes=$taskBytes; no_reparse_points=$true}
}
$taskReplayPath = Join-Path $taskEvidence 'restored_check_receipt.json'
$taskReplay = Get-Content -LiteralPath $taskReplayPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $taskReplay.passed -or $taskReplay.formal_arms -ne 32 -or $taskReplay.pairs -ne 48) { throw 'Actual public replay is incomplete' }
$taskPublic = Get-Content -LiteralPath (Join-Path $taskOut 'delivery\public_export_restore_receipt.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $taskPublic.one_actual_public_carrier_export -or -not $taskPublic.all_member_hashes_equal -or $taskPublic.members -ne 62310) { throw 'Public export/extraction gate failed' }
$taskRemote = Get-Content -LiteralPath (Join-Path $taskEvidence 'precleanup_remote_readback.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $taskRemote.passed -or -not $taskRemote.PR.isDraft -or $taskRemote.PR.state -ne 'OPEN' -or $taskRemote.PR.baseRefName -ne 'codex/round121-frozen-d1-confirmation') { throw 'Public Draft PR/readback gate failed' }
$taskProcesses = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^(python.*|ExactEBRP|Round122Reference|curl)\.exe$' -and (
        $_.CommandLine -like '*round122*' -or $_.ExecutablePath -eq 'C:\Users\Administrator\.codex\worktrees\round121-frozen-d1-confirmation\ExactEBRP\build\research\round120\ExactEBRP.exe')
} | Select-Object Name,ProcessId,CreationDate)
if ($taskProcesses.Count -ne 0) { throw 'Related solver/pack/replay/transfer process remains active' }
$taskManifestPath = Join-Path $taskOut 'compact_evidence\manifest.json'
$taskManifest = Get-Content -LiteralPath $taskManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($taskPart in $taskManifest.parts) {
    $taskPartPath = Join-Path $taskRoot $taskPart.path
    if ((Get-Item -LiteralPath $taskPartPath).Length -ne $taskPart.bytes -or (Get-FileHash -LiteralPath $taskPartPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskPart.SHA) { throw 'Retained canonical carrier part mismatch' }
}
$taskAssets = @(
    [pscustomobject]@{path='C:\Users\Administrator\.codex\worktrees\round121-frozen-d1-confirmation\ExactEBRP\build\research\round120\ExactEBRP.exe'; SHA='5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba'},
    [pscustomobject]@{path='D:\gurobi1302\win64\bin\gurobi130.dll'; SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'},
    [pscustomobject]@{path='C:\Users\Administrator\.codex\worktrees\round120-native-proof-disjunction\ExactEBRP\build\research\round120\libexact_ebrp_core.a'; SHA='f2f7608894793b60794b91fa204c7d5e8a7ce13078e6115be32ca645804c9acd'}
)
foreach ($taskAsset in $taskAssets) {
    if ((Get-FileHash -LiteralPath $taskAsset.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskAsset.SHA) { throw 'Necessary runtime asset is unavailable or changed' }
}
$taskInitial = Get-Content -LiteralPath (Join-Path $taskOut 'initialization_receipt.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($taskBinding in $taskInitial.main_dirty_SHA.PSObject.Properties) {
    $taskMainPath = Join-Path 'E:\codes\ExactEBRP' $taskBinding.Name
    if ((Get-FileHash -LiteralPath $taskMainPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskBinding.Value) { throw 'Protected main dirty file changed' }
}
$taskMainHead = & 'D:\Git\cmd\git.exe' -C 'E:\codes\ExactEBRP' rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $taskMainHead -ne $taskInitial.main_HEAD) { throw 'Protected main HEAD changed' }
$taskMeasured = @($taskTargets | ForEach-Object { Measure-OwnedTree $_ })
$taskExporter = Join-Path $taskWork 'build-cache\round122-reference\Round122Reference.exe'
if ((Get-FileHash -LiteralPath $taskExporter -Algorithm SHA256).Hash.ToLowerInvariant() -ne '991c5ac37a969734befda241e4d534a3dc55e3eda82cd1409ec8b47490a3a833') { throw 'Unexpected cache identity' }
$taskBefore = [IO.DriveInfo]::new('E').AvailableFreeSpace
$taskResult = [ordered]@{
    UTC=[DateTime]::UtcNow.ToString('o'); scientific_commit='9ed88cf9da87c3ceb7aebc43694f865eacbc86a7'; PR=$taskRemote.PR.url
    scope='Only four exact Round122-owned reconstructible paths under fixed E work root; no old/user/main tree deletion'
    candidate_prerecord=(Join-Path $taskEvidence 'cleanup_candidates.json'); replay_receipt=$taskReplayPath
    canonical_carrier=(Join-Path $taskOut 'compact_evidence'); canonical_part_count=6; retained_part_hashes_verified=$true
    related_processes_active=$taskProcesses; protected_main_HEAD=$taskMainHead; protected_main_dirty_SHA_equal=$true
    candidates=$taskMeasured; removed=@(); failed=@(); logical_bytes_deleted=[long]0
    E_free_before=$taskBefore; E_free_after=$null; observed_free_bytes_change=$null
    retained=@('Current sparse execution tree and unique native raw/model/Start/proof set','One canonical six-part carrier and manifest; public scienceA and delivery commits','External evidence/round122 receipts and cleanup record','All qualification/failure/source/generated input and authoritative tables','Verified frozen production PE and installed DLL/core/compiler/Python/license','All existing old C/D/E trees, user files, unpushed work and shared Git objects','Small current temp/bootstrap/inventory scripts and PR body retained for traceability')
    reasons=@('Public export tar duplicates manifest and canonical parts','Attempt01 directory is empty; TLS failure receipt is retained','Once-only expanded restore passed32/48 and is reconstructible from the retained public carrier','Reference exporter is rebuildable from retained source/compile command and existing frozen core; it is not the production PE')
    restore_or_export_repeated=$false; carrier_rebuilt=$false; global_settings_changed=$false; Optimize=0; native_starts=0
}
function Save-TaskResult {
    $taskResult | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $taskEvidence 'cleanup_summary.json') -Encoding UTF8
}
Save-TaskResult
foreach ($taskCandidate in $taskMeasured) {
    $taskChecked = Assert-TaskPath $taskCandidate.path
    try {
        Remove-Item -LiteralPath $taskChecked -Recurse -Force
        if (Test-Path -LiteralPath $taskChecked) { throw 'Owned target still exists after removal' }
        $taskResult.removed += $taskCandidate
        $taskResult.logical_bytes_deleted += $taskCandidate.logical_bytes
    } catch {
        $taskResult.failed += [pscustomobject]@{path=$taskChecked; error_class=$_.Exception.GetType().FullName; message=$_.Exception.Message}
    }
    Save-TaskResult
}
$taskResult.E_free_after = [IO.DriveInfo]::new('E').AvailableFreeSpace
$taskResult.observed_free_bytes_change = $taskResult.E_free_after - $taskBefore
$taskResult.engineering_seconds = $taskStarted.Elapsed.TotalSeconds
$taskResult.main_and_assets_rechecked_after_cleanup = $false
foreach ($taskAsset in $taskAssets) {
    if ((Get-FileHash -LiteralPath $taskAsset.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskAsset.SHA) { Save-TaskResult; throw 'Retained runtime changed after cleanup' }
}
foreach ($taskBinding in $taskInitial.main_dirty_SHA.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath (Join-Path 'E:\codes\ExactEBRP' $taskBinding.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskBinding.Value) { Save-TaskResult; throw 'Protected main changed after cleanup' }
}
$taskResult.main_and_assets_rechecked_after_cleanup = $true
Save-TaskResult
Copy-Item -LiteralPath (Join-Path $taskEvidence 'cleanup_summary.json') -Destination (Join-Path $taskOut 'cleanup_summary.json')
$taskResult | Select-Object logical_bytes_deleted,E_free_before,E_free_after,observed_free_bytes_change,main_and_assets_rechecked_after_cleanup,engineering_seconds | ConvertTo-Json
