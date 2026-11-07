"""Serial LaTeX/PDF rendering with actual artifacts; visual review is separate."""
import re,shutil
from round157_common import *
from round157_delivery import serial_idle

def render():
    serial_idle();tick=time.perf_counter()
    target=WORK/'temp/round157/paper';target.mkdir(parents=True,exist_ok=False)
    tex=OUT/'manuscript.tex';engine=Path('C:/Users/Administrator/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe')
    assert engine.is_file();calls=[]
    for number in (1,2):
        p=subprocess.run([str(engine),'-interaction=nonstopmode','-halt-on-error',
                          '-output-directory='+str(target),str(tex)],cwd=ROOT,capture_output=True,timeout=180)
        (target/f'pass{number}.stdout.txt').write_bytes(p.stdout);(target/f'pass{number}.stderr.txt').write_bytes(p.stderr)
        calls.append(dict(pass_number=number,returncode=p.returncode));assert p.returncode==0,p.stdout[-3000:]
    pdf=OUT/'manuscript.pdf';assert not pdf.exists();shutil.copyfile(target/'manuscript.pdf',pdf)
    qa=OUT/'paper_qa';qa.mkdir(exist_ok=False)
    meta=subprocess.run(['pdfinfo',str(pdf)],capture_output=True,text=True,check=True).stdout
    pages=int(re.search(r'(?m)^Pages:\s+(\d+)',meta)[1])
    p=subprocess.run(['pdftoppm','-r','110','-png',str(pdf),str(qa/'page')],capture_output=True,timeout=180)
    assert p.returncode==0,p.stderr
    text=subprocess.run(['pdftotext','-layout',str(pdf),'-'],capture_output=True,check=True).stdout
    (qa/'extracted_text.txt').write_bytes(text)
    images=sorted(qa.glob('page-*.png'));assert len(images)==pages
    log=(target/'manuscript.log').read_text(encoding='utf-8',errors='replace')
    assert 'Undefined control sequence' not in log and 'LaTeX Error' not in log
    record=dict(UTC=utc(),render_PASS=True,visual_review_complete=False,pages=pages,calls=calls,
        source_SHA=sha(tex),PDF_SHA=sha(pdf),engine=str(engine),engine_SHA=sha(engine),
        page_images=[dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p)) for p in images],
        log_path=str(target/'manuscript.log'),overfull_boxes=re.findall(r'Overfull[^\n]*',log),
        pure_writing_compile_render_seconds=time.perf_counter()-tick,not_G1=True,
        required_operation_marker='already executed exactly once before initial TeX authoring; not repeated')
    write(qa/'render_receipt.json',record);print(json.dumps(record),flush=True)

if __name__=='__main__':render()
