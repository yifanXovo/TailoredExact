"""Lightweight document/link/table/secret-marker checks, not content peer review."""
from pathlib import Path
import csv,hashlib,json,re
P=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 errors=[];links=0;bib=set(re.findall(r'@\w+\{([^,]+),',(P/'references.bib').read_text(encoding='utf-8')))
 for name in ['manuscript.md','model_appendix.md','algorithm_appendix.md','reproducibility.md','review_actions.md','research_decision.md','contribution_ledger.md','literature_scope.md']:
  text=(P/name).read_text(encoding='utf-8')
  for target in re.findall(r'\]\(([^)]+)\)',text):
   if target.startswith(('https://','http://','#')):continue
   links+=1
   if not (P/target.split('#')[0]).is_file():errors.append([name,'missing link',target])
  for cite in re.findall(r'@([A-Za-z][A-Za-z0-9]+)',text):
   if cite not in bib:errors.append([name,'missing citation',cite])
  for no,line in enumerate(text.splitlines(),1):
   if line.count('\\(')!=line.count('\\)'):errors.append([name,no,'inline math delimiter mismatch',line])
  if 'qquad' in text.replace('\\qquad',''):errors.append([name,'bare qquad'])
 tags={name:re.findall(r'\\tag\{([^}]+)\}',(P/name).read_text(encoding='utf-8')) for name in ['manuscript.md','model_appendix.md','algorithm_appendix.md']}
 for name,vals in tags.items():
  if len(vals)!=len(set(vals)):errors.append([name,'duplicate formula tag'])
 assert set(tags['model_appendix.md'])=={f'A{x}' for x in range(1,36)},tags['model_appendix.md']
 for name,n in [('r122_arms.csv',32),('r122_pairs.csv',48),('r123_arms.csv',3),('r123_pairs.csv',3)]:
  with (P/'tables'/name).open(newline='',encoding='utf-8') as f:assert len(list(csv.DictReader(f)))==n
 for r in json.loads((P/'checks/unchanged_tables.json').read_text())['files']:assert sha(P/'tables'/r['file'])==r['sha256']
 # Restrict scanning to the proposed lightweight text artifact, not unrelated history.
 markers=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'github_pat_[A-Za-z0-9_]{35,}',rb'(?i)(?:cookie|authorization)\s*:\s*(?:bearer\s+)?[A-Za-z0-9+/=_-]{24,}']
 scanned=0
 for p in P.rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts:continue
  assert p.suffix.lower() not in ['.exe','.dll','.pdf','.html','.zip','.lic'],p
  data=p.read_bytes();scanned+=len(data)
  if b'\0' in data:errors.append([str(p.relative_to(P)),'binary NUL'])
  for pattern in markers:
   if re.search(pattern,data):errors.append([str(p.relative_to(P)),'credential marker'])
 assert not errors,json.dumps(errors,ensure_ascii=False,indent=2)
 return {'status':'PASS','local_links_checked':links,'bib_entries':len(bib),'formula_tags':tags,'table_denominators':[32,48,3,3],'scanned_text_bytes':scanned,'scope':'new small artifacts only; historical security findings are not cleared; no semantic proof from syntax checks'}
if __name__=='__main__':
 result=check();(P/'checks/package_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='formula_tags'}))
