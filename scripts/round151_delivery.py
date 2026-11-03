"""Incremental current-round carriers, finite public member recovery and closeout."""
import gzip,io,re,zipfile
from round151_common import *
def files(root):return [p for p in root.rglob('*') if p.is_file()] if root.exists() else []
def idle(allow_current=False):
    configure();current=os.environ.get('ROUND140_METERED_PARENT_LABEL') if allow_current else None
    assert all(v['label']==current for v in budget()['unclosed'])
def local():
    idle(True);full=read(OUT/'reports/full.json');decision=read(OUT/'candidate_decision.json')
    assert not full['pending'] and decision['study_complete'] and decision['no_more_Optimize_queued']
    assert full['complete_Native_Optimize']==full['complete_Native_returned']
    assert full['diagnostic_LP_Optimize']==full['diagnostic_LP_returned']==2
    assert full['qualification_Native_Optimize']==full['qualification_Native_returned']
    manifest=read(OUT/'candidate_manifest.json')
    assert sha(manifest['production_PE'])==manifest['production_PE_SHA'] and sha(DLL)==DLL_SHA
    for p,h in manifest['source_hashes'].items():assert sha(ROOT/p)==h,p
    start=read(OUT/'start_receipt.json')
    for p,h in start['protected_entry_bytes'].items():assert sha(ROOT/p)==h,p
    assert not git('diff',BASE,'--',*[f'results/unified_exact_round{i}' for i in range(137,151)]).strip()
    original=Path('E:/codes/ExactEBRP')
    assert git('status','--porcelain=v1','--untracked-files=no',cwd=original).decode()==start['protected_original_status']
    for p,h in start['protected_modified_file_hashes'].items():assert sha(original/p)==h,p
    destinations=[Path(r['destination']) for r in full['formal_arms']]
    destinations+=[OUT/'campaign_qualification/raw/R151_qualification_NB35_C']
    for d in destinations:
        assert read(d/'round147_control_audit.json')['PASS'] and not read(d/'round147_control_audit.json')['GD']
        assert read(d/'round149_control_audit.json')['PASS'] and not read(d/'round149_control_audit.json')['enabled']
        assert read(d/'round151_control_audit.json')['PASS']
        for p,h in read(d/'producer_seal.json')['required_SHA'].items():assert sha(d/p)==h,p
    for tag in ['P','C']:
        d=OUT/'LP'/f'N-B35-S_{tag}';r=read(d/'result.json')
        assert r['qualified'] and sha(d/'model.mps')==r['model_SHA'] and sha(d/'solution.json.gz')==r['solution_SHA']
        assert sha(d/'dual.json.gz')==r['dual_SHA'] and (d/'return.json').exists()
    write(OUT/'local_semantic_check.json',dict(PASS=True,UTC=utc(),all_entered_preserved=True,
        all_native_calls_returned=True,source_PE_DLL_identity=True,all_producer_seals=True,
        stable_and_old_research_entries_unchanged=True,old_results_and_original_user_bytes_unchanged=True,
        Optimize=0,Native_load=0,compile=0))
    print('PASS local science identities, producer seals, old/user bytes and all calls')
def pack():
    idle();assert read(OUT/'local_semantic_check.json')['PASS']
    review=read(OUT/'review/final_scientific_review.json')
    assert review['decision']=='ACCEPT_SCIENTIFIC_CLOSEOUT' and review['independent_nonimplementer_review']
    tick=time.perf_counter();archives=[];index={};labels=set()
    def archive(filename,paths):
        target=OUT/'artifacts'/filename;target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
        members=[]
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(set(paths)):
                assert p.resolve().is_relative_to(ROOT.resolve())
                assert p.suffix.lower() not in {'.exe','.dll','.lic','.o','.obj','.a','.lib','.pyc'}
                member=p.relative_to(ROOT).as_posix();data=p.read_bytes();z.writestr(member,data)
                members.append(dict(member=member,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        assert target.stat().st_size<100_000_000,'Use deterministic splitting; retain evidence'
        relative=target.relative_to(ROOT).as_posix();index[relative]=members
        archives.append(dict(path=relative,SHA256=sha(target),bytes=target.stat().st_size,member_count=len(members)))
    for g in read(OUT/'confirmation_matrix.json')['groups']:
        label=f'confirmation_{g["position"]:03}';folder=OUT/g['group']
        labels.add(label)
        archive('campaign_'+label+'.zip',files(folder)+files(OUT/'fees'/label))
    diagnostics=[]
    for folder in ['LP','qualification','campaign_qualification','engineering','infra']:
        diagnostics+=files(OUT/folder)
    for folder in (OUT/'fees').iterdir():
        if folder.name not in labels:diagnostics+=files(folder)
    archive('diagnostics_qualification_failures_and_fees.zip',diagnostics)
    helpers=list((ROOT/'scripts').glob('round151*'))+[ROOT/'scripts/paper_s2_penalty_propagation.py',ROOT/'include/Round151Research.hpp',
        *[ROOT/'src'/n for n in ['main.cpp','GurobiBaseline.cpp','PaperExternalGiniTree.cpp']],
        ROOT/'.gitattributes',ROOT/'config/gi_tbc_penalty_propagation_round151.json',ROOT/'WORKSPACE_POLICY.md',
        ROOT/'docs/round151_research.md',ROOT/'docs/current_mainline.md',ROOT/'docs/unified_exact_research_index.md']
    archive('new_helpers_and_source.zip',helpers)
    excluded={'carrier_manifest.json','publication_pin.json','PR_delivery.json','PR_readback.json','PR_description.md',
        'public_restore_receipt.json','public_attempt_history.json','cleanup_record.json','public_restore_owner.json',
        'delivery_costs.json','delivery_snapshot.json'}
    science=[p for p in OUT.iterdir() if p.is_file() and p.name not in excluded]
    archive('science_and_paper.zip',science+files(OUT/'reports')+files(OUT/'review'))
    target=OUT/'artifacts/member_index.json.gz'
    target.write_bytes(gzip.compress(json.dumps(index,separators=(',',':'),ensure_ascii=False).encode(),compresslevel=6,mtime=0))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),schema='round151-incremental-carriers-v1',archives=archives,
        archive_count=len(archives),indexed_members=sum(len(v) for v in index.values()),
        compressed_bytes=sum(a['bytes'] for a in archives)+target.stat().st_size,
        member_index=dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size),
        inherited_fixed_science=SCIENCE150,inherited_members='reuse_index.json',old_large_history_duplicated=False,
        commercial_binaries_or_licenses_published=False,Optimize=0,Native_load=0,compile=0,seconds=time.perf_counter()-tick))
    print(json.dumps(dict(archives=len(archives),members=sum(len(v) for v in index.values()),seconds=time.perf_counter()-tick)))
def public(commit):
    idle();assert re.fullmatch('[0-9a-f]{40}',commit)
    history_path=OUT/'public_attempt_history.json';history=read(history_path) if history_path.exists() else []
    spent=sum(r['seconds'] for r in history);assert spent<1800;tick=time.perf_counter()
    target=WORK/'restore'/f'round151-public-{commit[:12]}-attempt{len(history)+1:02}'
    assert target.resolve().is_relative_to((WORK/'restore').resolve());target.mkdir(parents=True,exist_ok=False)
    write(OUT/'public_restore_owner.json',dict(directory=str(target),fixed_commit=commit,UTC=utc()))
    def fetch(relative,ref=commit):
        assert spent+time.perf_counter()-tick<1800
        relative=relative.replace('\\','/');url=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{ref}/{relative}'
        destination=target/(ref[:12]+'_'+Path(relative).name)
        run=subprocess.run(['C:/Windows/System32/curl.exe','--disable','--fail','--silent','--show-error','--location',
            '--max-time','90','--proto','=https','--proto-redir','=https','--output',str(destination),'--url',url],capture_output=True,timeout=100)
        assert run.returncode==0,run.stderr.decode(errors='replace')
        return destination.read_bytes(),url
    records=[];inherited_count=0
    try:
        raw,_=fetch('results/unified_exact_round151/carrier_manifest.json');assert hashlib.sha256(raw).hexdigest()==sha(OUT/'carrier_manifest.json')
        manifest=json.loads(raw);raw,_=fetch(manifest['member_index']['path'])
        assert hashlib.sha256(raw).hexdigest()==manifest['member_index']['SHA256'];index=json.loads(gzip.decompress(raw))
        assert set(index)=={a['path'] for a in manifest['archives']}
        for a in manifest['archives']:
            raw,url=fetch(a['path']);assert len(raw)==a['bytes'] and hashlib.sha256(raw).hexdigest()==a['SHA256']
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                members=index[a['path']];assert sorted(z.namelist())==sorted(x['member'] for x in members)
                for item in members:
                    data=z.read(item['member']);assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['SHA256']
            records.append(dict(path=a['path'],url=url,SHA256=a['SHA256'],members_checked=len(members)))
        reuse=read(OUT/'reuse_index.json')
        for domain in reuse['domains']:
            raw,url=fetch(domain['archive'],domain['fixed_science']);assert hashlib.sha256(raw).hexdigest()==domain['archive_SHA']
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                for member in domain['members']:
                    data=z.read(member['member']);assert len(data)==member['bytes'] and hashlib.sha256(data).hexdigest()==member['SHA256'];inherited_count+=1
        for item in reuse['inputs']:
            raw,_=fetch(item['path'],reuse['input_fixed_science']);assert hashlib.sha256(raw).hexdigest()==item['SHA256']
        receipt=dict(PASS=True,UTC=utc(),fixed_commit=commit,archives=records,
            new_members_checked=sum(r['members_checked'] for r in records),inherited_members_checked=inherited_count,
            old_inputs_checked=len(reuse['inputs']),seconds=time.perf_counter()-tick,credentials_used=False,
            TLS_verification_enabled=True,transport='Windows curl/Schannel; curlrc disabled; HTTPS only',
            Optimize=0,Native_load=0,compile=0,only_public_bytes_and_members=True)
    except BaseException as error:
        receipt=dict(PASS=False,UTC=utc(),fixed_commit=commit,archives=records,seconds=time.perf_counter()-tick,error=repr(error),Optimize=0,Native_load=0,compile=0)
        history.append(receipt);write(history_path,history);write(OUT/'public_restore_receipt.json',receipt);raise
    history.append(receipt);write(history_path,history);write(OUT/'public_restore_receipt.json',dict(receipt,cumulative_seconds=spent+receipt['seconds']))
    print(json.dumps(dict(PASS=True,archives=len(records),members=receipt['new_members_checked'],seconds=receipt['seconds'])))
def cleanup():
    idle();assert read(OUT/'public_restore_receipt.json')['PASS']
    space_before=__import__('shutil').disk_usage(str(WORK))
    owner=read(OUT/'public_restore_owner.json');restore=Path(owner['directory'])
    assert restore.resolve().is_relative_to((WORK/'restore').resolve())
    roots=[BUILD,TEMP,restore,WORK/'restore/round151-inherited'];rows_=[]
    for root in roots:
        rows_.append(dict(path=str(root),retained=True,file_bytes=sum(p.stat().st_size for p in files(root)),
            reason='Retain necessary local runtime, unique qualification/failure context and recovery bytes for reproducibility; no deletion needed'))
    space_after=__import__('shutil').disk_usage(str(WORK))
    write(OUT/'cleanup_record.json',dict(UTC=utc(),screening='Bounded current-round metadata only',deleted_paths=[],deleted_file_bytes=0,
        retained=rows_,old_rounds_or_user_assets_touched=False,active_tree_retained=True,
        volume_free_before=space_before.free,volume_free_after=space_after.free,
        observed_volume_free_change=space_after.free-space_before.free,
        no_recursive_delete_or_move=True,zero_deletion_is_authorized=True))
    print('Bounded cleanup complete: zero deletion; necessary current-round runtime/evidence retained')
if __name__=='__main__':
    if sys.argv[1]=='public':public(sys.argv[2])
    elif sys.argv[1]=='meter_local':
        configure();assert metered('local_semantic_check','diagnostic',[PYTHON,'-B',__file__,'local'],120,300)==0
    else:globals()[sys.argv[1]]()
