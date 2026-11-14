"""Round166 component-only assembly/export, explicitly inheriting R165 typography.

No legacy R137 generator, solver import, source mutation or historical rebuild.
The PDF cache identity additionally binds China date, actual toolchain and templates.
"""
from round166_common import *
import inspect,re,argparse
import round165_documents as old
PAPER=ROOT/'results/unified_exact_round137'
TEMP=WORK/'temp/round166/pdf'
old.ROOT=ROOT;old.PAPER=PAPER;old.OUT=OUT;old.TEMP=TEMP;old.BASE=BASE
_checks=old.source_checks
_typeset=old.typeset_text
COMPONENTS=old.COMPONENTS
def checks(allow_pending_generated=False):
    value=_checks(allow_pending_generated)
    tables=value['main_tables']
    good=tables==[str(i) for i in range(1,len(tables)+1)] and len(tables) in [15,16]
    if good:value['errors']=[e for e in value['errors'] if not e.startswith('Main table numbering is not unique/in order:')]
    else:value['errors'].append('Round166 requires unique ordered main tables1..15/16')
    app=(PAPER/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig')
    statements=re.findall(r'^\*\*(?:Proposition|Lemma) (A\d+)\b',app,re.M)
    if len(statements)!=len(set(statements)):value['errors'].append('Duplicate appendix proposition/lemma number')
    value['appendix_statement_numbers']=statements
    return value
def typeset(raw,supplement=False):
    # The inherited generic seven-significant-digit display must not round
    # an already outward-rounded lower endpoint upward or an upper downward.
    protected={};lines=[];safe_table=False
    for line in raw.splitlines():
        if not line.startswith('|'):safe_table=False
        elif any(header in line for header in ['Improvement interval','Worst absolute regret bound','Max archive regret upper','Safe improvement lower']):safe_table=True
        if safe_table:
            def keep(match):
                token='R166BOUNDNUMBER'+str(len(protected))+'TOKEN'
                protected[token]=match[0];return token
            line=re.sub(r'(?<![\w.])[-+]?\d+\.\d{7,}(?:[eE][-+]?\d+)?',keep,line)
        lines.append(line)
    title,text=_typeset('\n'.join(lines)+'\n',supplement)
    for token,number in protected.items():text=text.replace(token,number)
    if supplement:
        opening='```{=latex}\n\\begin{landscape}\n```\n\n'
        for marker in ['## Round166 compact representation and certified decisions',
            '### All twelve complete endpoints and costs',
            'The next table is explanatory accounting inside those same paid clocks.',
            'The first continuous canonical LP below is distinct from the first Native']:
            if marker in text:
                start=text.index(marker);begin=text.index(opening,start)
                assert begin-start<5000,('landscape introduction must remain local',marker)
                text=text[:start]+opening+text[start:begin]+text[begin+len(opening):]
    else:
        def reserve(lines):return '\n```{=latex}\n\\Needspace{'+str(lines)+'\\baselineskip}\n```\n\n'
        for marker,amount in [('**Table 5.',18),('**Table 6, panel (b).',14),('**Table 16.',20)]:
            if marker in text:text=text.replace(marker,reserve(amount)+marker,1)
    return title,text.replace('/blob/codex/round165-current-manuscript/','/blob/codex/round166-structure-and-paper/')
def assemble():
    start=time.perf_counter();report=checks(True);write(OUT/'source_checks.json',report)
    assert not report['errors'],report['errors']
    body=(PAPER/'paper_body.md').read_text(encoding='utf-8-sig')
    app=(PAPER/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig')
    (PAPER/'manuscript.md').write_text(body.rstrip()+'\n\n\\clearpage\n\n'+app.rstrip()+'\n',encoding='utf-8')
    figures={}
    for name in COMPONENTS[:-1]:
        raw=(PAPER/name).read_text(encoding='utf-8-sig')
        for target in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',raw):
            if target.startswith(('http:','https:')):continue
            p=(PAPER/target).resolve();assert p.exists(),p
            figures[p.relative_to(ROOT).as_posix()]=bind(p)
    source=read(OUT/'source_manifest.json')
    source.update(UTC=utc(),schema='round166-science-and-current-paper-v1',document_base_commit=BASE,
        authoritative_directory='results/unified_exact_round137',components=[bind(PAPER/n) for n in COMPONENTS],
        figures=list(figures.values()),assembled_manuscript=bind(PAPER/'manuscript.md'),
        generator=bind(Path(__file__)),inherited_typography=bind(ROOT/'scripts/round165_documents.py'),
        offline_analysis_generator=bind(ROOT/'scripts/round166_analysis.py'),
        document_goal_actual_input_path='C:/Users/Administrator/Downloads/TailoredExact_Round166_Complete_Goal.md',
        method_and_model_source_used=False)
    write(OUT/'source_manifest.json',source)
    write(PAPER/'document_assembly.json',dict(UTC=utc(),current_round=166,authority='component-only; no historical prose generation',
        components=COMPONENTS,manuscript_SHA=sha(PAPER/'manuscript.md'),bibliography_SHA=sha(PAPER/'references.bib'),
        complete_appendices=True,source_manifest='../unified_exact_round166/source_manifest.json',seconds=time.perf_counter()-start))
    lineage=read(PAPER/'document_lineage.json');lineage.update(current_revision=166,last_assembly_UTC=utc(),
        results_not_yet_assembled=False,current_assembled_manuscript_SHA=sha(PAPER/'manuscript.md'),
        current_maintained_components={n:sha(PAPER/n) for n in COMPONENTS},
        author_facts_destination='../unified_exact_round166/author_decision_memo.md')
    write(PAPER/'document_lineage.json',lineage)
    print('Current Round166 main/complete appendices assembled; source checks PASS.')
def inherited_function(fn,source_edits=()):
    source=inspect.getsource(fn)
    for before,after in source_edits:
        assert before in source,before;source=source.replace(before,after)
    namespace=dict(vars(old),source_checks=checks,typeset_text=typeset,__file__=str(Path(__file__).resolve()))
    exec(compile(source,__file__+'::R165_inherited_'+fn.__name__,'exec'),namespace)
    return namespace[fn.__name__]
def compile_exporter():
    edits=[("typography_policy='round165-v3')", "typography_policy='round166-v1',document_date=stamp,date_timezone='Asia/Shanghai',toolchain=versions,header_template_source_SHA256=sha(Path(__file__)),inherited_template_source_SHA256=sha(Path('scripts/round165_documents.py')))") ,
        ('scripts/round165_audit.py evidence','scripts/round166_analysis.py'),
        ('scripts/round165_documents.py','scripts/round166_documents.py'),
        ("commands=['python scripts/round166_analysis.py',", "commands=['python scripts/round166_analysis.py','python scripts/round166_figures.py',"),
        ('method_and_model_source_used=False,new_Optimize=0,production_compile=0,','method_and_model_source_used=False,new_Optimize=0,production_compile=0,operation_scope="document-only",'),
        ('current_round=165','current_round=166'),
        ('../unified_exact_round165/document_build.json','../unified_exact_round166/document_build.json')]
    return inherited_function(old.pdf,edits)
def pdf():
    compile_exporter()()
def qa():
    inherited_function(old.qa,[("topics=['Abstract'","topics=['C166','A.9','A.10','continuous-weight','Table 16.','Abstract'"),
        ('new_Optimize=0,','new_Optimize=0,operation_scope="document-QA-only",')])()
    report=read(OUT/'document_qa.json')
    expected=['0.2822618761','0.2822620892','0.2105292995','0.2105295021',
        '0.1112611656','0.3725317852','0.0600858983','0.3813035291']
    for document in report['documents']:
        text='\n'.join(p.read_text(encoding='utf-8') for p in sorted(Path(document['render_root']).glob('text-*.txt')))
        missing=[number for number in expected if number not in text]
        assert not missing,('PDF lost outward-rounded resource numbers',document['path'],missing)
        document['outward_bound_decimal_readback']=dict(PASS=True,values=expected)
    write(OUT/'document_qa.json',report)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['assemble','pdf','qa']);args=parser.parse_args()
    globals()[args.action]()
