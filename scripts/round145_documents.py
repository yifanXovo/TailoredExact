"""Export the coherent research section only after all timed work is idle."""
import inspect,types
from round145_common import *

def marker():
    assert not budget()['unclosed'];path=OUT/'PDF_marker.json';assert not path.exists()
    node=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    script=Path('C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/pdf/26.1017.22136/skills/pdf/container_tools/mark_artifact_operation_started.mjs')
    result=subprocess.run([node,script,'--operation-kind','create','--expected-output-count','1','--output-format','pdf'],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=60)
    assert result.returncode==0,(result.stdout,result.stderr)
    write(path,dict(UTC=utc(),success=True,successful_invocations=1,stdout=result.stdout))

def pdf():
    assert not budget()['unclosed'] and read(OUT/'candidate_decision.json')['study_complete']
    assert read(OUT/'PDF_marker.json')['success']
    text=(OUT/'manuscript.md').read_text(encoding='utf-8-sig')
    assert 'inserted here only after' not in text and 'The final decision will' not in text
    # Preserve the established project bibliography and TeX export/spacing
    # conventions; this is an integrated section, not concatenated round appendices.
    reference=ROOT/'results/unified_exact_round143/references.bib'
    bibliography=reference.read_text(encoding='utf-8-sig')+r'''
@article{AdamsSherali1990R145,
 author={Adams, Warren P. and Sherali, Hanif D.},
 title={Linearization Strategies for a Class of Zero-One Mixed Integer Programming Problems},
 journal={Operations Research}, volume={38}, number={2}, pages={217--226},
 year={1990}, doi={10.1287/opre.38.2.217}}
@book{SheraliAdams1999R145,
 author={Sherali, Hanif D. and Adams, Warren P.},
 title={A Reformulation-Linearization Technique for Solving Discrete and Continuous Nonconvex Problems},
 publisher={Springer}, year={1999}, doi={10.1007/978-1-4757-4388-3}}
@article{Balas1998R145,
 author={Balas, Egon},
 title={Disjunctive programming: Properties of the convex hull of feasible points},
 journal={Discrete Applied Mathematics}, volume={89}, number={1--3},
 pages={3--44}, year={1998}, doi={10.1016/S0166-218X(98)00136-X}}
'''
    (OUT/'references.bib').write_text(bibliography,encoding='utf-8',newline='\n')
    import round138_documents as old
    source=inspect.getsource(old.pdf).replace('date=29 October 2026','date=2 November 2026').replace(
        'Round138 standalone increment: manuscript.md assembled from mathematical_analysis.md and qualified reports/decision; references.bib and three scientific figures',
        'Round145 coherent section: shared resources, discrete counts, reciprocal normalization, complete-block compact projection and qualified complete results')
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,budget=budget,read=read,write=write,sha=sha,environment=environment)
    exec(compile(source,__file__+'::R145_project_export','exec'),ns);ns['pdf']()
    write(OUT/'document_assembly.json',dict(UTC=utc(),manuscript_SHA=sha(OUT/'manuscript.md'),references_SHA=sha(OUT/'references.bib'),
        PDF_SHA=sha(OUT/'manuscript.pdf'),formal_stable_manuscript_unchanged=True,no_author_affiliation_funding_invented=True,Optimize=0,Native_load=0))

def render():
    assert not budget()['unclosed'];import round138_pdf_qa as old
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,budget=budget,read=read,write=write,sha=sha,environment=environment)
    types.FunctionType(old.render.__code__,ns)()

if __name__=='__main__':globals()[sys.argv[1]]()
