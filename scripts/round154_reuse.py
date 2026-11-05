"""Small fixed metadata hydration and old-carrier member references only."""
from round154_common import *

METADATA=['goal.md','final_report.md','mathematical_analysis.md','deepening_plan.md','candidate_decision.json',
          'reports/scientific_table.json','reports/complete_pairs.json','reports/coupled_iterations.csv','reports/pricing_results.json',
          'review/final_scientific_review.md','cost_report.json','source_manifest.json','reuse_index.json','RESUME.md',
          'helper_manifest.json','candidate_manifest.json','carrier_manifest.json','public_manifest.json']

def hydrate():
    configure();assert not budget()['unclosed'],'metadata checkout is serial with experiments'
    tick=time.perf_counter();paths=['results/unified_exact_round153/'+p for p in METADATA];before={}
    for name in paths:
        p=ROOT/name;raw=subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
        expected=hashlib.sha256(raw).hexdigest()
        if p.exists():assert sha(p)==expected,('protect nonmatching historical metadata',name)
        before[name]=dict(existed=p.exists(),SHA256=expected,bytes=len(raw))
    command=['git','sparse-checkout','add','--stdin']
    assert sum(r['bytes'] for r in before.values())<50*1024*1024,'small metadata only, never old archives'
    result=subprocess.run(command,input='\n'.join('/'+p for p in paths)+'\n',cwd=ROOT,text=True,capture_output=True,check=True)
    for name,record in before.items():assert sha(ROOT/name)==record['SHA256']
    write(OUT/'infra/sparse_metadata_restore.json',dict(UTC=utc(),paths=before,
        reason='Adding the current round to the existing sparse definition de-materialized clean old metadata outside its prior patterns; restore only exact fixed metadata, retain all unique raw and shared Git history.',
        seconds=time.perf_counter()-tick,Native_Optimize=0,old_archives_materialized=0,no_user_file_overwritten=True,
        stdout=result.stdout,stderr=result.stderr,public_IO_separate=True))

def index():
    configure();assert not budget()['unclosed'];tick=time.perf_counter()
    manifest=read(OLD153/'public_manifest.json');thin={r['path']:r for r in manifest['files']};members={}
    for archive in manifest['archives']:
        rec=archive['member_index'];p=ROOT/rec['path']
        raw=p.read_bytes() if p.exists() else subprocess.check_output(['git','show',SCIENCE153+':'+rec['path']],cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest()==rec['SHA256']
        for item in json.loads(gzip.decompress(raw)):
            members[item['member']]=dict(item,commit=SCIENCE153,archive=archive['name'],archive_SHA256=archive['SHA256'],
                archive_parts=archive['parts'],member_index=rec)
    needed={('results/unified_exact_round153/'+p) for p in METADATA if p not in ('RESUME.md',)}
    for p in (OUT/'directions').glob('*/direction.json'):
        d=read(p)
        for value in [d['prior_result'],d['Q_path']]+([str(Path(d['source_iteration'])/'certificate.json.gz')] if d['source_iteration'] else []):
            q=Path(value).resolve()
            if OLD153.resolve() in q.parents:needed.add(q.relative_to(ROOT).as_posix())
        for record in d['inherited_price_sources']:
            q=Path(record['path']).resolve()
            if OLD153.resolve() in q.parents:needed.add(q.relative_to(ROOT).as_posix())
    for row in read(OLD153/'reports/scientific_table.json')['rows']:
        needed.add(row['coupled_result']);needed.add(row['support_result'])
    records=[]
    for name in sorted(needed):
        if name in thin:r=dict(thin[name],commit=SCIENCE153,resolution='fixed Git file')
        elif name in members:r=dict(members[name],resolution='fixed archive member')
        else:
            # The manifest and carrier index are fixed Git files intentionally
            # omitted from their own self-referential public file list.
            raw=subprocess.check_output(['git','show',SCIENCE153+':'+name],cwd=ROOT)
            r=dict(path=name,SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),commit=SCIENCE153,resolution='fixed Git metadata')
        p=ROOT/name
        if p.exists():assert sha(p)==r['SHA256'],name
        r['member']=name;records.append(r)
    candidate=read(OUT/'candidate_manifest.json');old_candidate=read(OLD153/'candidate_manifest.json');source=[]
    for name,digest in candidate['source_hashes'].items():
        if old_candidate['source_hashes'].get(name)==digest:
            source.append(dict(path=name,SHA256=digest,commit=BASE,resolution='unchanged fixed source, not repacked'))
    for name,digest in read(OUT/'helper_manifest.json')['helper_dependencies'].items():
        source.append(dict(path=name,SHA256=digest,commit=BASE,resolution='unchanged own-root helper source, not repacked'))
    value=dict(UTC=utc(),fixed_R153_science=SCIENCE153,verified_review_head=BASE,
        R153_public_manifest=dict(path='results/unified_exact_round153/public_manifest.json',commit=SCIENCE153,SHA256=sha(OLD153/'public_manifest.json')),
        dependencies=records,unchanged_sources=source,prior_transitive_index=dict(path='results/unified_exact_round153/reuse_index.json',
            commit=SCIENCE153,SHA256=sha(OLD153/'reuse_index.json')),
        old_archives_repacked=0,old_archive_members_downloaded=0,seconds=time.perf_counter()-tick,
        external_runtime=dict(python=str(PYTHON),DLL=str(DLL),DLL_SHA=DLL_SHA,necessary_local_PE_retained=True))
    write(OUT/'reuse_index.json',value);print(json.dumps(dict(dependencies=len(records),sources=len(source),old_repacked=0)),flush=True)

def carrier_availability():
    """Repair only missing fixed R153 compressed carriers after sparse reapply."""
    configure();assert not budget()['unclosed'];tick=time.perf_counter()
    manifest=read(OLD153/'public_manifest.json');records=[]
    for archive in manifest['archives']:
        for rec in archive['parts']+[archive['member_index']]:
            p=ROOT/rec['path'];assert p.resolve().is_relative_to(OLD153.resolve())
            existed=p.exists()
            if not existed:
                p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as stream:
                    done=subprocess.run(['git','show',SCIENCE153+':'+rec['path']],cwd=ROOT,stdout=stream,stderr=subprocess.PIPE)
                assert done.returncode==0,(rec['path'],done.stderr.decode(errors='replace'))
            assert p.stat().st_size==rec['bytes'] and sha(p)==rec['SHA256'],('protect nonmatching historical carrier',rec['path'])
            records.append(dict(rec,action='retained_verified' if existed else 'restored_exact_from_shared_Git'))
    write(OUT/'infra/historical_carrier_availability.json',dict(UTC=utc(),fixed_science=SCIENCE153,records=records,
        restored_bytes=sum(r['bytes'] for r in records if r['action']=='restored_exact_from_shared_Git'),
        archives=len(manifest['archives']),seconds=time.perf_counter()-tick,Native_Optimize=0,old_archives_repacked=0,
        old_network_downloads=0,no_delete_or_move=True,no_user_file_overwritten=True,public_IO_separate=True,
        scope='Bounded repair/check of the twelve R153 compressed carriers, without old producers or old member extraction'))
    print(json.dumps(dict(archives=len(manifest['archives']),restored_bytes=sum(r['bytes'] for r in records if r['action']=='restored_exact_from_shared_Git'),
                         old_network_downloads=0,seconds=time.perf_counter()-tick)),flush=True)

def history_metadata_availability():
    """Restore missing thin adjacent-history records, never raw or archives."""
    configure();assert not budget()['unclosed'];tick=time.perf_counter()
    roots=[f'results/unified_exact_round{n}' for n in range(136,154)]
    raw=subprocess.check_output(['git','ls-tree','-r','-l','-z',BASE,'--',*roots],cwd=ROOT)
    missing=[]
    for entry in raw.split(b'\0'):
        if not entry:continue
        header,name=entry.split(b'\t',1);mode,kind,blob,size=header.decode().split();name=name.decode('utf-8')
        parts=Path(name).parts
        thin=len(parts)==3 or len(parts)==4 and parts[2] in ('reports','review')
        if not thin or mode not in ('100644','100755') or int(size)>10*1024*1024:continue
        p=ROOT/name
        if p.exists():continue
        missing.append(dict(path=name,bytes=int(size),git_blob=blob))
    assert sum(r['bytes'] for r in missing)<50*1024*1024,'bounded thin records only'
    for record in missing:
        p=ROOT/record['path'];assert p.resolve().is_relative_to((ROOT/'results').resolve());p.parent.mkdir(parents=True,exist_ok=True)
        data=subprocess.check_output(['git','show',BASE+':'+record['path']],cwd=ROOT)
        assert len(data)==record['bytes'];record['SHA256']=hashlib.sha256(data).hexdigest()
        with p.open('xb') as stream:stream.write(data)
    write(OUT/'infra/historical_metadata_availability.json',dict(UTC=utc(),commit=BASE,restored=missing,
        bytes=sum(r['bytes'] for r in missing),seconds=time.perf_counter()-tick,Native_Optimize=0,
        only_missing_thin_files=True,no_existing_file_overwritten=True,no_raw_or_archive_materialization=True,
        old_status_files_are_historical_not_active=True,public_IO_separate=True))
    print(json.dumps(dict(restored_files=len(missing),bytes=sum(r['bytes'] for r in missing),seconds=time.perf_counter()-tick)),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
