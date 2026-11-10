"""Compile changed C++ units under inherited GNU flags; bind reused objects."""
from round161_common import *
from round153_build import COMPILER,SYSTEM

def build(version='v1'):
    configure();old=read(ROOT/'results/unified_exact_round160/candidate_manifest.json')
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    for p,h in old['objects'].items():assert sha(p)==h
    target=BUILD/version;target.mkdir(parents=True,exist_ok=False)
    flags=[f if not f.startswith('-I') or 'ExactEBRP-work' not in f else '-I'+str(ROOT/Path(f[2:]).name) for f in old['flags']]
    stems=['GurobiBaseline','MipStartMapping','Round161NativeRN','round161_research_main']
    for stem in stems:
        assert metered('compile_'+version+'_'+stem,'build',[COMPILER,*flags,'-c',ROOT/'src'/f'{stem}.cpp','-o',target/f'{stem}.o'],600)==0
    reused=[p for p in old['objects'] if Path(p).stem not in stems]
    pe=target/'Round161Research.exe'
    cmd=[COMPILER,*[target/f'{s}.o' for s in stems],*reused,old['archive']['path'],DLL,*SYSTEM,'-o',pe]
    assert metered('link_'+version,'build',cmd,180)==0
    value=dict(UTC=utc(),source_commit=git('rev-parse','HEAD').decode().strip(),base=BASE,
        source_hashes={p.relative_to(ROOT).as_posix():sha(p) for name in ('src','include') for p in (ROOT/name).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')},
        flags=flags,compiler=str(COMPILER),compiler_SHA=sha(COMPILER),production_PE=str(pe),production_PE_SHA=sha(pe),
        research_PE=str(pe),research_PE_SHA=sha(pe),DLL=str(DLL),DLL_SHA=sha(DLL),
        objects={p:sha(p) for p in reused},added_objects={str(target/f'{s}.o'):sha(target/f'{s}.o') for s in stems},
        archive=old['archive'],link_command=list(map(str,cmd)),default_off=True,
        contract='same existing PaperTerminalMip backend, MIPFocus0; development NodeLimit explicit; no optimization/fast-math change')
    write(OUT/f'build_{version}.json',value);write(OUT/'candidate_manifest.json',value)

if __name__=='__main__':build(*sys.argv[1:])
