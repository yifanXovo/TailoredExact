"""One anonymous science-A recovery into a new E-root; never invokes a solver."""
from pathlib import Path,PurePosixPath
from concurrent.futures import ThreadPoolExecutor
import argparse,datetime,hashlib,json,os,re,shutil,subprocess,sys,time,urllib.request,zipfile,zlib

def digest(data):return hashlib.sha256(data).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    a=argparse.ArgumentParser();a.add_argument('--commit',required=True);a.add_argument('--destination',required=True)
    a.add_argument('--receipt',required=True);a.add_argument('--resume',action='store_true');a.add_argument('--compile-pdf',action='store_true');args=a.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',args.commit)
    dest=Path(args.destination).resolve();allowed=Path('E:/codes/ExactEBRP-work/restore').resolve()
    assert dest.is_relative_to(allowed) and dest!=allowed
    receipt=Path(args.receipt).resolve();assert not receipt.is_relative_to(dest)
    state_path=dest/'restore_state.json'
    if dest.exists():assert args.resume and state_path.exists() and read(state_path)['commit']==args.commit
    else:dest.mkdir(parents=True);write(state_path,dict(commit=args.commit,owner='Round126 public science-A recovery'))
    for p in [dest,*dest.parents]:assert not p.is_junction() and not p.is_symlink()
    base=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{args.commit}/'
    tick=time.perf_counter();failures=[];transformations=[]
    def get(name):
        for attempt in range(3):
            try:
                with urllib.request.urlopen(base+name,timeout=45) as response:return response.read()
            except Exception as exc:
                failures.append(dict(path=name,attempt=attempt+1,error=repr(exc)))
                if attempt==2:raise
                time.sleep(1+attempt)
    try:
        name='results/unified_exact_round126/export_manifest.json';blob=get(name);manifest=json.loads(blob)
        path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blob)
        def fetch(row):
            rel=PurePosixPath(row['path']);assert not rel.is_absolute() and '..' not in rel.parts
            p=dest/str(rel);assert p.resolve().is_relative_to(dest)
            if p.is_file() and p.stat().st_size==row['bytes'] and digest(p.read_bytes())==row['SHA256']:return row['bytes']
            assert not p.exists(),('existing recovery bytes do not match; preserve them',row['path'])
            raw=get(row['path']);data=raw;mode='exact'
            if digest(data)!=row['SHA256'] and row['serialization'].startswith('exact bytes;'):
                normalized=raw.replace(b'\r\n',b'\n')
                for candidate,label in [(normalized,'LF'),(normalized.replace(b'\n',b'\r\n'),'CRLF')]:
                    if digest(candidate)==row['SHA256']:data=candidate;mode=label;break
            assert len(data)==row['bytes'] and digest(data)==row['SHA256'],('published byte identity',row['path'])
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            if mode!='exact':transformations.append(dict(path=row['path'],materialization=mode,Git_transport_SHA=digest(raw),materialized_SHA=digest(data)))
            return len(raw)
        start=time.perf_counter()
        with ThreadPoolExecutor(max_workers=4) as pool:sizes=list(pool.map(fetch,manifest['files']))
        retrieval=time.perf_counter()-start;out=dest/'results/unified_exact_round126';raw_manifest=read(out/'raw_archive_manifest.json')
        extraction_start=time.perf_counter();extracted=[]
        for archive in raw_manifest['archives']:
            joined=dest/'archive_transport'/archive['name'];joined.parent.mkdir(exist_ok=True)
            if not joined.exists():
                with joined.open('xb') as target:
                    for part in archive['pieces']:
                        p=dest/part['path'];assert digest(p.read_bytes())==part['SHA256']
                        with p.open('rb') as source:shutil.copyfileobj(source,target)
            assert joined.stat().st_size==archive['compressed_bytes'] and digest(joined.read_bytes())==archive['SHA256']
            with zipfile.ZipFile(joined) as z:
                infos=z.infolist();assert len(infos)==archive['file_count']
                assert sum(i.file_size for i in infos)==archive['uncompressed_bytes']
                for info in infos:
                    rel=PurePosixPath(info.filename)
                    assert not rel.is_absolute() and '..' not in rel.parts and all(':' not in s and '\\' not in s for s in rel.parts)
                    target=dest/str(rel);assert target.resolve().is_relative_to(dest)
                    if target.exists():
                        data=target.read_bytes();assert len(data)==info.file_size and zlib.crc32(data)&0xffffffff==info.CRC
                        continue
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with z.open(info) as source,target.open('xb') as stream:shutil.copyfileobj(source,stream)
                    assert target.stat().st_size==info.file_size
            extracted.append(dict(name=archive['name'],files=len(infos),bytes=archive['uncompressed_bytes'],SHA256=archive['SHA256']))
        extraction=time.perf_counter()-extraction_start;state=read(state_path)
        commands=[]
        if not state.get('portable_receipt_SHA'):
            command=[sys.executable,'-B',str(dest/'scripts/round126_portable_check.py')]
            start=time.perf_counter();r=subprocess.run(command,cwd=dest,capture_output=True,text=True)
            commands.append(dict(command=command,returncode=r.returncode,seconds=time.perf_counter()-start,stdout=r.stdout,stderr=r.stderr))
            assert r.returncode==0,commands[-1]
            state['portable_receipt_SHA']=digest((dest/'portable_check_receipt.json').read_bytes());write(state_path,state)
        assert digest((dest/'portable_check_receipt.json').read_bytes())==state['portable_receipt_SHA']
        pdf=None
        if args.compile_pdf:
            env=dict(os.environ,ROUND126_PDF_TEMP=str(dest/'compile'),ROUND126_PDF_DEST=str(dest/'compiled/manuscript.pdf'),
                ROUND126_PDF_RECEIPT=str(dest/'compiled/export.json'),TEMP=str(dest/'compile'),TMP=str(dest/'compile'))
            (dest/'compile').mkdir(exist_ok=True)
            command=[sys.executable,'-B',str(dest/'scripts/round126_export.py')]
            start=time.perf_counter();r=subprocess.run(command,cwd=dest,env=env,capture_output=True,text=True)
            commands.append(dict(command=command,returncode=r.returncode,seconds=time.perf_counter()-start,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,commands[-1]
            texts=[]
            for tag,path in [('published',out/'manuscript.pdf'),('rebuilt',dest/'compiled/manuscript.pdf')]:
                target=dest/'compiled'/(tag+'.txt')
                subprocess.run(['pdftotext','-layout',str(path),str(target)],check=True,capture_output=True)
                texts.append(target.read_text(encoding='utf-8'))
            assert texts[0]==texts[1],'PDF text changed; timestamps are not compared as science'
            pages=texts[1].split('\f');selected=[]
            for token in ['Table SC3','Algorithm 1','Appendix B. Executable']:
                hits=[i+1 for i,p in enumerate(pages) if token in p]
                if hits:selected.append(hits[-1])
            for page in sorted(set(selected)):
                subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-scale-to','1600','-png',str(dest/'compiled/manuscript.pdf'),str(dest/'compiled'/f'check_page{page:03d}')],check=True,capture_output=True)
            pdf=dict(compiled=True,text_equal=True,binary_timestamp_equality_not_required=True,rendered_pages=sorted(set(selected)),
                actual_visual_reread_pending=True,PDF=str(dest/'compiled/manuscript.pdf'))
        result=dict(status='PASS',commit=args.commit,destination=str(dest),anonymous=True,transport='Public raw HTTPS, no credentials',
            manifest_SHA=digest(blob),files=len(sizes),transport_bytes=sum(sizes),retrieval_wall_seconds=retrieval,
            serialization_materializations=transformations,archives=extracted,extraction_wall_seconds=extraction,
            portable_check=read(dest/'portable_check_receipt.json'),PDF=pdf,commands=commands,
            retried_retrieval_errors=failures,total_outer_task_wall_seconds=time.perf_counter()-tick,
            network_wall_is_not_reported_as_CPU=True,native_solver_starts=0,Optimize=0,production_compilations=0,
            scope='R126 finite science package only. No historical campaign, native binary or license restored; no re-solving.')
        write(receipt,result);print(json.dumps({k:v for k,v in result.items() if k not in ['commands','portable_check','serialization_materializations']}))
    except BaseException as exc:
        failure=receipt.with_name(receipt.stem+'_failure.json')
        prior=read(failure) if failure.exists() else []
        prior.append(dict(commit=args.commit,destination=str(dest),error=repr(exc),retrieval_failures=failures,
            seconds=time.perf_counter()-tick,preserved_partial_root=True));write(failure,prior);raise

if __name__=='__main__':main()
