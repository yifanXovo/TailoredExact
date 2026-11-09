"""Serial offline orchestration. The new repeated algorithm and DP run in C++."""
from round159_common import *
from round140_common import git

def build():
    configure();BUILD.mkdir(parents=True,exist_ok=True)
    compiler=Path('D:/msys64/ucrt64/bin/g++.exe')
    flags=['-std=c++17','-Wall','-Wextra','-Wpedantic','-I'+str(ROOT/'include'),'-ID:/gurobi1302/win64/include']
    # Match inherited production optimization policy (no fast-math or -O override).
    command=[compiler,*flags,ROOT/'src/Round159JointResource.cpp',ROOT/'src/round159_research_main.cpp',DLL,'-o',PE]
    rc=meter.metered('compile_v1','build',command,reservation=300,timeout=300,cwd=ROOT)
    assert rc==0
    write(OUT/'build_manifest.json',dict(UTC=utc(),command=list(map(str,command)),compiler=str(compiler),compiler_SHA=sha(compiler),
        flags=flags,PE=str(PE),PE_SHA=sha(PE),DLL=str(DLL),DLL_SHA=sha(DLL),source_base=BASE,
        sources={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'src/Round159JointResource.cpp',ROOT/'include/Round159JointResource.hpp',ROOT/'src/round159_research_main.cpp']},
        standalone_research_only=True,production_PE_executions=0,production_source='092bad58d677cd8bef934d91e11d8abff93cba83',
        historical_production_PE_SHA=sha(WORK/'build-cache/round156/v1/ExactEBRP.exe')))

def execute(mode,role,label,start='',deadline='3600'):
    manifest=read(OUT/'build_manifest.json');assert sha(PE)==manifest['PE_SHA'] and sha(DLL)==manifest['DLL_SHA']==DLL_SHA
    folder=OUT/'inputs_v2'/role;target=OUT/'runs'/label
    assert not target.exists()
    env=meter.environment();env['ROUND159_METHOD_DEADLINE']=str(float(deadline))
    command=[PE,mode,folder/'data.txt',folder/'rn.mps',target]
    if start:command.append(Path(start))
    write(OUT/'runs'/f'{label}_launch.json',dict(UTC=utc(),mode=mode,role=role,command=list(map(str,command)),
        PE_SHA=sha(PE),data_SHA=sha(folder/'data.txt'),RN_SHA=sha(folder/'rn.mps'),method_deadline=float(deadline),
        capacity=dict(block_size=8,iterations=12,nodes=512,baseline_nodes=2048,DP_states=16777216),
        external_fixed_stock_and_service=True,online_time_triggered_algorithm_switch=False))
    subprocess.run(list(map(str,command)),cwd=ROOT,env=env,check=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
