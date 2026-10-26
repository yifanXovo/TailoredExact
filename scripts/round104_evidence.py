"""Exact-byte compact evidence and bounded, non-overwriting restoration."""
from round104_common import *
import tarfile,hashlib,io

def selected():
    files=set()
    def add(p):
        p=Path(p).resolve();assert p.is_file(),str(p);assert p.is_relative_to(ROOT)
        files.add(p)
    for d in sorted((OUT/'diagnostics').iterdir()):
        if d.is_dir():
            for p in d.rglob('*'):
                if p.is_file():add(p)
            plan=d/'plan.json'
            if plan.exists():
                q=read(plan);add(ROOT/q['source'])
                old=q.get('inherited_pool')
                if old:
                    source=ROOT/old['path'];add(source)
                    for n in ['summary.json','contract.json']:add(source.parent/n)
                h=q.get('actual_H_pass')
                if h:
                    add(ROOT/h['path']);add(ROOT/h['path'].replace('.rows.json','.contract.json'))
    for name in ['native01','native02','control01']:
        camp=OUT/name
        if not camp.exists():continue
        add(camp/'identity.json')
        q=read(camp/'identity.json')
        for a in q['launches']:add(ROOT/a['panel']['input_path'])
        for p in camp.glob('*.json*'):add(p)
        for p in (camp/'reference').rglob('*'):
            if p.is_file():add(p)
        for a in q['launches']:
            d=Path(a['destination'])
            if not d.exists():continue
            for n in ['completion.json','audit.json','result.json','observations.json','launch.json',
                      'affinity.json','phases.csv','progress.csv','samples.jsonl','process_start_marker.json','stderr.log']:
                p=d/n
                if p.exists():add(p)
            # Complete bound payloads and receipt/publication clocks are already
            # in observations.json. Retain raw identity/call/witness records,
            # without thousands of duplicate scalar-bound event files.
            observed=d/'observations.json'
            if observed.exists():
                for e in read(observed):
                    if e['payload']['kind']=='bound':continue
                    for suffix in ['json','commit']:
                        p=d/'journal'/('event_'+str(e['sequence'])+'.'+suffix)
                        if p.exists():add(p)
            for folder in ['hga.csv.exchange','external/models','external/witnesses']:
                for p in (d/folder).rglob('*'):
                    if p.is_file():add(p)
            for p in (d/'external').glob('*'):
                if p.is_file():add(p)
            logdir=d/'external/native_logs'
            finals={}
            for p in logdir.glob('*.round104.summary.json'):
                s=read(p)
                if not s['cache_hit']:finals[str(p).removesuffix('.summary.json')]=s['pool_iterations']
            for p in logdir.glob('*'):
                if not p.is_file():continue
                if '.round104.iteration' in p.name:
                    prefix,tail=str(p).split('.iteration',1)
                    number=int(tail.split('.',1)[0])
                    if number not in [1,finals.get(prefix)]:continue
                add(p)
            if (d/'native.log').exists():add(d/'native.log')
    for category in ['fees','engineering']:
        for d in (OUT/category).iterdir():
            if not d.is_dir():continue
            if not (d/'receipt.json').exists():continue
            for n in ['launch.json','receipt.json','process.json','stdout.log','stderr.log']:
                p=d/n
                if p.exists():add(p)
    for p in (OUT/'review').rglob('*'):
        if p.is_file():add(p)
    for name in ['reports_final02','reports_final02_clocks','reader_provenance']:
        for p in (OUT/name).rglob('*'):
            if p.is_file():add(p)
    return sorted(files)

def pack():
    from round100_idle import ensure_idle
    ensure_idle();dest=OUT/'compact_evidence';dest.mkdir(exist_ok=False)
    members=[]
    with tarfile.open(dest/'evidence.tar.gz','w:gz',compresslevel=6) as archive:
        for p in selected():
            data=p.read_bytes();name=p.relative_to(ROOT).as_posix()
            info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;info.mode=0o644
            archive.addfile(info,io.BytesIO(data));members.append(dict(path=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
    write(dest/'manifest.json',dict(files=members,archive_sha256=sha(dest/'evidence.tar.gz'),
        archive_bytes=(dest/'evidence.tar.gz').stat().st_size,exact_source_bytes=sum(r['bytes'] for r in members),
        source_sha256=sha(__file__),omitted='intermediate generation point/membership files and duplicate scalar-bound journal files; complete observations, final pool/dual/full solutions/all ahead-of-call records and final memberships retained',
        scope='only observed completed/failure evidence; no executables, DLL, license or invented files'))
    print(json.dumps(dict(files=len(members),archive_bytes=(dest/'evidence.tar.gz').stat().st_size)))

def verify(restore=False):
    dest=OUT/'compact_evidence';q=read(dest/'manifest.json');archive=dest/'evidence.tar.gz'
    assert sha(archive)==q['archive_sha256'];expected={r['path']:r for r in q['files']};seen=set()
    with tarfile.open(archive,'r:gz') as a:
        for m in a:
            assert m.isfile() and m.name in expected and m.name not in seen
            path=(ROOT/m.name).resolve();assert path.is_relative_to(ROOT)
            assert m.name.startswith(('results/','reference/')),'unexpected restoration surface'
            data=a.extractfile(m).read();r=expected[m.name]
            assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'];seen.add(m.name)
            if restore:
                if path.exists():assert path.is_file() and sha(path)==r['sha256'],'existing different bytes: '+m.name
                else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    assert seen==set(expected)
    print(json.dumps(dict(verified=True,files=len(seen),restored_missing_only=restore,Optimize_calls=0)))

if __name__=='__main__':
    assert sys.argv[1] in ['pack','verify','restore']
    pack() if sys.argv[1]=='pack' else verify(sys.argv[1]=='restore')
