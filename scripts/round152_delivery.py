"""Current-only carriers, anonymous fixed-commit byte recovery and safe closeout.

No solver, compiler, historical producer, delete or move is called here.
Publication I/O timings are separate from experiment outer accounting.
"""
from pathlib import PurePosixPath
import concurrent.futures, re, shutil, zipfile
from urllib.parse import quote
from round152_common import *

HEAVY={'LP','projection','oracle','discovery','global','cycles','domains','qualification','qualification_aggregate',
       'qualification_aggregate_v2','qualification_normalized','small','fees','engineering','infra'}
EXCLUDED={'carrier_manifest.json','public_manifest.json','public_restore_receipt.json','publication.json','cleanup_record.json','RESUME.md','pr_body.md','stage_paths.json'}
FORBIDDEN={'.exe','.dll','.lib','.o','.obj','.a','.lic','.pyc','.ttf','.otf'}

def safe(name):
    p=PurePosixPath(name)
    assert name==p.as_posix() and not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name
    assert p.suffix.lower() not in FORBIDDEN and '.git' not in p.parts
    return p

def pack():
    assert not budget()['unclosed'];assert read(OUT/'candidate_decision.json')['study_complete']
    review=read(OUT/'review/final_scientific_review.json')
    assert review['disposition']=='ACCEPT_OFFLINE_SCIENTIFIC_STAGE' and not review['scientific_blockers']
    tick=time.perf_counter();art=OUT/'artifacts';art.mkdir(exist_ok=True);groups={}
    for role in ['N-B35-S','K-35-U','N-C20-U']:
        members=[]
        for name in ['LP','projection','oracle','discovery','global','cycles','domains']:
            for folder in (OUT/name).glob(role+'*'):
                members.extend(p for p in folder.rglob('*') if p.is_file())
        groups['research_'+role]=members
    groups['qualification_failures_and_fees']=[p for name in HEAVY-{'LP','projection','oracle','discovery','global','cycles','domains'}
                                              for p in (OUT/name).rglob('*') if p.is_file() and p.name!='initial_status.txt']
    archives=[];seen=set()
    for label,files in groups.items():
        dest=art/(label+'.zip');assert not dest.exists();members=[]
        with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(files):
                name=p.relative_to(ROOT).as_posix();safe(name);assert name not in seen;seen.add(name)
                assert p.suffix.lower() not in FORBIDDEN
                data=p.read_bytes();z.writestr(name,data)
                members.append(dict(member=name,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        idx=art/(label+'.members.json.gz');save_gz(idx,members)
        parts=[]
        if dest.stat().st_size>40*1024*1024:
            with dest.open('rb') as f:
                k=0
                while True:
                    data=f.read(32*1024*1024)
                    if not data:break
                    k+=1;p=dest.with_name(dest.name+f'.part{k:03}');assert not p.exists();p.write_bytes(data)
                    parts.append(dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),bytes=len(data)))
        else:parts=[dict(path=dest.relative_to(ROOT).as_posix(),SHA256=sha(dest),bytes=dest.stat().st_size)]
        archives.append(dict(name=dest.name,SHA256=sha(dest),bytes=dest.stat().st_size,parts=parts,
                             member_index=dict(path=idx.relative_to(ROOT).as_posix(),SHA256=sha(idx),bytes=idx.stat().st_size),
                             members=len(members),uncompressed_bytes=sum(m['bytes'] for m in members)))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),archives=archives,old_carriers_repacked=0,
          unique_raw_retained=True,pack_IO_seconds=time.perf_counter()-tick,all_failures_preserved=True))
    thin=[]
    for p in OUT.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(OUT)
        if rel.parts[0] in HEAVY|{'artifacts'} or p.name in EXCLUDED:continue
        thin.append(p)
    thin += list((ROOT/'scripts').glob('round152*.py'))
    thin += [ROOT/'docs'/n for n in ['round152_research.md','current_mainline.md','unified_exact_research_index.md']]
    thin += [ROOT/'.gitattributes']
    files=[dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),bytes=p.stat().st_size) for p in sorted(set(thin))]
    write(OUT/'public_manifest.json',dict(UTC=utc(),schema='round152-current-only-fixed-commit-v1',files=files,archives=archives,
          reference_index='results/unified_exact_round152/reuse_index.json',
          inherited_member_recovery='Use fixed commit/archive/member hashes. R150 roots already passed the accepted R151 public restore; no old producer is needed.',
          forbidden_operations=['Optimize','compile','old producer','delete','move'],pack_IO_seconds=time.perf_counter()-tick))
    stage=[x['path'] for x in files]+[(OUT/'carrier_manifest.json').relative_to(ROOT).as_posix(),(OUT/'public_manifest.json').relative_to(ROOT).as_posix(),(OUT/'RESUME.md').relative_to(ROOT).as_posix()]
    for a in archives:stage += [a['member_index']['path']]+[p['path'] for p in a['parts']]
    write(OUT/'stage_paths.json',stage)
    print(json.dumps(dict(archives=len(archives),members=len(seen),compressed_bytes=sum(a['bytes'] for a in archives),thin_files=len(files),IO_seconds=time.perf_counter()-tick)),flush=True)

def restore(commit):
    assert re.fullmatch('[0-9a-f]{40}',commit);tick=time.perf_counter()
    parent=(WORK/'restore').resolve();dest=(parent/f'round152-public-{commit[:12]}-attempt01').resolve()
    assert dest.is_relative_to(parent) and dest!=parent and not dest.exists();dest.mkdir()
    state=dict(UTC=utc(),commit=commit,destination=str(dest),initially_empty=True,owner='Round152 current-only anonymous public recovery',state='RUNNING')
    write(dest/'restore_state.json',state)
    def fetch(name):
        rel=safe(name);p=dest/Path(str(rel));p.parent.mkdir(parents=True,exist_ok=True)
        url='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+commit+'/'+quote(name,safe='/')
        proc=subprocess.run(['C:/Windows/System32/curl.exe','--fail','--location','--silent','--show-error','--retry','2','--output',str(p),url],capture_output=True,timeout=240)
        assert proc.returncode==0,(name,proc.stderr.decode(errors='replace'))
        return p
    try:
        manifest_path='results/unified_exact_round152/public_manifest.json';mp=fetch(manifest_path)
        assert sha(mp)==sha(OUT/'public_manifest.json');manifest=read(mp)
        requested=list(manifest['files'])
        for a in manifest['archives']:requested += a['parts']+[a['member_index']]
        def get(record):
            p=fetch(record['path']);assert p.stat().st_size==record['bytes'] and sha(p)==record['SHA256'],record['path']
            return dict(path=record['path'],SHA256=sha(p),bytes=p.stat().st_size)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:downloaded=list(pool.map(get,requested))
        count=0;uncompressed=0
        for a in manifest['archives']:
            if len(a['parts'])==1:archive=dest/a['parts'][0]['path']
            else:
                archive=dest/'assembled'/a['name'];archive.parent.mkdir(exist_ok=True)
                with archive.open('xb') as stream:
                    for p in a['parts']:
                        with (dest/p['path']).open('rb') as part:shutil.copyfileobj(part,stream)
            assert sha(archive)==a['SHA256'] and archive.stat().st_size==a['bytes']
            index=load_gz(dest/a['member_index']['path'])
            with zipfile.ZipFile(archive) as z:
                assert sorted(z.namelist())==sorted(m['member'] for m in index)
                for member in index:
                    name=member['member'];safe(name);p=(dest/name).resolve();assert p.is_relative_to(dest)
                    data=z.read(name);assert len(data)==member['bytes'] and hashlib.sha256(data).hexdigest()==member['SHA256']
                    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);count+=1;uncompressed+=len(data)
        state.update(state='PASS',files=len(downloaded),archives=len(manifest['archives']),members=count,member_bytes=uncompressed,
                     IO_seconds=time.perf_counter()-tick,no_Optimize_compiler_Native_or_old_producer=True,
                     old_carriers_downloaded=0,manifest_SHA=sha(mp))
        write(dest/'restore_state.json',state);write(OUT/'public_restore_receipt.json',state)
        print(json.dumps(state),flush=True)
    except BaseException as exc:
        state.update(state='FAILED_PRESERVED',error=repr(exc),IO_seconds=time.perf_counter()-tick);write(dest/'restore_state.json',state)
        write(OUT/'public_restore_failure.json',state);raise

def stage():
    paths=read(OUT/'stage_paths.json')+['results/unified_exact_round152/stage_paths.json']
    for k in range(0,len(paths),30):subprocess.run(['git','add','--sparse','--force','--',*paths[k:k+30]],cwd=ROOT,check=True)
    print(json.dumps(dict(staged_paths=len(paths))),flush=True)

def cleanup():
    tick=time.perf_counter();before=shutil.disk_usage(WORK.anchor)
    areas=[OUT,WORK/'raw/round152',WORK/'temp/round152',WORK/'restore/round152-inherited']
    areas += sorted((WORK/'restore').glob('round152-public-*'))
    stats=[]
    for area in areas:
        if not area.exists():continue
        absolute=area.resolve();assert absolute.is_relative_to(WORK.resolve())
        files=[p for p in area.rglob('*') if p.is_file()]
        stats.append(dict(path=str(absolute),files=len(files),bytes=sum(p.stat().st_size for p in files),action='retained'))
    after=shutil.disk_usage(WORK.anchor)
    write(OUT/'cleanup_record.json',dict(UTC=utc(),current_round_only=True,deleted_paths=[],deleted_bytes=0,
          reason='Retain active tree, unique science and failures, exact source snapshots, runtime dependencies and accepted public recovery. Zero deletion is permitted; no old-history authorization is inferred.',
          retained=stats,volume_before=dict(total=before.total,used=before.used,free=before.free),
          volume_after=dict(total=after.total,used=after.used,free=after.free),observed_free_change=after.free-before.free,
          no_recursive_delete_or_move=True,metadata_IO_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(deleted_bytes=0,retained_bytes=sum(s['bytes'] for s in stats),observed_free_change=after.free-before.free)),flush=True)

if __name__=='__main__':
    {'pack':pack,'restore':lambda:restore(sys.argv[2]),'stage':stage,'cleanup':cleanup}[sys.argv[1]]()
