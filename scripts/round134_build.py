"""Compile only two changed units; retain the qualified R133 archive and objects."""
from round134_common import *
from round130_common import ARCHIVE
from round133_build import SYSTEM
FLAGS=['-std=c++17','-Wall','-Wextra','-Wpedantic','-DEXACT_EBRP_ENABLE_GUROBI=1',
       '-I'+str(ROOT/'include'),'-I'+str(ROOT/'scripts'),'-ID:/gurobi1302/win64/include']
OLD=WORK/'build-cache/round133'
STEMS=['NativeEvidenceJournal','ControllingLeafScheduler','GurobiBaseline','PaperExternalGiniTree','IntervalRowFactory','CplexBaseline']
def objects():return [((BUILD if s in ('GurobiBaseline','PaperExternalGiniTree') else OLD)/f'{s}.o') for s in STEMS]
def build():
    BUILD.mkdir(parents=True,exist_ok=True)
    old=read(ROOT/'results/unified_exact_round133/candidate_build.json')
    assert sha(ORIGINAL_E3)==ORIGINAL_PE_SHA and sha(DLL)==DLL_SHA
    assert sha(COMPILER)==old['compiler_SHA']
    for stem in ('GurobiBaseline','PaperExternalGiniTree'):
        assert metered('compile_'+stem,'B',[COMPILER,*FLAGS,'-c',ROOT/'src'/f'{stem}.cpp','-o',BUILD/f'{stem}.o'],reservation=600,timeout=600)==0
    main=WORK/'build-cache/round130/main.o'
    args=[COMPILER,main,*objects(),ARCHIVE,*SYSTEM,'-o',E3]
    assert metered('link_production','B',args,reservation=120,timeout=120)==0
    sources={p.relative_to(ROOT).as_posix():sha(p) for folder in ('src','include') for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    write(OUT/'candidate_build.json',dict(UTC=utc(),production=native_identity(),
        source_hashes=sources,compiled_units=['GurobiBaseline','PaperExternalGiniTree'],
        source_ABI_unchanged=True,main_object=dict(path=str(main),SHA256=sha(main)),
        linked_objects={str(p):sha(p) for p in objects()},archive=dict(path=str(ARCHIVE),SHA256=sha(ARCHIVE)),
        compiler_SHA=sha(COMPILER),flags=FLAGS,link_command=list(map(str,args)),
        model_H_support_search_numeric_policy_unchanged=True,
        change='independent exact-zero original-objective proof after complete own fleet verification, regardless of native qualification'))
def tests():
    for stem in ['round134_independent_zero_tests','round133_terminal_tests','round133_inclusive_cutoff_tests','round27_paper_scheduling_tests']:
        exe=BUILD/f'{stem}.exe'
        assert metered('test_build_'+stem,'B',[COMPILER,*FLAGS,ROOT/'tests'/f'{stem}.cpp',*objects(),ARCHIVE,*SYSTEM,'-o',exe],reservation=120,timeout=120)==0
        assert metered('test_'+stem,'B',[exe],reservation=60,timeout=60,cwd=BUILD)==0
if __name__=='__main__':{'build':build,'tests':tests}[sys.argv[1]]()
