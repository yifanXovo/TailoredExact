param([Parameter(Mandatory=$true)][ValidateSet('preserve','build','export','readback')][string]$Step)
$ErrorActionPreference = 'Stop'
$repo = 'E:\codes\ExactEBRP'
$evidence = Join-Path $repo 'results\unified_exact_round92\qualification_002'
$build = Join-Path $repo 'build\research\round92-handling-activation'
$cmake = 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$python = Join-Path $repo 'build\research\round88-ot\venv\Scripts\python.exe'
$export = Join-Path $evidence 'canonical_export'
$oldExe = Join-Path $build 'Round92HandlingIntegrationTests.exe'
$savedExe = Join-Path $build 'failed_001\Round92HandlingIntegrationTests.exe'
$env:PATH = 'D:\msys64\ucrt64\bin;D:\gurobi1302\win64\bin;' + $env:PATH
switch ($Step) {
  preserve { $exe = 'Copy-Item'; $argv = @($oldExe,$savedExe) }
  build { $exe = $cmake; $argv = @('--build',$build,'--parallel','4','--target','Round92HandlingIntegrationTests') }
  export { $exe = $oldExe; $argv = @($export) }
  readback { $exe = $python; $argv = @((Join-Path $repo 'tests\round92_handling_lp_readback.py'),$export) }
}
$startedPath = Join-Path $evidence ($Step + '.started.json')
$receiptPath = Join-Path $evidence ($Step + '.receipt.json')
$stdoutPath = Join-Path $evidence ($Step + '.stdout.log')
$stderrPath = Join-Path $evidence ($Step + '.stderr.log')
foreach($p in @($startedPath,$receiptPath,$stdoutPath,$stderrPath)) {
  if(Test-Path -LiteralPath $p) { throw "Refusing to overwrite $p" }
}
$started = [DateTimeOffset]::UtcNow
@{stage=$Step; executable=$exe; argv=$argv; cwd=$repo;
  start_utc=$started.ToString('o'); path_prefix='D:\msys64\ucrt64\bin;D:\gurobi1302\win64\bin'} |
  ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $startedPath -Encoding UTF8
$clock = [Diagnostics.Stopwatch]::StartNew()
$exitCode = -1
try {
  if($Step -eq 'preserve') {
    if(Test-Path -LiteralPath $savedExe) { throw "Archive already exists: $savedExe" }
    New-Item -ItemType Directory -Path (Split-Path -Parent $savedExe) -ErrorAction Stop | Out-Null
    $before = (Get-FileHash -LiteralPath $oldExe -Algorithm SHA256).Hash.ToLower()
    Copy-Item -LiteralPath $oldExe -Destination $savedExe -ErrorAction Stop
    $after = (Get-FileHash -LiteralPath $savedExe -Algorithm SHA256).Hash.ToLower()
    if($before -ne $after) { throw 'Archived executable hash differs' }
    "source_sha256=$before`narchive_sha256=$after`narchive_path=$savedExe" |
      Set-Content -LiteralPath $stdoutPath -Encoding UTF8
    '' | Set-Content -LiteralPath $stderrPath -Encoding UTF8
    $exitCode = 0
  } else {
    $process = Start-Process -FilePath $exe -ArgumentList $argv -WorkingDirectory $repo `
      -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdoutPath `
      -RedirectStandardError $stderrPath
    $exitCode = $process.ExitCode
  }
} catch {
  ($_ | Out-String) | Set-Content -LiteralPath $stderrPath -Encoding UTF8
} finally {
  $clock.Stop()
  $finished = [DateTimeOffset]::UtcNow
  @{stage=$Step;exit_code=$exitCode;start_utc=$started.ToString('o');
    finish_utc=$finished.ToString('o');outer_wall_seconds=$clock.Elapsed.TotalSeconds;
    stdout_path=$stdoutPath;stderr_path=$stderrPath} |
    ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
}
Write-Output "$Step exit=$exitCode wall=$($clock.Elapsed.TotalSeconds)s receipt=$receiptPath"
if($exitCode -ne 0) { exit 1 }
