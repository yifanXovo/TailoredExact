"""One owned anonymous fixed-commit current-round recovery; no solver or Git."""
from pathlib import Path,PurePosixPath
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
import argparse,datetime,gzip,hashlib,json,os,re,subprocess,sys,time,zipfile

ROUND='results/unified_exact_round134'
OWNER='Round134 current-only public read-only recovery'
ALLOWED=Path('E:/codes/ExactEBRP-work/restore')
CURL=Path(os.environ.get('WINDIR','C:/Windows'))/'System32/curl.exe'
FORBIDDEN={'.exe','.dll','.o','.obj','.a','.lib','.lic','.ttf','.otf','.woff','.woff2','.pyc'}

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as stream:
        for part in iter(lambda:stream.read(1048576),b''):h.update(part)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_name(p.name+'.pending')
    temp.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8');os.replace(temp,p)
def safe(name):
    rel=PurePosixPath(name)
    assert name==rel.as_posix() and not rel.is_absolute() and '..' not in rel.parts
    assert '\\' not in name and ':' not in name and '.git' not in rel.parts
    assert rel.suffix.lower() not in FORBIDDEN
    return rel
def no_links(path):
    for p in (path,*path.parents):
        if p.exists():assert not p.is_symlink() and not getattr(p,'is_junction',lambda:False)()

class Recovery:
    def __init__(self,args):
        self.args=args;self.tick=time.perf_counter();self.dest=args.destination.resolve()
        assert re.fullmatch(r'[0-9a-f]{40}',args.commit)
        assert self.dest!=ALLOWED.resolve() and self.dest.is_relative_to(ALLOWED.resolve())
        no_links(self.dest);self.state_path=self.dest/'restore_state.json'
        self.prior=0.
        if self.dest.exists():
            assert self.state_path.is_file() and args.resume,'only the original owned failed root may resume'
            self.state=read(self.state_path)
            assert self.state['owner']==OWNER and self.state['commit']==args.commit
            assert self.state['destination']==str(self.dest) and self.state['initially_empty']
            assert self.state['state']=='FAILED_PRESERVE','completed/running root must not be rerun'
            self.prior=self.state['cumulative_seconds'];self.state['attempt']+=1
        else:
            assert not args.resume
            self.dest.mkdir(parents=True,exist_ok=False)
            self.state=dict(owner=OWNER,commit=args.commit,destination=str(self.dest),initially_empty=True,attempt=1,files={})
        assert not args.receipt.resolve().is_relative_to(self.dest)
        self.state.update(state='RUNNING',started_UTC=utc());write(self.state_path,self.state)
    def remaining(self):
        left=7200-(self.prior+time.perf_counter()-self.tick)
        assert left>0,'cumulative recovery 7200-second limit exhausted'
        return left
    def fetch(self,name,record=None):
        safe(name);target=self.dest.joinpath(*PurePosixPath(name).parts);no_links(target)
        if target.is_file() and record:
            if target.stat().st_size==record['bytes'] and sha(target)==record['SHA256']:return dict(path=name,reused_verified=True)
            raise AssertionError(('existing restored file fails identity',name))
        if target.is_file() and record is None:
            if self.state.get('manifest_SHA256'):assert sha(target)==self.state['manifest_SHA256']
            return dict(path=name,reused_verified=True,SHA256=sha(target))
        source_commit=(record or {}).get('source_commit') or self.args.commit
        source_path=(record or {}).get('source_path') or name
        assert re.fullmatch(r'[0-9a-f]{40}',source_commit);safe(source_path)
        url='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+source_commit+'/'+quote(source_path,safe='/')
        target.parent.mkdir(parents=True,exist_ok=True);partial=target.with_name(target.name+'.download')
        command=[str(CURL),'-q','--proto','=https','--proto-redir','=https','--tlsv1.2','--fail','--silent','--show-error',
            '--location','--connect-timeout','20','--max-time',str(min(240,int(self.remaining()))),
            '--retry','2','--retry-delay','1','--output',str(partial),url]
        # A failed transfer stays in this owned root. Retry resumes an actual
        # partial only when the server supports it; no healthy file is fetched again.
        if partial.exists():command[2:2]=['--continue-at','-']
        result=subprocess.run(command,capture_output=True,timeout=min(300,self.remaining()))
        if result.returncode:
            error=target.with_name(target.name+f'.attempt{self.state["attempt"]}.transport_error.txt')
            error.write_bytes(result.stderr);raise RuntimeError(('public transport failed',name,result.returncode))
        if record:
            assert partial.stat().st_size==record['bytes'] and sha(partial)==record['SHA256'],('public file identity mismatch',name)
        os.replace(partial,target)
        return dict(path=name,bytes=target.stat().st_size,SHA256=sha(target),source_commit=source_commit)
    def expand(self,record):
        folder=self.dest/ROUND/'artifacts';archive=folder/record['name']
        if not archive.exists():
            pending=archive.with_name(archive.name+f'.assemble_attempt{self.state["attempt"]}')
            with pending.open('xb') as output:
                for part in record['pieces']:
                    with (self.dest/part['path']).open('rb') as stream:
                        for data in iter(lambda:stream.read(1048576),b''):output.write(data)
            assert sha(pending)==record['SHA256'];os.replace(pending,archive)
        assert archive.stat().st_size==record['compressed_bytes'] and sha(archive)==record['SHA256']
        with gzip.open(self.dest/record['member_index']['path'],'rt',encoding='utf-8') as stream:members=json.load(stream)
        expected={m['path']:m for m in members};assert len(expected)==len(members)==record['file_count']
        with zipfile.ZipFile(archive) as z:
            assert len(z.namelist())==len(set(z.namelist()))==len(expected) and set(z.namelist())==set(expected)
            for info in z.infolist():
                self.remaining();safe(info.filename);assert not info.is_dir()
                item=expected[info.filename];target=self.dest/info.filename;no_links(target)
                if target.is_file():
                    assert target.stat().st_size==item['bytes'] and sha(target)==item['SHA256'];continue
                raw=z.read(info);assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['SHA256']
                target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('xb') as output:output.write(raw)
        return dict(name=record['name'],members=len(expected),SHA256=record['SHA256'])
    def run(self):
        try:
            self.fetch(ROUND+'/export_manifest.json');manifest=read(self.dest/ROUND/'export_manifest.json')
            assert manifest['schema']=='round134-current-only-fixed-commit-recovery-v1'
            self.state['manifest_SHA256']=sha(self.dest/ROUND/'export_manifest.json');write(self.state_path,self.state)
            records=[]
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures=[pool.submit(self.fetch,name,record) for name,record in manifest['files'].items()]
                for future in futures:records.append(future.result())
            expanded=[self.expand(r) for r in manifest['archives']]
            # Source helpers are mounted in memory by the checker from the
            # exact-byte capsule; no local original tree or raw fallback exists.
            semantic=self.args.receipt.with_name(self.args.receipt.stem+f'.semantic_attempt{self.state["attempt"]}.json')
            command=[sys.executable,str(self.dest/'scripts/round134_portable_check.py'),'--root',str(self.dest),'--receipt',str(semantic)]
            before=time.perf_counter();checked=subprocess.run(command,capture_output=True,timeout=min(3600,self.remaining()))
            self.args.receipt.with_suffix('.semantic_stdout.log').write_bytes(checked.stdout)
            self.args.receipt.with_suffix('.semantic_stderr.log').write_bytes(checked.stderr)
            assert checked.returncode==0,('pure current-reader replay failed',checked.stderr.decode(errors='replace')[-3000:])
            math=read(semantic);assert math['passed'] and math['formal_positions']==36
            assert math['Optimize']==math['compile']==math['vendor_DLL_loads']==0
            self.state.update(state='PASS',cumulative_seconds=self.prior+time.perf_counter()-self.tick,ended_UTC=utc())
            write(self.state_path,self.state)
            receipt=dict(passed=True,owner=OWNER,commit=self.args.commit,destination=str(self.dest),initially_empty=True,
                one_owned_root=True,attempt=self.state['attempt'],files=len(records),archives=expanded,
                manifest_SHA256=sha(self.dest/ROUND/'export_manifest.json'),semantic_receipt=str(semantic),semantic_SHA256=sha(semantic),
                semantic_seconds=time.perf_counter()-before,cumulative_seconds=self.state['cumulative_seconds'],
                Optimize=0,compile=0,vendor_DLL_loads=0,historical_campaign_recoveries=0,
                anonymous_fixed_commit_HTTPS=True,local_source_or_raw_fallback=False)
            write(self.args.receipt,receipt);print(json.dumps(dict(passed=True,files=len(records),archives=len(expanded),seconds=receipt['cumulative_seconds'])))
        except BaseException as error:
            self.state.update(state='FAILED_PRESERVE',error=repr(error),cumulative_seconds=self.prior+time.perf_counter()-self.tick,ended_UTC=utc())
            write(self.state_path,self.state);write(self.args.receipt,dict(passed=False,**self.state))
            raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--destination',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True);p.add_argument('--resume',action='store_true');Recovery(p.parse_args()).run()
