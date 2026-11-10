"""Build and serial bounded launches; all repeated neighborhood work is C++."""
from round160_common import *

def build(version='v1'):
    configure();BUILD.mkdir(parents=True,exist_ok=True)
    compiler=Path('D:/msys64/ucrt64/bin/g++.exe')
    flags=['-std=c++17','-Wall','-Wextra','-Wpedantic','-I'+str(ROOT/'include'),'-ID:/gurobi1302/win64/include']
    sources=[ROOT/'src'/f for f in ['Round160PhysicalNeighborhood.cpp','round160_research_main.cpp','Parser.cpp','Evaluator.cpp','Result.cpp']]
    command=[compiler,*flags,*sources,DLL,'-o',PE]
    snapshot('build_'+version)
    rc=meter.metered('compile_'+version,'build',command,reservation=300,timeout=300,cwd=ROOT)
    assert rc==0
    manifest=dict(UTC=utc(),command=list(map(str,command)),compiler=str(compiler),compiler_SHA=sha(compiler),flags=flags,
        PE=str(PE),PE_SHA=sha(PE),DLL=str(DLL),DLL_SHA=sha(DLL),source_base=BASE,
        sources={str(p.relative_to(ROOT)):sha(p) for p in sources+[ROOT/'include/Round160PhysicalNeighborhood.hpp']},
        optimization_policy='inherited GNU C++17 flags; no optimization override or fast-math',production=False)
    import shutil
    runtime=OUT/'runtime'/f'Round160Research_{version}.exe';runtime.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(PE,runtime);manifest['carrier_PE']=runtime.relative_to(ROOT).as_posix()
    write(OUT/f'engineering/build_{version}.json',manifest);write(OUT/'build_manifest.json',manifest)

def execute(role,label,seconds='21600',nodes='512',passes='1',mode='joint',*block):
    manifest=read(OUT/'build_manifest.json');assert sha(PE)==manifest['PE_SHA'] and sha(DLL)==DLL_SHA
    folder=OUT/'inputs'/role;source=read(folder/'source.json');p=source['panel'];target=OUT/'runs'/label
    assert not target.exists()
    command=[PE,folder/'instance.txt',p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],
             folder/'parent.txt',target,seconds,nodes,passes,mode,*block]
    write(OUT/'runs'/f'{label}_launch.json',dict(UTC=utc(),command=list(map(str,command)),role=role,mode=mode,
        input_SHA=sha(folder/'instance.txt'),parent_SHA=sha(folder/'parent.txt'),PE_SHA=sha(PE),
        nodes=int(nodes),passes=int(passes),method_deadline=float(seconds),Seed=0,Threads=1,
        global_proof_consumption=False))
    import ctypes
    ctypes.windll.kernel32.SetProcessAffinityMask(ctypes.windll.kernel32.GetCurrentProcess(),4)
    subprocess.run(list(map(str,command)),cwd=ROOT,env=meter.environment(),check=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
