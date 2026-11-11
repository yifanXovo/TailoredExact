"""Explicit new-only science staging; raw directories travel only in indexed ZIPs."""
from round162_common import *

def stage():
    assert not budget()['unclosed'];assert read(OUT/'carrier_manifest.json')['archives']
    paths=[]
    for p in OUT.iterdir():
        if p.is_file() and p.suffix in ('.json','.md','.csv'):paths.append(p)
    for directory in ('reports','inputs','artifacts'):
        paths.extend(p for p in (OUT/directory).rglob('*') if p.is_file())
    paths.extend(p for p in (OUT/'engineering').glob('*.json'))
    paths.extend((ROOT/'scripts').glob('round162*'))
    paths.extend(ROOT/p for p in ['.gitattributes','CMakeLists.txt','src/main.cpp','src/GurobiBaseline.cpp','src/PaperExternalGiniTree.cpp',
        'src/Round162PhysicalCompletion.cpp','src/Round162RootSource.cpp','src/round162_research_main.cpp','src/Round160PhysicalNeighborhoodStub.cpp',
        'include/Round162PhysicalCompletion.hpp','tests/round162_scope_tests.cpp','docs/round162_physical_completion.md','docs/current_mainline.md'])
    paths=sorted({p.resolve() for p in paths if p.is_file()})
    for path in paths:
        rel=path.relative_to(ROOT.resolve()).as_posix()
        assert '/infra/' not in rel and '/raw/' not in rel and '/fees/' not in rel
        assert path.suffix.lower() not in ('.exe','.dll','.lic','.key','.pfx')
        assert path.stat().st_size<95*1024*1024
    for start in range(0,len(paths),35):
        git('add','--',*[p.relative_to(ROOT.resolve()).as_posix() for p in paths[start:start+35]])
    print('Explicitly staged',len(paths),'science/code files; unpacked raw and protected inventory excluded',flush=True)

if __name__=='__main__':stage()
