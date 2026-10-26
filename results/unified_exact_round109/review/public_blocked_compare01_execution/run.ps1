$ErrorActionPreference = 'Stop'
$recoveredRoot = 'E:/codes/ExactEBRP-round109-restored01'
$reviewRoot = Join-Path $recoveredRoot 'results/unified_exact_round109/review'
$executionRoot = Join-Path $reviewRoot 'public_blocked_compare01_execution'
$auditRoot = Join-Path $reviewRoot 'public_blocked_compare01'
$reviewSource = Join-Path $reviewRoot 'round109_independent_final_compare.py'
$reportsRoot = Join-Path $recoveredRoot 'results/unified_exact_round109/reports_final'
$ownAudit = Join-Path $reviewRoot 'public_blocked_raw01/audit.json'
if ((Get-Location).Path -ne 'E:\codes\ExactEBRP-round109-restored01') { throw 'wrong cwd' }
if (Test-Path -LiteralPath $auditRoot) { throw 'exclusive comparison destination exists' }
if (Test-Path -LiteralPath (Join-Path $executionRoot 'receipt.json')) { throw 'execution already closed' }
$sourceHash = (Get-FileHash -LiteralPath $reviewSource -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sourceHash -ne 'b0454be1a28f1baf5a67ce5699a2dbd4db0da2e9e1bb23c3030d0b4bf4cbdae3') { throw 'restored comparison source mismatch' }
$ownReceipt = Get-Content -LiteralPath (Join-Path $reviewRoot 'public_blocked_raw01/receipt.json') -Raw | ConvertFrom-Json
if ($ownReceipt.exit_code -ne 0) { throw 'own actual public raw review not successful' }
Copy-Item -LiteralPath $reviewSource -Destination (Join-Path $executionRoot 'source_snapshot.py')
$argumentVector = @('-I', $reviewSource, '--root', $recoveredRoot, '--own-audit', $ownAudit, '--reports', $reportsRoot, '--out', $auditRoot)
$launch = @{
    executable = 'D:/msys64/ucrt64/bin/python.exe'
    argv = $argumentVector
    cwd = (Get-Location).Path
    source_SHA = $sourceHash
    own_actual_public_audit_SHA = (Get-FileHash -LiteralPath $ownAudit -Algorithm SHA256).Hash.ToLowerInvariant()
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
if (Test-Path -LiteralPath (Join-Path $auditRoot 'audit.json')) { $receipt.audit_SHA = (Get-FileHash -LiteralPath (Join-Path $auditRoot 'audit.json') -Algorithm SHA256).Hash.ToLowerInvariant() }
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $executionRoot 'receipt.json') -Encoding UTF8
Get-Content -LiteralPath (Join-Path $executionRoot 'stdout.txt')
Get-Content -LiteralPath (Join-Path $executionRoot 'stderr.txt')
if ($reviewExitCode -ne 0) { throw "public scientific comparison failed exit=$reviewExitCode" }
$receipt | ConvertTo-Json -Depth 8
