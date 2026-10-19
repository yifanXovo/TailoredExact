"""One Markdown-to-LaTeX reading PDF; compile only while native work is idle."""
from pathlib import Path
import json,re,shutil,subprocess,time,os

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round126'
TEMP_PARENT=Path(os.environ.get('ROUND126_PDF_TEMP','E:/codes/ExactEBRP-work/temp/round126/pdf'))

def landscape_tables(text):
    # Keep actual captions on the same landscape flow as their complete tables.
    pattern=r'((?:^\*\*Table[^\n]*|^#{1,3} Table[^\n]*)\n(?:\n|<!--[^\n]*-->\n)*)(^\|[^\n]*(?:\n\|[^\n]*)*)'
    # Fenced raw blocks keep the Markdown table outside TeX's raw environment
    # parser; a bare begin/end would cause Pandoc to copy the pipe table as TeX.
    def wrap(m):
        if m.group(2).splitlines()[0].count('|')-1<=5:return m.group(0)
        return '\n```{=latex}\n\\begin{landscape}\n```\n\n'+m.group(1)+m.group(2)+'\n\n```{=latex}\n\\end{landscape}\n```\n'
    return re.sub(pattern,wrap,text,flags=re.M)

def export():
    # Document-only guard; avoids importing the historical solver/reader graph in a public empty root.
    live=subprocess.check_output(['powershell.exe','-NoProfile','-Command',
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(ExactEBRP|gurobi_cl|cmake|ninja|g\\+\\+|cc1plus|MSBuild)\\.exe$' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"],text=True).strip()
    assert not live,('native/build task active; postpone PDF compilation',live)
    TEMP_PARENT.mkdir(parents=True,exist_ok=True);tick=time.perf_counter()
    number=1
    while (TEMP_PARENT/f'attempt{number:02d}').exists():number+=1
    TEMP=TEMP_PARENT/f'attempt{number:02d}';TEMP.mkdir()
    main=(OUT/'manuscript.md').read_text(encoding='utf-8-sig')
    title=main.splitlines()[0].lstrip('# ')
    main='\n'.join(main.splitlines()[1:])
    # The maintained Markdown remains source-faithful. These are export-only typography mappings.
    text=main+'\n\n# References\n\n::: {#refs}\n:::\n'
    for name in ['model_appendix.md','algorithm_appendix.md','tables/historical_display.md']:
        text+='\n\n\\clearpage\n\n'+(OUT/name).read_text(encoding='utf-8-sig')
    text=text.replace('ᶜ',r'\(\mathcal C\)').replace('∎',r'\(\square\)')
    for dash in ['\u2010','\u2011','\u2012','\u2013','\u2014','\u2015']:text=text.replace(dash,'-')
    symbols={'−':'-','≤':r'\le ','≥':r'\ge ','ℓ':r'\ell ','η':r'\eta ','μ':r'\mu ','β':r'\beta ','α':r'\alpha ','Δ':r'\Delta ','∈':r'\in '}
    def math_symbols(match):
        value=match.group(0)
        for a,b in symbols.items():value=value.replace(a,b)
        return value
    text=re.sub(r'\\\(.*?\\\)|\\\[.*?\\\]',math_symbols,text,flags=re.S)
    # Values in display tables can be rounded; all full-precision CSV authorities stay unchanged.
    display=[]
    for line in text.splitlines():
        if line.startswith('|'):
            cells=line.split('|')
            for j,cell in enumerate(cells):
                value=cell.strip()
                if len(value)>14 and re.fullmatch(r'[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?',value):cells[j]=' '+format(float(value),'.12g')+' '
            line='|'.join(cells)
        display.append(line)
    text='\n'.join(display)+'\n'
    text=landscape_tables(text)
    text=re.sub(r'(^~~~text\nAlgorithm [123][^\n]*\n.*?^~~~)',
        lambda m:'```{=latex}\n\\par\\medskip\\noindent\\begin{minipage}{\\linewidth}\n```\n\n'+m.group(1)+'\n\n```{=latex}\n\\end{minipage}\\par\\medskip\n```',text,flags=re.M|re.S)
    source=TEMP/'reading.md';source.write_text(text,encoding='utf-8')
    header=TEMP/'header.tex'
    header.write_text(r'''
\usepackage{pdflscape}
\usepackage{etoolbox}
\lstset{basicstyle=\ttfamily\footnotesize,breaklines=true,breakatwhitespace=false,
  columns=fullflexible,keepspaces=true,showstringspaces=false}
\AtBeginEnvironment{longtable}{\footnotesize}
\setlength{\emergencystretch}{3em}
\setlength{\LTpre}{6pt}
\setlength{\LTpost}{6pt}
\AtBeginDocument{\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue,citecolor=blue}}
''',encoding='utf-8')
    cmd=['pandoc',str(source),'-f','markdown+tex_math_single_backslash+tex_math_dollars+raw_tex+raw_attribute+fenced_divs',
        '--standalone','--listings','--citeproc','--bibliography',str(OUT/'references.bib'),'--toc','--toc-depth=2',
        '--metadata','title='+title,'--metadata','date=19 October 2026','--metadata','lang=en-US',
        '--variable','fontsize=11pt','--variable','geometry=margin=22mm',
        '--variable','mainfont=Times New Roman','--variable','sansfont=Arial','--variable','monofont=Consolas',
        '--include-in-header',str(header),'-o',str(TEMP/'reading.tex')]
    with (TEMP/'pandoc.log').open('wb') as log:
        r=subprocess.run(cmd,cwd=OUT,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    assert r.returncode==0,('pandoc',r.returncode,(TEMP/'pandoc.log').read_text(errors='replace')[-3000:])
    # This installed MiKTeX has fontspec and the standard AMS math fonts but no
    # unicode-math. All authored formulae are TeX; use the installed font route
    # without downloading packages or changing the maintained source.
    tex=TEMP/'reading.tex'
    value=tex.read_text(encoding='utf-8')
    value=value.replace(r'\usepackage{unicode-math}',r'\usepackage{fontspec}')
    value=value.replace(r'\usepackage{bookmark}',r'\usepackage{hyperref}')
    # There are no manuscript footnotes inside tables (or elsewhere). Avoid a
    # missing optional Pandoc table-footnote package without removing content.
    assert r'\footnote{' not in value
    value=value.replace(r'\IfFileExists{footnotehyper.sty}{\usepackage{footnotehyper}}{\usepackage{footnote}}','% No table footnotes in this manuscript.')
    value=value.replace(r'\makesavenoteenv{longtable}','')
    # Pandoc's listings path escapes inline identifiers. Render those as text
    # with explicit safe break opportunities; actual code blocks stay listings.
    def inline_code(match):
        body=match.group(2).replace('-',r'-\allowbreak{}').replace(r'\textbar{}',r'\textbar{}\allowbreak{}')
        body=re.sub(r'(?<![A-Za-z\\])[0-9a-f]{40,64}',lambda m:r'\allowbreak{}'.join(m.group(0)[i:i+8] for i in range(0,len(m.group(0)),8)),body)
        return r'\texttt{'+body+'}'
    value=re.sub(r'\\passthrough\{\\lstinline(.)(.*?)\1\}',inline_code,value)
    value=value.replace(r'\_',r'\_\allowbreak{}')
    tex.write_text(value,encoding='utf-8')
    passes=[]
    for n in range(1,4):
        command=['xelatex','-disable-installer','-interaction=nonstopmode','-halt-on-error','-file-line-error','-output-directory='+str(TEMP),str(TEMP/'reading.tex')]
        start=time.perf_counter()
        with (TEMP/f'xelatex_pass{n}.log').open('wb') as log:r=subprocess.run(command,cwd=TEMP,stdout=log,stderr=subprocess.STDOUT,timeout=240)
        passes.append(dict(pass_number=n,exit_code=r.returncode,seconds=time.perf_counter()-start))
        assert r.returncode==0,('xelatex',n,(TEMP/f'xelatex_pass{n}.log').read_text(errors='replace')[-4000:])
    pdf=TEMP/'reading.pdf';assert pdf.is_file()
    destination=Path(os.environ.get('ROUND126_PDF_DEST',str(OUT/'manuscript.pdf')))
    destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(pdf,destination)
    warnings=[]
    for p in [TEMP/'pandoc.log',TEMP/'xelatex_pass3.log']:
        warnings.extend(line for line in p.read_text(encoding='utf-8',errors='replace').splitlines() if any(k in line for k in ['Overfull','Missing character','undefined','Warning']))
    receipt=dict(exported=True,maintained_source='manuscript.md + model_appendix.md + algorithm_appendix.md + references.bib; six immutable historical tables',
        intermediate_root=str(TEMP),PDF=str(destination),bytes=pdf.stat().st_size,
        passes=passes,warnings=warnings,seconds=time.perf_counter()-tick,visual_review_pending=True,no_author_affiliation_or_funding_invented=True)
    receipt_path=Path(os.environ.get('ROUND126_PDF_RECEIPT',str(OUT/'pdf_export.json')))
    receipt_path.parent.mkdir(parents=True,exist_ok=True);receipt_path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))

if __name__=='__main__':export()
