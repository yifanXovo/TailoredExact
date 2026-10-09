$ErrorActionPreference = 'Stop'
$recoveredRoot = 'E:/codes/ExactEBRP-round109-restored01'
$reviewRoot = Join-Path $recoveredRoot 'results/unified_exact_round109/review'
$executionRoot = Join-Path $reviewRoot 'public_blocked_raw01_execution'
$auditRoot = Join-Path $reviewRoot 'public_blocked_raw01'
$reviewSource = Join-Path $reviewRoot 'round109_independent_blocked.py'
$reportsRoot = Join-Path $recoveredRoot 'results/unified_exact_round109/reports_final'
if ((Get-Location).Path -ne 'E:\codes\ExactEBRP-round109-restored01') { throw 'wrong cwd' }
if (Test-Path -LiteralPath $auditRoot) { throw 'exclusive audit destination exists' }
if (Test-Path -LiteralPath (Join-Path $executionRoot 'receipt.json')) { throw 'execution already closed' }
$sourceHash = (Get-FileHash -LiteralPath $reviewSource -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sourceHash -ne '3d15d3c9dc0995cc01485f62ea3c81f307f8f5ea25929b86a960ccda397b5219') { throw 'restored source mismatch' }
Copy-Item -LiteralPath $reviewSource -Destination (Join-Path $executionRoot 'source_snapshot.py')
$argumentVector = @('-I', $reviewSource, '--root', $recoveredRoot, '--public', '--out', $auditRoot, '--reports', $reportsRoot)
$launch = @{
    executable = 'D:/msys64/ucrt64/bin/python.exe'
    argv = $argumentVector
    cwd = (Get-Location).Path
    source_SHA = $sourceHash
    execution_source_SHA = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    restore_receipt_SHA = (Get-FileHash -LiteralPath (Join-Path $recoveredRoot 'restore_receipt.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    public_mode = $true
    isolated_python = $true
    original_workspace_reads = $false
    PE_opened = $false
    DLL_argument = $null
    Optimize = 0
    native_environments = 0
}
$launch | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $executionRoot 'launch.json') -Encoding UTF8
$startedUtc = [DateTime]::UtcNow
$stopwatch = [Diagnostics.Stopwatch]::StartNew()
& 'D:/msys64/ucrt64/bin/python.exe' @argumentVector 1> (Join-Path $executionRoot 'stdout.txt') 2> (Join-Path $executionRoot 'stderr.txt')
$reviewExitCode = $LASTEXITCODE
$stopwatch.Stop()
$receipt = @{
    exit_code = $reviewExitCode
    elapsed_seconds = $stopwatch.Elapsed.TotalSeconds
    actual_start_utc = $startedUtc.ToString('o')
    actual_end_utc = ([DateTime]::UtcNow).ToString('o')
    cwd = (Get-Location).Path
    explicit_read_root = $recoveredRoot
    source_SHA = $sourceHash
    execution_source_SHA = $launch.execution_source_SHA
    launch_SHA = (Get-FileHash -LiteralPath (Join-Path $executionRoot 'launch.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    stdout_SHA = (Get-FileHash -LiteralPath (Join-Path $executionRoot 'stdout.txt') -Algorithm SHA256).Hash.ToLowerInvariant()
    stderr_SHA = (Get-FileHash -LiteralPath (Join-Path $executionRoot 'stderr.txt') -Algorithm SHA256).Hash.ToLowerInvariant()
    public_mode = $true
    original_workspace_reads = $false
    Optimize = 0
    native_environments = 0
}
if (Test-Path -LiteralPath (Join-Path $auditRoot 'audit.json')) { $receipt.audit_SHA = (Get-FileHash -LiteralPath (Join-Path $auditRoot 'audit.json') -Algorithm SHA256).Hash.ToLowerInvariant() }
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $executionRoot 'receipt.json') -Encoding UTF8
Get-Content -LiteralPath (Join-Path $executionRoot 'stdout.txt')
Get-Content -LiteralPath (Join-Path $executionRoot 'stderr.txt')
if ($reviewExitCode -ne 0) { throw "public raw review failed exit=$reviewExitCode" }
$receipt | ConvertTo-Json -Depth 8
