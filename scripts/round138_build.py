"""Minimal ABI-preserving Round138 build; frozen Round137 objects stay intact."""
from round138_common import *

def main():
    old = read(ROOT/'results/unified_exact_round137/candidate_build.json')
    assert sha(COMPILER) == old['compiler_SHA'] and sha(DLL) == DLL_SHA
    archive = Path(old['archive']['path'])
    assert sha(archive) == old['archive']['SHA256']
    for path, digest in old['linked_objects'].items():
        assert sha(path) == digest, path
    flags = ['-std=c++17','-Wall','-Wextra','-Wpedantic','-DEXACT_EBRP_ENABLE_GUROBI=1',
             '-I'+str(ROOT/'include'),'-I'+str(ROOT/'scripts'),'-ID:/gurobi1302/win64/include']
    system = ['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32',
              '-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
    BUILD.mkdir(parents=True, exist_ok=True)
    for stem in ['CplexBaseline','main']:
        assert metered('compile_'+stem,'build',[COMPILER,*flags,'-c',ROOT/'src'/f'{stem}.cpp',
                    '-o',BUILD/f'{stem}.o'],timeout=600) == 0
    objects = [BUILD/'CplexBaseline.o' if Path(p).stem == 'CplexBaseline' else Path(p)
               for p in old['linked_objects']]
    assert metered('link_production','build',[COMPILER,BUILD/'main.o',*objects,archive,*system,
                    '-o',E3],timeout=120) == 0
    code = (ROOT/'scripts/round137_export.cpp').read_text(encoding='utf-8-sig')
    code = code.replace('#include "PaperK1AmSf.hpp"', '#include "PaperK1AmSf.hpp"\n#include "Round138Research.hpp"')
    needle = 'const std::string variant=argv[9]; opt.lambda=std::stod(argv[8]);'
    assert code.count(needle) == 1
    code = code.replace(needle, needle + '\n    if(variant!="off" && variant!="stock")throw std::runtime_error("Round138 export variant");\n    ebrp::round138().stock_rlt=variant=="stock";')
    target = ROOT/'scripts/round138_export.cpp'
    target.write_text(code,encoding='utf-8',newline='\n')
    assert metered('compile_exporter','build',[COMPILER,*flags,target,*objects,archive,*system,
                    '-o',BUILD/'Round138Export.exe'],timeout=180) == 0
    source = {p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include']
              for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    write(OUT/'candidate_build.json',dict(UTC=utc(),production=native_identity(),source_hashes=source,
          compiled_units=['CplexBaseline','main'],linked_objects={str(p):sha(p) for p in objects},
          archive=old['archive'],compiler_SHA=sha(COMPILER),flags=flags,source_ABI_unchanged=True,
          exporter_PE=str(BUILD/'Round138Export.exe'),exporter_SHA=sha(BUILD/'Round138Export.exe'),
          scope='Default-off four shared stock RLT rows; all other GI-TBC settings unchanged'))

if __name__ == '__main__': main()
