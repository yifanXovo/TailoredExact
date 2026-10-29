"""Render the final increment for actual page-by-page visual inspection."""
from round138_common import *
import re

def render():
    assert not budget()['unclosed']
    pdf=OUT/'manuscript.pdf';assert read(OUT/'pdf_export.json')['exported']
    dest=OUT/'qa_pages';dest.mkdir(exist_ok=False)
    tool=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
    tick=time.perf_counter()
    r=subprocess.run([tool,'-r','120','-png',pdf,dest/'page'],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=240)
    assert r.returncode==0,(r.stdout,r.stderr)
    info=subprocess.run([tool.parent/'pdfinfo.exe',pdf],cwd=ROOT,env=environment(),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
    assert info.returncode==0,info.stderr
    count=int(re.search(r'(?m)^Pages:\s+(\d+)',info.stdout)[1])
    from pypdf import PdfReader
    texts=[page.extract_text() or '' for page in PdfReader(pdf).pages]
    pages=sorted(dest.glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]));assert len(pages)==len(texts)==count>0
    facts=[]
    for j,(text,path) in enumerate(zip(texts,pages),1):
        assert text.strip(),('empty PDF text page',j)
        facts.append(dict(page=j,preview=path.relative_to(ROOT).as_posix(),PNG_SHA=sha(path),
            text_characters=len(text)))
    write(OUT/'pdf_render_manifest.json',dict(UTC=utc(),PDF_SHA=sha(pdf),pages=facts,
        seconds=time.perf_counter()-tick,DPI=120,renderer=str(tool),pdfinfo=info.stdout,
        actual_visual_review_pending=True,Optimize=0,vendor_DLL_loads=0))
    print(json.dumps(dict(pages=len(pages),seconds=time.perf_counter()-tick,visual_review_pending=True)))

if __name__=='__main__':globals()[sys.argv[1]]()
