"""Anonymous bounded public byte/member read; no Git fallback or native runtime."""
from round138_common import *
import urllib.request,zipfile,re
from round138_delivery import INDEX,BANNED

DEST=WORK/'restore/round138-public'
REPO='yifanXovo/TailoredExact'
LIMIT=1800.

def main():
    assert not budget()['unclosed'],'ordinary public I/O stays outside timed solves'
    pin=read(OUT/'publication_pin.json');commit=pin['commit']
    assert re.fullmatch('[0-9a-f]{40}',commit)
    root=DEST.resolve();assert root.is_relative_to(WORK.resolve())
    root.mkdir(parents=True,exist_ok=True)
    owner=root/'owner.json'
    if owner.exists():
        own=read(owner);assert own['round']==138 and own['repo']==REPO
    else:
        assert not any(root.iterdir()),'Refuse an unowned nonempty public-restore directory'
        own=dict(round=138,repo=REPO,commits=[])
    if commit not in own['commits']:own['commits'].append(commit)
    write(owner,own)
    history_path=root/'attempts.json';history=read(history_path) if history_path.exists() else []
    spent=sum(r['seconds'] for r in history);assert spent<LIMIT
    tick=time.perf_counter();deadline=tick+LIMIT-spent;attempt=len(history)+1;downloads=[];checked=[]
    def remaining():
        left=deadline-time.perf_counter()
        if left<=0:raise TimeoutError('cumulative 1800s public I/O/read bound reached')
        return left
    def target_path(relative):
        parts=Path(relative).parts
        assert not Path(relative).is_absolute() and '..' not in parts and '\\' not in relative
        target=(root/relative).resolve();assert target.is_relative_to(root)
        target.parent.mkdir(parents=True,exist_ok=True);return target
    def fetch(relative,digest,size=None,local_relative=None):
        remaining();target=target_path(local_relative or relative)
        if target.exists():
            if sha(target)==digest and (size is None or target.stat().st_size==size):return target
            preserved=target.with_name(target.name+f'.mismatch-attempt{attempt}')
            assert not preserved.exists();target.rename(preserved)
        part=target.with_name(target.name+'.part')
        if part.exists():
            # An interrupted final hash/rename is complete, not a Range request
            # starting beyond EOF. A full-sized corrupt tail must be retained
            # and retransferred, not extended indefinitely.
            if sha(part)==digest and (size is None or part.stat().st_size==size):
                part.rename(target);return target
            if size is not None and part.stat().st_size>=size:
                previous=part.with_name(part.name+f'.mismatch-attempt{attempt}')
                assert not previous.exists();part.rename(previous)
        have=part.stat().st_size if part.exists() else 0
        url=f'https://raw.githubusercontent.com/{REPO}/{commit}/{relative}'
        headers={'User-Agent':'TailoredExact-Round138-finite-read'}
        if have:headers['Range']=f'bytes={have}-'
        request=urllib.request.Request(url,headers=headers)
        start=time.perf_counter()
        with urllib.request.urlopen(request,timeout=min(30.,remaining())) as response:
            status=response.status
            if have and status!=206:
                previous=part.with_name(part.name+f'.range-ignored-attempt{attempt}')
                assert not previous.exists();part.rename(previous);have=0
            if have:assert response.headers.get('Content-Range','').startswith(f'bytes {have}-')
            with part.open('ab' if have else 'wb') as stream:
                while True:
                    remaining();block=response.read(1024*1024)
                    if not block:break
                    stream.write(block)
        assert sha(part)==digest,('public byte mismatch',relative)
        assert size is None or part.stat().st_size==size,('public size mismatch',relative)
        part.rename(target)
        downloads.append(dict(path=relative,status=status,resumed_bytes=have,bytes=target.stat().st_size,
                              SHA256=digest,seconds=time.perf_counter()-start))
        return target
    error=None
    try:
        manifest_path=fetch(pin['manifest_path'],pin['manifest_SHA'],pin['manifest_bytes'],
                            local_relative=f'metadata/{commit}/carrier_manifest.json')
        manifest=read(manifest_path)
        for carrier in manifest['carriers']:
            remaining();path=fetch(carrier['path'],carrier['SHA256'],carrier['bytes'])
            marker=target_path('checked/'+carrier['SHA256']+'.json')
            if marker.exists():
                prior=read(marker);assert prior['archive_SHA']==carrier['SHA256'] and prior['PASS']
                checked.append(prior);continue
            with zipfile.ZipFile(path) as z:
                names=z.namelist();assert len(names)==len(set(names))==carrier['members']+1
                raw=z.read(INDEX);assert hashlib.sha256(raw).hexdigest()==carrier['member_index_SHA']
                members=json.loads(raw);assert set(names)==set(members)|{INDEX}
                for name,record in members.items():
                    remaining();p=Path(name)
                    assert not p.is_absolute() and '..' not in p.parts and '\\' not in name
                    assert p.suffix.lower() not in BANNED,name
                    data=z.read(name)
                    assert len(data)==record['bytes'] and hashlib.sha256(data).hexdigest()==record['SHA256'],name
            fact=dict(PASS=True,path=carrier['path'],archive_SHA=carrier['SHA256'],members=carrier['members'])
            write(marker,fact);checked.append(fact)
    except BaseException as failure:
        error=dict(type=type(failure).__name__,message=str(failure))
    elapsed=time.perf_counter()-tick
    record=dict(attempt=attempt,commit=commit,seconds=elapsed,downloads=downloads,
        completed_archives=checked,error=error,ordinary_public_I_O=True)
    history.append(record);write(history_path,history)
    total=sum(r['seconds'] for r in history)
    receipt=dict(UTC=utc(),passed=error is None,scope='Finite anonymous fixed-commit archive and per-member byte readability; not a full public semantic replay',
        commit=commit,manifest_SHA=pin['manifest_SHA'],root=str(root),attempt=attempt,
        cumulative_seconds=total,limit_seconds=LIMIT,archives_checked=len(checked),
        members_checked=sum(r['members'] for r in checked),attempt_history_SHA=sha(history_path),
        Optimize=0,compilation=0,commercial_native_asset_loads=0,Git_fallback=0,
        prior_R137_public_semantic_receipt_unchanged=True,error=error)
    write(OUT/'public_restore_receipt.json',receipt)
    print(json.dumps(receipt),flush=True)
    if error:raise RuntimeError('Public read incomplete; preserve this root and resume only missing transfer/read')

if __name__=='__main__':main()
