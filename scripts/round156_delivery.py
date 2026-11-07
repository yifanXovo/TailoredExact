"""New-only public carriers and bounded recovery; never replay old producers."""
import inspect,zipfile,shutil
import round153_delivery as previous
from round156_common import *

HEAVY={'oracle','producer_checks','qualification','campaign_confirmation','fees','engineering','infra'}
EXCLUDED={'carrier_manifest.json','public_manifest.json','public_restore_receipt.json','public_restore_failure.json',
    'publication.json','cleanup_record.json','RESUME.md','pr_body.md','stage_paths.json','stage_verification.json','final_protection_readback.json'}
safe=previous.safe

def serial_idle():
    from round100_idle import ensure_idle
    configure();ensure_idle();assert not budget()['unclosed']

def protect():
    initial=read(OUT/'infra/protected_initial.json')
    for r in initial:assert sha(Path(r['tree'])/r['relative'])==r['sha256'],r
    return initial

def pack():
    serial_idle();protect()
    assert read(OUT/'final_decision.json')['study_complete']
    review=read(OUT/'review/final_scientific_review.json')
    assert review['disposition']=='ACCEPT_COMPLETE_ROUND156' and not review['scientific_blockers']
    tick=time.perf_counter();art=OUT/'artifacts';art.mkdir(exist_ok=True)
    groups={'inventory_oracles':[p for p in (OUT/'oracle').rglob('*') if p.is_file()],
        'qualification_failures_fees':[p for name in HEAVY-{'oracle','campaign_confirmation'} for p in (OUT/name).rglob('*') if p.is_file()]}
    for camp in sorted((OUT/'campaign_confirmation').iterdir()):
        if camp.is_dir():groups['complete_arm_'+camp.name]=[p for p in camp.rglob('*') if p.is_file()]
    seen=set();archives=[]
    for label,files in groups.items():
        if not files:continue
        dest=art/(label+'.zip');assert not dest.exists();members=[]
        with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for path in sorted(set(files)):
                name=path.relative_to(ROOT).as_posix();safe(name);assert name not in seen;seen.add(name)
                data=path.read_bytes();archive.writestr(name,data)
                members.append(dict(member=name,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        index=art/(label+'.members.json.gz');save_gz(index,members);parts=[]
        if dest.stat().st_size>40*1024*1024:
            with dest.open('rb') as stream:
                number=0
                while True:
                    data=stream.read(32*1024*1024)
                    if not data:break
                    number+=1;part=dest.with_name(dest.name+f'.part{number:03}')
                    with part.open('xb') as output:output.write(data)
                    parts.append(dict(path=part.relative_to(ROOT).as_posix(),SHA256=sha(part),bytes=len(data)))
        else:parts=[dict(path=dest.relative_to(ROOT).as_posix(),SHA256=sha(dest),bytes=dest.stat().st_size)]
        archives.append(dict(name=dest.name,SHA256=sha(dest),bytes=dest.stat().st_size,parts=parts,
            member_index=dict(path=index.relative_to(ROOT).as_posix(),SHA256=sha(index),bytes=index.stat().st_size),
            members=len(members),uncompressed_bytes=sum(m['bytes'] for m in members)))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),archives=archives,old_carriers_repacked=0,
        unique_raw_retained=True,all_failures_preserved=True,pack_IO_seconds=time.perf_counter()-tick))
    thin=[p for p in OUT.rglob('*') if p.is_file() and p.relative_to(OUT).parts[0] not in HEAVY|{'artifacts'} and p.name not in EXCLUDED]
    thin+=list((ROOT/'scripts').glob('round156*.py'))
    for name in ['.gitattributes','.gitignore','include/Round153Research.hpp','src/main.cpp',
        'config/gi_tbc_proof_floor_round156.json','docs/round156_research.md','docs/current_mainline.md',
        'docs/unified_exact_research_index.md','docs/paper_review.md']:
        if (ROOT/name).is_file():thin.append(ROOT/name)
    files=[dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),bytes=p.stat().st_size) for p in sorted(set(thin))]
    write(OUT/'public_manifest.json',dict(UTC=utc(),schema='round156-new-only-fixed-commit-v1',files=files,archives=archives,
        original_workspace=str(ROOT),reference_index='results/unified_exact_round156/reuse_index.json',
        inherited_member_recovery='Use fixed R137/R154/R155 commit/member hashes; this current-only recovery downloads no old carriers.',
        forbidden_operations=['Optimize','compile','old producer','delete','move'],pack_IO_seconds=time.perf_counter()-tick))
    paths=[f['path'] for f in files]+[(OUT/name).relative_to(ROOT).as_posix() for name in ['carrier_manifest.json','public_manifest.json','RESUME.md']]
    for a in archives:paths+=[a['member_index']['path']]+[p['path'] for p in a['parts']]
    write(OUT/'stage_paths.json',paths)
    print(json.dumps(dict(archives=len(archives),members=len(seen),compressed_bytes=sum(a['bytes'] for a in archives),thin_files=len(files))),flush=True)

def restore(commit):
    serial_idle()
    source=inspect.getsource(previous.restore).replace('round153','round156').replace('Round153','Round156')
    source=source.replace('max_workers=4','max_workers=1')
    ns=dict(vars(previous),ROOT=ROOT,OUT=OUT,WORK=WORK,safe=safe)
    exec(compile(source,__file__+'::bounded_public_restore','exec'),ns)
    return ns['restore'](commit)

def stage():
    serial_idle();paths=read(OUT/'stage_paths.json')+['results/unified_exact_round156/stage_paths.json']
    for k in range(0,len(paths),30):
        subprocess.run(['git','add','--sparse','--force','--',*paths[k:k+30]],cwd=ROOT,check=True)
    facts=[]
    for path in paths:
        data=subprocess.check_output(['git','show',':'+path],cwd=ROOT)
        assert hashlib.sha256(data).hexdigest()==sha(ROOT/path),path
        facts.append(dict(path=path,SHA256=sha(ROOT/path),bytes=len(data)))
    write(OUT/'stage_verification.json',dict(PASS=True,files=facts,exact_index_blobs=True))
    print(json.dumps(dict(staged_paths=len(paths),exact_blobs=True)),flush=True)

def cleanup():
    serial_idle();initial=protect();assert read(OUT/'public_restore_receipt.json')['state']=='PASS'
    tick=time.perf_counter();before=shutil.disk_usage(WORK.anchor)
    areas=[OUT,WORK/'raw/round156',WORK/'temp/round156',WORK/'build-cache/round156']
    areas+=sorted((WORK/'restore').glob('round156-public-*'));stats=[]
    for area in areas:
        if not area.exists():continue
        absolute=area.resolve();assert absolute.is_relative_to(WORK.resolve())
        files=[p for p in area.rglob('*') if p.is_file()]
        stats.append(dict(path=str(absolute),files=len(files),bytes=sum(p.stat().st_size for p in files),action='retained'))
    after=shutil.disk_usage(WORK.anchor)
    write(OUT/'cleanup_record.json',dict(UTC=utc(),current_round_only=True,deleted_paths=[],deleted_bytes=0,
        reason='Retain active tree, unique science/failures, exact source snapshots, required PE/DLL and accepted recovery; zero deletion is permitted.',
        retained=stats,volume_before=dict(total=before.total,used=before.used,free=before.free),
        volume_after=dict(total=after.total,used=after.used,free=after.free),observed_free_change=after.free-before.free,
        no_recursive_delete_or_move=True,metadata_IO_seconds=time.perf_counter()-tick))
    write(OUT/'final_protection_readback.json',dict(PASS=True,files=len(initial),initial_snapshot_SHA=sha(OUT/'infra/protected_initial.json'),
        checked_after_public_restore=True,untracked_user_trees_untouched=True))
    print(json.dumps(dict(deleted_bytes=0,protected=len(initial),retained_bytes=sum(s['bytes'] for s in stats))),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
