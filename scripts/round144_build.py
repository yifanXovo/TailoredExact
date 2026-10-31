"""Rebuild all four affected units against the verified R143 object lineage."""
from round144_common import *
BUILD=WORK/'build-cache/round144'
COMPILER=Path('D:/msys64/ucrt64/bin/g++.exe')
STEMS=['ObjectiveResourceCompression','GurobiBaseline','PaperExternalGiniTree','main']
SYSTEM=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
def main():
    assert not budget()['unclosed']
    old=read(ROOT/'results/unified_exact_round143/candidate_manifest.json')
    flags=old['flags'];assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    for path,digest in old['objects'].items():assert sha(path)==digest,path
    assert sha(old['main_object']['path'])==old['main_object']['SHA']
    changed=[p for p,h in old['source_hashes'].items() if sha(ROOT/p)!=h]
    assert sorted(changed)==sorted([f'src/{s}.cpp' for s in STEMS]+['include/ObjectiveResourceCompression.hpp']),changed
    BUILD.mkdir(parents=True,exist_ok=False)
    for stem in STEMS:
        assert metered('compile_'+stem,'build',[COMPILER,*flags,'-c',ROOT/'src'/f'{stem}.cpp','-o',BUILD/f'{stem}.o'],timeout=600)==0
    objects=[BUILD/f'{Path(p).stem}.o' if Path(p).stem in STEMS else Path(p) for p in old['objects']]
    objects.append(BUILD/'ObjectiveResourceCompression.o')
    command=[COMPILER,BUILD/'main.o',*objects,old['archive']['path'],*SYSTEM,'-o',BUILD/'ExactEBRP.exe']
    assert metered('link_production','build',command,timeout=120)==0
    source={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include'] for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    pe=BUILD/'ExactEBRP.exe'
    manifest=dict(schema='round144-RN-projection-v1',source_commit=git('rev-parse','HEAD').decode().strip(),base=BASE,
        source_hashes=source,compiled_units=STEMS,changed_old_source=changed,flags=flags,
        inherited_manifest_SHA=sha(ROOT/'results/unified_exact_round143/candidate_manifest.json'),
        production_PE=str(pe),production_PE_SHA=sha(pe),research_PE=str(pe),research_PE_SHA=sha(pe),
        DLL=str(DLL),DLL_SHA=DLL_SHA,objects={str(p):sha(p) for p in objects},
        main_object=dict(path=str(BUILD/'main.o'),SHA=sha(BUILD/'main.o')),archive=old['archive'],compiler_SHA=sha(COMPILER),
        source_ABI_unchanged=True,link_command=list(map(str,command)),default_off=True,
        carrier='Stable R137 + once-root RN source and one original-selector/G projected row; zero formal RN columns')
    write(OUT/'candidate_build.json',manifest);write(OUT/'candidate_manifest.json',manifest)
if __name__=='__main__':main()
