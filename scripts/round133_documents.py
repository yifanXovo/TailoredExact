"""Use the inherited single-manuscript PDF route after native work has ended."""
from round133_common import *
import inspect, re

def idle():
    current=os.environ.get('ROUND133_METERED_PARENT_LABEL')
    pending=[value for value in budget()['unclosed'] if value.get('label')!=current]
    assert not pending,pending
    for stage,count in (('D1',14),('D3',8)):
        matrix=read(OUT/'plans'/f'{stage}_matrix_frozen.json')
        assert len(matrix['groups'])==count
        for group in matrix['groups']:
            assert (Path(group['launch']['destination'])/'verification_closeout.json').is_file()
    live=subprocess.check_output(['powershell.exe','-NoProfile','-Command',
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(ExactEBRP|Round133Research|gurobi_cl|cmake|ninja|g\\+\\+|cc1plus|MSBuild)\\.exe$' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"],text=True).strip()
    assert not live,live

def pdf():
    idle()
    import round126_export as old
    bindings={name:sha(ROOT/name) for name in ('scripts/round126_export.py','scripts/round133_documents.py',
        'results/unified_exact_round133/manuscript.md','results/unified_exact_round133/references.bib')}
    source=inspect.getsource(old.export)
    replacements=[
        ("for name in ['model_appendix.md','algorithm_appendix.md','tables/historical_display.md']:","for name in []:"),
        ("Path(os.environ.get('ROUND126_PDF_DEST',str(OUT/'manuscript.pdf')))","OUT/'manuscript.pdf'"),
        ("Path(os.environ.get('ROUND126_PDF_RECEIPT',str(OUT/'pdf_export.json')))","OUT/'pdf_export.json'"),
        ('text=landscape_tables(text)','text=caption_breaks(landscape_tables(text))'),
        (r'\usepackage{etoolbox}',r'\usepackage{etoolbox}'+'\n'+r'\usepackage{needspace}'),
        (r'\setlength{\emergencystretch}{3em}',r'\setlength{\emergencystretch}{8em}'),
        ("tex.write_text(value,encoding='utf-8')","value=break_plain_hashes(value)\n    tex.write_text(value,encoding='utf-8')"),
        ('date=19 October 2026','date=25 October 2026')]
    for before,after in replacements:
        assert source.count(before)==1,('inherited export recipe changed',before)
        source=source.replace(before,after)
    def caption_breaks(text):
        begin='\n```{=latex}\n\\begin{landscape}\n```\n'
        end='\n```{=latex}\n\\end{landscape}\n```\n'
        first=text.index('**Table Q2.');last=text.index('**Table Q4.')
        left=text.rfind(begin,0,first);right=text.index(end,last)+len(end)
        assert left>=0
        block=text[left:right]
        assert block.count(begin)==block.count(end)==3
        # Keep the qualification/bridge tables and their intervening prose
        # in one landscape flow, avoiding separate nearly empty pages.
        text=text[:left]+begin+block.replace(begin,'\n').replace(end,'\n')+end+text[right:]
        pattern=r"^The first D1 position's original postverifier[^\n]*$"
        assert len(re.findall(pattern,text,flags=re.M))==1
        text=re.sub(pattern,lambda m:'\n```{=latex}\n\\begingroup\\footnotesize\n```\n\n'+m.group(0)+
            '\n\n```{=latex}\n\\par\\endgroup\n```\n',text,flags=re.M)
        prefix='\n```{=latex}\n\\Needspace{8\\baselineskip}\n```\n\n'
        text=re.sub(r'^\*\*Table[^\n]*\*\*$',lambda m:prefix+m.group(0),text,flags=re.M)
        return re.sub(r'^For two finite optimal LPs[^\n]*$',lambda m:prefix+m.group(0),text,flags=re.M)
    def break_plain_hashes(value):
        # Typeset bare prose hashes with breaks, while preserving hyperlink
        # destinations byte-for-byte. This changes no scientific source text.
        protected=[]
        def hide(match):
            protected.append(match.group(0));return 'URLPROTECTEDTOKEN'+str(len(protected)-1)+'ENDTOKEN'
        value=re.sub(r'\\(?:href|url)\{[^{}]*\}',hide,value)
        value=re.sub(r'(?<![0-9a-f])[0-9a-f]{40,64}(?![0-9a-f])',
            lambda m:r'\allowbreak{}'.join(m.group(0)[i:i+8] for i in range(0,len(m.group(0)),8)),value)
        for i,url in enumerate(protected):value=value.replace('URLPROTECTEDTOKEN'+str(i)+'ENDTOKEN',url)
        return value
    ns=dict(vars(old),OUT=OUT,TEMP_PARENT=TEMP/'pdf',caption_breaks=caption_breaks,break_plain_hashes=break_plain_hashes)
    exec(compile(source,__file__+'::single_authority_export','exec'),ns);ns['export']()
    for name,digest in bindings.items():assert sha(ROOT/name)==digest
    receipt=read(OUT/'pdf_export.json');path=OUT/'manuscript.pdf'
    assert Path(receipt['PDF']).resolve()==path.resolve() and path.is_file()
    assert Path(receipt['intermediate_root']).resolve().is_relative_to((TEMP/'pdf').resolve())
    receipt.update(actual_source_bindings=bindings,model_algorithm_appendices_already_in_full_manuscript=True,
        maintained_source='manuscript.md (complete model, algorithm and Appendices A-C) + references.bib; no duplicate appendix injection',
        protected_original_round=132,
        original_manuscript_and_PDF_unchanged=True,page_visual_QA='PENDING actual rendered-page inspection',
        native_Optimize=0,native_starts=0)
    write(OUT/'pdf_export.json',receipt)

if __name__=='__main__':pdf()
