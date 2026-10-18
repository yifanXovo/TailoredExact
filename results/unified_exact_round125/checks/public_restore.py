"""One anonymous, lightweight science-A export and portable reconstruction.
No authentication, repository clone, native binary, historical carrier or solver.
"""
from pathlib import Path, PurePosixPath
from concurrent.futures import ThreadPoolExecutor
import argparse,datetime,hashlib,json,subprocess,sys,time,urllib.request
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--commit',required=True);a.add_argument('--destination',required=True);a.add_argument('--receipt',required=True);args=a.parse_args()
 assert len(args.commit)==40 and all(x in '0123456789abcdef' for x in args.commit)
 dest=Path(args.destination).resolve();allowed=Path('E:/codes/ExactEBRP-work/restore').resolve()
 assert dest.is_relative_to(allowed) and dest!=allowed and not dest.exists(),dest
 receipt=Path(args.receipt).resolve();assert not receipt.is_relative_to(dest)
 base=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{args.commit}/results/unified_exact_round125/'
 started=time.perf_counter();started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat();attempts=[]
 def get(name):
  for attempt in range(3):
   try:
    with urllib.request.urlopen(base+name,timeout=30) as f:return f.read()
   except Exception as e:
    attempts.append({'file':name,'attempt':attempt+1,'error':str(e)})
    if attempt==2:raise
    time.sleep(1+attempt)
 manifest_bytes=get('export_manifest.json');manifest=json.loads(manifest_bytes);dest.mkdir(parents=True)
 (dest/'export_manifest.json').write_bytes(manifest_bytes)
 def fetch(row):
  rel=PurePosixPath(row['path']);assert not rel.is_absolute() and '..' not in rel.parts
  p=dest/str(rel);assert p.resolve().is_relative_to(dest)
  data=get(row['path']);assert len(data)==row['bytes'] and sha(data)==row['sha256'],row['path']
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return len(data)
 with ThreadPoolExecutor(max_workers=6) as pool:sizes=list(pool.map(fetch,manifest['files']))
 expected=json.loads((dest/'checks/finite_results.json').read_text())
 commands=[]
 for script in ['finite_checks.py','package_checks.py']:
  r=subprocess.run([sys.executable,str(dest/'checks'/script)],cwd=dest,capture_output=True,text=True);commands.append({'script':script,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr});assert r.returncode==0,commands[-1]
 actual=json.loads((dest/'checks/finite_results.json').read_text());expected.pop('elapsed_seconds');actual.pop('elapsed_seconds');assert actual==expected,'typed JSON results differ'
 result={'status':'PASS','science_commit':args.commit,'anonymous':True,'transport':'public raw HTTPS, no credentials','manifest_sha256':sha(manifest_bytes),'files_downloaded':len(sizes),'payload_bytes':sum(sizes),'manifest_bytes':len(manifest_bytes),'destination':str(dest),'started_utc':started_utc,'elapsed_seconds':time.perf_counter()-started,'typed_JSON_comparison':'equal after excluding only elapsed_seconds','commands':commands,'retrieval_failures_retried':attempts,'solver_processes':0,'optimization_calls':0,'production_compilations':0,'scope':'current lightweight package only; no historical campaign reconstruction'}
 receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['commands','retrieval_failures_retried']}))
if __name__=='__main__':main()
