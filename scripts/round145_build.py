"""Rebuild exactly the three units affected by RN-JP and its header dependencies."""
from round145_common import *
COMPILER=Path('D:/msys64/ucrt64/bin/g++.exe')
BUILD=WORK/'build-cache/round145'
SYSTEM=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
STEMS=['GurobiBaseline','PaperExternalGiniTree','main']
def driver():
    configure();old=read(ROOT/'results/unified_exact_round144/candidate_manifest.json');BUILD.mkdir(parents=True,exist_ok=True)
    assert sha(COMPILER)==old['compiler_SHA']
    obj=next(p for p in old['objects'] if Path(p).stem=='ObjectiveResourceCompression');assert sha(obj)==old['objects'][obj]
    pe=BUILD/'Round145Project.exe'
    assert metered('compile_project','build',[COMPILER,*old['flags'],ROOT/'scripts/round145_project.cpp',obj,'-o',pe],timeout=180)==0
    write(OUT/'qualification_driver.json',dict(PE=str(pe),PE_SHA=sha(pe),source_SHA=sha(ROOT/'scripts/round145_project.cpp'),inherited_object=dict(path=obj,SHA=sha(obj))))
def production():
    configure();assert not budget()['unclosed'];old=read(ROOT/'results/unified_exact_round144/candidate_manifest.json')
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA and sha(old['archive']['path'])==old['archive']['SHA256']
    for p,h in old['objects'].items():assert sha(p)==h,p
    assert sha(old['main_object']['path'])==old['main_object']['SHA']
    changed=[p for p,h in old['source_hashes'].items() if sha(ROOT/p)!=h]
    assert sorted(changed)==sorted(['include/Round144Research.hpp']+[f'src/{s}.cpp' for s in STEMS]),changed
    BUILD.mkdir(parents=True,exist_ok=True)
    for stem in STEMS:
        assert metered('compile_'+stem,'build',[COMPILER,*old['flags'],'-c',ROOT/'src'/f'{stem}.cpp','-o',BUILD/f'{stem}.o'],timeout=600)==0
    objects=[BUILD/f'{Path(p).stem}.o' if Path(p).stem in STEMS else Path(p) for p in old['objects']]
    pe=BUILD/'ExactEBRP.exe';command=[COMPILER,BUILD/'main.o',*objects,old['archive']['path'],*SYSTEM,'-o',pe]
    assert metered('link_production','build',command,timeout=120)==0
    source={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include'] for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    manifest=dict(schema='round145-RN-NC-TS-joint-projection-v1',source_commit=git('rev-parse','HEAD').decode().strip(),base=BASE,
        source_hashes=source,compiled_units=STEMS,changed_old_source=changed,flags=old['flags'],
        inherited_manifest_SHA=sha(ROOT/'results/unified_exact_round144/candidate_manifest.json'),
        production_PE=str(pe),production_PE_SHA=sha(pe),research_PE=str(pe),research_PE_SHA=sha(pe),
        DLL=str(DLL),DLL_SHA=DLL_SHA,objects={str(p):sha(p) for p in objects},main_object=dict(path=str(BUILD/'main.o'),SHA=sha(BUILD/'main.o')),
        archive=old['archive'],compiler_SHA=sha(COMPILER),source_ABI_unchanged=True,link_command=list(map(str,command)),default_off=True,
        carrier='Stable R137 + once-root complete RN/NC/TS block projected to one original-variable row; no formal RN columns')
    write(OUT/'candidate_manifest.json',manifest)
if __name__=='__main__':globals()[sys.argv[1]]()
