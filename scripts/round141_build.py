"""Replace only changed translation units, preserving public structure ABIs."""
from round141_common import *
BUILD=WORK/'build-cache/round141'
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
        assert metered('compile_'+stem,'build',[COMPILER,*old['flags'],'-c',ROOT/'src'/f'{stem}.cpp','-o',BUILD/f'{stem}.o'],timeout=600)==0
    objects=[BUILD/f'{Path(p).stem}.o' if Path(p).stem in stems else Path(p) for p in old['linked_objects']]
    objects.append(BUILD/'MipStartMapping.o')
    system=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
    command=[COMPILER,BUILD/'main.o',*objects,old['archive']['path'],*system,'-o',BUILD/'ExactEBRP.exe']
    assert metered('link_production','build',command,timeout=120)==0
    source={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include']
            for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    manifest=dict(schema='round141-root-count-disjunction-v1',source_commit=git('rev-parse','HEAD').decode().strip(),
        base=BASE,source_hashes=source,compiled_units=stems,
        production=dict(PE=str(BUILD/'ExactEBRP.exe'),PE_SHA=sha(BUILD/'ExactEBRP.exe'),DLL=str(DLL),DLL_SHA=DLL_SHA),
        objects={str(p):sha(p) for p in objects},archive=old['archive'],compiler_SHA=sha(COMPILER),
        source_ABI_unchanged=True,link_command=list(map(str,command)),
        default_off=True,carrier='stock BOTH + old TC + TC2',selection='maximum weighted remainder then LP-floor',
        root_once=True,count_probes_local=True,BranchPriority=0)
    write(OUT/'candidate_build.json',manifest)
    write(OUT/'candidate_manifest.json',manifest)

if __name__=='__main__':main()
