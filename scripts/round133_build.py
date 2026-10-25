"""Independent Round133 binaries; reuse immutable objects without ABI changes."""
from round133_common import *
from round130_common import ARCHIVE

FLAGS=['-std=c++17','-Wall','-Wextra','-Wpedantic','-DEXACT_EBRP_ENABLE_GUROBI=1',
       '-I'+str(ROOT/'include'),'-I'+str(ROOT/'scripts'),'-ID:/gurobi1302/win64/include']
SYSTEM=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32',
        '-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
STEMS=['NativeEvidenceJournal','ControllingLeafScheduler','GurobiBaseline','PaperExternalGiniTree','IntervalRowFactory','CplexBaseline']
FROZEN=WORK/'build-cache/round130'
OLDRESEARCH=WORK/'build-cache/round132'

def research_source():
    """Exactly the R132 expression transformation on the corrected emitter."""
    source=(ROOT/'src/CplexBaseline.cpp').read_text(encoding='utf-8-sig')
    source='#include "Round132Expression.hpp"\n'+source
    needle='for (const CanonicalLinearRow& row : shared_interval_rows.rows) {'
    assert source.count(needle)==1
    source=source.replace(needle,'''if (ebrp::round132Expression()!="off" && !round128InclusiveRoot())
            throw std::runtime_error("Round132 only admits the legal S2R root");
        const auto r132_w=vars.bounds.find("W_SP");
        if(ebrp::round132SP() && r132_w==vars.bounds.end())
            throw std::runtime_error("W projection requested without active W");
        const auto r132_rows=ebrp::round132Rows(shared_interval_rows.rows,
            r132_w==vars.bounds.end()?0.:r132_w->second.first,
            r132_w==vars.bounds.end()?0.:r132_w->second.second);
        for (const CanonicalLinearRow& row : r132_rows) {''')
    needle='    out << "Bounds\\n";\n    for (const auto& kv : vars.bounds) {'
    assert source.count(needle)==1
    source=source.replace(needle,needle+'\n        if(ebrp::round132SP() && kv.first=="W_SP")continue;')
    needle='    std::filesystem::create_directories(lp_path.parent_path());'
    assert source.count(needle)==3
    source=source.replace(needle,'''    if(ebrp::round132Expression()!="off" && !use_shared_interval_rows)
        throw std::runtime_error("Round132 requires the qualified shared canonical emitter");
'''+needle,1)
    target=BUILD/'CplexBaselineResearch.cpp';target.write_text(source,encoding='utf-8')
    return target

def compile_candidates():
    BUILD.mkdir(parents=True,exist_ok=True)
    assert sha(COMPILER)=='8cd0aa578687e4182532222c8734439b3f34ac78b6ce23cba1071c5838025fc1'
    assert sha(ARCHIVE)=='f2f7608894793b60794b91fa204c7d5e8a7ce13078e6115be32ca645804c9acd'
    headers={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'include').rglob('*.hpp')}
    generated=research_source()
    for stem in STEMS+['CplexBaselineResearch']:
        source=generated if stem=='CplexBaselineResearch' else ROOT/'src'/f'{stem}.cpp'
        obj=BUILD/f'{stem}.o';binding=BUILD/f'{stem}_binding.json'
        signature=dict(source_SHA=sha(source),headers=headers,compiler_SHA=sha(COMPILER),flags=FLAGS,
            includes={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'src').glob('Round*Gurobi*.inc')})
        if obj.exists() and binding.exists() and read(binding)==signature:continue
        attempt=len(list((OUT/'fees').glob(f'build_{stem}_*')))+1
        assert metered(f'build_{stem}_{attempt:02}','D',[COMPILER,*FLAGS,'-c',source,'-o',obj],
                       reservation=600,timeout=600)==0
        write(binding,signature)
    replaced=[BUILD/f'{stem}.o' for stem in STEMS if stem!='CplexBaseline']
    fixed=[]
    binaries={}
    for name,main,compact,target in [
        ('production',FROZEN/'main.o',BUILD/'CplexBaseline.o',E3),
        ('research',OLDRESEARCH/'main.o',BUILD/'CplexBaselineResearch.o',RESEARCH)]:
        args=[COMPILER,main,compact,*fixed,*replaced,ARCHIVE,*SYSTEM,'-o',target]
        link_binding=BUILD/f'link_{name}_binding.json'
        signature={str(p):sha(p) for p in [main,compact,*fixed,*replaced,ARCHIVE]}
        if not (target.exists() and link_binding.exists() and read(link_binding)==signature):
            attempt=len(list((OUT/'fees').glob(f'link_{name}_*')))+1
            label=f'link_{name}_{attempt:02}'
            assert metered(label,'D',args,reservation=120,timeout=120)==0
            write(link_binding,signature)
        binaries[name]=dict(**native_identity(target),main_object=dict(path=str(main),SHA=sha(main)),
            compact_object=dict(path=str(compact),SHA=sha(compact)),link_command=list(map(str,args)))
    write(OUT/'candidate_build.json',dict(UTC=utc(),base=BASE,binaries=binaries,
        source_bindings={str(p.relative_to(ROOT)):sha(p) for p in
            [*[ROOT/'src'/f'{s}.cpp' for s in STEMS],*(ROOT/'src').glob('Round*Gurobi*.inc')]},
        header_bindings=headers,replaced_complete_translation_units=STEMS,
        generated_research_source=dict(path=str(generated),SHA=sha(generated),
            expression_header_SHA=sha(ROOT/'scripts/Round132Expression.hpp'),
            recipe='same R132 transformation; current inclusive-cutoff emitter'),
        reused_archive=dict(path=str(ARCHIVE),SHA=sha(ARCHIVE)),
        reused_objects={str(p):sha(p) for p in fixed},compiler_SHA=sha(COMPILER),flags=FLAGS,
        SolveOptions_Result_FixedIntervalOutcome_ABI_unchanged=True,
        numerical_policy='R133 declared defaults; requested Seed/Presolve match; local qualification; source revocation; qualified-open physical gap',
        physical_problem_H_support_leaf_policy_unchanged=True,
        model_change='Remove artificial 0<=-1 no-improver marker from shared and fallback inclusive-cutoff emitters; retain legal penalty floor',
        qualification='PENDING'))

def tests():
    replaced=[BUILD/f'{stem}.o' for stem in STEMS]
    selected=sys.argv[2:] or ['native_evidence_journal_tests','round133_terminal_tests','round133_inclusive_cutoff_tests','round27_paper_scheduling_tests']
    for stem in selected:
        exe=BUILD/f'{stem}.exe'
        args=[COMPILER,*FLAGS,ROOT/'tests'/f'{stem}.cpp',*replaced,
            ARCHIVE,*SYSTEM,'-o',exe]
        attempt=len(list((OUT/'fees').glob(f'test_build_{stem}_*')))+1
        assert metered(f'test_build_{stem}_{attempt:02}','D',args,reservation=120,timeout=120)==0
        assert metered(f'test_run_{stem}_{attempt:02}','D',[exe],reservation=60,timeout=60,cwd=BUILD)==0

if __name__=='__main__':
    {'build':compile_candidates,'tests':tests}[sys.argv[1]]()
