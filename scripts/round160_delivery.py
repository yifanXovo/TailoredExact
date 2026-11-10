"""Current-round-only safe carrier, staged-byte manifest, finite public recovery."""
import shutil,zipfile,urllib.request,urllib.parse
from pathlib import PurePosixPath
from round160_common import *

PRIVATE={'infra/protected_initial.json','infra/protected_status_bytes.json'}
RAW_DIRS=('runs','qualification','engineering','fees','inputs')
REPO='https://raw.githubusercontent.com/yifanXovo/TailoredExact'

def closed():
    configure();assert read(OUT/'final_review.json')['PASS']
    assert all(p['label']==os.environ.get('ROUND140_METERED_PARENT_LABEL') for p in budget()['unclosed'])

def safe_file(path):
    assert path.resolve().is_relative_to(OUT.resolve())
    rel=path.relative_to(OUT).as_posix()
    current=os.environ.get('ROUND140_METERED_PARENT_LABEL')
    if current and rel.startswith('fees/'+current+'/'):return False
    if rel in PRIVATE:return False
    if path.suffix.lower() in ('.exe','.dll','.o','.a','.lib','.lic','.key','.pem','.pfx'):return False
    if path.name=='.env' or path.name.endswith('.tmp'):return False
    if rel.startswith('inputs/') and path.name in ('instance.txt','parent.json'):return False
    return True

def package():
    closed();art=OUT/'artifacts';art.mkdir(exist_ok=True)
    assert not list(art.glob('*.zip'))
    sets=[('new_core',[p for name in RAW_DIRS for p in (OUT/name).rglob('*') if p.is_file() and safe_file(p)])]
    for group in sorted((OUT/'campaign_confirmation').iterdir()):
        if group.is_dir():sets.append(('complete_'+group.name,[p for p in group.rglob('*') if p.is_file() and safe_file(p)]))
    records=[]
    # New evidence only; old archive/runtime assets are never copied.
    for label,files in sets:
        members=[];target=art/(label+'.zip')
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            for p in sorted(set(files)):
                name=p.relative_to(ROOT).as_posix();z.write(p,name)
                members.append(dict(member=name,SHA256=sha(p),bytes=p.stat().st_size))
        assert target.stat().st_size<95000000,'split a new carrier before staging; do not commit oversized files'
        write(art/(label+'.members.json'),members)
        records.append(dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size,
            members=len(members),uncompressed_bytes=sum(x['bytes'] for x in members),
            index=(art/(label+'.members.json')).relative_to(ROOT).as_posix()))
    reused=[]
    matrix=read(OUT/'confirmation_matrix.json')
    for role in sorted({g['launch']['id'] for g in matrix['groups']}):
        group=next(g for g in matrix['groups'] if g['launch']['id']==role)
        original=read(OUT/group['group']/'identity.json')['original_frozen_launch']['panel']
        reused.append(dict(role=role,commit=BASE,path=original['input_path'],SHA256=original['input_sha256'],
            destination=f'results/unified_exact_round160/inputs/{role}/instance.txt'))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),archives=records,reused_fixed_input_blobs=reused,
        commercial_runtime_or_credentials_included=False,project_PE_retained_locally=True,
        private_protected_user_metadata_not_published=sorted(PRIVATE),new_only=True))
    print(json.dumps(records),flush=True)

def manifest():
    closed();paths=git('diff','--cached','--name-only',BASE).decode().splitlines();files=[]
    for name in paths:
        if name=='results/unified_exact_round160/public_manifest.json':continue
        if name.startswith('results/unified_exact_round160/artifacts/') and name.endswith('.zip'):continue
        raw=git('show',':'+name)
        assert not name.endswith(('.exe','.dll','.lic','.key','.pem'))
        files.append(dict(path=name,SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
    carriers=read(OUT/'carrier_manifest.json')
    write(OUT/'public_manifest.json',dict(schema='round160-public-staged-content-v1',UTC=utc(),files=files,
        archives=carriers['archives'],reused_fixed_input_blobs=carriers['reused_fixed_input_blobs'],
        actual_index_bytes=True,manifest_self_excluded=True,source_CPP_commit=read(OUT/'candidate_manifest.json')['source_commit'],
        source_dependency=BASE,old_carrier_downloads_required=0,new_Optimize_on_recovery=0))

def download(commit,name):
    url=REPO+'/'+commit+'/'+urllib.parse.quote(name,safe='/')
    request=urllib.request.Request(url,headers={'User-Agent':'Round160-finite-anonymous-recovery'})
    with urllib.request.urlopen(request,timeout=60) as response:return response.read()

def restore(science):
    configure();expected=read(OUT/'public_manifest.json')
    folder=WORK/'restore'/('round160_'+science[:12]);folder.mkdir(parents=True,exist_ok=False)
    source=download(science,'results/unified_exact_round160/public_manifest.json')
    assert json.loads(source)==expected
    (folder/'public_manifest.json').write_bytes(source)
    downloaded=members=member_bytes=0
    for item in expected['files']:
        raw=download(science,item['path']);assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['SHA256']
        dest=folder/'root'/item['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);downloaded+=1
    for item in expected['reused_fixed_input_blobs']:
        raw=download(item['commit'],item['path']);assert hashlib.sha256(raw).hexdigest()==item['SHA256']
        dest=folder/'root'/item['destination'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);downloaded+=1
    for archive in expected['archives']:
        raw=download(science,archive['path']);assert len(raw)==archive['bytes'] and hashlib.sha256(raw).hexdigest()==archive['SHA256']
        path=folder/Path(archive['path']).name;path.write_bytes(raw);downloaded+=1
        index=read(folder/'root'/archive['index']);by={x['member']:x for x in index}
        with zipfile.ZipFile(path) as z:
            assert set(z.namelist())==set(by)
            for name in z.namelist():
                parts=PurePosixPath(name).parts
                assert '..' not in parts and not PurePosixPath(name).is_absolute()
                assert name.startswith('results/unified_exact_round160/')
                body=z.read(name);item=by[name]
                assert len(body)==item['bytes'] and hashlib.sha256(body).hexdigest()==item['SHA256']
                dest=folder/'root'/Path(*parts);assert dest.resolve().is_relative_to((folder/'root').resolve())
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body);members+=1;member_bytes+=len(body)
    write(OUT/'public_restore_receipt.json',dict(UTC=utc(),PASS=True,science_commit=science,root=str(folder),
        anonymous=True,downloaded=downloaded,archives=len(expected['archives']),members=members,member_bytes=member_bytes,
        old_carrier_downloads=0,fixed_old_input_blobs=4,Optimize=0,compilation=0,
        source_and_new_evidence_only=True,public_manifest_SHA=hashlib.sha256(source).hexdigest()))

def cleanup(pr_url):
    assert read(OUT/'public_restore_receipt.json')['PASS']
    before=shutil.disk_usage(WORK).free;files=[p for p in OUT.rglob('*') if p.is_file()]
    bytes_total=sum(p.stat().st_size for p in files)
    protected=read(OUT/'infra/protected_status_bytes.json');count=0
    for tree in protected['trees']:
        for name,info in tree['files'].items():assert sha(Path(tree['tree'])/name)==info['SHA256'];count+=1
    after=shutil.disk_usage(WORK).free
    write(OUT/'cleanup_record.json',dict(UTC=utc(),PR=pr_url,bounded_scope=str(OUT),screened_files=len(files),
        screened_file_bytes=bytes_total,deleted_files=0,deleted_file_bytes=0,
        observed_free_bytes_before=before,observed_free_bytes_after=after,observed_space_change=after-before,
        reason='Retain the active tree, unique science/failures, required measured runtime and accepted recovery; zero deletion is permitted',
        retained_runtime='local only; no commercial DLL/credentials published',protected_raw_dirty_files_unchanged=count,
        old_round_deletions=0,global_settings_changes=0,actual_cleanup_complete=True))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
