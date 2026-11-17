"""R170 thin component exporter, retaining the working R169 typography/toolchain."""
from round170_common import *
import argparse, inspect, re
import round169_documents as previous

PAPER=ROOT/'results/unified_exact_round137'
TEMP=WORK/'temp/round170/pdf'
old=previous.old
COMPONENTS=old.COMPONENTS
for module in [previous,previous.r168,previous.r168.previous,old]:
    module.ROOT=ROOT;module.PAPER=PAPER;module.OUT=OUT;module.TEMP=TEMP;module.BASE=BASE

def checks(allow_pending_generated=False):
    value=old.source_checks(allow_pending_generated)
    value['errors']=[v for v in value['errors'] if not v.startswith('Main table numbering is not unique/in order:')]
    if value['main_tables']!=[str(i) for i in range(1,12)]:value['errors'].append('R170 main tables must be 1..11 in order')
    body=(PAPER/'paper_body.md').read_text(encoding='utf-8-sig')
    if '**Table 7.' in body.split('## 6. Conclusions',1)[-1]:value['errors'].append('Paid result table left in Conclusions')
    if '### 4.6 Paid objective diversification' not in body:value['errors'].append('Missing focused paid experimental integration')
    app=(PAPER/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig')
    tags=re.findall(r'^\*\*(?:Proposition|Lemma) (A\d+)\b',app,re.M)
    if len(tags)!=len(set(tags)):value['errors'].append('Duplicate appendix statement')
    value['appendix_statements']=tags
    return value

def typeset(raw,supplement=False):
    title,text=previous.typeset(raw,supplement)
    if not supplement:
        text=text.replace('**Table 7.','```{=latex}\n\\Needspace{18\\baselineskip}\n```\n\n**Table 7.',1)
        # Finish the last resource/weight figure before opening Conclusions.
        text=text.replace('## 6. Conclusions','\\clearpage\n\n## 6. Conclusions',1)
    elif '## S170' in text:
        at=text.index('## S170');head,tail=text[:at],text[at:]
        for marker in ['```{=latex}\n\\begin{landscape}\n```\n\n','```{=latex}\n\\end{landscape}\n```\n\n']:
            tail=tail.replace(marker,'')
        for number,lines in [(1,24),(2,24),(3,16),(4,16),(5,24)]:
            marker=f'**Table S170.{number}.'
            tail=tail.replace(marker,f'```{{=latex}}\n\\Needspace{{{lines}\\baselineskip}}\n```\n\n'+marker,1)
        text=head+tail
    return title,text

def assemble():
    source=inspect.getsource(previous.r168.assemble)
    source=source.replace('round168','round170').replace('Round168','Round170').replace('current_revision=168','current_revision=170').replace('current_round=168','current_round=170')
    ns=dict(vars(previous.r168),ROOT=ROOT,OUT=OUT,BASE=BASE,TEMP=TEMP,PAPER=PAPER,checks=checks,__file__=__file__)
    exec(compile(source,__file__+'::assemble','exec'),ns);ns['assemble']()

def inherit(fn,edits):
    source=inspect.getsource(fn)
    for before,after in edits:
        assert before in source,before;source=source.replace(before,after)
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,PAPER=PAPER,source_checks=checks,typeset_text=typeset,__file__=__file__)
    exec(compile(source,__file__+'::'+fn.__name__,'exec'),ns);return ns[fn.__name__]

def pdf():
    inherit(old.pdf,[
        ("typography_policy='round165-v3')","typography_policy='round170-v1',document_date=stamp,date_timezone='Asia/Shanghai',toolchain=versions,header_template_source_SHA256=sha(Path(__file__)),inherited_template_source_SHA256=sha(Path('scripts/round165_documents.py')))") ,
        ('scripts/round165_audit.py evidence','scripts/round170_results.py'),
        ('scripts/round165_documents.py','scripts/round170_documents.py'),
        ('current_round=165','current_round=170'),
        ('../unified_exact_round165/document_build.json','../unified_exact_round170/document_build.json')])()

def qa():
    source=inspect.getsource(previous.qa)
    source=source.replace("['Table 11.','S169','paid objective','matched multistart','Paquete']",
        "['Table 7.','S170','4.6 Paid','matched cold','fixed candidate','Paquete','Conclusions','difference interval','C169','A.10']")
    ns=dict(vars(previous),ROOT=ROOT,OUT=OUT,TEMP=TEMP,PAPER=PAPER,checks=checks,old=old,__file__=__file__)
    exec(compile(source,__file__+'::qa','exec'),ns);ns['qa']()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['assemble','pdf','qa']);globals()[parser.parse_args().action]()
