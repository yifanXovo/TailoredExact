"""One matched B/E/J PE, retaining the existing floor producer unchanged."""
from round154_common import *
from round153_build import dependencies,COMPILER,SYSTEM,STEMS
from round140_common import git
BUILD=WORK/'build-cache/round154'

def helper():
    deps=dependencies(ROOT/'scripts/round153_online.py')
    old=read(OLD153/'helper_manifest.json')
    assert deps==old['helper_dependencies'],'producer changed; placement contrast requires the same producer'
    value=dict(old,source_commit=git('rev-parse','HEAD').decode().strip(),
               placement_study=154,unchanged_producer_manifest_SHA=sha(OLD153/'helper_manifest.json'))
    write(OUT/'helper_manifest.json',value)

def production(label='v1'):
    configure();old=read(OLD153/'candidate_manifest.json')
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    for path,digest in old['objects'].items():assert sha(path)==digest,path
    current={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include']
             for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    changes=[p for p,h in old['source_hashes'].items() if current[p]!=h]
    assert set(changes)=={'src/main.cpp','src/PaperExternalGiniTree.cpp','include/Round153Research.hpp'},changes
    assert set(current)-set(old['source_hashes'])=={'include/Round154Research.hpp'}
    build=BUILD/label;build.mkdir(parents=True,exist_ok=False)
    for stem in STEMS:
        assert meter.metered('compile_'+stem+'_'+label,'build',
            [COMPILER,*old['flags'],'-c',ROOT/'src'/f'{stem}.cpp','-o',build/f'{stem}.o'],timeout=600)==0
    objects=[build/f'{Path(p).stem}.o' if Path(p).stem in STEMS else Path(p) for p in old['objects']]
    pe=build/'ExactEBRP.exe';command=[COMPILER,build/'main.o',*objects,old['archive']['path'],*SYSTEM,'-o',pe]
    assert meter.metered('link_production_'+label,'build',command,timeout=120)==0
    write(OUT/'candidate_manifest.json',dict(schema='round154-proof-placement-v1',
        source_commit=git('rev-parse','HEAD').decode().strip(),base=BASE,source_hashes=current,
        compiled_units=STEMS,changed_old_source=changes,new_header='include/Round154Research.hpp',flags=old['flags'],
        inherited_manifest_SHA=sha(OLD153/'candidate_manifest.json'),production_PE=str(pe),production_PE_SHA=sha(pe),
        research_PE=str(pe),research_PE_SHA=sha(pe),DLL=str(DLL),DLL_SHA=DLL_SHA,
        objects={str(p):sha(p) for p in objects},main_object=dict(path=str(build/'main.o'),SHA=sha(build/'main.o')),
        archive=old['archive'],compiler_SHA=sha(COMPILER),source_ABI_unchanged=True,link_command=list(map(str,command)),
        methods=dict(B='stable R137 GI-TBC',J='same existing own-root floor in Native row',
                     E='same own-root producer, covered proof ledger only; raw search/AM bounds preserved'),
        default_off=True,new_formal_columns=0,extra_formal_root_LP=0,own_helper_Native_cost_included=True))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
