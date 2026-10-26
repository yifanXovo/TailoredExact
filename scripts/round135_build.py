"""Recompile only writer/main; retain all qualified R134 production objects."""
from round135_common import *
import shutil
from round130_common import ARCHIVE
from round133_build import SYSTEM
FLAGS=['-std=c++17','-Wall','-Wextra','-Wpedantic','-DEXACT_EBRP_ENABLE_GUROBI=1',
       '-I'+str(ROOT/'include'),'-I'+str(ROOT/'scripts'),'-ID:/gurobi1302/win64/include']
def objects():
    old=read(ROOT/'results/unified_exact_round134/candidate_build.json')
    return [BUILD/'CplexBaseline.o' if Path(p).stem=='CplexBaseline' else Path(p) for p in old['linked_objects']]
def build():
    BUILD.mkdir(parents=True,exist_ok=True)
    old=read(ROOT/'results/unified_exact_round134/candidate_build.json')
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    for p,digest in old['linked_objects'].items():assert sha(p)==digest,p
    revision='_writer_exact02' if (OUT/'candidate_build.json').exists() else ''
    if revision:
        (OUT/'repair').mkdir(parents=True,exist_ok=True)
        shutil.copyfile(OUT/'candidate_build.json',OUT/'repair/pre_exact_AP_writer_build.json')
    for stem in ('CplexBaseline','main'):
        assert metered('compile_'+stem+revision,'B',[COMPILER,*FLAGS,'-c',ROOT/'src'/f'{stem}.cpp','-o',BUILD/f'{stem}.o'],reservation=600,timeout=600)==0
    args=[COMPILER,BUILD/'main.o',*objects(),ARCHIVE,*SYSTEM,'-o',E3]
    assert metered('link_production'+revision,'B',args,reservation=120,timeout=120)==0
    sources={p.relative_to(ROOT).as_posix():sha(p) for folder in ('src','include') for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    write(OUT/'candidate_build.json',dict(UTC=utc(),production=native_identity(),source_hashes=sources,
        compiled_units=['CplexBaseline','main'],source_ABI_unchanged=True,
        linked_objects={str(p):sha(p) for p in objects()},archive=dict(path=str(ARCHIVE),SHA256=sha(ARCHIVE)),
        compiler_SHA=sha(COMPILER),flags=FLAGS,link_command=list(map(str,args)),
        change='Default-off AP flag, exactly one weighted state-penalty row in the unified writer; no other algorithm change'))
def exporter():
    code=(ROOT/'scripts/round130_export.cpp').read_text(encoding='utf-8-sig')
    code=code.replace('#include "Round127Research.hpp"','#include "Round127Research.hpp"\n#include "Round135Research.hpp"')
    code=code.replace('const std::string mode=argv[6];ebrp::round127().mode=mode;',
        'const std::string mode=argv[6];ebrp::round127().mode=mode;\n    ebrp::round135AggregatePenalty()=argc==9 && std::string(argv[8])=="ap";ebrp::round135Validate();')
    source=ROOT/'scripts/round135_export.cpp';source.write_text(code,encoding='utf-8')
    args=[COMPILER,*FLAGS,source,*objects(),ARCHIVE,*SYSTEM,'-o',BUILD/'Round135Export.exe']
    revision='_writer_exact02' if (OUT/'fees/compile_exporter').exists() else ''
    assert metered('compile_exporter'+revision,'B',args,reservation=120,timeout=120)==0
if __name__=='__main__':{'build':build,'exporter':exporter}[sys.argv[1]]()
