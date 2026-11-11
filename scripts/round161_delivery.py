"""New-only carrier, staged public hashes, one bounded anonymous restore, zero deletion."""
from round161_common import *
import shutil,zipfile,urllib.request,urllib.parse

PRIVATE={'infra/protected_initial.json'}
RAW=('runs','qualification','fees','launches','engineering')
REMOTE='https://raw.githubusercontent.com/yifanXovo/TailoredExact'

def package():
    assert read(OUT/'final_review.json')['PASS'] and not budget()['unclosed']
    folder=OUT/'artifacts';folder.mkdir(exist_ok=True);archive=folder/'new_evidence.zip';assert not archive.exists()
    members=[]
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for base in RAW:
            for p in sorted((OUT/base).rglob('*')):
                if not p.is_file():continue
                assert p.resolve().is_relative_to(OUT.resolve())
                if p.suffix.lower() in ('.exe','.dll','.o','.a','.lic','.key','.pem','.pfx'):continue
                name=p.relative_to(ROOT).as_posix();z.write(p,name)
                members.append(dict(member=name,SHA256=sha(p),bytes=p.stat().st_size))
    write(folder/'new_evidence.members.json',members)
    inputs=read(OUT/'input_manifest.json')
    reused=[dict(commit=BASE,path=r['input_path'],SHA256=r['input_SHA'],destination=f"results/unified_exact_round161/inputs/{r['role']}/instance.txt") for r in inputs['roles']]
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),new_only=True,archives=[dict(path=archive.relative_to(ROOT).as_posix(),SHA256=sha(archive),bytes=archive.stat().st_size,
        members=len(members),uncompressed_bytes=sum(x['bytes'] for x in members),index=(folder/'new_evidence.members.json').relative_to(ROOT).as_posix())],
        reused_inputs=reused,offline_parent_reference='input_manifest.json fixed R160 archive/member/SHA; same fleet is in new journal witness events',
        runtime='Measured PE retained locally; commercial Gurobi runtime/licence/credentials excluded',private_excluded=sorted(PRIVATE)))

def manifest():
    names=git('diff','--cached','--name-only',BASE).decode().splitlines();items=[]
    for name in names:
        if name=='results/unified_exact_round161/public_manifest.json' or name.endswith('.zip'):continue
        assert not name.endswith(('.exe','.dll','.lic','.key','.pem','.pfx')) and not any(name.endswith(p) for p in PRIVATE)
        raw=git('show',':'+name);items.append(dict(path=name,bytes=len(raw),SHA256=hashlib.sha256(raw).hexdigest()))
    carrier=read(OUT/'carrier_manifest.json')
    write(OUT/'public_manifest.json',dict(UTC=utc(),files=items,archives=carrier['archives'],reused_inputs=carrier['reused_inputs'],
        measured_CPP_commit=read(OUT/'measured_manifest.json')['verified_CPP_commit'],dependency=BASE,
        staged_bytes=True,self_excluded=True,old_archives_downloaded_on_restore=0,new_Optimize_on_restore=0))

def fetch(commit,path):
    request=urllib.request.Request(REMOTE+'/'+commit+'/'+urllib.parse.quote(path,safe='/'),headers={'User-Agent':'Round161-bounded-public-recovery'})
    with urllib.request.urlopen(request,timeout=60) as response:return response.read()

def restore(commit):
    began=time.perf_counter();target=WORK/'restore'/('round161_'+commit[:12]);target.mkdir(parents=True,exist_ok=False)
    expected=read(OUT/'public_manifest.json');public=fetch(commit,'results/unified_exact_round161/public_manifest.json')
    assert json.loads(public)==expected;(target/'public_manifest.json').write_bytes(public)
    count=total=members=0
    for item in expected['files']+expected['reused_inputs']:
        raw=fetch(item.get('commit',commit),item['path']);assert hashlib.sha256(raw).hexdigest()==item['SHA256']
        if 'bytes' in item:assert len(raw)==item['bytes']
        p=target/'root'/item.get('destination',item['path']);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);count+=1;total+=len(raw)
    for item in expected['archives']:
        raw=fetch(commit,item['path']);assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['SHA256']
        p=target/Path(item['path']).name;p.write_bytes(raw);count+=1;total+=len(raw)
        index=read(target/'root'/item['index']);lookup={x['member']:x for x in index}
        with zipfile.ZipFile(p) as z:
            assert len(z.namelist())==len(lookup)==item['members']
            for name in z.namelist():
                raw=z.read(name);ref=lookup[name];assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['SHA256']
                dest=(target/'root'/name).resolve();assert dest.is_relative_to((target/'root').resolve())
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);members+=1
    write(OUT/'public_restore_receipt.json',dict(PASS=True,UTC=utc(),science_commit=commit,target=str(target),anonymous=True,files_downloaded=count,
        bytes_downloaded=total,archive_members=members,old_archives_downloaded=0,Optimize=0,commercial_runtime_downloaded=False,
        elapsed_seconds=time.perf_counter()-began,category='public I/O; excluded from scientific meter'))

def cleanup():
    before=shutil.disk_usage(WORK).free;items=[];limit=100000
    bases=[OUT,BUILD,WORK/'temp/round161',WORK/'temp/round161_plot_deps',WORK/'temp/round161_plot_config']
    if (OUT/'public_restore_receipt.json').exists():
        recovered=Path(read(OUT/'public_restore_receipt.json')['target']).resolve()
        assert recovered.is_relative_to((WORK/'restore').resolve()) and recovered.name.startswith('round161_')
        bases.append(recovered)
    for base in bases:
        if not base.exists():continue
        assert base.resolve().is_relative_to(WORK.resolve())
        for p in base.rglob('*'):
            if p.is_file():
                items.append(dict(root=str(base),bytes=p.stat().st_size));assert len(items)<=limit
    protected=read(OUT/'infra/protected_initial.json');dirty=0
    for tree in protected['trees']:
        for name,h in tree['dirty'].items():assert sha(Path(tree['tree'])/name)==h;dirty+=1
    after=shutil.disk_usage(WORK).free
    write(OUT/'cleanup_record.json',dict(UTC=utc(),screening='bounded metadata only for R161 output/build/temp/plot dependencies/current public recovery; no old-round enumeration/deletion',
        screened_roots=[str(p) for p in bases],
        screening_file_limit=limit,screened_files=len(items),screened_file_bytes=sum(i['bytes'] for i in items),deleted_files=0,deleted_file_bytes=0,
        free_bytes_before=before,free_bytes_after=after,observed_free_change=after-before,protected_dirty_hashes_unchanged=dirty,
        retained='Unique raw science, failed calls, same measured PE and necessary objects, archives, public recovery and active worktree',
        reason='Zero deletion is permitted; retain this finite evidence chain and runtime. No temporary duplicate requires deletion.',
        no_global_settings_changed=True))

def gitio(*args):
    assert args and args[0] in ('commit','push')
    assert not any(a in ('--force','-f','--force-with-lease','--delete') for a in args)
    p=subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True)
    print(p.stdout,end='');print(p.stderr,end='',file=sys.stderr)
    assert p.returncode==0,f'git {args[0]} failed with {p.returncode}'

def record_io(action,args):
    began=time.perf_counter();started=utc();ok=False
    try:
        globals()[action](*args);ok=True
    finally:
        path=OUT/'publication_costs.json'
        v=read(path) if path.exists() else dict(category='publication/archive/recovery/cleanup I/O; excluded from scientific meter',records=[])
        v['records'].append(dict(action=action,args=args,start_UTC=started,end_UTC=utc(),elapsed_seconds=time.perf_counter()-began,success=ok))
        v['total_seconds']=sum(x['elapsed_seconds'] for x in v['records']);v['no_new_Optimize']=True
        v['final_metadata_push']='Receipt after the metadata commit is retained locally; no self-referential commit loop.'
        write(path,v)

if __name__=='__main__':record_io(sys.argv[1],sys.argv[2:])
