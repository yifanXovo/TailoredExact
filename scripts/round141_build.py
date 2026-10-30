"""Replace only changed translation units, preserving public structure ABIs."""
from round141_common import *
BUILD=WORK/'build-cache'/('round141'+(sys.argv[1] if len(sys.argv)>1 else ''))
COMPILER=Path('D:/msys64/ucrt64/bin/g++.exe')

def main():
    assert not budget()['unclosed']
    old=read(ROOT/'results/unified_exact_round140/candidate_build.json')
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    for path,digest in old['linked_objects'].items():assert sha(path)==digest,path
    BUILD.mkdir(parents=True,exist_ok=False)
    stems=['NativeEvidenceJournal','GurobiBaseline','PaperExternalGiniTree','MipStartMapping','main']
    for stem in stems:
        assert metered(BUILD.name+'_compile_'+stem,'build',[COMPILER,*old['flags'],'-c',ROOT/'src'/f'{stem}.cpp','-o',BUILD/f'{stem}.o'],timeout=600)==0
    objects=[BUILD/f'{Path(p).stem}.o' if Path(p).stem in stems else Path(p) for p in old['linked_objects']]
    objects.append(BUILD/'MipStartMapping.o')
    system=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
    command=[COMPILER,BUILD/'main.o',*objects,old['archive']['path'],*system,'-o',BUILD/'ExactEBRP.exe']
    assert metered(BUILD.name+'_link_production','build',command,timeout=120)==0
    source={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include']
            for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    manifest=dict(schema='round141-root-count-disjunction-v1',source_commit=git('rev-parse','HEAD').decode().strip(),
        base=BASE,source_hashes=source,compiled_units=stems,
        production=dict(PE=str(BUILD/'ExactEBRP.exe'),PE_SHA=sha(BUILD/'ExactEBRP.exe'),DLL=str(DLL),DLL_SHA=DLL_SHA),
        objects={str(p):sha(p) for p in objects},archive=old['archive'],compiler_SHA=sha(COMPILER),
        source_ABI_unchanged=True,link_command=list(map(str,command)),
        default_off=True,carrier='stock BOTH + old TC + TC2',selection='maximum weighted remainder then LP-floor',
        root_once=True,count_probes_local=True,BranchPriority=0)
    manifest.update(production_PE=str(BUILD/'ExactEBRP.exe'),production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),
        research_PE=str(BUILD/'ExactEBRP.exe'),research_PE_SHA=sha(BUILD/'ExactEBRP.exe'),DLL=str(DLL),DLL_SHA=DLL_SHA)
    write(OUT/'candidate_build.json',manifest)
    write(OUT/'candidate_manifest.json',manifest)

def tree_repair():
    """Only this translation unit changed after the previous admitted build."""
    assert not budget()['unclosed']
    prior=read(OUT/'candidate_build.json');old=read(ROOT/'results/unified_exact_round140/candidate_build.json')
    changed=[name for name,digest in prior['source_hashes'].items() if sha(ROOT/name)!=digest]
    assert changed==['src/PaperExternalGiniTree.cpp'],changed
    for path,digest in prior['objects'].items():assert sha(path)==digest,path
    BUILD.mkdir(parents=True,exist_ok=False)
    assert metered(BUILD.name+'_compile_tree','build',[COMPILER,*old['flags'],'-c',ROOT/changed[0],'-o',BUILD/'PaperExternalGiniTree.o'],timeout=600)==0
    objects=[BUILD/'PaperExternalGiniTree.o' if Path(p).stem=='PaperExternalGiniTree' else Path(p) for p in prior['objects']]
    main_object=Path(prior['production_PE']).parent/'main.o'
    # Later repairs may inherit an already recorded explicit main object.
    if not main_object.exists():main_object=Path(prior['main_object']['path'])
    system=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
    command=[COMPILER,main_object,*objects,prior['archive']['path'],*system,'-o',BUILD/'ExactEBRP.exe']
    assert metered(BUILD.name+'_link_production','build',command,timeout=120)==0
    manifest=dict(prior,source_commit=git('rev-parse','HEAD').decode().strip(),
        source_hashes={name:sha(ROOT/name) for name in prior['source_hashes']},compiled_units=['PaperExternalGiniTree'],
        objects={str(p):sha(p) for p in objects},main_object=dict(path=str(main_object),SHA=sha(main_object)),
        prior_build_SHA=sha(OUT/'candidate_build.json'),link_command=list(map(str,command)),
        production_PE=str(BUILD/'ExactEBRP.exe'),production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),
        research_PE=str(BUILD/'ExactEBRP.exe'),research_PE_SHA=sha(BUILD/'ExactEBRP.exe'))
    manifest['production']=dict(PE=manifest['production_PE'],PE_SHA=manifest['production_PE_SHA'],DLL=str(DLL),DLL_SHA=DLL_SHA)
    write(OUT/'candidate_build.json',manifest);write(OUT/'candidate_manifest.json',manifest)

if __name__=='__main__':tree_repair() if len(sys.argv)>2 and sys.argv[2]=='tree_repair' else main()
