"""Bounded carriers, fixed-byte public recovery and current-round closeout.

These commands are pure I/O, with no solver import, compilation or Native load.
Run only after all experimental producers have returned.
"""
import io,re,shutil,zipfile,urllib.request
from round143_common import *

def idle():assert not budget()['unclosed'],'delivery waits for all timed producers'
def local():
    idle();tick=time.perf_counter();m=read(OUT/'candidate_manifest.json');full=read(OUT/'reports/full.json')
    assert sha(m['production_PE'])==m['production_PE_SHA'] and sha(DLL)==DLL_SHA
    for p,digest in m['source_hashes'].items():assert sha(ROOT/p)==digest,p
    protected=[]
    with zipfile.ZipFile(io.BytesIO(git('archive','--format=zip',BASE,'scripts','config'))) as z:
        for name in z.namelist():
            if not ((name.startswith('scripts/paper_s2') and name.endswith('.py')) or
                (name.startswith('config/gi_tbc') and name.endswith('.json')) or name=='config/paper_s2.json'):continue
            raw=z.read(name);actual=(ROOT/name).read_bytes();assert actual.replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n'),name
            protected.append(dict(path=name,current_SHA=sha(ROOT/name),original_semantics_and_bytes_modulo_EOL=True))
    LP=[]
    for p in (OUT/'LP').glob('*/result.json'):
        r=read(p);assert r['qualified'] and r['Seed']==0 and r['Threads']==1
        assert sha(p.parent/'model.mps')==r['canonical_SHA'] and sha(p.parent/'solution.json.gz')==r['solution_SHA']
        assert read(p.parent/'native_return.json')['state']=='OPTIMIZE_RETURNED';LP.append(r)
    assert len(LP)==4
    native=0;raw=[]
    for r in full['qualification']+full['new_arms']:
        d=Path(r['destination']);a=read(d/'round135_endpoint.json');v=read(d/'verification_closeout.json')
        assert v['implementation_qualified'] and v['native_proof_qualified'] and v['performance_eligible']
        assert a['declared_calls']==a['returned_calls'];native+=a['returned_calls']
        seal=read(d/'producer_seal.json')
        for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest,name
        raw.append(dict(arm_id=a['arm_id'],endpoint_SHA=sha(d/'round135_endpoint.json'),closeout_SHA=sha(d/'verification_closeout.json'),
            input_SHA=sha(ROOT/next(g['launch']['panel']['input_path'] for matrix in OUT.glob('*_matrix.json')
                for g in read(matrix).get('groups',[]) if g['arm_id']==a['arm_id']))))
    assert native==22 and len(full['new_arms'])==4 and len(full['qualification'])==1
    review=read(OUT/'review/final_scientific_review.json');render=read(OUT/'pdf_render_manifest.json');assert review['PASS']
    assert read(OUT/'pdf_visual_review.json')['PASS'] and sha(OUT/'manuscript.pdf')==render['PDF_SHA']
    assert read(OUT/'PDF_marker.json')['successful_invocations']==1
    assert read(OUT/'candidate_decision.json')['study_complete'] and not read(OUT/'candidate_decision.json')['additional_experiments_admitted']
    assert 'gurobipy' not in sys.modules
    write(OUT/'local_semantic_check.json',dict(PASS=True,UTC=utc(),raw=raw,protected_prior_entries_profiles=protected,
        Native_Optimize=22,standalone_LP_Optimize=4,total_Optimize=26,all_returned=True,unclosed=[],
        experiment_seconds=budget()['G1_seconds'],within_28800_seconds=budget()['G1_seconds']<=28800,
        final_scientific_review_SHA=sha(OUT/'review/final_scientific_review.json'),PDF_SHA=render['PDF_SHA'],
        current_check_Optimize=0,current_check_Native_load=0,seconds=time.perf_counter()-tick))
    print('Local source/entry/raw/seal/PDF checks PASS; all 26 Optimize calls returned')

def pack():
    idle();tick=time.perf_counter();archives=[]
    def archive(name,paths):
        target=OUT/'artifacts'/name;target.parent.mkdir(parents=True,exist_ok=True);members=[]
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(set(paths)):
                assert p.is_file() and ROOT.resolve() in p.resolve().parents
                assert p.suffix.lower() not in {'.exe','.dll','.lib','.a','.o','.obj','.lic'},p
                rel=p.relative_to(ROOT).as_posix();data=p.read_bytes();z.writestr(rel,data)
                members.append(dict(member=rel,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        archives.append(dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size,members=members))
    def files(folder):return [p for p in folder.rglob('*') if p.is_file()] if folder.exists() else []
    diagnostics=[]
    for folder in ['LP','math','domains','inherited','qualification/writer','failures']:
        diagnostics+=files(OUT/folder)
    for d in (OUT/'fees').iterdir():
        if d.name.startswith(('LP_','compile_','link_','tiny_cpp','native_writer')):diagnostics+=files(d)
    archive('diagnostics_and_failures.zip',diagnostics)
    archive('complete_qualification.zip',files(OUT/'qualification/runs')+files(OUT/'fees/qualification_001'))
    for matrix_path in sorted(OUT.glob('*_matrix.json')):
        matrix=read(matrix_path)
        if 'batch' not in matrix or matrix['batch'].startswith('qualification'):continue
        for g in matrix['groups']:
            d=OUT/g['group']
            if not (Path(g['launch']['destination'])/'verification_closeout.json').exists():continue
            archive(f'campaign_{matrix["batch"]}_{g["position"]:03}.zip',files(d)+files(OUT/'fees'/f'{matrix["batch"]}_{g["position"]:03}'))
    sources=[]
    manifest=read(OUT/'candidate_manifest.json')
    sources+=[ROOT/p for p in manifest['source_hashes']]
    for matrix_path in OUT.glob('*_matrix.json'):
        matrix=read(matrix_path)
        if 'helpers' in matrix:sources+=[ROOT/p for p in matrix['helpers']]
        for group in matrix.get('groups',[]):
            p=group['launch']['panel']
            sources += [ROOT/p[k] for k in ['input_path','selection_path','landscape_path'] if p.get(k)]
    for scope in (OUT/'inherited/roots').glob('*/scope.json'):
        p=read(scope)['panel'];sources+=[ROOT/p[k] for k in ['input_path','selection_path','landscape_path'] if p.get(k)]
    sources+=list((ROOT/'scripts').glob('round143_*'))+[ROOT/'scripts/paper_s2_rn.py',ROOT/'config/gi_tbc_rn_round143.json',ROOT/'CMakeLists.txt',ROOT/'WORKSPACE_POLICY.md']
    archive('source_and_helpers.zip',[p for p in sources if p.is_file()])
    science=[p for p in OUT.iterdir() if p.is_file() and p.name not in {
        'carrier_manifest.json','archive_local_check.json','nonexperimental_accounting.json',
        'publication_pin.json','public_restore_owner.json','public_attempt_history.json','public_restore_receipt.json',
        'cleanup_record.json','PR_delivery.json','PR_readback.json','PR_description.md','delivery_costs.json'}]
    science+=files(OUT/'reports')+files(OUT/'review')
    science += [p for p in files(OUT/'layout_history') if p.suffix!='.png']
    for folder in (OUT/'fees').iterdir():
        if folder.name.startswith(('document_','render_')):science+=files(folder)
    archive('science_and_paper.zip',science)
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),archives=archives,archive_count=len(archives),
        indexed_members=sum(len(a['members']) for a in archives),compressed_bytes=sum(a['bytes'] for a in archives),
        Optimize=0,Native_load=0,seconds=time.perf_counter()-tick,commercial_binaries_or_licenses_published=False))
    print(json.dumps(dict(archives=len(archives),members=sum(len(a['members']) for a in archives),bytes=sum(a['bytes'] for a in archives))))

def public(commit):
    idle();assert re.fullmatch('[0-9a-f]{40}',commit)
    history_path=OUT/'public_attempt_history.json';history=read(history_path) if history_path.exists() else []
    spent=sum(r['seconds'] for r in history);assert spent<1800
    tick=time.perf_counter();records=[];target=WORK/'restore'/f'round143-public-{commit[:12]}-attempt{len(history)+1:02}'
    assert WORK.resolve() in target.resolve().parents
    target.mkdir(parents=True,exist_ok=False)
    manifest=read(OUT/'carrier_manifest.json')
    write(OUT/'public_restore_owner.json',dict(UTC=utc(),directory=str(target),fixed_commit=commit,scope='Current-round carriers only'))
    try:
        manifest_url=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{commit}/results/unified_exact_round143/carrier_manifest.json'
        with urllib.request.urlopen(urllib.request.Request(manifest_url,headers={'User-Agent':'Round143-finite-public-recovery'}),timeout=30) as response:remote_manifest=response.read()
        assert hashlib.sha256(remote_manifest).hexdigest()==sha(OUT/'carrier_manifest.json') and json.loads(remote_manifest)==manifest
        (target/'carrier_manifest.json').write_bytes(remote_manifest)
        for a in manifest['archives']:
            assert spent+time.perf_counter()-tick<1800,'bounded cumulative public I/O ceiling'
            url=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{commit}/{a["path"]}'
            request=urllib.request.Request(url,headers={'User-Agent':'Round143-finite-public-recovery'})
            with urllib.request.urlopen(request,timeout=120) as response:data=response.read()
            assert hashlib.sha256(data).hexdigest()==a['SHA256'] and len(data)==a['bytes']
            checked=0
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                assert sorted(z.namelist())==sorted(m['member'] for m in a['members'])
                for m in a['members']:
                    raw=z.read(m['member']);assert len(raw)==m['bytes'] and hashlib.sha256(raw).hexdigest()==m['SHA256'];checked+=1
            destination=target/Path(a['path']).name;destination.write_bytes(data)
            records.append(dict(url=url,path=a['path'],SHA256=a['SHA256'],bytes=len(data),members_checked=checked,anonymous=True))
        receipt=dict(PASS=True,UTC=utc(),fixed_commit=commit,archives=records,seconds=time.perf_counter()-tick,
            manifest_url=manifest_url,manifest_SHA256=sha(OUT/'carrier_manifest.json'),
            Optimize=0,Native_load=0,compile=0,only_public_bytes_and_members=True,credentials_used=False)
    except BaseException as error:
        receipt=dict(PASS=False,UTC=utc(),fixed_commit=commit,archives=records,seconds=time.perf_counter()-tick,error=repr(error),
            Optimize=0,Native_load=0,compile=0,settings_changed=False)
        history.append(receipt);write(history_path,history);write(OUT/'public_restore_receipt.json',dict(receipt,cumulative_seconds=spent+receipt['seconds']));raise
    history.append(receipt);write(history_path,history)
    write(OUT/'public_restore_receipt.json',dict(receipt,cumulative_seconds=spent+receipt['seconds']))
    print(json.dumps(dict(PASS=True,archives=len(records),seconds=receipt['seconds'])))

def cleanup():
    idle();assert read(OUT/'public_restore_receipt.json')['PASS'] and read(OUT/'PR_readback.json')['draft']
    before=shutil.disk_usage(WORK).free;roots=[WORK/'build-cache/round143',WORK/'temp/round143',OUT]
    retained=[]
    for root in roots:
        resolved=root.resolve();require_within=WORK.resolve()==resolved or WORK.resolve() in resolved.parents;assert require_within
        paths=[p for p in root.rglob('*') if p.is_file()] if root.exists() else []
        retained.append(dict(path=str(root),files=len(paths),logical_bytes=sum(p.stat().st_size for p in paths),
            reason='Unique current-round raw/failures, source evidence, necessary runtime objects and active tree retained'))
    after=shutil.disk_usage(WORK).free
    write(OUT/'cleanup_record.json',dict(UTC=utc(),deleted_paths=[],deleted_logical_bytes=0,retained=retained,
        free_bytes_before=before,free_bytes_after=after,observed_volume_delta=after-before,
        volume_delta_not_attributed_to_deletion=True,bounded_current_round_only=True,old_rounds_deleted=False,
        original_user_tree_modified=False,zero_deletion_reason='No deletion needed; all unique evidence and runtime dependencies retained',
        public_acceptance_SHA=sha(OUT/'public_restore_receipt.json'),PR_readback_SHA=sha(OUT/'PR_readback.json')))
    print('Bounded current-round cleanup: zero deletion; unique science/runtime/active tree retained')

if __name__=='__main__':
    if sys.argv[1]=='public':public(sys.argv[2])
    else:globals()[sys.argv[1]]()
