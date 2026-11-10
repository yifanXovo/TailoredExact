"""Same-PE incremental production build; unchanged old objects are hash-bound."""
from round160_common import *
from round153_build import COMPILER,SYSTEM,dependencies

def production(version='v1'):
    configure();assert not budget()['unclosed']
    oldpath=WORK/'worktrees/round156/results/unified_exact_round156/candidate_manifest.json'
    old=read(oldpath);assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    for p,digest in old['objects'].items():assert sha(p)==digest
    current={p.relative_to(ROOT).as_posix():sha(p) for folder in ('src','include') for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    semantic=[]
    for name in old['source_hashes']:
        if name=='src/main.cpp':continue
        a=(ROOT/name).read_bytes().replace(b'\r\n',b'\n')
        b=git('show','092bad58d677cd8bef934d91e11d8abff93cba83:'+name).replace(b'\r\n',b'\n')
        if a!=b:semantic.append(name)
    assert not semantic,semantic
    flags=[]
    for flag in old['flags']:
        if flag.startswith('-I') and Path(flag[2:]).name in ('include','scripts'):
            flag='-I'+str(ROOT/Path(flag[2:]).name)
        flags.append(flag)
    target=BUILD/('production_'+version);target.mkdir(parents=True,exist_ok=False)
    snapshot('production_'+version)
    units=['main','Round160PhysicalNeighborhood']
    for stem in units:
        command=[COMPILER,*flags,'-c',ROOT/'src'/f'{stem}.cpp','-o',target/f'{stem}.o']
        assert meter.metered('production_compile_'+stem+'_'+version,'build',command,timeout=600,cwd=ROOT)==0
    pe=target/'ExactEBRP.exe'
    command=[COMPILER,target/'main.o',target/'Round160PhysicalNeighborhood.o',*old['objects'],old['archive']['path'],DLL,*SYSTEM,'-o',pe]
    assert meter.metered('production_link_'+version,'build',command,timeout=120,cwd=ROOT)==0
    value=dict(schema='round160-own-physical-primal-v1',source_commit=git('rev-parse','HEAD').decode().strip(),base=BASE,
        source_hashes=current,compiled_units=units,flags=flags,inherited_manifest_SHA=sha(oldpath),
        production_PE=str(pe),production_PE_SHA=sha(pe),research_PE=str(pe),research_PE_SHA=sha(pe),
        DLL=str(DLL),DLL_SHA=DLL_SHA,compiler_SHA=sha(COMPILER),objects=old['objects'],archive=old['archive'],
        added_objects={str(target/f'{s}.o'):sha(target/f'{s}.o') for s in units},
        link_command=list(map(str,command)),ABI_unchanged=True,all_other_production_source_semantically_equal=True,
        default_off=True,same_PE_off_on=True,new_global_proof_rows=0,online_capacity=read(OUT/'candidate_decision.json'))
    write(OUT/'candidate_manifest.json',value)
    deps=dependencies(ROOT/'scripts/round156_online.py')
    write(OUT/'helper_manifest_Eplus.json',dict(schema='round160-common-Eplus-helper-v1',
        source_commit=value['source_commit'],helper_dependencies=deps,python=str(PYTHON),python_SHA=sha(PYTHON),
        DLL=str(DLL),DLL_SHA=DLL_SHA,entry='scripts/round156_online.py',transitive_static_import_closure=True,
        loaded_project_sources_checked_online=True,NodeLimit=16384,MIPGap=0,original_price_MIPGapAbs=1e-4,
        Seed=0,Threads=1,producer_rule='RN16384_original_gap',fixed_step_wall_cap=False,
        whole_method_global_deadline=True,old_inventory_or_potentials_loaded=False))
    print(json.dumps(dict(PE=str(pe),SHA=sha(pe))),flush=True)

if __name__=='__main__':production(*sys.argv[1:])
