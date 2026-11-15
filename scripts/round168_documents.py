"""Round168 thin component exporter; inherited R166 typography, isolated R168 identities."""
from round168_common import *
import inspect,re,argparse
import round166_documents as previous
old=previous.old
PAPER=ROOT/'results/unified_exact_round137'
TEMP=WORK/'temp/round168/pdf'
for module in [previous,old]:
    module.ROOT=ROOT;module.PAPER=PAPER;module.OUT=OUT;module.TEMP=TEMP;module.BASE=BASE
COMPONENTS=old.COMPONENTS
def checks(allow_pending_generated=False):
    result=old.source_checks(allow_pending_generated)
    result['errors']=[e for e in result['errors'] if not e.startswith('Main table numbering is not unique/in order:')]
    tables=result['main_tables']
    if tables!=[str(i) for i in range(1,11)]:result['errors'].append('Round168 requires unique ordered main tables1..10: '+str(tables))
    app=(PAPER/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig')
    tags=re.findall(r'^\*\*(?:Proposition|Lemma) (A\d+)\b',app,re.M)
    if len(tags)!=len(set(tags)):result['errors'].append('Duplicate appendix statement number')
    if '## A.11' not in app:result['errors'].append('Missing conditional representation proof')
    result['appendix_statements']=tags
    return result
def typeset(raw,supplement=False):
    title,text=previous.typeset(raw,supplement)
    if supplement:
        marker='## S167.3 Conditional representation diagnostics'
        opening='```{=latex}\n\\begin{landscape}\n```\n\n'
        if marker in text:
            start=text.index(marker);at=text.index(opening,start)
            text=text[:start]+opening+text[start:at]+text[at+len(opening):]
        # The six-column R168 table fits portrait. Do not inherit the generic
        # all-supplement-table landscape rule, which orphans its caption.
        marker='## S168 Complete route-family target attainability'
        if marker in text:
            at=text.index(marker);tail=text[at:]
            closing='```{=latex}\n\\end{landscape}\n```\n\n'
            assert opening in tail and closing in tail
            tail=tail.replace(opening,'',1).replace(closing,'',1)
            tail=tail.replace('**Table S168.','```{=latex}\n\\Needspace{20\\baselineskip}\n```\n\n**Table S168.',1)
            text=text[:at]+'\\clearpage\n\n'+tail
    return title,text.replace('/blob/codex/round166-structure-and-paper/','/blob/codex/round168-route-family/')
def assemble():
    start=time.perf_counter();report=checks(True);write(OUT/'source_checks.json',report);assert not report['errors'],report['errors']
    body=(PAPER/'paper_body.md').read_text(encoding='utf-8-sig');app=(PAPER/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig')
    (PAPER/'manuscript.md').write_bytes((body.rstrip()+'\n\n\\clearpage\n\n'+app.rstrip()+'\n').encode('utf-8'))
    figures={}
    for name in COMPONENTS[:-1]:
        for target in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',(PAPER/name).read_text(encoding='utf-8-sig')):
            if target.startswith(('https:','http:')):continue
            p=(PAPER/target).resolve();assert p.is_file(),p;figures[str(p)]=bind(p)
    source=read(OUT/'source_manifest.json');source.update(UTC=utc(),schema='round168-current-components-and-diagnostic-v1',
        authoritative_directory='results/unified_exact_round137',document_base_commit=BASE,
        components=[bind(PAPER/n) for n in COMPONENTS],figures=list(figures.values()),
        assembled_manuscript=bind(PAPER/'manuscript.md'),generator=bind(Path(__file__)),
        inherited_exporter=bind(ROOT/'scripts/round166_documents.py'),inherited_typography=bind(ROOT/'scripts/round165_documents.py'),
        no_legacy_R137_generation=True,no_parameter_resource_recomputation=True)
    write(OUT/'source_manifest.json',source)
    write(PAPER/'document_assembly.json',dict(UTC=utc(),current_round=168,authority='current component-only assembly',components=COMPONENTS,
        manuscript_SHA=sha(PAPER/'manuscript.md'),bibliography_SHA=sha(PAPER/'references.bib'),complete_appendices=True,
        source_manifest='../unified_exact_round168/source_manifest.json',seconds=time.perf_counter()-start))
    lineage=read(PAPER/'document_lineage.json');lineage.update(current_revision=168,last_assembly_UTC=utc(),results_not_yet_assembled=False,
        current_assembled_manuscript_SHA=sha(PAPER/'manuscript.md'),current_maintained_components={n:sha(PAPER/n) for n in COMPONENTS},
        author_facts_destination='../unified_exact_round168/author_decision_memo.md')
    write(PAPER/'document_lineage.json',lineage)
    counts=read(OUT/'manuscript_word_counts.json') if (OUT/'manuscript_word_counts.json').exists() else dict(before_whitespace_words=9003,no_compression_target=True)
    counts.update(after_whitespace_words=len(body.split()),sections=[dict(heading=s.splitlines()[0],words=len(s.split())) for s in re.split(r'(?=^## )',body,flags=re.M)])
    write(OUT/'manuscript_word_counts.json',counts)
    print('Assembled current Round168 components:',len(body.split()),'body words.')
def inherited(fn,edits=()):
    source=inspect.getsource(fn)
    for before,after in edits:assert before in source,before;source=source.replace(before,after)
    namespace=dict(vars(old),source_checks=checks,typeset_text=typeset,__file__=str(Path(__file__).resolve()))
    exec(compile(source,__file__+'::inherited_'+fn.__name__,'exec'),namespace)
    return namespace[fn.__name__]
def pdf():
    inherited(old.pdf,[
        ("typography_policy='round165-v3')","typography_policy='round168-v1',document_date=stamp,date_timezone='Asia/Shanghai',toolchain=versions,header_template_source_SHA256=sha(Path(__file__)),inherited_template_source_SHA256=sha(Path('scripts/round165_documents.py')))") ,
        ('scripts/round165_audit.py evidence','scripts/round168_diagnostics.py summarize'),
        ('scripts/round165_documents.py','scripts/round168_documents.py'),
        ('current_round=165','current_round=168'),
        ('../unified_exact_round165/document_build.json','../unified_exact_round168/document_build.json')])()
def qa():
    inherited(old.qa,[("topics=['Abstract'","topics=['route-family','S168','Fixed-route','conditional','A.11','Table 6.','Table 8.','Table 10.','continuous-weight','Abstract'")])()
    report=read(OUT/'document_qa.json')
    expected=['0.2822618761','0.2822620892','0.2105292995','0.2105295021','0.1112611656','0.3725317852','0.0600858983','0.3813035291']
    for doc in report['documents']:
        text='\n'.join(p.read_text(encoding='utf-8') for p in Path(doc['render_root']).glob('text-*.txt'))
        assert all(v in text for v in expected),('lost outward-rounded resource values',doc['path'])
        doc['resource_decimal_readback']=dict(PASS=True,values=expected)
    write(OUT/'document_qa.json',report)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assemble','pdf','qa']);args=p.parse_args();globals()[args.action]()
