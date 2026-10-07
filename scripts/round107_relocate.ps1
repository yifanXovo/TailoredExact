$ErrorActionPreference = 'Stop'
$src107 = [System.IO.Path]::GetFullPath('C:/Users/Administrator/.codex/worktrees/round107-ens-frontier-route-events/ExactEBRP/results/unified_exact_round107')
$dst107 = [System.IO.Path]::GetFullPath('E:/r107-data01')
if ($src107 -ne 'C:\Users\Administrator\.codex\worktrees\round107-ens-frontier-route-events\ExactEBRP\results\unified_exact_round107' -or $dst107 -ne 'E:\r107-data01') { throw 'Resolved path mismatch' }
if (Test-Path -LiteralPath $dst107) { throw 'Destination already exists' }
if ((Get-Item -LiteralPath $src107).Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw 'Source must be the original ordinary results directory' }
$eng107 = Join-Path $src107 'engineering/resource_relocation01'
New-Item -ItemType Directory -Path $eng107 | Out-Null
$watch107 = [System.Diagnostics.Stopwatch]::StartNew()
$launch107 = [ordered]@{engineering=$true; Optimize_calls=0; IIS_calls=0; source=$src107; destination=$dst107; script_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant(); reason='C free space below serial supervisor 10GiB threshold; preserve exact paths via directory junction'; started_utc=[DateTime]::UtcNow.ToString('o')}
$launch107 | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $eng107 'launch.json') -Encoding utf8NoBOM
$snapshot107 = @(Get-ChildItem -LiteralPath $src107 -Recurse -File | ForEach-Object { [ordered]@{path=$_.FullName.Substring($src107.Length+1).Replace('\','/'); bytes=$_.Length; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()} })
Move-Item -LiteralPath $src107 -Destination $dst107
New-Item -ItemType Junction -Path $src107 -Target $dst107 | Out-Null
if ((Get-ChildItem -LiteralPath $dst107 -Recurse -File).Count -ne $snapshot107.Count) { throw 'Relocated file count differs' }
foreach ($entry107 in $snapshot107) {
    $file107 = Join-Path $dst107 $entry107.path
    if ((Get-Item -LiteralPath $file107).Length -ne $entry107.bytes -or (Get-FileHash -LiteralPath $file107 -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry107.sha256) { throw ('Relocated bytes differ: ' + $entry107.path) }
}
$snapshot107 | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $eng107 'exact_files.json') -Encoding utf8NoBOM
$receipt107 = [ordered]@{engineering=$true; exit_code=0; outer_seconds=$watch107.Elapsed.TotalSeconds; conservative_process_starts=0; Optimize_calls=0; IIS_calls=0; verified_files=$snapshot107.Count; verified_bytes=($snapshot107 | Measure-Object bytes -Sum).Sum; original_path=$src107; relocated_path=$dst107; exact_paths_preserved=$true; file_bytes_preserved=$true; stop_reason='normal_return'}
$receipt107 | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $eng107 'receipt.json') -Encoding utf8NoBOM
$receipt107 | ConvertTo-Json -Compress
