from pathlib import Path
import hashlib,json,re,subprocess,sys
from pypdf import PdfReader

root=Path('E:/codes/ExactEBRP-work/worktrees/round131')
out=root/'results/unified_exact_round131'
temp=Path('E:/codes/ExactEBRP-work/temp/round131')
pdf=out/'manuscript.pdf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
reader=PdfReader(pdf)
texts=[p.extract_text() or '' for p in reader.pages]
if sys.argv[1]=='locate':
    markers=['Abstract','The paper has three contributions','6.11 Primary','6.12 Absolute','6.13 Finite','Table R131.A','Table R131.B','Table R131.C','8. Discussion','9. Conclusion','Table R131.S','S.131 Final-version']
    pages=[]
    for n,(p,t) in enumerate(zip(reader.pages,texts),1):
        found=[s for s in markers if s in t]
        pages.append(dict(page=n,width=float(p.mediabox.width),height=float(p.mediabox.height),markers=found,first=t[:250],text=t))
    write(temp/'pdf_page_map.json',dict(PDF_SHA=sha(pdf),pages=pages))
    sys.path.insert(0,str(root/'scripts'))
    from round127_release import BAD
    alltext='\n'.join(texts).encode('utf-8')
    hits=[i for i,pattern in enumerate(BAD) if re.search(pattern,alltext)]
    assert not hits,('credential patterns in actual PDF text',hits)
    assert all('�' not in t for t in texts)
    write(out/'review/pdf_text_scan.json',dict(status='PASS',PDF_SHA=sha(pdf),pages=len(texts),extracted_text_bytes=len(alltext),credential_patterns_checked=len(BAD),actual_extracted_text_scanned=True,not_a_visual_layout_check=True))
    print(json.dumps(dict(PDF_SHA=sha(pdf),pages=len(texts),markers=[{k:p[k] for k in ['page','markers','first']} for p in pages if p['markers']],tail_pages=[{k:p[k] for k in ['page','first']} for p in pages[-7:]]),ensure_ascii=True))
elif sys.argv[1]=='render':
    numbers=[int(x) for x in sys.argv[2:]]
    renders=temp/('pdf_render_'+sha(pdf)[:8]);renders.mkdir(exist_ok=True)
    poppler=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
    pages=[]
    for n in numbers:
        prefix=renders/f'page{n:03d}'
        subprocess.run([str(poppler),'-f',str(n),'-l',str(n),'-singlefile','-scale-to','1700','-png',str(pdf),str(prefix)],check=True,timeout=60,capture_output=True)
        path=prefix.with_suffix('.png')
        pages.append(dict(page=n,path=str(path),SHA256=sha(path)))
    write(out/'review/pdf_render_manifest.json',dict(PDF_SHA=sha(pdf),pages=pages,scope='selected actual affected pages; no claim of inspecting every unchanged historical page'))
    print(json.dumps(dict(rendered=len(pages),pages=numbers)))
