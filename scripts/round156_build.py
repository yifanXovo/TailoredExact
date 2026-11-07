"""Rebuild exactly the three translation units including Round153Controls."""
from round153_build import dependencies,COMPILER,SYSTEM,STEMS
from round140_common import git
from round156_common import *

def helpers():
    for suffix,entry,nodes in [('E','round153_online.py',4096),('Eplus','round156_online.py',16384)]:
        deps=dependencies(ROOT/'scripts'/entry)
        value=dict(schema='round156-own-root-helper-v1',source_commit=git('rev-parse','HEAD').decode().strip(),
            helper_dependencies=deps,python=str(PYTHON),python_SHA=sha(PYTHON),DLL=str(DLL),DLL_SHA=sha(DLL),
            entry='scripts/'+entry,transitive_static_import_closure=True,loaded_project_sources_checked_online=True,
            NodeLimit=nodes,MIPGap=0,original_price_MIPGapAbs=1e-4,Seed=0,Threads=1,
            producer_rule='RN16384_original_gap' if nodes==16384 else 'RN4096_original_gap',
            fixed_step_wall_cap=False,whole_method_global_deadline=True,old_inventory_or_potentials_loaded=False)
        write(OUT/f'helper_manifest_{suffix}.json',value)

def production(label):
    configure();assert not budget()['unclosed']
    old=read(PRIOR/'results/unified_exact_round154/candidate_manifest.json')
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    for path,digest in old['objects'].items():assert sha(path)==digest,path
    current={p.relative_to(ROOT).as_posix():sha(p) for folder in ('src','include')
        for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    semantic_changes=[];line_endings=[]
    for path,digest in old['source_hashes'].items():
        if current[path]==digest:continue
        actual=(ROOT/path).read_bytes();prior=(PRIOR/path).read_bytes()
        if actual.replace(b'\r\n',b'\n')==prior.replace(b'\r\n',b'\n'):
            line_endings.append(path)
        else:semantic_changes.append(path)
    assert set(semantic_changes)=={'src/main.cpp','include/Round153Research.hpp'},semantic_changes
    flags=[x.replace(str(PRIOR),str(ROOT)).replace(PRIOR.as_posix(),ROOT.as_posix()) for x in old['flags']]
    build=WORK/'build-cache/round156'/label;build.mkdir(parents=True,exist_ok=False)
    for stem in STEMS:
        assert meter.metered('compile_'+stem+'_'+label,'build',
            [COMPILER,*flags,'-c',ROOT/'src'/f'{stem}.cpp','-o',build/f'{stem}.o'],timeout=600,cwd=ROOT)==0
    objects=[build/f'{Path(p).stem}.o' if Path(p).stem in STEMS else Path(p) for p in old['objects']]
    pe=build/'ExactEBRP.exe';command=[COMPILER,build/'main.o',*objects,old['archive']['path'],*SYSTEM,'-o',pe]
    assert meter.metered('link_production_'+label,'build',command,timeout=120,cwd=ROOT)==0
    write(OUT/'candidate_manifest.json',dict(schema='round156-uniform-rn-capacity-v1',
        source_commit=git('rev-parse','HEAD').decode().strip(),base=BASE,source_hashes=current,
        compiled_units=STEMS,changed_old_source=semantic_changes,LF_CRLF_only=line_endings,flags=flags,
        inherited_manifest_SHA=sha(PRIOR/'results/unified_exact_round154/candidate_manifest.json'),
        production_PE=str(pe),production_PE_SHA=sha(pe),research_PE=str(pe),research_PE_SHA=sha(pe),DLL=str(DLL),DLL_SHA=DLL_SHA,
        objects={str(p):sha(p) for p in objects},main_object=dict(path=str(build/'main.o'),SHA=sha(build/'main.o')),
        archive=old['archive'],compiler_SHA=sha(COMPILER),link_command=list(map(str,command)),
        ABI_recompiled_all_Round153Controls_users=True,default_off=True,new_formal_columns=0,extra_formal_root_LP=0,
        methods=dict(B='stable GI-TBC',E='unchanged RN4096 proof-only',Eplus='uniform RN16384 proof-only'),
        own_helper_Native_cost_included=True))
    helpers()
    print(json.dumps(dict(PE=str(pe),SHA=sha(pe))),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
