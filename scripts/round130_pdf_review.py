"""Render only changed reading-draft regions; actual inspection remains separate."""
from pathlib import Path
import hashlib, json, re, subprocess, unicodedata
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/unified_exact_round130'
TEMP = Path('E:/codes/ExactEBRP-work/temp/round130')
POPPLER = Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pdf = OUT/'manuscript.pdf'
    reader = PdfReader(pdf)
    texts = [' '.join(unicodedata.normalize('NFKC', page.extract_text() or '').replace('\u00ad', '').split()) for page in reader.pages]
    # The table of contents also contains headings. Pick the last occurrence
    # before the next body region, rather than rendering every shifted old page.
    def locate(needle, after=0):
        candidates = [i for i, text in enumerate(texts) if i >= after and needle in text]
        assert candidates, (needle, after)
        return candidates[-1]
    intro = locate('1. Introduction')
    related = locate('2. Related work', intro)
    method = locate('4. Formulations', related)
    history = locate('6. Versioned certification', method)
    r128 = locate('6.8 Inclusive-root control', history)
    r129 = locate('6.9 Prospective confirmation', history)
    r130 = locate('6.10 Fixed-version same-start', r129)
    extended = locate('7. Extended endpoint', r130)
    discussion = locate('8. Discussion, limitations', extended)
    references = locate('References and supporting material', discussion)
    appendix_a = locate('Appendix A. Complete model', references)
    appendix_b = locate('Appendix B. Executable method', appendix_a)
    b2 = locate('B.2 State, identity and order', appendix_b)
    b13 = locate('B.13 Uniform support candidate', b2)
    b14 = locate('B.14 Current pair-support', b2)
    ranges = dict(
        front_and_introduction=[0, related],
        current_method_and_historical_gateway=[method, history],
        historical_R128_qualifiers_R129_scope_and_R130_attribution=[r128, extended],
        discussion_and_conclusion=[discussion, references],
        appendix_A_version_banner=[appendix_a, min(appendix_a+1, appendix_b-1)],
        appendix_B_version_entry_and_command=[appendix_b, b2],
        appendix_B_R129_chronology_and_current_control_note=[b13, b14])
    selected = sorted({page for first, last in ranges.values() for page in range(first, last+1)})
    complete = '\n'.join(texts)
    for needle in ['uniform pair-support', 'S2R', 'PS', '147.147', '151.415',
                   'B.14 Current pair-support', 'Fixed-version same-start']:
        assert needle in complete, needle
    folder = TEMP/'pdf_review'
    attempt = 1
    while folder.exists():
        attempt += 1
        folder = TEMP/f'pdf_review{attempt:02d}'
    folder.mkdir(parents=True, exist_ok=False)
    rows = []
    for page in selected:
        prefix = folder/f'page{page+1:03d}'
        command = [str(POPPLER), '-f', str(page+1), '-l', str(page+1), '-r', '115',
                   '-png', '-singlefile', str(pdf), str(prefix)]
        subprocess.run(command, check=True, capture_output=True, timeout=60)
        image = prefix.with_suffix('.png')
        rows.append(dict(page=page+1, path=str(image), SHA=digest(image)))
    value = dict(status='RENDERED_PENDING_ACTUAL_VISUAL_INSPECTION', PDF=str(pdf), PDF_SHA=digest(pdf),
        pages=len(reader.pages), changed_region_ranges={k: [a+1, b+1] for k, (a,b) in ranges.items()},
        rendered_images=rows, retained_historical_pages_not_all_rerendered=True,
        scope='Changed version, method, R129 chronology, R130 tables and interpretation, discussion/conclusion, appendix version entries and B.14; actual visual inspection not yet asserted')
    manifest=OUT/'review/pdf_render_manifest.json'
    if manifest.exists():
        number=1
        while manifest.with_name(f'pdf_render_manifest.prior{number:02d}.json').exists():number+=1
        manifest.with_name(f'pdf_render_manifest.prior{number:02d}.json').write_bytes(manifest.read_bytes())
    manifest.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(pages=len(reader.pages), rendered_pages=[r['page'] for r in rows], PDF_SHA=value['PDF_SHA'])))


if __name__ == '__main__':
    main()
