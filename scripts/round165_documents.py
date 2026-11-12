"""Current component-only paper build and bounded PDF QA. No solver imports.

python scripts/round165_documents.py assemble
python scripts/round165_documents.py pdf
python scripts/round165_documents.py qa
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse, hashlib, json, os, re, shutil, subprocess, sys, time

ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'results/unified_exact_round137'
OUT=ROOT/'results/unified_exact_round165'
TEMP=Path(os.environ.get('ROUND165_DOCUMENT_TEMP','E:/codes/ExactEBRP-work/temp/round165/pdf'))
BASE='de01e8fb27a954d031abac5fe99442d6c8d29d44'
COMPONENTS=['paper_body.md','model_and_algorithm_appendices.md','mathematical_analysis.md','supplement.md','references.bib']
POPPLER=Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin')

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def binding(p):
    p=Path(p);return dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,SHA256=sha(p))
def run(command,cwd=ROOT,timeout=180):
    try:
        return subprocess.check_output([str(x) for x in command],cwd=cwd,timeout=timeout,stderr=subprocess.STDOUT).decode('utf-8',errors='replace')
    except subprocess.CalledProcessError as error:
        output=error.output.decode('utf-8',errors='replace')
        folder=TEMP/'failures';folder.mkdir(parents=True,exist_ok=True)
        log=folder/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.log')
        log.write_text(output,encoding='utf-8')
        raise RuntimeError(f'{command[0]} failed; retained {log}:\n'+output[-2500:]) from error
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),*['| '+' | '.join(str(v) for v in row)+' |' for row in rows]])+'\n'

def source_checks(allow_pending_generated=False):
    errors=[];warnings=[];links=[]
    bib=(PAPER/'references.bib').read_text(encoding='utf-8-sig')
    defined=set(re.findall(r'@\w+\{([^,]+),',bib))
    for name in COMPONENTS[:-1]:
        text=(PAPER/name).read_text(encoding='utf-8-sig')
        for key in set(re.findall(r'(?<![A-Za-z0-9])@([A-Za-z][\w.-]*)',text)):
            if key not in defined: errors.append(f'{name}: undefined citation {key}')
        for token in [r'\bTODO\b',r'\bNaN\b',r'@@\w+@@',r'paper_body.md#71-one-next-research-question',r'single Round163 next question']:
            if re.search(token,text,re.I): errors.append(f'{name}: forbidden unresolved marker {token}')
        for label,target in re.findall(r'\[([^\]]*)\]\(([^)\s]+)\)',text):
            if target.startswith(('https://','http://','mailto:','#')): continue
            target=target.split('#')[0]
            if not target: continue
            p=(PAPER/target).resolve()
            exists=p.exists()
            if not exists:
                try:
                    rel=p.relative_to(ROOT).as_posix()
                    subprocess.check_output(['git','cat-file','-e',BASE+':'+rel],cwd=ROOT,stderr=subprocess.DEVNULL)
                    exists=True
                except (ValueError,subprocess.CalledProcessError): pass
            links.append(dict(source=name,target=target,exists_in_worktree_or_fixed_source=exists))
            pending=allow_pending_generated and p in [OUT/'source_manifest.json',OUT/'document_build.json']
            if not exists and not pending: errors.append(f'{name}: missing local link {target}')
    body=(PAPER/'paper_body.md').read_text(encoding='utf-8-sig')
    tables=re.findall(r'^\*\*Table (\d+)\.',body,re.M)
    if tables!=[str(n) for n in range(1,16)]: errors.append('Main table numbering is not unique/in order: '+str(tables))
    app=(PAPER/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig')
    tags=re.findall(r'\\tag\{([^}]+)\}',app)
    if len(tags)!=len(set(tags)):errors.append('Duplicate appendix equation tag')
    for section in ['B.'+str(i) for i in range(12)]:
        if not re.search(r'^## '+re.escape(section)+r'(?: |$)',app,re.M):errors.append('Missing complete appendix '+section)
    if 'Algorithm 2  ProcessLeaf / ChooseAction' not in app or 'Algorithm 3  FinalizeAndUpdateCover' not in app: errors.append('Missing leaf/cover algorithm')
    return dict(UTC=utc(),errors=errors,warnings=warnings,local_links=links,defined_citations=sorted(defined),main_tables=tables,appendix_equation_tags=tags)

def assemble():
    start=time.perf_counter()
    checks=source_checks(allow_pending_generated=True);write(OUT/'source_checks.json',checks)
    assert not checks['errors'],checks['errors']
    body=(PAPER/'paper_body.md').read_text(encoding='utf-8-sig')
    app=(PAPER/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig')
    manuscript=body.rstrip()+'\n\n\\clearpage\n\n'+app.rstrip()+'\n'
    (PAPER/'manuscript.md').write_text(manuscript,encoding='utf-8')
    components=[binding(PAPER/n) for n in COMPONENTS]
    figures=[binding(p) for p in sorted((PAPER/'figures').glob('*.png')) if p.name in ['resource_endpoints.png','three_seed_endpoints.png']]
    figures.append(binding(ROOT/'results/unified_exact_round135/figures/count_bound_scope.png'))
    source=dict(UTC=utc(),schema='round165-current-paper-v1',document_base_commit=BASE,
        goal_input=binding(OUT/'goal.md'),goal_actual_input_path='C:/Users/Administrator/Downloads/TailoredExact_Round165_Complete_Goal.md',
        authoritative_directory='results/unified_exact_round137',components=components,figures=figures,
        assembled_manuscript=binding(PAPER/'manuscript.md'),
        historical_non_input='method_and_model_source.md (historical old-generator input; excluded)',
        generator=binding(Path(__file__)),offline_data_generator=binding(ROOT/'scripts/round165_audit.py'),
        R137_experiments=dict(source='results/unified_exact_round137/candidate_manifest.json',source_capsule='results/unified_exact_round137/source_publication.json',role='historical breadth/resource/weight/AM/mechanisms; 120 positions; not generated in R165'),
        later_measured_CPP='e920b92e199e825ec89a2932f701861ff158e0d4',
        later_measured_PE_SHA256='fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93',
        Gurobi_13_0_2_DLL_SHA256='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88',
        historical_line_pointer_commit='355eefd2be3fe5651195681faf7b3a63ee4032f8',
        historical_E3_attribution_commit='7564a5415331b380e24d1ec06936dcfd56557e67',
        R163_delivery='8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb',
        R164_numeric_commit='b93a8a01ff1b7f3cbee67807be3ac6591db4767f',
        R164_science_carrier_commit='a29a70d132ecc17e18bc48a660225a6380722f45',
        R164_delivery=BASE,new_Optimize=0,production_rebuild=0,main_defaults_changed=False,
        evidence_inputs=[binding(ROOT/'results'/n) for n in [
            'unified_exact_round137/reports/summary.json','unified_exact_round137/reports/arms.json','unified_exact_round137/reports/operations.json',
            'unified_exact_round163/reports/complete_arms.json','unified_exact_round163/reports/summary.json',
            'unified_exact_round164/reports/complete_arms.json','unified_exact_round164/reports/three_seed_comparisons.json','unified_exact_round164/reports/primal_target_arrival.json']])
    write(OUT/'source_manifest.json',source)
    write(PAPER/'document_assembly.json',dict(UTC=utc(),current_round=165,
        authority='component-only assembly; no legacy prepare/assemble call',
        component_paths=COMPONENTS,manuscript_SHA=sha(PAPER/'manuscript.md'),
        bibliography_SHA=sha(PAPER/'references.bib'),complete_appendices=True,
        source_manifest='../unified_exact_round165/source_manifest.json',seconds=time.perf_counter()-start))
    lineage=read(PAPER/'document_lineage.json')
    lineage.update(current_revision=165,last_assembly_UTC=utc(),results_not_yet_assembled=False,
        current_assembled_manuscript_SHA=sha(PAPER/'manuscript.md'),
        current_maintained_components={n:sha(PAPER/n) for n in COMPONENTS},
        method_source_role='Historical, excluded from current build',
        pending_author_facts_preserved_in_supplement_and_review_packet=False,
        author_facts_destination='../unified_exact_round165/author_decision_memo.md')
    write(PAPER/'document_lineage.json',lineage)
    print('Assembled current main + complete Appendix A/B; source checks PASS.')

def typeset_text(raw,supplement=False):
    title=raw.splitlines()[0].lstrip('# ')
    text='\n'.join(raw.splitlines()[1:])+'\n\n\\clearpage\n\n# References\n\n::: {#refs}\n:::\n'
    text=text.replace('ᶜ',r'\(\mathcal C\)').replace('∎',r'\(\square\)')
    for dash in ['\u2010','\u2011','\u2012','\u2013','\u2014','\u2015']:text=text.replace(dash,'-')
    symbols={'−':'-','≤':r'\le ','≥':r'\ge ','ℓ':r'\ell ','η':r'\eta ','μ':r'\mu ','β':r'\beta ','α':r'\alpha ','Δ':r'\Delta ','∈':r'\in '}
    def math_symbols(m):
        s=m[0]
        for a,b in symbols.items():s=s.replace(a,b)
        return s
    text=re.sub(r'\\\(.*?\\\)|\\\[.*?\\\]',math_symbols,text,flags=re.S)
    # Fix display precision only; all machine sources and maintained numbers stay intact.
    lines=[]
    for line in text.splitlines():
        if line.startswith('|'):
            line=re.sub(r'(?<![\w.])[-+]?\d+\.\d{7,}(?:[eE][-+]?\d+)?',lambda m:format(float(m[0]),'.7g'),line)
        lines.append(line)
    text='\n'.join(lines)+'\n'
    if not supplement:
        text=text.replace('## Abstract','\\clearpage\n\n## Abstract',1)
    # PDF links go to the review branch; source Markdown keeps checked local links.
    def link(m):
        target=m[2]
        if target.startswith(('https://','http://','mailto:','#')):return m[0]
        path,_,frag=target.partition('#')
        p=(PAPER/path).resolve()
        try:rel=p.relative_to(ROOT).as_posix()
        except ValueError:return m[0]
        return '['+m[1]+'](https://github.com/yifanXovo/TailoredExact/blob/codex/round165-current-manuscript/'+rel+('#'+frag if frag else '')+')'
    text=re.sub(r'(?<!!)\[([^\]]*)\]\(([^)\s]+)\)',link,text)
    if supplement:
        # Keep adjacent headings inside landscape flow; otherwise the heading
        # alone would be left on an almost empty portrait page.
        pattern=r'((?:(?:^#{2,6} [^\n]+|^\*\*[^\n]*\*\*)\n\n)+)?(^\|[^\n]*(?:\n\|[^\n]*)*)'
        def supplement_table(m):
            rows=m[2].splitlines();columns=rows[0].count('|')-1
            if columns>5 and len(rows)>=8:
                return '\n```{=latex}\n\\begin{landscape}\n```\n\n'+(m[1] or '')+m[2]+'\n\n```{=latex}\n\\end{landscape}\n```\n'
            if len(rows)<=18:
                reserve=min(520,50+22*len(rows))
                return '\n```{=latex}\n\\Needspace{'+str(reserve)+'pt}\n```\n\n'+m[0]
            return m[0]
        text=re.sub(pattern,supplement_table,text,flags=re.M)
        # Two explanatory blocks belong with their adjacent landscape table,
        # rather than on isolated near-empty portrait pages.
        boundary='\n\n```{=latex}\n\\end{landscape}\n```\n'
        text=re.sub(re.escape(boundary)+r'\n*(Every adverse direction is retained\..*?)(?=\n\n)',lambda m:'\n\n'+m[1]+boundary,text,flags=re.S)
        heading='## All pre-frozen feasible-target availability intervals'
        if heading in text:
            start=text.index(heading);opening='```{=latex}\n\\begin{landscape}\n```\n\n'
            table_start=text.index(opening,start)
            prefix=text[start:table_start]
            text=text[:start]+opening+prefix+text[table_start+len(opening):]
    text=re.sub(r'^\*\*Table[^\n]*\*\*$',lambda m:'\n```{=latex}\n\\Needspace{'+('20' if m[0].startswith('**Table 1.') else '8')+'\\baselineskip}\n```\n\n'+m[0],text,flags=re.M)
    text=re.sub(r'^(\*\*(?:Proposition|Lemma)[^\n]*)$',lambda m:'\n```{=latex}\n\\Needspace{8\\baselineskip}\n```\n\n'+m[0],text,flags=re.M)
    text=re.sub(r'(^~~~text\nAlgorithm [123][^\n]*\n.*?^~~~)',lambda m:'```{=latex}\n\\par\\medskip\\noindent\\begin{minipage}{\\linewidth}\n```\n\n'+m[1]+'\n\n```{=latex}\n\\end{minipage}\\par\\medskip\n```',text,flags=re.M|re.S)
    return title,text

def pdf():
    checks=source_checks(allow_pending_generated=True);assert not checks['errors'],checks['errors']
    manifest=read(OUT/'source_manifest.json')
    assert all(sha(ROOT/r['path'])==r['SHA256'] for r in manifest['components']), 'Reassemble changed sources first'
    TEMP.mkdir(parents=True,exist_ok=True)
    os.environ.update(TEMP=str(TEMP),TMP=str(TEMP),PYTHONDONTWRITEBYTECODE='1')
    number=1
    while (TEMP/f'attempt{number:02d}').exists():number+=1
    attempt=TEMP/f'attempt{number:02d}';attempt.mkdir()
    tick=time.perf_counter()
    document_date=datetime.now(timezone(timedelta(hours=8)))
    stamp=f"{document_date.day} {'January February March April May June July August September October November December'.split()[document_date.month-1]} {document_date.year}"
    versions={name:run([name,'--version']).strip() for name in ['pandoc','xelatex']}
    versions.update(Python=sys.version,Python_executable=sys.executable)
    outputs=[]
    for stem in ['manuscript','supplement']:
        folder=attempt/stem;folder.mkdir()
        title,text=typeset_text((PAPER/(stem+'.md')).read_text(encoding='utf-8-sig'),stem=='supplement')
        render_identity=dict(reading_SHA256=hashlib.sha256(text.encode('utf-8')).hexdigest(),bibliography=sha(PAPER/'references.bib'),figures=manifest['figures'],typography_policy='round165-v3')
        # An already successful identical export need not be typeset again.
        previous=[p for p in sorted(TEMP.glob('attempt*/'+stem),reverse=True) if p!=folder and (p/'render_identity.json').exists() and (p/'xelatex_pass3.log').exists() and (p/'reading.pdf').exists() and read(p/'render_identity.json')==render_identity]
        if previous:
            old=previous[0];destination=PAPER/(stem+'.pdf');retained=PAPER/(stem+'_export.tex')
            shutil.copyfile(old/'reading.pdf',destination);shutil.copyfile(old/'reading.tex',retained)
            log=(old/'xelatex_pass3.log').read_text(encoding='utf-8')
            warnings=[l for l in (old/'pandoc.log').read_text(encoding='utf-8').splitlines()+log.splitlines() if any(k in l for k in ['Overfull','Missing character','undefined','Warning'])]
            outputs.append(dict(**binding(destination),source=binding(PAPER/(stem+'.md')),intermediate_TeX=binding(retained),reused_identical_successful_export=str(old),passes='three prior successful passes, identical reading.md',warnings=warnings,log_root=str(old)))
            continue
        source=folder/'reading.md';source.write_text(text,encoding='utf-8')
        write(folder/'render_identity.json',render_identity)
        header=folder/'header.tex'
        header.write_text(r'''
\usepackage{pdflscape}
\usepackage{etoolbox}
\usepackage{needspace}
\lstset{basicstyle=\ttfamily\footnotesize,breaklines=true,breakatwhitespace=false,
  columns=fullflexible,keepspaces=true,showstringspaces=false}
\AtBeginEnvironment{longtable}{\footnotesize}
\AtBeginEnvironment{CSLReferences}{\interlinepenalty=10000}
\setlength{\emergencystretch}{8em}
\widowpenalty=10000\clubpenalty=10000
\setlength{\LTpre}{6pt}\setlength{\LTpost}{6pt}
\setlength{\tabcolsep}{5.8pt}
\AtBeginDocument{\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue,citecolor=blue}}
''',encoding='utf-8')
        tex=folder/'reading.tex'
        cmd=['pandoc',source,'-f','markdown+tex_math_single_backslash+tex_math_dollars+raw_tex+raw_attribute+fenced_divs',
             '--standalone','--listings','--citeproc','--bibliography',PAPER/'references.bib','--toc','--toc-depth=2',
             '--metadata','title='+title,'--metadata','date='+stamp,'--metadata','lang=en-US',
             '--variable','fontsize=11pt','--variable','geometry=margin=22mm','--variable','mainfont=Times New Roman',
             '--variable','sansfont=Arial','--variable','monofont=Consolas','--include-in-header',header,'-o',tex]
        log=run(cmd,cwd=PAPER);(folder/'pandoc.log').write_text(log,encoding='utf-8')
        value=tex.read_text(encoding='utf-8')
        value=value.replace(r'\usepackage{unicode-math}',r'\usepackage{fontspec}').replace(r'\usepackage{bookmark}',r'\usepackage{hyperref}')
        assert r'\footnote{' not in value
        value=value.replace(r'\IfFileExists{footnotehyper.sty}{\usepackage{footnotehyper}}{\usepackage{footnote}}','% No table footnotes.').replace(r'\makesavenoteenv{longtable}','')
        def inline(m):
            s=m[2].replace('-',r'-\allowbreak{}').replace(r'\textbar{}',r'\textbar{}\allowbreak{}')
            s=re.sub(r'(?<![A-Za-z\\])[0-9a-f]{40,64}',lambda v:r'\allowbreak{}'.join(v[0][i:i+8] for i in range(0,len(v[0]),8)),s)
            return r'\texttt{'+s+'}'
        value=re.sub(r'\\passthrough\{\\lstinline(.)(.*?)\1\}',inline,value)
        value=value.replace(r'\_',r'\_\allowbreak{}')
        # Plain prose hashes: safe breaks; URL/hash paths are excluded by preceding '/'.
        value=re.sub(r'(?<![A-Za-z0-9/])[0-9a-f]{40,64}(?![A-Za-z0-9])',lambda v:r'\allowbreak{}'.join(v[0][i:i+8] for i in range(0,len(v[0]),8)),value)
        tex.write_text(value,encoding='utf-8')
        passes=[]
        for n in range(1,4):
            command=['xelatex','-disable-installer','-interaction=nonstopmode','-halt-on-error','-file-line-error','-output-directory='+str(folder),tex]
            start=time.perf_counter();log=run(command,cwd=PAPER,timeout=180)
            (folder/f'xelatex_pass{n}.log').write_text(log,encoding='utf-8')
            passes.append(dict(number=n,seconds=time.perf_counter()-start,return_code=0))
        destination=PAPER/(stem+'.pdf');shutil.copyfile(folder/'reading.pdf',destination)
        retained=PAPER/(stem+'_export.tex');shutil.copyfile(tex,retained)
        warnings=[l for l in (folder/'pandoc.log').read_text(encoding='utf-8').splitlines()+log.splitlines() if any(k in l for k in ['Overfull','Missing character','undefined','Warning'])]
        outputs.append(dict(**binding(destination),source=binding(PAPER/(stem+'.md')),intermediate_TeX=binding(retained),commands=[[str(x) for x in cmd],[str(x) for x in command]],passes=passes,warnings=warnings,log_root=str(folder)))
    build=dict(UTC=utc(),document_date=stamp,date_timezone='Asia/Shanghai',versions=versions,outputs=outputs,
        source_manifest_SHA256=sha(OUT/'source_manifest.json'),sources=manifest['components'],
        commands=['python scripts/round165_audit.py evidence','python scripts/round165_documents.py assemble','python scripts/round165_documents.py pdf','python scripts/round165_documents.py qa'],
        legacy_assembler_invoked=False,method_and_model_source_used=False,new_Optimize=0,production_compile=0,
        document_operation_marker_successful_invocations=1,seconds=time.perf_counter()-tick,visual_QA_pending=True)
    write(OUT/'document_build.json',build)
    write(PAPER/'pdf_export.json',dict(UTC=utc(),current_round=165,exported=True,
        manuscript_SHA256=sha(PAPER/'manuscript.pdf'),supplement_SHA256=sha(PAPER/'supplement.pdf'),
        source='current components; see ../unified_exact_round165/document_build.json',visual_review_pending=True,
        document_date_requested=stamp,document_date_timezone='Asia/Shanghai'))
    print(json.dumps(dict(outputs=[dict(path=o['path'],bytes=o['bytes'],warnings=o['warnings']) for o in outputs],seconds=build['seconds'])))

def qa():
    import pdfplumber
    from PIL import Image,ImageDraw,ImageOps
    build=read(OUT/'document_build.json');results=[]
    topics=['Abstract','Algorithm 1','Table 2.','Table 8.','Table 9.','Table 10.','Table 12.','Table 14.','Appendix A.','Appendix B.','B.0','References','Three-Seed','pre-frozen feasible-target']
    for output in build['outputs']:
        pdf=ROOT/output['path'];assert sha(pdf)==output['SHA256']
        folder=TEMP/('QA_'+pdf.stem+'_'+sha(pdf)[:12]);folder.mkdir(parents=True,exist_ok=True)
        pngs=sorted(folder.glob('page-*.png'))
        if not pngs:
            run([POPPLER/'pdftoppm.exe','-r','65','-png',pdf,folder/'page'],timeout=180)
            pngs=sorted(folder.glob('page-*.png'))
        pages=[]
        with pdfplumber.open(pdf) as document:
            for n,page in enumerate(document.pages,1):
                text=page.extract_text() or ''
                (folder/f'text-{n:03}.txt').write_text(text,encoding='utf-8')
                outside=[dict(text=c.get('text'),x0=c['x0'],x1=c['x1'],top=c['top'],bottom=c['bottom']) for c in page.chars if c['x0']<-.5 or c['x1']>page.width+.5 or c['top']<-.5 or c['bottom']>page.height+.5]
                pages.append(dict(page=n,width=page.width,height=page.height,characters=len(page.chars),outside_page=outside,replacements=text.count('\ufffd'),topics=[t for t in topics if t in text],opening=text[:140]))
        assert len(pngs)==len(pages)
        contacts=[]
        for start in range(0,len(pngs),12):
            sheet=Image.new('RGB',(1800,2480),'#d8d8d8');draw=ImageDraw.Draw(sheet)
            for j,p in enumerate(pngs[start:start+12]):
                with Image.open(p) as img: thumb=ImageOps.contain(img.convert('RGB'),(580,780))
                x=(j%3)*600+(600-thumb.width)//2;y=(j//3)*620+25
                thumb.thumbnail((580,580))
                sheet.paste(thumb,(x,y));draw.text(((j%3)*600+10,(j//3)*620+7),f'{pdf.stem} page {start+j+1}',fill='black')
            dest=folder/f'contact-{start//12+1:02}.png';sheet.save(dest);contacts.append(str(dest))
        result=dict(path=output['path'],SHA256=sha(pdf),page_count=len(pages),pages=pages,contact_sheets=contacts,
            actual_visual_inspection_complete=False,render_root=str(folder),blank_pages=[p['page'] for p in pages if p['characters']<20],
            outside_page_characters=sum(len(p['outside_page']) for p in pages),replacement_characters=sum(p['replacements'] for p in pages))
        results.append(result)
    write(OUT/'document_qa.json',dict(UTC=utc(),status='RENDERED_PENDING_VISUAL_REVIEW',documents=results,
        source_checks=source_checks(),evidence_checks_SHA256=sha(OUT/'evidence_checks.json'),new_Optimize=0,
        visual_acceptance_not_inferred_from_file_existence=True))
    print(json.dumps([dict(path=r['path'],pages=r['page_count'],outside=r['outside_page_characters'],blank=r['blank_pages'],contacts=r['contact_sheets'],topic_pages=[dict(page=p['page'],topics=p['topics']) for p in r['pages'] if p['topics']]) for r in results]))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['assemble','pdf','qa']);args=parser.parse_args()
    globals()[args.action]()
