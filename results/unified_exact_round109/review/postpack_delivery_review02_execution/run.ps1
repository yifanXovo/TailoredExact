$ErrorActionPreference = 'Stop'
$authoringRoot = 'E:/codes/ExactEBRP-round109'
$reviewRoot = Join-Path $authoringRoot 'results/unified_exact_round109/review'
$executionRoot = Join-Path $reviewRoot 'postpack_delivery_review02_execution'
$sourcePath = Join-Path $executionRoot 'check.py'
$auditPath = Join-Path $reviewRoot 'postpack_delivery_review02/audit.json'
if ((Get-Location).Path -ne 'E:\codes\ExactEBRP-round109') { throw 'wrong cwd' }
if (Test-Path -LiteralPath (Join-Path $executionRoot 'receipt.json')) { throw 'execution already closed' }
$argumentVector = @('-I', $sourcePath)
$launch = @{
    executable = 'D:/msys64/ucrt64/bin/python.exe'
    argv = $argumentVector
    cwd = (Get-Location).Path
    source_SHA = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
    execution_source_SHA = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    phase = 'post-pack authoring-document and copied closed-receipt review'
    new_raw_rebuilds = 0
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
    explicit_read_root = $authoringRoot
    source_SHA = $launch.source_SHA
    execution_source_SHA = $launch.execution_source_SHA
    launch_SHA = (Get-FileHash -LiteralPath (Join-Path $executionRoot 'launch.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    stdout_SHA = (Get-FileHash -LiteralPath (Join-Path $executionRoot 'stdout.txt') -Algorithm SHA256).Hash.ToLowerInvariant()
    stderr_SHA = (Get-FileHash -LiteralPath (Join-Path $executionRoot 'stderr.txt') -Algorithm SHA256).Hash.ToLowerInvariant()
    new_raw_rebuilds = 0
    Optimize = 0
    native_environments = 0
}
if (Test-Path -LiteralPath $auditPath) { $receipt.audit_SHA = (Get-FileHash -LiteralPath $auditPath -Algorithm SHA256).Hash.ToLowerInvariant() }
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $executionRoot 'receipt.json') -Encoding UTF8
Get-Content -LiteralPath (Join-Path $executionRoot 'stdout.txt')
Get-Content -LiteralPath (Join-Path $executionRoot 'stderr.txt')
if ($reviewExitCode -ne 0) { throw "post-pack narrative review failed exit=$reviewExitCode" }
$receipt | ConvertTo-Json -Depth 8
