"""One same-PE complete E+/STOCK/PC build and unchanged own-paid E+ helper binding."""
from round162_common import *
from round153_build import COMPILER,SYSTEM,dependencies

def build(version='v1'):
    assert not budget()['unclosed'];old=read(OUT/'build_v6.json')
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    objects={**old['objects'],**old['added_objects']}
    for p,h in objects.items():assert sha(p)==h,p
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    target=BUILD/('complete_'+version);target.mkdir(parents=True,exist_ok=False)
    source_hashes={p.relative_to(ROOT).as_posix():sha(p) for name in ('src','include') for p in (ROOT/name).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    stems=['main','PaperExternalGiniTree','GurobiBaseline','Round162PhysicalCompletion','Round162RootSource','Round160PhysicalNeighborhood']
    flags=old['flags']
    snapshots={}
    for name in ['src/'+s+'.cpp' for s in stems]+['include/Round162PhysicalCompletion.hpp']:
        raw=(ROOT/name).read_bytes();h=hashlib.sha256(raw).hexdigest();p=OUT/'engineering/complete_source_bytes'/f'{h}.txt'
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);snapshots[name]=dict(SHA256=h,path=p.relative_to(ROOT).as_posix())
    for stem in stems:
        assert metered('complete_compile_'+version+'_'+stem,'build',[COMPILER,*flags,'-c',ROOT/'src'/f'{stem}.cpp','-o',target/f'{stem}.o'],600)==0,stem
    exclude=stems+['round162_research_main','Round161NativeRN','round161_research_main']
    reused=[p for p in objects if Path(p).stem not in exclude]
    for p in reused:
        name='src/'+Path(p).stem+'.cpp';assert sha(ROOT/name)==old['source_hashes'][name],name
    executable=target/'ExactEBRP.exe'
    command=[COMPILER,*[target/f'{s}.o' for s in stems],*reused,old['archive']['path'],DLL,*SYSTEM,'-o',executable]
    assert metered('complete_link_'+version,'build',command,180)==0
    assert all(sha(ROOT/name)==digest for name,digest in source_hashes.items()),'source changed during build; PE is engineering-only and cannot be admitted'
    m=dict(UTC=utc(),source_commit=git('rev-parse','HEAD').decode().strip(),base=BASE,
        source_hashes=source_hashes,
        flags=flags,compiler=str(COMPILER),compiler_SHA=sha(COMPILER),production_PE=str(executable),production_PE_SHA=sha(executable),
        research_PE=str(executable),research_PE_SHA=sha(executable),
        DLL=str(DLL),DLL_SHA=DLL_SHA,objects={p:sha(p) for p in reused},added_objects={str(target/f'{s}.o'):sha(target/f'{s}.o') for s in stems},
        archive=old['archive'],link_command=list(map(str,command)),measured_source_bytes=snapshots,
        all_three_same_PE=True,default_off=True,no_development_NodeLimit=True,source_once=True,source_lower_diagnostic_only=True)
    write(OUT/f'complete_build_{version}.json',m);write(OUT/'complete_candidate_manifest.json',m)
    helper=dict(schema='round162-common-Eplus-proof-only-helper-v1',source_commit=m['source_commit'],
        helper_dependencies=dependencies(ROOT/'scripts/round156_online.py'),python=str(PYTHON),python_SHA=sha(PYTHON),DLL=str(DLL),DLL_SHA=DLL_SHA,
        entry='scripts/round156_online.py',transitive_static_import_closure=True,loaded_project_sources_checked_online=True,
        NodeLimit=16384,MIPGap=0,original_price_MIPGapAbs=1e-4,Seed=0,Threads=1,producer_rule='RN16384_original_gap',
        fixed_step_wall_cap=False,whole_method_global_deadline=True,old_inventory_or_potentials_loaded=False)
    write(OUT/'helper_manifest_Eplus.json',helper)
    print(json.dumps(dict(PE=str(executable),SHA256=sha(executable))),flush=True)

if __name__=='__main__':build(*sys.argv[1:])
