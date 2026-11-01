"""Research appendix only. PDF compilation/rendering require idle timed work."""
import inspect,types
from round144_common import *
def require_idle():
    own=os.environ.get('ROUND140_METERED_PARENT_LABEL')
    assert not [r for r in budget()['unclosed'] if not (r['label']==own and r['kind']=='document')]
def document_budget():
    value=budget();own=os.environ.get('ROUND140_METERED_PARENT_LABEL');value['unclosed']=[r for r in value['unclosed'] if not (r['label']==own and r['kind']=='document')];return value
def marker():
    require_idle();path=OUT/'PDF_marker.json';assert not path.exists()
    script=Path('C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/pdf/26.1017.22136/skills/pdf/container_tools/mark_artifact_operation_started.mjs')
    node=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    r=subprocess.run([node,script,'--operation-kind','create','--expected-output-count','1','--output-format','pdf'],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=60)
    assert r.returncode==0,(r.stdout,r.stderr);write(path,dict(UTC=utc(),success=True,successful_invocations=1,stdout=r.stdout))
def assemble():
    require_idle();assert read(OUT/'PDF_marker.json')['success'] and read(OUT/'candidate_decision.json')['study_complete']
    body=(OUT/'mathematical_analysis.md').read_text(encoding='utf-8-sig')
    title,content=body.split('\n',1);body=title+'\n\n# Mathematical foundation and source contract\n'+content
    report=(OUT/'final_report.md').read_text(encoding='utf-8-sig');body+='\n\n# Matched LP and complete-method evidence\n\n'+report.split('\n',1)[1]
    body+='\nThe linear-fractional and Gini antecedents remain standard [@CharnesCooper1962; @Yue2013; @ChenHooker2023].\n'
    (OUT/'manuscript.md').write_text(body,encoding='utf-8',newline='\n')
    # Reuse the established bibliographic authority without inventing literature.
    reference=ROOT/'results/unified_exact_round143/references.bib'
    (OUT/'references.bib').write_bytes(reference.read_bytes())
    write(OUT/'document_assembly.json',dict(UTC=utc(),manuscript_SHA=sha(OUT/'manuscript.md'),references_SHA=sha(OUT/'references.bib'),formal_stable_manuscript_unchanged=True,Optimize=0,Native_load=0))
def pdf():
    require_idle();import round138_documents as old
    source=inspect.getsource(old.pdf).replace('date=29 October 2026','date=1 November 2026').replace(
        'Round138 standalone increment: manuscript.md assembled from mathematical_analysis.md and qualified reports/decision; references.bib and three scientific figures',
        'Round144 RN original-variable projection increment: exact box transport, matched LP retention, complete same-PE outcomes and full cost')
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,budget=document_budget,read=read,write=write,sha=sha,environment=environment)
    exec(compile(source,__file__+'::increment_export','exec'),ns);ns['pdf']()
def render():
    require_idle();import round138_pdf_qa as old
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,budget=document_budget,read=read,write=write,sha=sha,environment=environment)
    types.FunctionType(old.render.__code__,ns,'render',old.render.__defaults__,old.render.__closure__)()
if __name__=='__main__':
    if sys.argv[1]=='all':marker();assemble();pdf()
    else:globals()[sys.argv[1]]()
