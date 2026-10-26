"""One anonymous science-commit recovery, same-root repair only, zero native work."""
from pathlib import Path,PurePosixPath
from concurrent.futures import ThreadPoolExecutor
import argparse,datetime,gzip,hashlib,json,os,re,shutil,subprocess,sys,time,zipfile

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--commit',required=True);parser.add_argument('--destination',required=True)
    parser.add_argument('--receipt',required=True);parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',args.commit)
    dest=Path(args.destination).resolve();allowed=Path('E:/codes/ExactEBRP-work/restore').resolve();receipt=Path(args.receipt).resolve()
    assert dest.is_relative_to(allowed) and dest!=allowed and not receipt.is_relative_to(dest)
    state=dest/'restore_state.json'
    if dest.exists():assert args.resume and read(state)['commit']==args.commit
    else:dest.mkdir(parents=True);write(state,dict(commit=args.commit,owner='Round128 single science-commit recovery'))
    for p in [dest,*dest.parents]:assert not p.is_symlink() and not p.is_junction()
    attempts=receipt.parent/'review/public_recovery_attempts';attempts.mkdir(parents=True,exist_ok=True)
    number=1
    while (attempts/f'attempt{number:02d}').exists():number+=1
    attempt_dir=attempts/f'attempt{number:02d}';attempt_dir.mkdir()
    if receipt.exists():
        assert args.resume and read(receipt)['science_commit']==args.commit
        shutil.copyfile(receipt,attempt_dir/'prior_receipt.json')
    curl=Path(os.environ['WINDIR'])/'System32/curl.exe';base=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{args.commit}/'
    tick=time.perf_counter();failures=[];transformations=[];transfers=[]
    def get(name):
        for attempt in range(3):
            try:
                remaining=1500-(time.perf_counter()-tick);assert remaining>1
                command=[str(curl),'--disable','--proto','=https','--proto-redir','=https','--fail','--location',
                    '--silent','--show-error','--max-time',str(min(60,remaining)),base+name]
                r=subprocess.run(command,capture_output=True,timeout=min(60,remaining)+3)
                assert r.returncode==0,(r.returncode,r.stderr.decode('utf-8',errors='replace'))
                transfers.append(dict(path=name,bytes=len(r.stdout),SHA256=digest(r.stdout),ordinary_HTTPS_validation=True,
                    application_credentials_supplied=False,curlrc_disabled=True));return r.stdout
            except Exception as error:
                failures.append(dict(path=name,attempt=attempt+1,error=repr(error)))
                if attempt==2:raise
    def destination(name):
        rel=PurePosixPath(name);assert not rel.is_absolute() and '..' not in rel.parts
        assert all(':' not in part and '\\' not in part for part in rel.parts)
        p=dest.joinpath(*rel.parts);p.parent.mkdir(parents=True,exist_ok=True)
        for parent in [p.parent,*p.parent.parents]:assert not parent.is_junction() and not parent.is_symlink()
        assert p.parent.resolve().is_relative_to(dest) and not p.is_symlink() and not p.is_junction();return p
    try:
        name='results/unified_exact_round128/export_manifest.json';blob=get(name);manifest=json.loads(blob);destination(name).write_bytes(blob)
        def fetch(row):
            p=destination(row['path'])
            if p.exists():assert p.stat().st_size==row['bytes'] and sha(p)==row['SHA256'];return
            raw=get(row['path']);data=raw
            if digest(data)!=row['SHA256'] and row['serialization'].startswith('exact bytes;'):
                lf=raw.replace(b'\r\n',b'\n')
                for candidate,mode in [(lf,'LF'),(lf.replace(b'\n',b'\r\n'),'CRLF')]:
                    if digest(candidate)==row['SHA256']:
                        data=candidate;transformations.append(dict(path=row['path'],materialization=mode,transport_SHA256=digest(raw)));break
            assert len(data)==row['bytes'] and digest(data)==row['SHA256'],('published bytes',row['path'])
            p.write_bytes(data)
        with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(fetch,manifest['files']))
        out=dest/'results/unified_exact_round128';archives=read(out/'raw_archive_manifest.json')['archives'];extracted=[]
        assert len(archives)==6 and {a['name'] for a in archives}=={f'formal_group{n:02d}.zip' for n in range(1,6)}|{'qualification_closed_fees_parent_sources.zip'}
        for a in archives:
            joined=destination('archive_transport/'+a['name'])
            if not joined.exists():
                with joined.open('xb') as f:
                    for part in a['pieces']:
                        p=destination(part['path']);assert sha(p)==part['SHA256']
                        with p.open('rb') as source:shutil.copyfileobj(source,f)
            assert joined.stat().st_size==a['compressed_bytes'] and sha(joined)==a['SHA256']
            index=a['member_index'];data=(dest/index['path']).read_bytes();assert digest(data)==index['SHA256']
            decoded=gzip.decompress(data);assert len(decoded)==index['decoded_bytes'] and digest(decoded)==index['decoded_SHA256']
            members=json.loads(decoded);by={m['path']:m for m in members};assert len(by)==len(members)==a['file_count']
            with zipfile.ZipFile(joined) as z:
                assert set(z.namelist())==set(by) and len(z.infolist())==len(by)
                for info in z.infolist():
                    m=by[info.filename];assert info.file_size==m['bytes'];p=destination(info.filename)
                    if p.exists():assert sha(p)==m['SHA256'];continue
                    with z.open(info) as source,p.open('xb') as target:shutil.copyfileobj(source,target)
                    assert sha(p)==m['SHA256']
            extracted.append(dict(name=a['name'],members=len(members),SHA256=a['SHA256']))
        check_receipt=dest/'portable_check_receipt.json'
        r=subprocess.run([sys.executable,str(dest/'scripts/round128_portable_check.py'),'--receipt',str(check_receipt)],cwd=dest,
            capture_output=True,timeout=600,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        (dest/'portable_stdout.log').write_bytes(r.stdout);(dest/'portable_stderr.log').write_bytes(r.stderr)
        assert r.returncode==0,r.stderr.decode('utf-8',errors='replace')[-4000:]
        assert read(check_receipt)['status']=='PASS'
        write(receipt,dict(status='PASS',science_commit=args.commit,destination=str(dest),export_manifest_SHA=sha(out/'export_manifest.json'),
            files=manifest['file_count'],archives=extracted,portable_check=read(check_receipt),seconds=time.perf_counter()-tick,
            failures_preserved=failures,Git_text_materializations=transformations,transfers=transfers,
            anonymous_public_HTTPS=True,local_raw_or_old_checkout_fallback=False,Optimize=0,native_starts=0,compilation=0))
        print(json.dumps(dict(status='PASS',files=manifest['file_count'],members=sum(a['members'] for a in extracted),seconds=time.perf_counter()-tick)))
    except Exception as error:
        write(receipt,dict(status='FAILED_PRESERVE_SAME_ROOT',science_commit=args.commit,destination=str(dest),error=repr(error),
            failures=failures,transfers=transfers,seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,compilation=0));raise
    finally:
        if receipt.exists():shutil.copyfile(receipt,attempt_dir/'receipt.json')
        for name in ['restore_state.json','portable_stdout.log','portable_stderr.log','portable_check_receipt.json']:
            if (dest/name).is_file():shutil.copyfile(dest/name,attempt_dir/name)

if __name__=='__main__':main()
