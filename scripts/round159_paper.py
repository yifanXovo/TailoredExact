"""Serial paper compile/render, separate from scientific calls and budget."""
import re,shutil
from round159_common import *

def render():
    configure();assert not budget()['unclosed']
    tick=time.perf_counter();target=WORK/'temp/round159/paper-001';target.mkdir(parents=True,exist_ok=False)
    for name in ('manuscript.tex','empirical_results.tex','decision_and_cost.tex'):shutil.copyfile(OUT/name,target/name)
    engine=Path('C:/Users/Administrator/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe')
    calls=[]
    for no in (1,2):
        p=subprocess.run([str(engine),'-interaction=nonstopmode','-halt-on-error','-output-directory='+str(target),str(target/'manuscript.tex')],cwd=target,capture_output=True,timeout=180)
        (target/f'pass{no}.stdout.txt').write_bytes(p.stdout);(target/f'pass{no}.stderr.txt').write_bytes(p.stderr)
        calls.append(dict(pass_number=no,returncode=p.returncode));assert p.returncode==0,p.stdout[-3000:]
    pdf=OUT/'manuscript.pdf';assert not pdf.exists();shutil.copyfile(target/'manuscript.pdf',pdf)
    qa=OUT/'paper_qa';qa.mkdir(exist_ok=True)
    info=subprocess.run(['pdfinfo',str(pdf)],capture_output=True,text=True,check=True).stdout;pages=int(re.search(r'(?m)^Pages:\s+(\d+)',info)[1])
    p=subprocess.run(['pdftoppm','-r','110','-png',str(pdf),str(qa/'page')],capture_output=True,timeout=180);assert p.returncode==0,p.stderr
    text=subprocess.run(['pdftotext','-layout',str(pdf),'-'],capture_output=True,check=True).stdout;(qa/'extracted_text.txt').write_bytes(text)
    images=sorted(qa.glob('page-*.png'));assert len(images)==pages
    log=(target/'manuscript.log').read_text(errors='replace')
    assert 'Undefined control sequence' not in log and 'LaTeX Error' not in log
    record=dict(UTC=utc(),render_PASS=True,visual_review_complete=False,pages=pages,calls=calls,PDF_SHA=sha(pdf),engine=str(engine),engine_SHA=sha(engine),
        source_SHA={n:sha(OUT/n) for n in ('manuscript.tex','empirical_results.tex','decision_and_cost.tex')},
        page_images=[dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p)) for p in images],
        overfull_boxes=re.findall(r'Overfull[^\n]*',log),pure_writing_compile_render_seconds=time.perf_counter()-tick,
        not_G1=True,marker='Successfully executed once immediately before first R159 TeX authoring command')
    write(qa/'render_receipt.json',record);print(json.dumps(record))

if __name__=='__main__':render()
