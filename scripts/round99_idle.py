"""Read-only idle admission excluding this process and its waiting launcher."""
import os,subprocess
import round90_lp_g_g3 as r90
def ensure_idle():
    # Windows venv python.exe is a redirector. Its parent waits for this child
    # while retaining the same command line; it performs no simultaneous solve.
    owned={os.getpid(),os.getppid()}
    foreign=[p for p in r90.foreign_heavy_processes() if int(p['ProcessId']) not in owned]
    assert not foreign,('foreign solver or build process active',foreign)
    raw=subprocess.check_output(['powershell.exe','-NoProfile','-Command',
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?\\.exe$' -and $_.CommandLine -match 'round96_fixed_route|round96_.*prototype' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"],text=True).strip()
    assert not raw,('R96 diagnostic/prototype active',raw)
