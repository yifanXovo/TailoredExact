"""Standalone research appendix, exported only when timed producers are idle."""
import inspect,types
from round143_common import *
from round143_analyze import require_idle

def document_budget():
    value=budget();own=os.environ.get('ROUND140_METERED_PARENT_LABEL')
    value['unclosed']=[r for r in value['unclosed'] if not (r['label']==own and r['kind']=='document')]
    return value

def marker():
    require_idle();path=OUT/'PDF_marker.json';assert not path.exists(),'one successful artifact marker per authoring operation'
    script=Path('C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/pdf/26.1017.22136/skills/pdf/container_tools/mark_artifact_operation_started.mjs')
    node=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    r=subprocess.run([node,script,'--operation-kind','create','--expected-output-count','1','--output-format','pdf'],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=60)
    assert r.returncode==0,(r.stdout,r.stderr)
    write(path,dict(UTC=utc(),success=True,successful_invocations=1,stdout=r.stdout))

def assemble():
    require_idle();assert read(OUT/'PDF_marker.json')['success'] and read(OUT/'candidate_decision.json')['study_complete']
    math_note=(OUT/'mathematical_analysis.md').read_text(encoding='utf-8-sig')
    report=(OUT/'final_report.md').read_text(encoding='utf-8-sig')
    body=math_note+'\n\n# Matched LP and complete-method results\n\n'+report.split('\n',1)[1]
    body+='\nThe standard antecedents are [@CharnesCooper1962; @Yue2013; @ChenHooker2023].\n'
    (OUT/'manuscript.md').write_text(body,encoding='utf-8',newline='\n')
    bib='''@article{CharnesCooper1962,
  author={Charnes, Abraham and Cooper, William W.},
  title={Programming with linear fractional functionals},
  journal={Naval Research Logistics Quarterly}, year={1962}, volume={9},
  number={3-4}, pages={181--186}, doi={10.1002/nav.3800090303}}
@article{Yue2013,
  author={Yue, Dajun and Guill{\\'e}n-Gos{\\'a}lbez, Gonzalo and You, Fengqi},
  title={Global optimization of large-scale mixed-integer linear fractional programming problems: A reformulation-linearization method and process scheduling applications},
  journal={AIChE Journal}, year={2013}, volume={59}, pages={4255--4272}, doi={10.1002/aic.14185}}
@article{ChenHooker2023,
  author={Chen, Violet Xinying and Hooker, John N.},
  title={A guide to formulating fairness in an optimization model},
  journal={Annals of Operations Research}, year={2023}, volume={326},
  pages={581--619}, doi={10.1007/s10479-023-05264-y}}
'''
    (OUT/'references.bib').write_text(bib,encoding='utf-8',newline='\n')
    write(OUT/'document_assembly.json',dict(UTC=utc(),manuscript_SHA=sha(OUT/'manuscript.md'),references_SHA=sha(OUT/'references.bib'),
        formal_stable_manuscript_unchanged=True,Optimize=0,Native_load=0))

def pdf():
    require_idle()
    import round138_documents as old
    source=inspect.getsource(old.pdf).replace('date=29 October 2026','date=1 November 2026').replace(
        'Round138 standalone increment: manuscript.md assembled from mathematical_analysis.md and qualified reports/decision; references.bib and three scientific figures',
        'Round143 standalone reciprocal-normalization increment: exact integer extension, matched LPs, complete same-PE methods and qualified cost')
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,budget=document_budget,read=read,write=write,sha=sha,environment=environment)
    exec(compile(source,__file__+'::increment_export','exec'),ns);ns['pdf']()

def render():
    require_idle()
    import round138_pdf_qa as old
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,budget=document_budget,read=read,write=write,sha=sha,environment=environment)
    types.FunctionType(old.render.__code__,ns,'render',old.render.__defaults__,old.render.__closure__)()

if __name__=='__main__':
    if sys.argv[1]=='all':marker();assemble();pdf()
    else:globals()[sys.argv[1]]()
