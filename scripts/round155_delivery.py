"""Round155-only carriers and bounded anonymous recovery of their exact bytes.

Inherited Q/pools/inputs/source stay fixed-commit references. No historical
carrier, runtime, producer or compiler is included or invoked.
"""
import inspect,zipfile
import round153_delivery as previous
from round155_common import *

HEAVY={'coupled','support_LP','qualification','fees','engineering','infra','campaign_confirmation','directions','fixed_prices'}
EXCLUDED={'carrier_manifest.json','public_manifest.json','public_restore_receipt.json','public_restore_failure.json',
          'publication.json','cleanup_record.json','RESUME.md','pr_body.md','stage_paths.json',
          'stage_verification.json','final_protection_readback.json'}
safe=previous.safe

def serial_idle():
    from round100_idle import ensure_idle
    configure();ensure_idle()
    assert not budget()['unclosed'],'serialize public I/O after all experiments and audits'


def protected_later():
    record=read(OUT/'review/later_protected_bytes.json')
    assert record['pre_task_byte_snapshot_available'] is False
    assert record['not_a_claim_of_pre_task_byte_equality'] is True
    for item in record['files']:
        assert sha(Path(item['root'])/item['path'])==item['SHA256'],('later protected bytes changed',item['root'],item['path'])
    return record


def pack():
    serial_idle()
    protected_later()
    assert read(OUT/'candidate_decision.json')['study_complete']
    review=read(OUT/'review/final_scientific_review.json')
    assert review['disposition']=='ACCEPT_COMPLETE_ROUND155' and not review['scientific_blockers']
    tick=time.perf_counter();art=OUT/'artifacts';art.mkdir(exist_ok=True);groups={};assigned=set()
    for role in ['N-B35-S','K-35-U','N-C20-U']:
        members=[]
        for name in ['coupled','support_LP']:
            for folder in (OUT/name).glob(role+'*'):
                members.extend(p for p in folder.rglob('*') if p.is_file())
        for direction in (OUT/'directions').glob('*/direction.json'):
            if read(direction)['role']!=role:continue
            members.extend(p for p in direction.parent.rglob('*') if p.is_file())
            members.extend(p for p in (OUT/'fixed_prices'/direction.parent.name).rglob('*') if p.is_file())
        if members:groups['research_'+role]=members;assigned.update(members)
    groups['qualification_failures_and_fees']=[p for name in HEAVY-{'campaign_confirmation'} for p in (OUT/name).rglob('*')
        if p.is_file() and p not in assigned]
    for camp in sorted((OUT/'campaign_confirmation').glob('*')):
        if camp.is_dir():groups['complete_arm_'+camp.name]=[p for p in camp.rglob('*') if p.is_file()]
    archives=[];seen=set()
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
    thin+=list((ROOT/'scripts').glob('round155*.py'))
    for name in ['.gitattributes','.gitignore','docs/round155_research.md','docs/current_mainline.md',
                 'docs/unified_exact_research_index.md','docs/paper_review.md']:
        if (ROOT/name).is_file():thin.append(ROOT/name)
    files=[dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),bytes=p.stat().st_size) for p in sorted(set(thin))]
    write(OUT/'public_manifest.json',dict(UTC=utc(),schema='round155-new-only-fixed-commit-v1',files=files,archives=archives,
        reference_index='results/unified_exact_round155/reuse_index.json',
        inherited_member_recovery='Use the fixed R153/R154 science/member/source hashes in reuse_index; this current-only recovery downloads no old carrier.',
        forbidden_operations=['Optimize','compile','old producer','delete','move'],pack_IO_seconds=time.perf_counter()-tick))
    paths=[f['path'] for f in files]+[(OUT/name).relative_to(ROOT).as_posix()
        for name in ['carrier_manifest.json','public_manifest.json','RESUME.md']]
    for archive in archives:paths+=[archive['member_index']['path']]+[p['path'] for p in archive['parts']]
    write(OUT/'stage_paths.json',paths)
    print(json.dumps(dict(archives=len(archives),members=len(seen),compressed_bytes=sum(a['bytes'] for a in archives),
        thin_files=len(files),IO_seconds=time.perf_counter()-tick)),flush=True)

def inherited_function(name,*args):
    source=inspect.getsource(getattr(previous,name)).replace('round153','round155').replace('Round153','Round155')
    namespace=dict(vars(previous),ROOT=ROOT,WORK=WORK,OUT=OUT)
    exec(compile(source,__file__+'::'+name,'exec'),namespace)
    return namespace[name](*args)

def restore(commit):
    serial_idle()
    return inherited_function('restore',commit)

def stage():
    serial_idle()
    tick=time.perf_counter();protection=protected_later()
    paths=read(OUT/'stage_paths.json')+['results/unified_exact_round155/stage_paths.json']
    protected={item['path'] for item in protection['files'] if Path(item['root']).resolve()==ROOT.resolve()}
    assert not set(paths)&protected
    permitted={'.gitattributes','.gitignore','docs/round155_research.md','docs/current_mainline.md',
               'docs/unified_exact_research_index.md','docs/paper_review.md'}
    for name in paths:
        safe(name)
        assert name in permitted or name.startswith(('results/unified_exact_round155/','scripts/round155'))
    already=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
    assert set(already)<=set(paths),('unrelated staged files must be preserved',already)
    for index in range(0,len(paths),30):
        subprocess.run(['git','add','--sparse','--force','--',*paths[index:index+30]],cwd=ROOT,check=True)
    manifest=read(OUT/'public_manifest.json');records=list(manifest['files'])
    for archive in manifest['archives']:records+=archive['parts']+[archive['member_index']]
    for name in ['carrier_manifest.json','public_manifest.json','RESUME.md','stage_paths.json']:
        path=OUT/name;records.append(dict(path=path.relative_to(ROOT).as_posix(),SHA256=sha(path),bytes=path.stat().st_size))
    for item in records:
        raw=subprocess.check_output(['git','show',':'+item['path']],cwd=ROOT)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['SHA256'],('staged blob bytes differ',item['path'])
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
    assert set(staged)<=set(paths) and not set(staged)&protected
    protected_later()
    result=dict(UTC=utc(),PASS=True,staged_paths=staged,verified_manifest_and_metadata_blobs=len(records),
        public_manifest_SHA=sha(OUT/'public_manifest.json'),protected_snapshot_SHA=sha(OUT/'review/later_protected_bytes.json'),
        pre_task_byte_snapshot_available=False,all_actual_index_blob_bytes_equal_declared_bytes=True,
        no_preexisting_status_path_staged=True,IO_seconds=time.perf_counter()-tick)
    write(OUT/'stage_verification.json',result)
    print(json.dumps(dict(PASS=True,staged_paths=len(staged),verified_blobs=len(records),IO_seconds=result['IO_seconds'])),flush=True)

def cleanup():
    serial_idle()
    assert read(OUT/'public_restore_receipt.json')['state']=='PASS'
    assert read(OUT/'publication.json')['draft'] is True
    protected_later();inherited_function('cleanup');record=protected_later()
    write(OUT/'final_protection_readback.json',dict(UTC=utc(),PASS=True,
        later_snapshot_SHA=sha(OUT/'review/later_protected_bytes.json'),files=len(record['files']),
        pre_task_byte_snapshot_available=False,bytes_equal_later_snapshot=True,
        no_claim_of_unavailable_pre_task_byte_comparison=True))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
