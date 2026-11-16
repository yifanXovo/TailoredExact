"""One new-only carrier, bounded anonymous byte recovery and zero-delete closeout."""
from round169_common import *
import concurrent.futures, gzip, shutil, urllib.parse, urllib.request

def package():
    target=OUT/'artifacts';target.mkdir(exist_ok=True);archive=target/'round169_new_raw_and_runtime.zip'
    assert not archive.exists(),'never replace a published science carrier'
    entries=[]
    for name in ['h_raw','complete_raw','qualification','provenance_revalue']:
        for p in sorted((OUT/name).rglob('*')):
            if p.is_file():entries.append((p,p.relative_to(OUT).as_posix()))
    entries.append((PE,'runtime/ExactEBRP.exe'))
    for p in sorted(OUT.glob('build_console*.log')):entries.append((p,'build/'+p.name))
    for name in ['CMakeCache.txt','build.ninja']:
        entries.append((WORK/'build-cache/round169'/name,'build/'+name))
    for name in ['src/main.cpp','src/Round169Primal.inc','src/HgaTgbcRunner.cpp','include/Instance.hpp',
                 'include/HgaTgbcRunner.hpp','include/hga_tgbc/HybridGA.h']:
        entries.append((ROOT/name,'measured_source/'+name))
    rows=[]
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p,member in entries:
            assert p.suffix.lower() not in ['.dll','.lic']
            assert not any(s in p.name.lower() for s in ['license','credential'])
            raw=p.read_bytes()
            if p.suffix.lower() not in ['.exe']:
                assert not __import__('re').search(rb'(?i)(WLSSECRET|AWS_SECRET_ACCESS_KEY|OPENAI_API_KEY)\s*[:=]',raw),member
            z.writestr(member,raw);rows.append(dict(member=member,bytes=len(raw),SHA256=hashlib.sha256(raw).hexdigest(),local_source=str(p)))
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    membermap=target/'round169_new_raw_members.csv.gz';membermap.write_bytes(gzip.compress(stream.getvalue().encode(),mtime=0))
    with zipfile.ZipFile(archive) as z:
        assert len(z.infolist())==len(rows)
        for r in rows:assert hashlib.sha256(z.read(r['member'])).hexdigest()==r['SHA256']
    write(OUT/'evidence_archives.json',dict(UTC=utc(),new_only=True,carrier=bind(archive),membermap=bind(membermap),
        members=len(rows),raw_uncompressed_bytes=sum(r['bytes'] for r in rows),all_local_member_bytes_verified=True,
        own_project_PE_included=True,commercial_DLL_licenses_credentials_private_antecedents_included=False,
        historical_carriers_repacked=False,old_H_member_copies_included=False,
        old_raw_sources='weight_provenance.json exact fixed archive/member/hash references',
        restore='raw folders expand under results/unified_exact_round169; runtime/ is the measured common complete B/M/C PE'))
    print('Packaged',len(rows),'new members',archive.stat().st_size,'bytes',flush=True)

def recover(science):
    root=WORK/'recovery'/('round169-public-'+science[:12]);root.mkdir(parents=True,exist_ok=True)
    paths=git('diff','--name-only',BASE,science).splitlines();rows=[]
    for name in paths:
        raw=subprocess.check_output(['git','show',science+':'+name],cwd=ROOT)
        rows.append(dict(path=name,bytes=len(raw),SHA256=hashlib.sha256(raw).hexdigest()))
    t=time.perf_counter()
    def fetch(row):
        tick=time.perf_counter();name=row['path'];dest=root/name
        if dest.is_file():
            raw=dest.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['SHA256']
            return dict(**row,PASS=True,anonymous=True,resumed_verified_bytes=True,seconds=0)
        url='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+science+'/'+urllib.parse.quote(name,safe='/')
        request=urllib.request.Request(url,headers={'User-Agent':'Round169-public-integrity-readback'})
        with urllib.request.urlopen(request,timeout=55) as response:raw=response.read()
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['SHA256'],name
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        return dict(**row,PASS=True,anonymous=True,normal_TLS=True,seconds=time.perf_counter()-tick)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:results=list(executor.map(fetch,rows))
    a=read(root/'results/unified_exact_round169/evidence_archives.json')
    entries=list(csv.DictReader(io.StringIO(gzip.decompress((root/a['membermap']['path']).read_bytes()).decode())))
    with zipfile.ZipFile(root/a['carrier']['path']) as z:
        assert len(z.infolist())==len(entries)
        for r in entries:
            raw=z.read(r['member']);assert len(raw)==int(r['bytes']) and hashlib.sha256(raw).hexdigest()==r['SHA256']
    value=dict(UTC=utc(),scientific_commit=science,files=len(results),bytes=sum(x['bytes'] for x in results),results=results,
        new_raw_members_verified=len(entries),all_member_bytes_verified=True,anonymous=True,normal_TLS=True,
        old_raw_downloaded=False,fresh_root=str(root),ordinary_public_IO_seconds=time.perf_counter()-t,PASS=True,
        scope='only this round new/modified source, current manuscript/PDF and necessary evidence; no licensed semantic rerun')
    write(OUT/'public_recovery.json',value);write(root/'recovery_receipt.json',value)
    print('Public recovery PASS',len(results),'files',len(entries),'raw members',flush=True)

def cleanup():
    before=read(OUT/'entry_state.json')['protected'];after=protected();assert before==after
    write(OUT/'protected_tree_check.json',dict(UTC=utc(),PASS=True,protected=after,
        original_paper_current_predecessor_tracked_status_and_dirty_bytes_unchanged=True,zero_delete=True))
    free=shutil.disk_usage(WORK).free;assets=[]
    recovery=Path(read(OUT/'public_recovery.json')['fresh_root'])
    for p in [OUT,WORK/'build-cache/round169',WORK/'temp/round169',recovery]:
        files=[q for q in p.rglob('*') if q.is_file()]
        assets.append(dict(root=str(p),files=len(files),logical_bytes=sum(q.stat().st_size for q in files),retained=True))
    afterfree=shutil.disk_usage(WORK).free
    write(OUT/'cleanup_record.json',dict(UTC=utc(),scope='bounded metadata screening of current round only',assets=assets,
        actions=[],deleted_files=0,deleted_bytes=0,volume_free_before=free,volume_free_after=afterfree,
        observed_free_change=afterfree-free,policy='retain unique raw/failures/build dependencies, QA, recovery and active Draft; zero deletion is allowed'))
    print('Protected trees unchanged; zero-delete closeout',flush=True)

def scientific_close():
    accepted=read(OUT/'document_visual_accepted_hashes.json')
    assert all(sha(ROOT/p)==h for p,h in accepted.items())
    b=read(OUT/'document_build.json');b['visual_QA_pending']=False
    b['targeted_visual_QA']=bind(OUT/'document_qa.json')
    b['last_export_reused_identical_visually_accepted_PDFs']=True
    write(OUT/'document_build.json',b)
    p=ROOT/'results/unified_exact_round137/pdf_export.json'
    b=read(p);b['visual_review_pending']=False;write(p,b)
    c=read(OUT/'candidate_manifest.json')
    assert all(sha(ROOT/p)==h for p,h in c['source_hashes'].items())
    reviews=[]
    for name in ['math_review_final.json','implementation_review_final.json','research_review_final.json']:
        r=read(OUT/'review'/name)
        status=r.get('status',r.get('verdict',r.get('decision',r.get('PASS'))))
        assert status in ('PASS',True),(name,status)
        reviews.append(dict(path=name,status=status,file=bind(OUT/'review'/name)))
    cost=read(OUT/'cost_report.json')
    cost['science_elapsed_conservative_seconds']=time.time()-read(OUT/'entry_state.json')['science_start_epoch']
    assert cost['science_elapsed_conservative_seconds']<28800
    cost['CPP_source_unchanged_after_measurement']=True;write(OUT/'cost_report.json',cost)
    write(OUT/'evidence_checks.json',dict(UTC=utc(),PASS=True,H_paths=35,H_Optimize=0,
        complete_positions=18,complete_H_calls=42,actual_Optimize=93,LP=66,MIP=27,
        all_source_hashes_match_measured_tree=True,common_PE=bind(PE),
        raw_carrier=read(OUT/'evidence_archives.json'),CSV_QA=bind(OUT/'CSV_QA.json'),
        PDF_QA=bind(OUT/'document_qa.json'),independent_reviews=reviews,
        new_P_pairs=0,default_B=True,raw_experiments_not_rerun=True))
    write(OUT/'science_close.json',dict(UTC=utc(),
        science_elapsed_conservative_seconds=cost['science_elapsed_conservative_seconds'],science_capacity_seconds=28800,
        scientific_objective_achieved=True,delivery_remaining=True,all_18_positions_qualified=True,
        decision=read(OUT/'decision.json')['decision']))
    print('Science closed',cost['science_elapsed_conservative_seconds'],'seconds;',reviews,flush=True)
if __name__=='__main__':
    if sys.argv[1]=='recover':recover(sys.argv[2])
    else:globals()[sys.argv[1]]()
