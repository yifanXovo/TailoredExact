param([Parameter(Mandatory=$true)][ValidateSet('configure','build','ctest','export','readback')][string]$Step)
$ErrorActionPreference = 'Stop'
$repo = 'E:\codes\ExactEBRP'
$evidence = Join-Path $repo 'results\unified_exact_round92\qualification_001'
$build = Join-Path $repo 'build\research\round92-handling-activation'
$cmake = 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$ctest = 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe'
$python = Join-Path $repo 'build\research\round88-ot\venv\Scripts\python.exe'
$export = Join-Path $evidence 'canonical_export'
$env:PATH = 'D:\msys64\ucrt64\bin;D:\gurobi1302\win64\bin;' + $env:PATH
switch ($Step) {
    configure {
        $exe = $cmake
        $argv = @('-S', $repo, '-B', $build, '-G', 'Ninja',
            '-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe',
            '-DCMAKE_MAKE_PROGRAM=D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe',
            '-DEXACT_EBRP_ENABLE_GUROBI=ON', '-DGUROBI_ROOT=D:/gurobi1302/win64')
    }
    build {
        $exe = $cmake
        $argv = @('--build', $build, '--parallel', '4', '--target', 'ExactEBRP',
            'Round92HandlingActivationTests', 'Round92HandlingIntegrationTests')
    }
    ctest {
        $exe = $ctest
        $argv = @('--test-dir', $build, '--output-on-failure', '-R',
            '^(Round92HandlingActivationTests|Round92HandlingActivationCliTests)$')
    }
    export {
        $exe = Join-Path $build 'Round92HandlingIntegrationTests.exe'
        $argv = @($export)
    }
    readback {
        $exe = $python
        $argv = @((Join-Path $repo 'tests\round92_handling_lp_readback.py'), $export)
    }
}
$startedPath = Join-Path $evidence ($Step + '.started.json')
$receiptPath = Join-Path $evidence ($Step + '.receipt.json')
$stdoutPath = Join-Path $evidence ($Step + '.stdout.log')
$stderrPath = Join-Path $evidence ($Step + '.stderr.log')
foreach ($path in @($startedPath,$receiptPath,$stdoutPath,$stderrPath)) {
    if (Test-Path -LiteralPath $path) { throw "Refusing to overwrite $path" }
}
$started = [DateTimeOffset]::UtcNow
$command = @{
    stage = $Step; executable = $exe; argv = $argv; cwd = $repo
    start_utc = $started.ToString('o')
    path_prefix = 'D:\msys64\ucrt64\bin;D:\gurobi1302\win64\bin'
}
$command | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $startedPath -Encoding UTF8
$clock = [Diagnostics.Stopwatch]::StartNew()
Push-Location -LiteralPath $repo
try {
    & $exe @argv 1> $stdoutPath 2> $stderrPath
    $exitCode = $LASTEXITCODE
} catch {
    $_ | Out-String | Add-Content -LiteralPath $stderrPath
    $exitCode = -1
} finally {
    Pop-Location
    $clock.Stop()
}
$finished = [DateTimeOffset]::UtcNow
$receipt = @{
    stage = $Step; exit_code = $exitCode; start_utc = $started.ToString('o')
    finish_utc = $finished.ToString('o'); outer_wall_seconds = $clock.Elapsed.TotalSeconds
    stdout_path = $stdoutPath; stderr_path = $stderrPath
}
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
Write-Output "$Step exit=$exitCode wall=$($clock.Elapsed.TotalSeconds)s receipt=$receiptPath"
if ($exitCode -ne 0) { exit 1 }
