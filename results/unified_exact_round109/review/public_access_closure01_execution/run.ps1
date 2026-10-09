$ErrorActionPreference = 'Stop'
$recoveredRoot = 'E:/codes/ExactEBRP-round109-restored01'
$executionRoot = Join-Path $recoveredRoot 'results/unified_exact_round109/review/public_access_closure01_execution'
$checkSource = Join-Path $executionRoot 'check.py'
$auditPath = Join-Path $recoveredRoot 'results/unified_exact_round109/review/public_access_closure01/audit.json'
if ((Get-Location).Path -ne 'E:\codes\ExactEBRP-round109-restored01') { throw 'wrong cwd' }
if (Test-Path -LiteralPath (Join-Path $executionRoot 'receipt.json')) { throw 'execution already closed' }
$sourceHash = (Get-FileHash -LiteralPath $checkSource -Algorithm SHA256).Hash.ToLowerInvariant()
$argumentVector = @('-I', $checkSource)
$launch = @{
    executable = 'D:/msys64/ucrt64/bin/python.exe'
    argv = $argumentVector
    cwd = (Get-Location).Path
    source_SHA = $sourceHash
    execution_source_SHA = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    public_mode = $true
    original_workspace_reads = $false
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
if (Test-Path -LiteralPath $auditPath) { $receipt.audit_SHA = (Get-FileHash -LiteralPath $auditPath -Algorithm SHA256).Hash.ToLowerInvariant() }
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $executionRoot 'receipt.json') -Encoding UTF8
Get-Content -LiteralPath (Join-Path $executionRoot 'stdout.txt')
Get-Content -LiteralPath (Join-Path $executionRoot 'stderr.txt')
if ($reviewExitCode -ne 0) { throw "public access closure failed exit=$reviewExitCode" }
$receipt | ConvertTo-Json -Depth 8
