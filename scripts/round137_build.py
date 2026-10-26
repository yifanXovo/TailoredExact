"""ABI-preserving build and zero-Optimize exporter, reusing verified objects."""
from round137_common import *

ARCHIVE=Path('C:/Users/Administrator/.codex/worktrees/round120-native-proof-disjunction/ExactEBRP/build/research/round120/libexact_ebrp_core.a')
SYSTEM=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
FLAGS=['-std=c++17','-Wall','-Wextra','-Wpedantic','-DEXACT_EBRP_ENABLE_GUROBI=1',
       '-I'+str(ROOT/'include'),'-I'+str(ROOT/'scripts'),'-ID:/gurobi1302/win64/include']
CHANGED=['CplexBaseline','IntervalRowFactory','PaperExternalGiniTree','GurobiBaseline']

def build():
    BUILD.mkdir(parents=True,exist_ok=True)
    old=read(ROOT/'results/unified_exact_round135/candidate_build.json')
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(ARCHIVE)=='f2f7608894793b60794b91fa204c7d5e8a7ce13078e6115be32ca645804c9acd'
    for p,digest in old['linked_objects'].items():assert sha(p)==digest,p
    for stem in CHANGED+['main']:
        assert metered('compile_'+stem,'build',[COMPILER,*FLAGS,'-c',ROOT/'src'/f'{stem}.cpp','-o',BUILD/f'{stem}.o'],timeout=600)==0
    objects=[BUILD/(Path(p).stem+'.o') if Path(p).stem in CHANGED else Path(p) for p in old['linked_objects']]
    cmd=[COMPILER,BUILD/'main.o',*objects,ARCHIVE,*SYSTEM,'-o',E3]
    assert metered('link_production','build',cmd,timeout=120)==0
    source={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include'] for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    write(OUT/'candidate_build.json',dict(UTC=utc(),production=native_identity(),source_hashes=source,
        compiled_units=CHANGED+['main'],linked_objects={str(p):sha(p) for p in objects},
        archive=dict(path=str(ARCHIVE),SHA256=sha(ARCHIVE)),compiler_SHA=sha(COMPILER),flags=FLAGS,
        link_command=list(map(str,cmd)),source_ABI_unchanged=True,
        scope='Default-off single-group deletions and explicit actual AM threshold; accepted ms2/AP-off unchanged when unused'))
    code=(ROOT/'scripts/round130_export.cpp').read_text(encoding='utf-8-sig')
    code=code.replace('if(argc!=8 && argc!=9)', 'if(argc!=10)')
    code=code.replace('    if(argc==9 && std::string(argv[8])=="fallback")opt.interval_row_factory_round19=false;', '')
    needle='const std::string mode=argv[6];ebrp::round127().mode=mode;'
    assert code.count(needle)==1
    code=code.replace(needle,needle+'''
    const std::string variant=argv[9]; opt.lambda=std::stod(argv[8]);
    ebrp::round137().delete_ab=variant=="no-ab";
    ebrp::round137().delete_cr=variant=="no-cr";
    ebrp::round137().delete_cg=variant=="no-cg";
    ebrp::round137Apply(opt,mode);
''')
    code=code.replace('opt.plain_baseline=true;spec.station_state_formulation',
                      'opt.plain_baseline=true;opt.lambda=std::stod(argv[8]);spec.station_state_formulation')
    target=ROOT/'scripts/round137_export.cpp';target.write_text(code,encoding='utf-8',newline='\n')
    cmd=[COMPILER,*FLAGS,target,*objects,ARCHIVE,*SYSTEM,'-o',BUILD/'Round137Export.exe']
    assert metered('compile_exporter','build',cmd,timeout=120)==0
    write(OUT/'exporter_build.json',dict(PE=str(BUILD/'Round137Export.exe'),SHA=sha(BUILD/'Round137Export.exe'),
        source_SHA=sha(target),command=list(map(str,cmd)),Optimize=0))

def refresh_main():
    label=sha(ROOT/'src/main.cpp')[:10]
    assert metered('compile_main_'+label,'build',[COMPILER,*FLAGS,'-c',ROOT/'src/main.cpp','-o',BUILD/'main.o'],timeout=600)==0
    previous=read(OUT/'candidate_build.json');objects=list(map(Path,previous['linked_objects']))
    cmd=[COMPILER,BUILD/'main.o',*objects,ARCHIVE,*SYSTEM,'-o',E3]
    assert metered('link_'+label,'build',cmd,timeout=120)==0
    write(OUT/'infra/pre_readback_build.json',previous)
    previous.update(UTC=utc(),production=native_identity(),source_hashes={p.relative_to(ROOT).as_posix():sha(p)
        for folder in ['src','include'] for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')},
        link_command=list(map(str,cmd)))
    write(OUT/'candidate_build.json',previous)

def refresh_writer():
    label=sha(ROOT/'src/CplexBaseline.cpp')[:10]
    assert metered('compile_writer_'+label,'build',[COMPILER,*FLAGS,'-c',ROOT/'src/CplexBaseline.cpp','-o',BUILD/'CplexBaseline.o'],timeout=600)==0
    previous=read(OUT/'candidate_build.json');objects=list(map(Path,previous['linked_objects']))
    cmd=[COMPILER,BUILD/'main.o',*objects,ARCHIVE,*SYSTEM,'-o',E3]
    assert metered('link_writer_'+label,'build',cmd,timeout=120)==0
    write(OUT/'infra/pre_AB_emission_fix_build.json',previous)
    previous.update(UTC=utc(),production=native_identity(),source_hashes={p.relative_to(ROOT).as_posix():sha(p)
        for folder in ['src','include'] for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')},
        linked_objects={str(p):sha(p) for p in objects},link_command=list(map(str,cmd)))
    write(OUT/'candidate_build.json',previous)
    cmd=[COMPILER,*FLAGS,ROOT/'scripts/round137_export.cpp',*objects,ARCHIVE,*SYSTEM,'-o',BUILD/'Round137Export.exe']
    assert metered('link_exporter_'+label,'build',cmd,timeout=120)==0
    write(OUT/'exporter_build.json',dict(PE=str(BUILD/'Round137Export.exe'),SHA=sha(BUILD/'Round137Export.exe'),
        source_SHA=sha(ROOT/'scripts/round137_export.cpp'),command=list(map(str,cmd)),Optimize=0))

if __name__=='__main__':
    dict(build=build,**{'refresh-main':refresh_main,'refresh-writer':refresh_writer})[sys.argv[1] if len(sys.argv)>1 else 'build']()
