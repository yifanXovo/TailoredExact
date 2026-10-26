$ErrorActionPreference = 'Stop'
$restorePublicRoot = 'E:\evidence\round110-public-20261010'
$restoreDestination = 'E:\evidence\round110-restored-20261010'
$restoreReceiptDirectory = 'E:\codes\ExactEBRP-round110\results\unified_exact_round110\engineering\public_restore01'
$restorePython = 'D:\msys64\ucrt64\bin\python.exe'
$restoreSource = Join-Path $restorePublicRoot 'scripts\round110_public.py'
if ((Test-Path -LiteralPath $restoreDestination) -or (Test-Path -LiteralPath $restoreReceiptDirectory)) { throw 'Restore destination and execution receipt directory must be fresh.' }
if ((Get-Location).Path -ne $restorePublicRoot) { throw 'Actual wrapper cwd must be the exported public root.' }
New-Item -ItemType Directory -Path $restoreReceiptDirectory | Out-Null
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $restoreReceiptDirectory 'launcher_at_execution.ps1')
$restoreArguments = @($restoreSource, 'restore', '--public-root', $restorePublicRoot, '--out', $restoreDestination)
$restoreLaunch = [ordered]@{ argv = @($restorePython) + $restoreArguments; cwd = $restorePublicRoot; source = $restoreSource; source_SHA = (Get-FileHash -LiteralPath $restoreSource -Algorithm SHA256).Hash.ToLower(); launcher_SHA = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLower(); started_UTC = [DateTime]::UtcNow.ToString('o'); engineering = $true; conservative_solver_starts = 0; original_worktree_child_reads = $false }
$restoreLaunch | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $restoreReceiptDirectory 'launch.json') -Encoding utf8
$restoreTimer = [Diagnostics.Stopwatch]::StartNew()
$restoreStdout = Join-Path $restoreReceiptDirectory 'stdout.log'
$restoreStderr = Join-Path $restoreReceiptDirectory 'stderr.log'
$restoreProcess = Start-Process -FilePath $restorePython -ArgumentList $restoreArguments -WorkingDirectory $restorePublicRoot -RedirectStandardOutput $restoreStdout -RedirectStandardError $restoreStderr -WindowStyle Hidden -PassThru
[void]$restoreProcess.Handle
@{ pid = $restoreProcess.Id } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $restoreReceiptDirectory 'process.json') -Encoding utf8
$restoreProcess.WaitForExit()
$restoreTimer.Stop()
$restoreCode = $restoreProcess.ExitCode
$restoreReceipt = [ordered]@{ exit_code = $restoreCode; seconds = $restoreTimer.Elapsed.TotalSeconds; cwd = $restorePublicRoot; source_SHA = $restoreLaunch.source_SHA; stdout_SHA = (Get-FileHash -LiteralPath $restoreStdout -Algorithm SHA256).Hash.ToLower(); stderr_SHA = (Get-FileHash -LiteralPath $restoreStderr -Algorithm SHA256).Hash.ToLower(); engineering = $true; conservative_solver_starts = 0; ended_UTC = [DateTime]::UtcNow.ToString('o') }
$restoreReceipt | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $restoreReceiptDirectory 'receipt.json') -Encoding utf8
$restoreReceipt | ConvertTo-Json -Compress
if ($restoreCode -ne 0) { Get-Content -LiteralPath $restoreStderr -Tail 20; throw 'Actual public-source restore failed; preserve the partial destination.' }
