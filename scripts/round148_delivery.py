"""Idle-only incremental carriers, bounded public recovery and safe closeout."""
import gzip
import io
import re
import shutil
import zipfile
from round148_common import *


def files(root):return [p for p in root.rglob('*') if p.is_file()] if root.exists() else []


def idle():
    configure();assert not budget()['unclosed']


def local():
    idle();full=read(OUT/'reports/full.json')
    assert not full['pending'] and read(OUT/'candidate_decision.json')['study_complete']
    assert full['complete_Native_Optimize']==full['complete_Native_returned']
    assert read(OUT/'review/final_scientific_review.json')['PASS']
    manifest=read(OUT/'candidate_manifest.json')
    assert sha(manifest['production_PE'])==manifest['production_PE_SHA'] and sha(DLL)==DLL_SHA
    for p,h in manifest['source_hashes'].items():assert sha(ROOT/p)==h,p
    protected=[p for p in git('ls-tree','-r','--name-only',BASE,'--','config','scripts').decode().splitlines()
        if p.startswith(('config/gi_tbc','scripts/paper_s2'))]
    for p in protected:assert not git('diff',BASE,'--',p).strip(),p
    assert not git('diff',BASE,'--',*[f'results/unified_exact_round{i}' for i in range(137,148)]).strip()
    original=Path('E:/codes/ExactEBRP');start=read(OUT/'start_receipt.json')
    assert git('status','--porcelain=v1','--untracked-files=no',cwd=original).decode()==(OUT/'protected_original_tracked_status.txt').read_text(encoding='utf-8')
    for p,h in start['protected_modified_file_hashes'].items():assert sha(original/p)==h,p
    for row in full['formal_arms']+full['qualification_arms']:
        d=Path(row['destination']);assert read(d/'round148_control_audit.json')['PASS']
        for p,h in read(d/'producer_seal.json')['required_SHA'].items():assert sha(d/p)==h,p
    write(OUT/'local_semantic_check.json',dict(PASS=True,UTC=utc(),all_entered_preserved=True,
        all_new_formal_arms_same_new_PE=True,source_and_PE_identity=True,
        historical_results_entries_profiles_unchanged=True,original_user_modified_bytes_unchanged=True,
        Optimize=0,Native_load=0,compile=0))
    print('PASS local identities, protected old/user bytes and all entered seals')


def pack():
    idle();assert read(OUT/'local_semantic_check.json')['PASS'];tick=time.perf_counter()
    archives=[];index={}
    def archive(name,paths):
        target=OUT/'artifacts'/name;target.parent.mkdir(parents=True,exist_ok=True)
        assert not target.exists();members=[]
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as zipped:
            for path in sorted(set(paths)):
                assert path.resolve().is_relative_to(ROOT.resolve())
                assert path.suffix.lower() not in {'.exe','.dll','.lic','.o','.obj','.a','.lib','.pyc'}
                name=path.relative_to(ROOT).as_posix();data=path.read_bytes()
                zipped.writestr(name,data);members.append(dict(member=name,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        assert target.stat().st_size<100_000_000
        relative=target.relative_to(ROOT).as_posix();index[relative]=members
        archives.append(dict(path=relative,SHA256=sha(target),bytes=target.stat().st_size,member_count=len(members)))
    armfees=set()
    for path in sorted(OUT.glob('*_matrix.json')):
        matrix=read(path)
        for g in matrix['groups']:
            label=f'{matrix["batch"]}_{g["position"]:03}';armfees.add(label)
            archive(f'campaign_{label}.zip',files(OUT/g['group'])+files(OUT/'fees'/label))
    diagnostics=files(OUT/'LP')+files(OUT/'qualification')+files(OUT/'engineering')+files(OUT/'infra')
    diagnostics += [p for folder in (OUT/'fees').iterdir() if folder.name not in armfees for p in files(folder)]
    archive('diagnostics_qualification_failures.zip',diagnostics)
    source=[*ROOT.glob('scripts/round148*'),ROOT/'scripts/paper_s2_shared_s.py',
        ROOT/'include/Round148Research.hpp',ROOT/'config/gi_tbc_shared_s_round148.json',ROOT/'.gitattributes']
    source += [ROOT/p for p in ('src/main.cpp','src/PaperExternalGiniTree.cpp','src/GurobiBaseline.cpp')]
    archive('new_source_and_helpers.zip',source)
    excluded={'carrier_manifest.json','publication_pin.json','PR_delivery.json','PR_readback.json','PR_description.md',
        'public_restore_receipt.json','public_attempt_history.json','cleanup_record.json','public_restore_owner.json','delivery_costs.json'}
    science=[p for p in OUT.iterdir() if p.is_file() and p.name not in excluded]
    for folder in ('reports','review'):science+=files(OUT/folder)
    archive('science_and_paper.zip',science)
    target=OUT/'artifacts/member_index.json.gz'
    target.write_bytes(gzip.compress(json.dumps(index,separators=(',',':'),ensure_ascii=False).encode(),compresslevel=6,mtime=0))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),schema='round148-incremental-carriers-v1',archives=archives,
        archive_count=len(archives),indexed_members=sum(len(v) for v in index.values()),
        compressed_bytes=sum(a['bytes'] for a in archives)+target.stat().st_size,
        member_index=dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size),
        inherited_R146_fixed_science=SCIENCE146,inherited_members='reuse_index.json',
        old_large_history_duplicated=False,commercial_binaries_or_licenses_published=False,
        Optimize=0,Native_load=0,compile=0,seconds=time.perf_counter()-tick))
    print(json.dumps(dict(archives=len(archives),members=sum(len(v) for v in index.values()),seconds=time.perf_counter()-tick)))


def public(commit):
    idle();assert re.fullmatch('[0-9a-f]{40}',commit)
    history_path=OUT/'public_attempt_history.json';history=read(history_path) if history_path.exists() else []
    spent=sum(r['seconds'] for r in history);assert spent<1800;tick=time.perf_counter()
    target=WORK/'restore'/f'round148-public-{commit[:12]}-attempt{len(history)+1:02}'
    assert target.resolve().is_relative_to((WORK/'restore').resolve());target.mkdir(parents=True,exist_ok=False)
    write(OUT/'public_restore_owner.json',dict(directory=str(target),fixed_commit=commit,UTC=utc()))
    records=[]
    def fetch(relative,ref=commit):
        assert spent+time.perf_counter()-tick<1800
        url=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{ref}/{relative}'
        destination=target/(ref[:12]+'_'+Path(relative).name)
        run=subprocess.run(['C:/Windows/System32/curl.exe','--disable','--fail','--silent','--show-error',
            '--location','--max-time','90','--proto','=https','--proto-redir','=https','--output',str(destination),
            '--url',url],capture_output=True,timeout=100)
        assert run.returncode==0,run.stderr.decode(errors='replace')
        return destination.read_bytes(),url
    try:
        raw,url=fetch('results/unified_exact_round148/carrier_manifest.json')
        assert hashlib.sha256(raw).hexdigest()==sha(OUT/'carrier_manifest.json');manifest=json.loads(raw)
        mi=manifest['member_index'];raw,index_url=fetch(mi['path'])
        assert len(raw)==mi['bytes'] and hashlib.sha256(raw).hexdigest()==mi['SHA256']
        index=json.loads(gzip.decompress(raw));assert set(index)=={a['path'] for a in manifest['archives']}
        for a in manifest['archives']:
            raw,url=fetch(a['path']);assert len(raw)==a['bytes'] and hashlib.sha256(raw).hexdigest()==a['SHA256']
            members=index[a['path']]
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                assert sorted(z.namelist())==sorted(x['member'] for x in members)
                for item in members:
                    data=z.read(item['member']);assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['SHA256']
            records.append(dict(path=a['path'],url=url,SHA256=a['SHA256'],bytes=len(raw),members_checked=len(members)))
        # Recover only the finite inherited input evidence, not old performance
        # panels. New carriers refer to these exact fixed-commit member hashes.
        reuse=read(OUT/'reuse_index.json');domains=reuse['domains'];archive=domains[0]['archive']
        raw,oldurl=fetch(archive,SCIENCE146);assert hashlib.sha256(raw).hexdigest()==domains[0]['archive_SHA']
        oldmembers={x['archive_member']:x['SHA256'] for d in domains for x in d['files']}
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for member,digest in oldmembers.items():assert hashlib.sha256(z.read(member)).hexdigest()==digest
        receipt=dict(PASS=True,UTC=utc(),fixed_commit=commit,archives=records,
            inherited_archive_url=oldurl,inherited_members_checked=len(oldmembers),
            new_members_checked=sum(r['members_checked'] for r in records),
            seconds=time.perf_counter()-tick,credentials_used=False,TLS_verification_enabled=True,
            transport='Windows curl/Schannel, curlrc disabled, HTTPS only, default certificate verification',
            helper_SHA256=sha(__file__),Optimize=0,Native_load=0,compile=0,only_public_bytes_and_members=True)
    except BaseException as error:
        receipt=dict(PASS=False,UTC=utc(),fixed_commit=commit,archives=records,
            seconds=time.perf_counter()-tick,error=repr(error),Optimize=0,Native_load=0,compile=0)
        history.append(receipt);write(history_path,history);write(OUT/'public_restore_receipt.json',receipt);raise
    history.append(receipt);write(history_path,history)
    write(OUT/'public_restore_receipt.json',dict(receipt,cumulative_seconds=spent+receipt['seconds']))
    print(json.dumps(dict(PASS=True,archives=len(records),new_members=receipt['new_members_checked'],inherited_members=len(oldmembers),seconds=receipt['seconds'])))


def cleanup():
    idle();assert read(OUT/'public_restore_receipt.json')['PASS'] and read(OUT/'PR_readback.json')['draft']
    tick=time.perf_counter();before=shutil.disk_usage(WORK).free
    roots=[OUT,TEMP,WORK/'build-cache/round148',Path(read(OUT/'public_restore_owner.json')['directory'])]
    retained=[]
    for root in roots:
        assert root.resolve().is_relative_to(WORK.resolve());paths=files(root)
        retained.append(dict(path=str(root),files=len(paths),logical_bytes=sum(p.stat().st_size for p in paths),
            reason='Unique raw/failures, active science, required runtime/build identity or bounded verified public restore'))
    manifest=read(OUT/'candidate_manifest.json');runtime=[Path(manifest['production_PE']),DLL,
        Path(read(ROOT/'results/unified_exact_round146/rows_driver.json')['PE'])]
    after=shutil.disk_usage(WORK).free
    write(OUT/'cleanup_record.json',dict(UTC=utc(),deleted_paths=[],deleted_logical_bytes=0,
        retained=retained,retained_runtime_files=[dict(path=str(p),bytes=p.stat().st_size,SHA256=sha(p)) for p in runtime],
        free_bytes_before=before,free_bytes_after=after,observed_volume_delta=after-before,
        volume_delta_not_attributed_to_deletion=True,bounded_current_round_only=True,seconds=time.perf_counter()-tick,
        old_rounds_deleted=False,original_user_tree_modified=False,
        zero_deletion_reason='Retain unique raw/failures, necessary PE/DLL and active tree; goal I explicitly accepts zero deletion',
        public_acceptance_SHA=sha(OUT/'public_restore_receipt.json'),PR_readback_SHA=sha(OUT/'PR_readback.json')))
    print('Bounded metadata screening and cleanup complete: zero deletion')


if __name__=='__main__':
    if sys.argv[1]=='public':public(sys.argv[2])
    else:globals()[sys.argv[1]]()
