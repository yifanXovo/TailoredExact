"""Build actual affected units, retaining the verified R142 object lineage."""
from round143_common import *
BUILD=WORK/'build-cache/round143'
COMPILER=Path('D:/msys64/ucrt64/bin/g++.exe')
STEMS=['CplexBaseline','GurobiBaseline','MipStartMapping','main']
SYSTEM=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']

def main():
    assert not budget()['unclosed']
    old=read(ROOT/'results/unified_exact_round142/candidate_manifest.json')
    flags=read(ROOT/'results/unified_exact_round140/candidate_build.json')['flags']
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    for path,digest in old['objects'].items():assert sha(path)==digest,path
    changed=[name for name,digest in old['source_hashes'].items() if sha(ROOT/name)!=digest]
    assert sorted(changed)==[f'src/{s}.cpp' for s in STEMS],changed
    BUILD.mkdir(parents=True,exist_ok=False)
    for stem in STEMS:
        assert metered('compile_'+stem,'build',[COMPILER,*flags,'-c',ROOT/'src'/f'{stem}.cpp','-o',BUILD/f'{stem}.o'],timeout=600)==0
    objects=[BUILD/f'{Path(p).stem}.o' if Path(p).stem in STEMS else Path(p) for p in old['objects']]
    command=[COMPILER,BUILD/'main.o',*objects,old['archive']['path'],*SYSTEM,'-o',BUILD/'ExactEBRP.exe']
    assert metered('link_production','build',command,timeout=120)==0
    source={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include'] for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    pe=BUILD/'ExactEBRP.exe'
    manifest=dict(schema='round143-reciprocal-normalization-v1',source_commit=git('rev-parse','HEAD').decode().strip(),base=BASE,
        source_hashes=source,compiled_units=STEMS,changed_old_source=changed,flags=flags,
        inherited_manifest_SHA=sha(ROOT/'results/unified_exact_round142/candidate_manifest.json'),
        production_PE=str(pe),production_PE_SHA=sha(pe),research_PE=str(pe),research_PE_SHA=sha(pe),
        DLL=str(DLL),DLL_SHA=DLL_SHA,objects={str(p):sha(p) for p in objects},
        main_object=dict(path=str(BUILD/'main.o'),SHA=sha(BUILD/'main.o')),archive=old['archive'],compiler_SHA=sha(COMPILER),
        source_ABI_unchanged=True,link_command=list(map(str,command)),default_off=True,
        carrier='stable R137 GI-TBC + RN; R138-R142 and AP off')
    write(OUT/'candidate_build.json',manifest);write(OUT/'candidate_manifest.json',manifest)

if __name__=='__main__':main()
