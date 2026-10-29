"""Minimal ABI-preserving placement build; preserve all historical PE/objects."""
from round139_common import *

def main():
    assert not budget()['unclosed']
    old=read(ROOT/'results/unified_exact_round138/candidate_repair_build.json')
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    for path,digest in old['linked_objects'].items(): assert sha(path)==digest,path
    BUILD.mkdir(parents=True,exist_ok=False)
    flags=old['flags']
    for stem in ['PaperExternalGiniTree','main']:
        assert metered('compile_'+stem,'build',[COMPILER,*flags,'-c',ROOT/'src'/f'{stem}.cpp','-o',BUILD/f'{stem}.o'],timeout=600)==0
    objects=[BUILD/'PaperExternalGiniTree.o' if Path(p).stem=='PaperExternalGiniTree' else Path(p) for p in old['linked_objects']]
    system=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
    command=[COMPILER,BUILD/'main.o',*objects,old['archive']['path'],*system,'-o',E3]
    assert metered('link_production','build',command,timeout=120)==0
    source={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include'] for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    write(OUT/'candidate_build.json',dict(UTC=utc(),production=native_identity(),source_hashes=source,
        compiled_units=['PaperExternalGiniTree','main'],linked_objects={str(p):sha(p) for p in objects},
        archive=old['archive'],compiler_SHA=old['compiler_SHA'],flags=flags,link_command=list(map(str,command)),
        source_ABI_unchanged=True,V2_writer_object_unchanged=True,
        scope='Uniform explicit LP/MIP placement; legacy off/both paths preserved; asymmetric role transition discards native model and rebuilds immutable canonical without clearing same-domain LP evidence'))
    print('Built Round139 production PE; legacy PE and V2 writer retained')

if __name__=='__main__':main()
