param([int]$Minutes = 1000)
$ErrorActionPreference = 'Stop'
$taskRepo = Split-Path -Parent $PSScriptRoot
$taskOut = Join-Path $taskRepo 'results/unified_exact_round123'
$taskWatch = [Diagnostics.Stopwatch]::StartNew()
$taskMe = [Diagnostics.Process]::GetCurrentProcess()
$taskLaunch = [ordered]@{
    PID = $PID
    ActualCreationUTC = $taskMe.StartTime.ToUniversalTime().ToString('o')
    ObservedUTC = [DateTime]::UtcNow.ToString('o')
    Scope = 'Read existing fixed-frequency samples; no native control, callback change or scientific endpoint writing'
    NativeStarts = 0
    PollSeconds = 55
}
$taskLaunch | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskOut 'engineering/watch_launch.json') -Encoding utf8
try {
    while ($taskWatch.Elapsed.TotalMinutes -lt $Minutes) {
        $taskControllerReceipt = Join-Path $taskOut 'controller/formal01/receipt.json'
        if (Test-Path -LiteralPath $taskControllerReceipt) {
            $taskClosed = Get-Content -LiteralPath $taskControllerReceipt -Raw | ConvertFrom-Json
            Write-Output ("Formal group controller exited {0}; existing receipt is ready for final review." -f $taskClosed.exit_code)
            break
        }
        $taskRaw = Join-Path $taskOut 'campaign/group01/raw'
        $taskDirs = @('01_PB-C50-S_S0_P-GRB','02_PB-C50-S_S0_M-B','03_PB-C50-S_S0_ENS-C')
        $taskCurrent = $null
        foreach ($taskName in $taskDirs) {
            $taskDir = Join-Path $taskRaw $taskName
            if (Test-Path -LiteralPath (Join-Path $taskDir 'child_process_origin.json')) { $taskCurrent = $taskDir }
        }
        if ($null -ne $taskCurrent) {
            $taskOrigin = Get-Content -LiteralPath (Join-Path $taskCurrent 'child_process_origin.json') -Raw | ConvertFrom-Json
            $taskLabel = Split-Path -Leaf $taskCurrent
            $taskSample = Join-Path $taskCurrent 'samples.jsonl'
            $taskAudit = Join-Path $taskCurrent 'audit.json'
            if (Test-Path -LiteralPath $taskAudit) {
                $taskAuditData = Get-Content -LiteralPath $taskAudit -Raw | ConvertFrom-Json
                if ($taskAuditData.passed -eq $false) {
                    Write-Output ("Attention: {0} has a retained audit failure; inspect original producer and fee before any continuation." -f $taskLabel)
                    break
                }
            }
            if (Test-Path -LiteralPath $taskSample) {
                try {
                    $taskS = Get-Content -LiteralPath $taskSample -Tail 1 | ConvertFrom-Json
                    Write-Output ("{0}: existing sample {1:F0}s, observed U={2:G11}, L={3:G11}, gap={4:G11}; provisional, no final certificate inferred." -f $taskS.arm,$taskS.process_seconds,$taskS.provisional_U,$taskS.provisional_L,$taskS.provisional_gap)
                } catch { Write-Output ("{0}: waiting for a complete existing sample record." -f $taskLabel) }
            }
            $taskModulePath = Join-Path $taskOut ("campaign/group01/actual_loaded_modules_{0}.json" -f $taskOrigin.arm)
            # Birth receipt's command is authoritative even when it has no arm field.
            $taskShort = if ($taskLabel -like '*_P-GRB') { 'P' } elseif ($taskLabel -like '*_M-B') { 'M_B' } else { 'ENS_C' }
            $taskModulePath = Join-Path $taskOut ("campaign/group01/actual_loaded_modules_{0}.json" -f $taskShort)
            if (-not (Test-Path -LiteralPath $taskModulePath)) {
                $taskNative = Get-Process -Id $taskOrigin.pid -ErrorAction SilentlyContinue
                if ($null -ne $taskNative) {
                    $taskModules = @($taskNative.Modules | Where-Object { $_.ModuleName -match '^gurobi|^ExactEBRP' } | Select-Object ModuleName,FileName)
                    if (@($taskModules | Where-Object { $_.ModuleName -eq 'gurobi130.dll' }).Count -eq 1) {
                        [ordered]@{ ProcessId=$taskOrigin.pid; BirthReceiptCreationUnix=$taskOrigin.actual_creation_unix; Modules=$taskModules; ObservedUTC=[DateTime]::UtcNow.ToString('o'); ReadOnlyHostEvidence=$true } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $taskModulePath -Encoding utf8
                    }
                }
            }
        } else { Write-Output 'Waiting for an original formal child birth receipt; no new native work is launched by this observer.' }
        Start-Sleep -Seconds 55
    }
} finally {
    [ordered]@{ PID=$PID; Seconds=$taskWatch.Elapsed.TotalSeconds; NativeStarts=0; Optimize=0; ExistingSamplesOnly=$true; EndUTC=[DateTime]::UtcNow.ToString('o'); OverlapsFormalGroupWallClock=$true } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskOut 'engineering/watch_receipt.json') -Encoding utf8
}
