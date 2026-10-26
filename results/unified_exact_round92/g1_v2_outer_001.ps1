$ErrorActionPreference = 'Stop'
$repo = 'E:\codes\ExactEBRP'
$base = Join-Path $repo 'results\unified_exact_round92'
$python = 'D:\msys64\ucrt64\bin\python.exe'
$arguments = @('scripts/round92_g1_v2_qualification.py', '--admission',
               'results/unified_exact_round92/g1_v2_execution_admission.json')
$startedPath = Join-Path $base 'g1_v2_outer_001.started.json'
$receiptPath = Join-Path $base 'g1_v2_outer_001.receipt.json'
$stdoutPath = Join-Path $base 'g1_v2_outer_001.stdout.log'
$stderrPath = Join-Path $base 'g1_v2_outer_001.stderr.log'
foreach ($path in @($startedPath, $receiptPath, $stdoutPath, $stderrPath)) {
    if (Test-Path -LiteralPath $path) { throw "Refusing to overwrite $path" }
}
$started = [DateTimeOffset]::UtcNow
$clock = [Diagnostics.Stopwatch]::StartNew()
@{schema='round92-g1-v2-outer-launch-v1'; start_utc=$started.ToString('o');
  executable=$python; argv=$arguments; cwd=$repo; complete_process_runs_planned=1} |
  ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $startedPath -Encoding UTF8
$exitCode = -1
$failure = $null
try {
    $child = Start-Process -FilePath $python -ArgumentList $arguments `
        -WorkingDirectory $repo -WindowStyle Hidden -Wait -PassThru `
        -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $exitCode = $child.ExitCode
} catch {
    $failure = ($_ | Out-String)
    Add-Content -LiteralPath $stderrPath -Value $failure -Encoding UTF8
} finally {
    $clock.Stop()
    @{schema='round92-g1-v2-outer-receipt-v1'; start_utc=$started.ToString('o');
      finish_utc=([DateTimeOffset]::UtcNow).ToString('o');
      full_external_wall_seconds=$clock.Elapsed.TotalSeconds;
      child_exit_code=$exitCode; failure=$failure;
      executable=$python; argv=$arguments; cwd=$repo;
      stdout=$stdoutPath; stderr=$stderrPath} |
      ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
}
Write-Output "G1 v2 outer child exit=$exitCode wall=$($clock.Elapsed.TotalSeconds)s"
if ($exitCode -ne 0) { exit 1 }
