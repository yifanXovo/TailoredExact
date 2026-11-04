"""Incremental same-PE build and transitive own-root helper binding."""
import ast
from round153_common import *
from round140_common import git

BUILD=WORK/'build-cache/round153'
COMPILER=Path('D:/msys64/ucrt64/bin/g++.exe')
SYSTEM=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
STEMS=['GurobiBaseline','PaperExternalGiniTree','main']

def dependencies(entry):
    todo=[Path(entry)];seen={}
    while todo:
        path=todo.pop().resolve();name=path.relative_to(ROOT).as_posix()
        if name in seen:continue
        seen[name]=sha(path)
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            names=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) else []
            for module in names:
                if module:
                    child=ROOT/'scripts'/(module.split('.')[0]+'.py')
                    if child.exists():todo.append(child)
    return dict(sorted(seen.items()))

def helper():
    configure();deps=dependencies(ROOT/'scripts/round153_online.py')
    value=dict(schema='round153-own-root-helper-v2',source_commit=git('rev-parse','HEAD').decode().strip(),
        helper_dependencies=deps,python=str(PYTHON),python_SHA=sha(PYTHON),DLL=str(DLL),DLL_SHA=sha(DLL),
        entry='scripts/round153_online.py',transitive_static_import_closure=True,loaded_project_sources_checked_online=True,
        NodeLimit=4096,MIPGap=0,original_price_MIPGapAbs=1e-4,Seed=0,Threads=1,
        fixed_step_wall_cap=False,whole_method_global_deadline=True,old_inventory_or_potentials_loaded=False)
    write(OUT/'helper_manifest.json',value)
    print(json.dumps(dict(helper_manifest_SHA=sha(OUT/'helper_manifest.json'),project_sources=len(deps))),flush=True)

def production(label='v1'):
    configure();oldpath=ROOT/'results/unified_exact_round151/candidate_manifest.json';old=read(oldpath)
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    for p,h in old['objects'].items():assert sha(p)==h,p
    assert sha(old['main_object']['path'])==old['main_object']['SHA']
    changed=[p for p,h in old['source_hashes'].items() if sha(ROOT/p)!=h]
    assert sorted(changed)==sorted(f'src/{s}.cpp' for s in STEMS),changed
    build=BUILD/label;build.mkdir(parents=True,exist_ok=False)
    for stem in STEMS:
        assert meter.metered('compile_'+stem+'_'+label,'build',[COMPILER,*old['flags'],'-c',ROOT/'src'/f'{stem}.cpp','-o',build/f'{stem}.o'],timeout=600)==0
    objects=[build/f'{Path(p).stem}.o' if Path(p).stem in STEMS else Path(p) for p in old['objects']]
    pe=build/'ExactEBRP.exe';command=[COMPILER,build/'main.o',*objects,old['archive']['path'],*SYSTEM,'-o',pe]
    assert meter.metered('link_production_'+label,'build',command,timeout=120)==0
    source={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include']
        for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    write(OUT/'candidate_manifest.json',dict(schema='round153-own-root-floor-v1',
        source_commit=git('rev-parse','HEAD').decode().strip(),base=BASE,source_hashes=source,
        compiled_units=STEMS,changed_old_source=changed,new_header='include/Round153Research.hpp',flags=old['flags'],
        inherited_manifest_SHA=sha(oldpath),production_PE=str(pe),production_PE_SHA=sha(pe),research_PE=str(pe),research_PE_SHA=sha(pe),
        DLL=str(DLL),DLL_SHA=DLL_SHA,objects={str(p):sha(p) for p in objects},
        main_object=dict(path=str(build/'main.o'),SHA=sha(build/'main.o')),archive=old['archive'],
        compiler_SHA=sha(COMPILER),source_ABI_unchanged=True,link_command=list(map(str,command)),default_off=True,
        methods=dict(B='stable R137 GI-TBC',J='B plus self-paid uniform own-root integer total-objective floor'),
        new_formal_columns=0,extra_formal_root_LP=0,own_helper_Native_cost_included=True))

def driver():
    configure();old=read(ROOT/'results/unified_exact_round151/candidate_manifest.json');BUILD.mkdir(parents=True,exist_ok=True)
    pe=BUILD/'Round153HelperControl.exe'
    assert meter.metered('compile_helper_control','build',[COMPILER,*old['flags'],ROOT/'scripts/round153_helper_control.cpp','-o',pe],timeout=180)==0
    write(OUT/'helper_control_driver.json',dict(PE=str(pe),PE_SHA=sha(pe),source_SHA=sha(ROOT/'scripts/round153_helper_control.cpp'),header_SHA=sha(ROOT/'include/Round153Research.hpp')))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
