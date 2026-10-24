from pathlib import Path
import json,hashlib,subprocess,time
from PIL import Image,ImageOps,ImageDraw
from pypdf import PdfReader
root=Path.cwd();out=root/'results/unified_exact_round132';pdf=out/'manuscript.pdf';target=Path('E:/codes/ExactEBRP-work/temp/round132/pdf/render04');target.mkdir(parents=True,exist_ok=False)
start=time.perf_counter();poppler='C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe'
subprocess.run([poppler,'-png','-r','110',str(pdf),str(target/'page')],check=True,timeout=600)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
reader=PdfReader(str(pdf));texts=[p.extract_text() or '' for p in reader.pages];pages=sorted(target.glob('page-*.png'));assert len(pages)==len(reader.pages)
rows=[dict(page=i+1,path=str(p.resolve()),SHA256=sha(p),bytes=p.stat().st_size,dimensions=Image.open(p).size,text_characters=len(texts[i])) for i,p in enumerate(pages)]
sheets=[]
for j in range(0,len(pages),2):
 group=pages[j:j+2];ims=[Image.open(p).convert('RGB') for p in group];w=sum(im.width for im in ims);h=max(im.height for im in ims)+34
 sheet=Image.new('RGB',(w,h),'#d8d8d8');draw=ImageDraw.Draw(sheet);x=0
 for k,im in enumerate(ims):draw.text((x+8,8),f'PDF page {j+k+1}',fill='black');sheet.paste(im,(x,34));x+=im.width
 p=target/f'sheet-{j+1:02d}-{min(j+2,len(pages)):02d}.png';sheet.save(p)
 sheets.append(dict(pages=list(range(j+1,min(j+2,len(pages))+1)),path=str(p.resolve()),SHA256=sha(p),bytes=p.stat().st_size))
r=dict(PDF=str(pdf.resolve()),PDF_SHA=sha(pdf),page_count=len(pages),dpi=110,pages=rows,sheets=sheets,seconds=time.perf_counter()-start,visual_inspection_pending=True,no_source_or_PDF_changed=True)
(target/'render_inventory.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');(target/'page_texts.json').write_text(json.dumps(texts,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(pages=len(pages),sheets=len(sheets),seconds=r['seconds'],inventory=str(target/'render_inventory.json'))))

fonts={}
for page in reader.pages:
 resources=page.get('/Resources').get_object();fontdict=resources.get('/Font',{})
 if hasattr(fontdict,'get_object'):fontdict=fontdict.get_object()
 for ref in fontdict.values():
  font=ref.get_object();name=str(font.get('/BaseFont','unknown'));actual=font
  if '/DescendantFonts' in font:actual=font['/DescendantFonts'][0].get_object()
  descriptor=actual.get('/FontDescriptor');descriptor=descriptor.get_object() if descriptor else {}
  fonts[name]=dict(subtype=str(font.get('/Subtype')),embedded=any(k in descriptor for k in ['/FontFile','/FontFile2','/FontFile3']))
checks=dict(PDF_SHA=sha(pdf),pages=len(reader.pages),encrypted=reader.is_encrypted,all_pages_have_text=all(len(t)>30 for t in texts),replacement_glyph_present=any('\ufffd' in t for t in texts),fonts=fonts,all_fonts_embedded=all(f['embedded'] for f in fonts.values()),standalone_font_files_published=False,visual_QA_separate=True)
assert checks['all_pages_have_text'] and checks['all_fonts_embedded'] and not checks['encrypted']
(out/'review/pdf_document_checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
