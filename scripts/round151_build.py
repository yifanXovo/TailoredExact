"""Incremental same-new-PE build; costs separate from experimental budget."""
from round151_common import *
COMPILER=Path('D:/msys64/ucrt64/bin/g++.exe')
SYSTEM=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
STEMS=['GurobiBaseline','PaperExternalGiniTree','main']
def driver():
    configure();old=read(ROOT/'results/unified_exact_round149/candidate_manifest.json')
    assert sha(COMPILER)==old['compiler_SHA'];BUILD.mkdir(parents=True,exist_ok=True)
    pe=BUILD/'Round151Rows.exe'
    assert metered('compile_rows_v2','build',[COMPILER,*old['flags'],ROOT/'scripts/round151_rows.cpp','-o',pe],timeout=180)==0
    write(OUT/'rows_driver.json',dict(PE=str(pe),PE_SHA=sha(pe),source_SHA=sha(ROOT/'scripts/round151_rows.cpp'),header_SHA=sha(ROOT/'include/Round151Research.hpp')))
def production():
    configure();old=read(ROOT/'results/unified_exact_round149/candidate_manifest.json')
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    for p,h in old['objects'].items():assert sha(p)==h,p
    assert sha(old['main_object']['path'])==old['main_object']['SHA']
    changed=[p for p,h in old['source_hashes'].items() if sha(ROOT/p)!=h]
    assert sorted(changed)==sorted(f'src/{s}.cpp' for s in STEMS),changed
    for stem in STEMS:
        assert metered('compile_'+stem,'build',[COMPILER,*old['flags'],'-c',ROOT/'src'/f'{stem}.cpp','-o',BUILD/f'{stem}.o'],timeout=600)==0
    objects=[BUILD/f'{Path(p).stem}.o' if Path(p).stem in STEMS else Path(p) for p in old['objects']]
    pe=BUILD/'ExactEBRP.exe';command=[COMPILER,BUILD/'main.o',*objects,old['archive']['path'],*SYSTEM,'-o',pe]
    assert metered('link_production','build',command,timeout=120)==0
    source={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include']
        for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    write(OUT/'candidate_manifest.json',dict(schema='round151-standalone-penalty-propagation-v1',
        source_commit=git('rev-parse','HEAD').decode().strip(),base=BASE,source_hashes=source,
        compiled_units=STEMS,changed_old_source=changed,new_header='include/Round151Research.hpp',flags=old['flags'],
        inherited_manifest_SHA=sha(ROOT/'results/unified_exact_round149/candidate_manifest.json'),
        production_PE=str(pe),production_PE_SHA=sha(pe),research_PE=str(pe),research_PE_SHA=sha(pe),
        DLL=str(DLL),DLL_SHA=DLL_SHA,objects={str(p):sha(p) for p in objects},
        main_object=dict(path=str(BUILD/'main.o'),SHA=sha(BUILD/'main.o')),archive=old['archive'],
        compiler_SHA=sha(COMPILER),source_ABI_unchanged=True,link_command=list(map(str,command)),default_off=True,
        methods=dict(B='stable R137 GI-TBC, GD off, propagation off',P='B plus uniform frozen root caps',C='B plus conditional frozen root caps'),
        method_definition_science=dict(B=SCIENCE137),new_columns=0,source_solves=0,extra_root_LP=0))
if __name__=='__main__':globals()[sys.argv[1]]()
