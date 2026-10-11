"""Read-only admission: exclude actual waiting ancestors, not arbitrary launchers."""
import json, os, subprocess
import round90_lp_g_g3 as r90
def ensure_idle():
    raw=subprocess.check_output(['powershell.exe','-NoProfile','-Command',
        'Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json -Compress'],text=True,timeout=30)
    processes=json.loads(raw);by_id={int(p['ProcessId']):p for p in processes}
    ancestors=set();pid=os.getpid()
    while pid and pid not in ancestors:
        ancestors.add(pid);pid=int(by_id.get(pid,{}).get('ParentProcessId',0))
    foreign=[p for p in r90.foreign_heavy_processes() if int(p['ProcessId']) not in ancestors]
    foreign += [p for p in processes if int(p['ProcessId']) not in ancestors and
        p['Name'].lower() in ('python.exe','pythonw.exe') and
        any(x in (p.get('CommandLine') or '') for x in ('round96_fixed_route','round96_route_prototype','round96_quantity_prototype'))]
    assert not foreign,('foreign optimizer/build process active',foreign)
