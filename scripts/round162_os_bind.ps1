# Lightweight, current-round live process observation. No hashing/Optimize.
$RoundRoot = Join-Path $PSScriptRoot '..\results\unified_exact_round162'
$RoundActive = Get-Content -LiteralPath (Join-Path $RoundRoot 'complete_active_position.json') -Raw | ConvertFrom-Json
$RoundMatrix = Get-Content -LiteralPath (Join-Path $RoundRoot 'complete_matrix.json') -Raw | ConvertFrom-Json
$RoundGroup = $RoundMatrix.groups[$RoundActive.position-1]
$RoundRecord = Join-Path (Join-Path $RoundRoot $RoundGroup.group) 'runtime_os_binding.json'
if (Test-Path -LiteralPath $RoundRecord) { exit 0 }
$RoundOriginPath = Join-Path $RoundGroup.launch.destination 'child_process_origin.json'
if (!(Test-Path -LiteralPath $RoundOriginPath)) { exit 0 }
$RoundOrigin = Get-Content -LiteralPath $RoundOriginPath -Raw | ConvertFrom-Json
$RoundProcess = Get-Process -Id $RoundOrigin.pid -ErrorAction SilentlyContinue
if (!$RoundProcess) { exit 0 }
$RoundBirth = [DateTimeOffset]::new($RoundProcess.StartTime.ToUniversalTime()).ToUnixTimeMilliseconds()/1000
if ([Math]::Abs($RoundBirth-$RoundOrigin.actual_creation_unix) -gt 0.01) { throw 'Process birth mismatch' }
$RoundModules = @($RoundProcess.Modules | Where-Object { $_.ModuleName -eq 'gurobi130.dll' } | Select-Object ModuleName,FileName)
if ($RoundModules.Count -eq 0) { exit 0 }
if ($RoundProcess.MainModule.FileName -ne $RoundGroup.launch.command[0]) { throw 'Actual PE path mismatch' }
[ordered]@{UTC=[DateTime]::UtcNow.ToString('o');PID=$RoundProcess.Id;CreationUnix=$RoundBirth;
    PE=$RoundProcess.MainModule.FileName;DLL=$RoundModules;PrelaunchSHA=$RoundOrigin.PE_SHA;
    HashingDuringTimedSolve=$false;CommercialDLLPublished=$false} | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath $RoundRecord -Encoding utf8
