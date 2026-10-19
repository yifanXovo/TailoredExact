"""Render all manuscript pages and compact contact sheets for actual human/agent review."""
from pathlib import Path
import hashlib,json,subprocess,sys,time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round126'
ASSETS=Path('E:/codes/ExactEBRP-work/temp/round126/pdf_review')
PIL_PYTHON='C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'

def compose(folder):
    from PIL import Image,ImageOps,ImageDraw
    folder=Path(folder)
    pages=sorted(folder.glob('page-*.png'))
    for i in range(0,len(pages),4):
        canvas=Image.new('RGB',(1420,2080),'#dedede');draw=ImageDraw.Draw(canvas)
        for j,p in enumerate(pages[i:i+4]):
            im=Image.open(p).convert('RGB');im.thumbnail((680,990))
            x=15+(j%2)*710+(680-im.width)//2;y=35+(j//2)*1040
            canvas.paste(im,(x,y));draw.text((x,y-22),p.stem,fill='black')
        canvas.save(folder/f'contact_{i//4+1:02d}.jpg',quality=90)

def render():
    start=time.perf_counter();pdf=OUT/'manuscript.pdf'
    digest=hashlib.sha256(pdf.read_bytes()).hexdigest()
    folder=ASSETS/digest[:12];folder.mkdir(parents=True,exist_ok=False)
    for cmd in [
        ['pdfinfo',str(pdf)],
        ['pdftotext','-layout',str(pdf),str(folder/'reading.txt')],
        ['pdftoppm','-scale-to','1400','-png',str(pdf),str(folder/'page')]]:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=480)
        assert p.returncode==0,(cmd,p.stdout,p.stderr)
        if cmd[0]=='pdfinfo':(folder/'pdfinfo.txt').write_text(p.stdout,encoding='utf-8')
    p=subprocess.run([PIL_PYTHON,'-B',__file__,'--compose',str(folder)],capture_output=True,text=True,timeout=180)
    assert p.returncode==0,(p.stdout,p.stderr)
    pages=(folder/'reading.txt').read_text(encoding='utf-8').split('\f')
    inventory=[]
    for i,page in enumerate(pages,1):
        if not page.strip():continue
        tokens=[t for t in ['Algorithm 1','Algorithm 2','Table SC1','Table SC2','Table SC3','Table SC4','Table SC5','Appendix A.','Appendix B.','References','(A35)'] if t in page]
        inventory.append(dict(page=i,characters=len(page.strip()),tokens=tokens))
    receipt=dict(PDF=str(pdf),PDF_SHA256=digest,render_root=str(folder),pages=len(inventory),page_inventory=inventory,
        rendered_PNGs=len(list(folder.glob('page-*.png'))),contact_sheets=len(list(folder.glob('contact_*.jpg'))),
        seconds=time.perf_counter()-start,visual_review_pending=True)
    (OUT/'review/pdf_page_inventory.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='page_inventory'}))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--compose':compose(sys.argv[2])
    else:render()
