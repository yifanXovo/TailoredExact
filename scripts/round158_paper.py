"""Serial final LaTeX/PDF rendering; visual page inspection remains explicit."""
import re,shutil
from round158_common import *
from round158_delivery import serial_idle

def render(attempt='paper-001'):
    serial_idle();assert Path(attempt).name==attempt and attempt not in ('.','..')
    assert (OUT/'empirical_results.tex').is_file(),'actual checked empirical insertion is required'
    tick=time.perf_counter();target=WORK/'temp/round158'/attempt;target.mkdir(parents=True,exist_ok=False)
    for name in ('manuscript.tex','empirical_results.tex'):shutil.copyfile(OUT/name,target/name)
    engine=Path('C:/Users/Administrator/AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe');assert engine.is_file()
    calls=[]
    for no in (1,2):
        p=subprocess.run([str(engine),'-interaction=nonstopmode','-halt-on-error',
            '-output-directory='+str(target),str(target/'manuscript.tex')],cwd=target,capture_output=True,timeout=180)
        (target/f'pass{no}.stdout.txt').write_bytes(p.stdout);(target/f'pass{no}.stderr.txt').write_bytes(p.stderr)
        calls.append(dict(pass_number=no,returncode=p.returncode));assert p.returncode==0,p.stdout[-3000:]
    pdf=OUT/'manuscript.pdf'
    if pdf.exists():shutil.copyfile(pdf,target/'previous_manuscript.pdf')
    shutil.copyfile(target/'manuscript.pdf',pdf);qa=OUT/'paper_qa';qa.mkdir(exist_ok=True)
    info=subprocess.run(['pdfinfo',str(pdf)],capture_output=True,text=True,check=True).stdout
    pages=int(re.search(r'(?m)^Pages:\s+(\d+)',info)[1])
    process=subprocess.run(['pdftoppm','-r','110','-png',str(pdf),str(qa/'page')],capture_output=True,timeout=180)
    assert process.returncode==0,process.stderr
    text=subprocess.run(['pdftotext','-layout',str(pdf),'-'],capture_output=True,check=True).stdout
    (qa/'extracted_text.txt').write_bytes(text)
    images=[qa/f'page-{no:0{len(str(pages))}d}.png' for no in range(1,pages+1)]
    assert all(p.is_file() for p in images)
    log=(target/'manuscript.log').read_text(encoding='utf-8',errors='replace')
    assert 'Undefined control sequence' not in log and 'LaTeX Error' not in log
    record=dict(UTC=utc(),render_PASS=True,visual_review_complete=False,pages=pages,calls=calls,
        source_SHA={n:sha(OUT/n) for n in ('manuscript.tex','empirical_results.tex')},PDF_SHA=sha(pdf),
        engine=str(engine),engine_SHA=sha(engine),
        page_images=[dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p)) for p in images],
        log_path=str(target/'manuscript.log'),overfull_boxes=re.findall(r'Overfull[^\n]*',log),
        pure_writing_compile_render_seconds=time.perf_counter()-tick,not_G1=True,
        required_operation_marker='Successfully run exactly once immediately before first TeX authoring; do not repeat')
    write(qa/'render_receipt.json',record);print(json.dumps(record),flush=True)

if __name__=='__main__':render(*sys.argv[1:])
