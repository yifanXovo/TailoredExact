"""R169 thin exporter: current components, inherited typography, isolated identity."""
from round169_common import *
import argparse, inspect, re, types
import round168_documents as r168
old=r168.old
PAPER=ROOT/'results/unified_exact_round137'
TEMP=WORK/'temp/round169/pdf'
COMPONENTS=old.COMPONENTS
for module in [r168,r168.previous,old]:
    module.ROOT=ROOT;module.PAPER=PAPER;module.OUT=OUT;module.TEMP=TEMP;module.BASE=BASE

def checks(allow_pending_generated=False):
    r=old.source_checks(allow_pending_generated)
    r['errors']=[e for e in r['errors'] if not e.startswith('Main table numbering is not unique/in order:')]
    if r['main_tables']!=[str(i) for i in range(1,12)]:r['errors'].append('R169 main tables must be 1..11: '+str(r['main_tables']))
    app=(PAPER/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig')
    tags=re.findall(r'^\*\*(?:Proposition|Lemma) (A\d+)\b',app,re.M)
    if len(tags)!=len(set(tags)):r['errors'].append('Duplicate appendix statement')
    r['appendix_statements']=tags
    return r

def typeset(raw,supplement=False):
    title,text=r168.typeset(raw,supplement)
    if not supplement:
        text=text.replace('**Table 11.','```{=latex}\n\\Needspace{10\\baselineskip}\n```\n\n**Table 11.',1)
    elif '## S169' in text:
        at=text.index('## S169');head,tail=text[:at],text[at:]
        # The new compact tables fit portrait. Keep captions with the tables,
        # instead of inheriting old wide-table landscape page boundaries.
        for marker in ['```{=latex}\n\\begin{landscape}\n```\n\n','```{=latex}\n\\end{landscape}\n```\n\n']:
            tail=tail.replace(marker,'')
        for number,lines in [(1,14),(2,14),(3,28),(4,28)]:
            marker=f'**Table S169.{number}.'
            tail=tail.replace(marker,f'```{{=latex}}\n\\Needspace{{{lines}\\baselineskip}}\n```\n\n'+marker,1)
        text=head+tail
    return title,text.replace('/blob/codex/round168-route-family/','/blob/codex/round169-primal-reweight/')

def assemble():
    source=inspect.getsource(r168.assemble).replace('round168','round169').replace('Round168','Round169').replace('current_revision=168','current_revision=169').replace('current_round=168','current_round=169')
    ns=dict(vars(r168),ROOT=ROOT,OUT=OUT,BASE=BASE,TEMP=TEMP,PAPER=PAPER,checks=checks,__file__=__file__)
    exec(compile(source,__file__+'::assemble','exec'),ns);ns['assemble']()

def inherit(fn,edits):
    source=inspect.getsource(fn)
    for before,after in edits:
        assert before in source,before;source=source.replace(before,after)
    ns=dict(vars(old),ROOT=ROOT,OUT=OUT,TEMP=TEMP,PAPER=PAPER,source_checks=checks,typeset_text=typeset,__file__=__file__)
    exec(compile(source,__file__+'::'+fn.__name__,'exec'),ns);return ns[fn.__name__]

def pdf():
    inherit(old.pdf,[
        ("typography_policy='round165-v3')","typography_policy='round169-v1',document_date=stamp,date_timezone='Asia/Shanghai',toolchain=versions,header_template_source_SHA256=sha(Path(__file__)),inherited_template_source_SHA256=sha(Path('scripts/round165_documents.py')))") ,
        ('scripts/round165_audit.py evidence','scripts/round169_analysis.py'),
        ('scripts/round165_documents.py','scripts/round169_documents.py'),
        ('current_round=165','current_round=169'),
        ('../unified_exact_round165/document_build.json','../unified_exact_round169/document_build.json')])()

def qa():
    import pdfplumber
    from PIL import Image,ImageDraw,ImageOps
    documents=[]
    for output in read(OUT/'document_build.json')['outputs']:
        p=ROOT/output['path'];assert sha(p)==output['SHA256']
        folder=TEMP/('QA_'+p.stem+'_'+sha(p)[:12]);folder.mkdir(parents=True,exist_ok=True)
        pages=[]
        with pdfplumber.open(p) as doc:
            for n,page in enumerate(doc.pages,1):
                text=page.extract_text() or '';(folder/f'text-{n:03}.txt').write_text(text,encoding='utf-8')
                outside=[dict(text=c.get('text'),x0=c['x0'],x1=c['x1'],top=c['top'],bottom=c['bottom']) for c in page.chars if c['x0']<-.5 or c['x1']>page.width+.5 or c['top']<-.5 or c['bottom']>page.height+.5]
                topics=[k for k in ['Table 11.','S169','paid objective','matched multistart','Paquete'] if k in text]
                pages.append(dict(page=n,characters=len(page.chars),outside_page=outside,replacements=text.count('\ufffd'),topics=topics))
        expected=['0.2822618761','0.2822620892','0.2105292995','0.2105295021','0.1112611656','0.3725317852','0.0600858983','0.3813035291']
        all_text='\n'.join(q.read_text(encoding='utf-8') for q in folder.glob('text-*.txt'))
        assert all(v in all_text for v in expected),('lost inherited outward-rounded resource values',p)
        selected={1}
        for page in pages:
            if page['topics']:selected.update(range(max(1,page['page']-1),min(len(pages),page['page']+1)+1))
        images=[]
        for n in sorted(selected):
            target=folder/f'page-{n:03}.png'
            if not target.exists():old.run([old.POPPLER/'pdftoppm.exe','-f',str(n),'-l',str(n),'-singlefile','-r','110','-png',p,target.with_suffix('')],timeout=60)
            images.append(target)
        contacts=[]
        for start in range(0,len(images),6):
            sheet=Image.new('RGB',(1800,2400),'#dedede');draw=ImageDraw.Draw(sheet)
            for j,f in enumerate(images[start:start+6]):
                with Image.open(f) as im:thumb=ImageOps.contain(im.convert('RGB'),(880,750))
                x=(j%2)*900+(900-thumb.width)//2;y=(j//2)*800+25;sheet.paste(thumb,(x,y));draw.text(((j%2)*900+10,(j//2)*800+7),f'{p.stem}: {f.stem}',fill='black')
            f=folder/f'contact-{start//6+1:02}.png';sheet.save(f);contacts.append(str(f))
        documents.append(dict(path=output['path'],SHA256=sha(p),page_count=len(pages),pages=pages,rendered_pages=sorted(selected),
            render_root=str(folder),contact_sheets=contacts,outside_page_characters=sum(len(x['outside_page']) for x in pages),
            replacement_characters=sum(x['replacements'] for x in pages),blank_pages=[x['page'] for x in pages if x['characters']<20],
            actual_visual_inspection_complete=False))
    write(OUT/'document_qa.json',dict(UTC=utc(),status='TARGETED_RENDER_PENDING_VISUAL',documents=documents,source_checks=checks(),Optimize=0))
    print(json.dumps([{k:v for k,v in d.items() if k not in ['pages']} for d in documents],indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assemble','pdf','qa']);globals()[p.parse_args().action]()
