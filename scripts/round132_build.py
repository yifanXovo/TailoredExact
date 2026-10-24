"""Separate research PE: source generation is deterministic and default-off.

Only CplexBaseline and main are rebuilt; the other qualified complete E3
translation units and the original archive are linked without editing them.
"""
from round132_common import *
import round130_common as inherited

PE=BUILD/'Round132Research.exe'
EXPORT=BUILD/'Round132Export.exe'
FLAGS=['-std=c++17','-Wall','-Wextra','-Wpedantic','-DEXACT_EBRP_ENABLE_GUROBI=1',
       '-I'+str(ROOT/'include'),'-I'+str(ROOT/'scripts'),'-ID:/gurobi1302/win64/include']

def generated():
    frozen_identity();BUILD.mkdir(exist_ok=True,parents=True);paths={}
    text=(ROOT/'src/CplexBaseline.cpp').read_text(encoding='utf-8-sig')
    text='#include "Round132Expression.hpp"\n'+text
    needle='for (const CanonicalLinearRow& row : shared_interval_rows.rows) {'
    assert text.count(needle)==1
    text=text.replace(needle,'''if (ebrp::round132Expression()!="off" && !round128InclusiveRoot())
            throw std::runtime_error("Round132 only admits the legal S2R root");
        const auto r132_w=vars.bounds.find("W_SP");
        if(ebrp::round132SP() && r132_w==vars.bounds.end())
            throw std::runtime_error("W projection requested without active W");
        const auto r132_rows=ebrp::round132Rows(shared_interval_rows.rows,
            r132_w==vars.bounds.end()?0.:r132_w->second.first,
            r132_w==vars.bounds.end()?0.:r132_w->second.second);
        for (const CanonicalLinearRow& row : r132_rows) {''')
    needle='    out << "Bounds\\n";\n    for (const auto& kv : vars.bounds) {';assert text.count(needle)==1
    text=text.replace(needle,needle+'\n        if(ebrp::round132SP() && kv.first=="W_SP")continue;')
    # Other emitters are outside this finite research qualification scope.
    needle='    std::filesystem::create_directories(lp_path.parent_path());'
    assert text.count(needle)==3
    text=text.replace(needle,'''    if(ebrp::round132Expression()!="off" && !use_shared_interval_rows)
        throw std::runtime_error("Round132 requires the qualified shared canonical emitter");
'''+needle,1)
    paths['CplexBaseline']=BUILD/'CplexBaseline.cpp';paths['CplexBaseline'].write_text(text,encoding='utf-8')
    text=(ROOT/'src/main.cpp').read_text(encoding='utf-8-sig')
    needle='else if (arg == "--round127-mode")';assert text.count(needle)==1
    text='#include "Round132Expression.hpp"\n'+text.replace(needle,
        'else if (arg == "--round132-expression") ebrp::round132SetExpression(lowerAscii(requireValue(i, argc, argv)));\n        '+needle)
    paths['main']=BUILD/'main.cpp';paths['main'].write_text(text,encoding='utf-8')
    text=(ROOT/'scripts/round130_export.cpp').read_text(encoding='utf-8-sig')
    text='#include "Round132Expression.hpp"\n'+text
    needle='const std::string mode=argv[6];ebrp::round127().mode=mode;';assert text.count(needle)==1
    text=text.replace(needle,needle+'\n    if(argc==9 && std::string(argv[8])!="fallback")ebrp::round132SetExpression(argv[8]);')
    paths['export']=BUILD/'export.cpp';paths['export'].write_text(text,encoding='utf-8')
    return paths

def build():
    paths=generated();objects=[]
    for stem in ['CplexBaseline','main']:
        obj=BUILD/(stem+'.o');signature=dict(source=sha(paths[stem]),header=sha(ROOT/'scripts/Round132Expression.hpp'),flags=FLAGS)
        receipt=BUILD/(stem+'_binding.json')
        if not (obj.exists() and receipt.exists() and read(receipt)==signature):
            attempt=1+len(list((OUT/'fees').glob('C_build_'+stem+'_*')))
            assert metered(f'C_build_{stem}_{attempt:02d}','qualification',[COMPILER,*FLAGS,'-c',paths[stem],'-o',obj],timeout=600)==0
            write(receipt,signature)
        objects.append(obj)
    fixed=[WORK/'build-cache/round130'/(s+'.o') for s in ['IntervalRowFactory','PaperExternalGiniTree','GurobiBaseline']]
    archive=inherited.ARCHIVE;assert archive.is_file()
    system=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
    assert metered('C_link_PE_01','qualification',[COMPILER,objects[1],objects[0],*fixed,archive,*system,'-o',PE],timeout=120)==0
    assert metered('C_link_export_01','qualification',[COMPILER,*FLAGS,paths['export'],objects[0],*fixed,archive,'-o',EXPORT],timeout=120)==0
    write(OUT/'research_build.json',dict(UTC=utc(),PE=str(PE),PE_SHA=sha(PE),exporter=str(EXPORT),exporter_SHA=sha(EXPORT),
        DLL=str(DLL),DLL_SHA=sha(DLL),compiler_SHA=sha(COMPILER),archive_SHA=sha(archive),
        generated_sources={n:dict(path=str(p),SHA=sha(p)) for n,p in paths.items()},generator_SHA=sha(__file__),
        header_SHA=sha(ROOT/'scripts/Round132Expression.hpp'),fixed_objects={str(p):sha(p) for p in fixed},
        default='off',options=['off','geom','sp'],production_src_include_unchanged=True,D_uses_original_E3=True,
        algorithm_ABI_unchanged=True,qualification_pending=True))
    frozen_identity();print('RESEARCH_BUILD_CREATED; original E3 and all production source bytes preserved.')
if __name__=='__main__':build()
