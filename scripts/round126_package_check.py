"""Publication syntax/link/identity checks, not a substitute for actual review."""
from round126_common import *
import ast,csv,re

def check():
    identity();errors=[];links=0
    sources=['manuscript.md','model_appendix.md','algorithm_appendix.md','reproducibility.md','research_decision.md','review_actions.md','final_report.md']
    bib=set(re.findall(r'@\w+\{([^,]+),',(OUT/'references.bib').read_text(encoding='utf-8')))
    for name in sources:
        text=(OUT/name).read_text(encoding='utf-8-sig')
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if target.startswith(('http://','https://','#')):continue
            links+=1
            if not (OUT/target.split('#')[0]).is_file():errors.append([name,'missing local link',target])
        for key in re.findall(r'@([A-Za-z][A-Za-z0-9]+)',text):
            if key not in bib:errors.append([name,'missing bibliography key',key])
        if text.count('\\(')!=text.count('\\)'):errors.append([name,'unbalanced inline math delimiters'])
        if text.count('\\[')!=text.count('\\]'):errors.append([name,'unbalanced display math delimiters'])
    tags={name:re.findall(r'\\tag\{([^}]+)\}',(OUT/name).read_text(encoding='utf-8')) for name in sources[:3]}
    assert set(tags['model_appendix.md'])=={f'A{n}' for n in range(1,36)}
    for name,values in tags.items():assert len(values)==len(set(values)),(name,'duplicate formula tags')
    for name,n in [('r122_arms.csv',32),('r122_pairs.csv',48),('r123_arms.csv',3),('r123_pairs.csv',3)]:
        with (OUT/'tables'/name).open(newline='',encoding='utf-8-sig') as f:assert len(list(csv.DictReader(f)))==n
    old=ROOT/'results/unified_exact_round125/tables'
    for p in old.iterdir():
        if p.is_file():assert sha(p)==sha(OUT/'tables'/p.name)
    with (OUT/'arms.csv').open(newline='',encoding='utf-8-sig') as f:assert len(list(csv.DictReader(f)))==12
    with (OUT/'certification_pairs.csv').open(newline='',encoding='utf-8-sig') as f:assert len(list(csv.DictReader(f)))==6
    scripts=list((ROOT/'scripts').glob('*round126*.py'))
    for p in scripts:ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
    assert not errors,errors
    result=dict(status='PASS',local_links=links,bibliography_keys=len(bib),formula_tags=tags,syntax_checked_scripts=len(scripts),
        unchanged_historical_tables=6,new_arm_denominator=12,new_pair_denominator=6,
        scope='Only syntax, links, exact saved identities and denominators; no claim of native proof or page-by-page review from these checks.')
    write(OUT/'review/package_checks.json',result);print(json.dumps(result))

if __name__=='__main__':check()
