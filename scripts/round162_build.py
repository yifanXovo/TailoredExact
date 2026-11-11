"""Compile new core/driver and changed backend under the inherited GNU policy."""
from round162_common import *
from round153_build import COMPILER,SYSTEM

def build(version='v1'):
    old=read(PRIOR/'build_v6.json')
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    objects={**old['objects'],**old['added_objects']}
    for p,h in objects.items(): assert sha(p)==h,p
    target=BUILD/version;target.mkdir(parents=True,exist_ok=False)
    flags=[f if not f.startswith('-I') or 'ExactEBRP-work' not in f else '-I'+str(ROOT/Path(f[2:]).name) for f in old['flags']]
    stems=['GurobiBaseline','Round162PhysicalCompletion','round162_research_main']
    for stem in stems:
        assert metered('compile_'+version+'_'+stem,'build',[COMPILER,*flags,'-c',ROOT/'src'/f'{stem}.cpp','-o',target/f'{stem}.o'],600)==0,stem
    reused=[p for p in objects if Path(p).stem not in stems+['Round161NativeRN','round161_research_main']]
    for p in reused:
        name='src/'+Path(p).stem+'.cpp'
        assert name in old['source_hashes'] and sha(ROOT/name)==old['source_hashes'][name],name
    executable=target/'Round162Research.exe'
    command=[COMPILER,*[target/f'{s}.o' for s in stems],*reused,old['archive']['path'],DLL,*SYSTEM,'-o',executable]
    assert metered('link_'+version,'build',command,180)==0
    value=dict(UTC=utc(),source_commit=git('rev-parse','HEAD').decode().strip(),base=BASE,
        source_hashes={p.relative_to(ROOT).as_posix():sha(p) for name in ('src','include') for p in (ROOT/name).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')},
        flags=flags,compiler=str(COMPILER),compiler_SHA=sha(COMPILER),research_PE=str(executable),research_PE_SHA=sha(executable),
        DLL=str(DLL),DLL_SHA=sha(DLL),objects={p:sha(p) for p in reused},added_objects={str(target/f'{s}.o'):sha(target/f'{s}.o') for s in stems},
        archive=old['archive'],link_command=list(map(str,command)),default_off=True,old_objective_replacement=False,
        contract='Inherited PaperLpRelaxation/PaperTerminalMip; Seed0 Threads1 MIPFocus0; no optimization/fast-math/tolerance changes')
    write(OUT/f'build_{version}.json',value);write(OUT/'candidate_manifest.json',value)

if __name__=='__main__':build(*sys.argv[1:])
