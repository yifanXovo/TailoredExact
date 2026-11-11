"""Finite, serial OLD/RN whole-native bridge. Each real call owns one deadline."""
from round161_common import *

def command(role,form,mode,label,cap,nodes):
    source=read(OUT/'inputs'/role/'source.json');p=source['panel'];folder=OUT/'inputs'/role
    return [PE,folder/'instance.txt',p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],
        folder/'parent.txt',OUT/'runs'/label,form,mode,cap,nodes]

def call(role,form,mode,label,cap='900',nodes='4096'):
    manifest=read(OUT/'candidate_manifest.json');assert sha(PE)==manifest['research_PE_SHA'] and sha(DLL)==DLL_SHA
    cmd=command(role,form,mode,label,float(cap),int(nodes))
    write(OUT/'launches'/f'{label}.json',dict(UTC=utc(),command=list(map(str,cmd)),PE_SHA=sha(PE),DLL_SHA=sha(DLL),
        input_SHA=sha(cmd[1]),parent_SHA=sha(cmd[6]),Seed=0,Threads=1,MIPFocus=0,NodeLimit=int(nodes),outer_cap=float(cap),
        source_hashes={name:sha(ROOT/name) for name in ('src/Round161NativeRN.cpp','src/round161_research_main.cpp','src/MipStartMapping.cpp','src/GurobiBaseline.cpp')}))
    rc=metered(label,'native',cmd,float(cap)+30)
    if rc:raise RuntimeError((label,rc))

def panel():
    for role in ('R-X35-S-T2','N-B35-S'):
        for mode in ('LP','MIP'):
            for form in ('OLD','RN'):
                label=f'{role}_{form}_{mode}_v1'
                call(role,form,mode,label,300 if mode=='LP' else 900, -1 if mode=='LP' else 4096)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
