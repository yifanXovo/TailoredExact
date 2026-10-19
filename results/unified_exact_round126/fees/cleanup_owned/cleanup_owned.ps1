$ErrorActionPreference='Stop'
$taskWork='E:\codes\ExactEBRP-work'
$taskOut='E:\codes\ExactEBRP-work\worktrees\round126\results\unified_exact_round126'
$taskA='1ca177b9f0624eb0a806b96c87c1151b172d198e'
$taskTargets=@('E:\codes\ExactEBRP-work\temp\round126\archives','E:\codes\ExactEBRP-work\restore\round126-public-A','E:\codes\ExactEBRP-work\temp\round126\pdf_review')
$taskLive=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(ExactEBRP|gurobi_cl|xelatex|lualatex|cmake|ninja|MSBuild)\.exe$' })
if($taskLive.Count -ne 0){throw 'Related native/compiler process still active; preserve all targets'}
$taskRemote=Get-Content -LiteralPath (Join-Path $taskOut 'review\remote_A_verification.json') -Raw | ConvertFrom-Json
$taskRestore=Get-Content -LiteralPath (Join-Path $taskOut 'review\public_restore_A.json') -Raw | ConvertFrom-Json
if($taskRemote.status -ne 'PASS' -or $taskRestore.status -ne 'PASS' -or $taskRestore.PDF.actual_visual_reread.status -ne 'PASS'){throw 'Actual remote/recovery/page checks not complete'}
$taskState=Get-Content -LiteralPath (Join-Path $taskTargets[1] 'restore_state.json') -Raw | ConvertFrom-Json
if($taskState.commit -ne $taskA -or $taskState.owner -ne 'Round126 public science-A recovery'){throw 'Restore ownership mismatch'}
$taskPlans=@()
foreach($taskLiteral in $taskTargets){
  $taskResolved=(Resolve-Path -LiteralPath $taskLiteral).ProviderPath
  if(-not $taskResolved.Equals([IO.Path]::GetFullPath($taskLiteral),[StringComparison]::OrdinalIgnoreCase) -or -not $taskResolved.StartsWith($taskWork+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Target is outside exact owned workspace path'}
  $taskAnc=Get-Item -LiteralPath $taskResolved
  while($null -ne $taskAnc){if(($taskAnc.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Reparse point ancestor; preserve target'}; $taskAnc=$taskAnc.Parent}
  $taskItems=@(Get-ChildItem -LiteralPath $taskResolved -Recurse -Force)
  if(@($taskItems | Where-Object {($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0}).Count -ne 0){throw 'Unexpected reparse point inside owned target'}
  $taskFiles=@($taskItems | Where-Object {-not $_.PSIsContainer})
  $taskBytes=($taskFiles | Measure-Object -Property Length -Sum).Sum
  $taskPlans+= [pscustomobject]@{path=$taskResolved;file_count=$taskFiles.Count;logical_bytes=[long]$taskBytes}
}
$taskManifest=Get-Content -LiteralPath (Join-Path $taskOut 'raw_archive_manifest.json') -Raw | ConvertFrom-Json
$taskZipFiles=@(Get-ChildItem -LiteralPath $taskTargets[0] -File)
if($taskZipFiles.Count -ne $taskManifest.archives.Count){throw 'Unexpected archive temporary file; preserve all'}
foreach($taskArchive in $taskManifest.archives){
  $taskTempZip=Join-Path $taskTargets[0] $taskArchive.name
  if((Get-FileHash -LiteralPath $taskTempZip -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskArchive.SHA256){throw 'Temporary archive hash mismatch'}
  foreach($taskPart in $taskArchive.pieces){$taskKept=Join-Path 'E:\codes\ExactEBRP-work\worktrees\round126' $taskPart.path; if((Get-FileHash -LiteralPath $taskKept -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskPart.SHA256){throw 'Retained published carrier mismatch'}}
}
$taskAllowedRestore=@('restore_state.json','results','scripts','archive_transport','rebuilt_inputs','portable_check_receipt.json','compile','compiled')
foreach($taskChild in Get-ChildItem -LiteralPath $taskTargets[1] -Force){if($taskChild.Name -notin $taskAllowedRestore){throw 'Unknown file in owned restore root; preserve it'}}
$taskPdfBases=@()
$taskCandidates=@(Join-Path $taskOut 'manuscript.pdf')+@(Get-ChildItem -LiteralPath 'E:\codes\ExactEBRP-work\temp\round126\pdf' -Filter 'reading.pdf' -Recurse -File | Select-Object -ExpandProperty FullName)
foreach($taskRender in Get-ChildItem -LiteralPath $taskTargets[2] -Directory){
  $taskFound=$null
  foreach($taskCandidate in $taskCandidates){$taskHash=(Get-FileHash -LiteralPath $taskCandidate -Algorithm SHA256).Hash.ToLowerInvariant(); if($taskHash.StartsWith($taskRender.Name)){$taskFound=[pscustomobject]@{render_root=$taskRender.FullName;retained_PDF=$taskCandidate;SHA256=$taskHash};break}}
  if($null -eq $taskFound){throw 'No retained identical PDF to regenerate page copies'}
  $taskPdfBases+=$taskFound
}
$taskBackup='E:\codes\ExactEBRP-work\evidence\round126\public_reread'
New-Item -ItemType Directory -Path $taskBackup | Out-Null
$taskRetained=@()
$taskCopySources=@(Get-ChildItem -LiteralPath (Join-Path $taskTargets[1] 'compiled') -Filter 'visual*.png' -File | Select-Object -ExpandProperty FullName)
$taskCopySources+=@(Join-Path $taskTargets[1] 'compiled\export.json';Join-Path $taskTargets[1] 'portable_check_receipt.json';Join-Path $taskTargets[1] 'restore_state.json')
foreach($taskSource in $taskCopySources){$taskTo=Join-Path $taskBackup ([IO.Path]::GetFileName($taskSource));Copy-Item -LiteralPath $taskSource -Destination $taskTo; $taskRetained+=[pscustomobject]@{path=$taskTo;SHA256=(Get-FileHash -LiteralPath $taskTo -Algorithm SHA256).Hash.ToLowerInvariant()}}
$taskResults=@()
foreach($taskPlan in $taskPlans){
  try {Remove-Item -LiteralPath $taskPlan.path -Recurse -ErrorAction Stop; $taskResults+=[pscustomobject]@{path=$taskPlan.path;removed=(-not(Test-Path -LiteralPath $taskPlan.path));file_count=$taskPlan.file_count;logical_bytes=$taskPlan.logical_bytes;error=$null}}
  catch {$taskResults+=[pscustomobject]@{path=$taskPlan.path;removed=$false;file_count=$taskPlan.file_count;logical_bytes=$taskPlan.logical_bytes;error=$_.Exception.Message}}
}
$taskReceipt=[ordered]@{status='COMPLETE';content_commit_A=$taskA;exact_paths_checked=$true;related_processes_exited=$true;metadata_only_screening=$true;removed=$taskResults;logical_removed_bytes=($taskResults | Where-Object {$_.removed} | Measure-Object -Property logical_bytes -Sum).Sum;volume_space_gain_not_claimed=$true;retained_public_reread=$taskRetained;page_regeneration_bases=$taskPdfBases;authority_raw_preserved=(Join-Path $taskOut 'campaign');published_carriers_preserved=(Join-Path $taskOut 'artifacts');all_PDF_attempt_sources_logs_and_failed_records_preserved='E:\codes\ExactEBRP-work\temp\round126\pdf';user_main_files_old_worktrees_Git_objects_and_unpushed_B_receipts_untouched=$true;no_worktree_removed=$true;no_force_gc_repack_prune=$true;restoration_failures_preserved=(Join-Path $taskOut 'review\public_restore_A_failure.json')}
$taskReceipt | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $taskOut 'review\safe_cleanup.json') -Encoding UTF8
$taskReceipt | Select-Object status,logical_removed_bytes,authority_raw_preserved | ConvertTo-Json -Compress
