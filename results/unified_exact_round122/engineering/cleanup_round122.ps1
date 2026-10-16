$ErrorActionPreference = 'Stop'
$taskWork = 'E:\codes\ExactEBRP-work'
$taskRoot = Join-Path $taskWork 'worktrees\round122'
$taskOut = Join-Path $taskRoot 'results\unified_exact_round122'
$taskEvidence = Join-Path $taskWork 'evidence\round122'
$taskRestore = Join-Path $taskWork 'restore\round122-9ed88cf9da87'
$taskScience = '9ed88cf9da87c3ceb7aebc43694f865eacbc86a7'
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
if (-not $taskReplay.passed -or $taskReplay.formal_arms -ne 32 -or $taskReplay.pairs -ne 48 -or $taskReplay.scientific_commit -ne $taskScience -or $taskReplay.fresh_empty_root -ne $taskRestore -or $taskReplay.stage -ne 'BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION' -or -not $taskReplay.typed_JSON_all_fields_values_arrays_and_signed_zero_equal -or -not $taskReplay.no_original_raw_helper_or_runtime_binary_fallback -or -not $taskReplay.all_other_carrier_members_byte_unchanged -or $taskReplay.Optimize -ne 0 -or $taskReplay.native_starts -ne 0 -or $taskReplay.boundary -ne 'Python open/module/process/network audit; not an OS sandbox; standard runtime prefix allowed') { throw 'Actual bound public replay is incomplete' }
if ((Get-FileHash -LiteralPath $taskReplayPath -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath (Join-Path $taskRestore 'restored_check_receipt.json') -Algorithm SHA256).Hash) { throw 'External replay receipt differs from actual restored receipt' }
$taskPublic = Get-Content -LiteralPath (Join-Path $taskOut 'delivery\public_export_restore_receipt.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $taskPublic.one_actual_public_carrier_export -or -not $taskPublic.all_member_hashes_equal -or $taskPublic.members -ne 62310 -or $taskPublic.scientific_commit -ne $taskScience -or $taskPublic.fresh_empty_root -ne $taskRestore -or -not $taskPublic.no_original_raw_fallback -or $taskPublic.public_HTTP_export.scientific_commit -ne $taskScience -or -not $taskPublic.public_HTTP_export.no_local_part_or_original_raw_fallback) { throw 'Bound public export/extraction gate failed' }
$taskCandidatesPath = Join-Path $taskEvidence 'cleanup_candidates.json'
$taskCandidates = Get-Content -LiteralPath $taskCandidatesPath -Raw -Encoding UTF8 | ConvertFrom-Json
$taskCandidateSet = @($taskCandidates.candidates | ForEach-Object { Assert-TaskPath $_.path })
if ($taskCandidateSet.Count -ne 4 -or @($taskCandidateSet | Sort-Object -Unique).Count -ne 4 -or @(Compare-Object ($taskCandidateSet | Sort-Object) ($taskTargets | Sort-Object)).Count -ne 0) { throw 'Candidate prerecord does not bind the exact four owned targets' }
$taskRemote = Get-Content -LiteralPath (Join-Path $taskEvidence 'precleanup_remote_readback.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $taskRemote.passed -or -not $taskRemote.PR.isDraft -or $taskRemote.PR.state -ne 'OPEN' -or $taskRemote.PR.baseRefName -ne 'codex/round121-frozen-d1-confirmation') { throw 'Public Draft PR/readback gate failed' }
$taskCurrentHead = & 'D:\Git\cmd\git.exe' -C $taskRoot rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $taskCurrentHead -ne $taskRemote.PR.headRefOid) { throw 'Actual PR head differs from local delivery head' }
$taskProcesses = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^(python.*|ExactEBRP|Round122Reference|curl)\.exe$' -and (
        $_.CommandLine -like '*round122*' -or $_.ExecutablePath -eq 'C:\Users\Administrator\.codex\worktrees\round121-frozen-d1-confirmation\ExactEBRP\build\research\round120\ExactEBRP.exe')
} | Select-Object Name,ProcessId,CreationDate)
if ($taskProcesses.Count -ne 0) { throw 'Related solver/pack/replay/transfer process remains active' }
$taskManifestPath = Join-Path $taskOut 'compact_evidence\manifest.json'
$taskManifest = Get-Content -LiteralPath $taskManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$taskManifestText = [IO.File]::ReadAllText($taskManifestPath,[Text.Encoding]::UTF8).Replace("`r`n","`n")
if ($taskManifestText.Contains("`r")) { throw 'Unsupported manifest newline' }
$taskHashAlgorithm = [Security.Cryptography.SHA256]::Create()
try { $taskManifestPublicSHA = ([BitConverter]::ToString($taskHashAlgorithm.ComputeHash([Text.Encoding]::UTF8.GetBytes($taskManifestText)))).Replace('-','').ToLowerInvariant() }
finally { $taskHashAlgorithm.Dispose() }
if ($taskManifestPublicSHA -ne '0bc5561235ce9419452a647c7c8d1e50c735a59e956a41f344638438ea777746' -or $taskManifestPublicSHA -ne $taskPublic.public_HTTP_export.expected_public_manifest_SHA -or $taskManifestPublicSHA -ne $taskPublic.public_HTTP_export.fetched[0].SHA -or $taskManifest.parts.Count -ne 6 -or $taskPublic.public_HTTP_export.fetched.Count -ne 7) { throw 'Canonical manifest/public metadata binding failed' }
$taskCanonical = [IO.Path]::GetFullPath((Join-Path $taskOut 'compact_evidence'))
$taskCanonicalParent = $taskCanonical
while ($taskCanonicalParent) {
    if (((Get-Item -LiteralPath $taskCanonicalParent -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Canonical carrier parent is a reparse point' }
    $taskCanonicalParent = [IO.Path]::GetDirectoryName($taskCanonicalParent)
}
for ($taskIndex=0; $taskIndex -lt $taskManifest.parts.Count; $taskIndex++) {
    $taskPart = $taskManifest.parts[$taskIndex]
    $taskExpectedPath = 'results/unified_exact_round122/compact_evidence/evidence.tar.gz.part{0:d3}' -f ($taskIndex+1)
    $taskFetchedPart = $taskPublic.public_HTTP_export.fetched[$taskIndex+1]
    if ($taskPart.path -ne $taskExpectedPath -or $taskFetchedPart.path -ne $taskPart.path -or $taskFetchedPart.bytes -ne $taskPart.bytes -or $taskFetchedPart.SHA -ne $taskPart.SHA) { throw 'Retained carrier part metadata differs from actual public bytes' }
    $taskPartPath = [IO.Path]::GetFullPath((Join-Path $taskRoot $taskPart.path))
    if (-not $taskPartPath.StartsWith($taskCanonical+'\',[StringComparison]::OrdinalIgnoreCase) -or ((Get-Item -LiteralPath $taskPartPath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Retained carrier path is outside canonical directory or reparse' }
    foreach ($taskTarget in $taskTargets) { if ($taskPartPath.StartsWith($taskTarget+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Carrier overlaps cleanup target' } }
    if ((Get-Item -LiteralPath $taskPartPath).Length -ne $taskPart.bytes -or (Get-FileHash -LiteralPath $taskPartPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskPart.SHA) { throw 'Retained canonical carrier part mismatch' }
}
if ($taskPublic.archive -ne (Join-Path $taskWork 'temp\round122\public-export\public_carrier.tar') -or (Get-FileHash -LiteralPath $taskPublic.archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskPublic.archive_SHA) { throw 'Actual duplicate export tar identity differs' }
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
    candidate_prerecord=$taskCandidatesPath; candidate_prerecord_SHA=(Get-FileHash -LiteralPath $taskCandidatesPath -Algorithm SHA256).Hash.ToLowerInvariant(); replay_receipt=$taskReplayPath
    replay_receipt_SHA=(Get-FileHash -LiteralPath $taskReplayPath -Algorithm SHA256).Hash.ToLowerInvariant()
    canonical_carrier=$taskCanonical; canonical_manifest_public_SHA=$taskManifestPublicSHA; canonical_part_count=$taskManifest.parts.Count; retained_part_hashes_verified=$true
    related_processes_active=$taskProcesses; protected_main_HEAD=$taskMainHead; protected_main_dirty_SHA_equal=$true
    candidates=$taskMeasured; removed=@(); failed=@(); logical_bytes_deleted=[long]0
    E_free_before=$taskBefore; E_free_after=$null; observed_free_bytes_change=$null
    retained=@('Current sparse execution tree and unique native raw/model/Start/proof set','One canonical six-part carrier and manifest; public scienceA and delivery commits','External evidence/round122 receipts and cleanup record','All qualification/failure/source/generated input and authoritative tables','Verified frozen production PE and installed DLL/core/compiler/Python/license','All existing old C/D/E trees, user files, unpushed work and shared Git objects','Small current temp/bootstrap/inventory scripts and PR body retained for traceability')
    reasons=@('Public export tar duplicates manifest and canonical parts','Attempt01 directory is empty; TLS failure receipt is retained','Once-only expanded restore passed32/48 and is reconstructible from the retained public carrier','Reference exporter is rebuildable from retained source/compile command and existing frozen core; it is not the production PE')
    restore_or_export_repeated=$false; carrier_rebuilt=$false; global_settings_changed=$false; Optimize=0; native_starts=0; cleanup_passed=$false
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
$taskFinalMainHead = & 'D:\Git\cmd\git.exe' -C 'E:\codes\ExactEBRP' rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $taskFinalMainHead -ne $taskInitial.main_HEAD) { Save-TaskResult; throw 'Protected main HEAD changed after cleanup' }
$taskResult.main_and_assets_rechecked_after_cleanup = $true
$taskResult.cleanup_passed = $taskResult.failed.Count -eq 0 -and @($taskTargets | Where-Object { Test-Path -LiteralPath $_ }).Count -eq 0
Save-TaskResult
Copy-Item -LiteralPath (Join-Path $taskEvidence 'cleanup_summary.json') -Destination (Join-Path $taskOut 'cleanup_summary.json')
$taskResult | Select-Object cleanup_passed,logical_bytes_deleted,E_free_before,E_free_after,observed_free_bytes_change,main_and_assets_rechecked_after_cleanup,engineering_seconds | ConvertTo-Json
if (-not $taskResult.cleanup_passed) { throw 'Cleanup partial failure; persisted actual summary must be inspected' }
