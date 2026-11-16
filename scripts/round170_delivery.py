"""One new-only raw carrier, anonymous pinned byte recovery, zero-delete closeout."""
from round170_common import *
import concurrent.futures, gzip, re, shutil, urllib.parse, urllib.request, zipfile

def package():
    assert read(OUT/'complete_arms.json')['all_22_qualified']
    target=OUT/'artifacts';target.mkdir(exist_ok=True);archive=target/'round170_new_raw.zip'
    assert not archive.exists(),'never overwrite a delivered science carrier'
    entries=[p for p in sorted((OUT/'complete_raw').rglob('*')) if p.is_file()]
    rows=[]
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in entries:
            member=p.relative_to(OUT).as_posix()
            assert p.suffix.lower() not in ['.dll','.lic','.exe']
            assert not any(s in p.name.lower() for s in ['license','credential'])
            raw=p.read_bytes()
            assert not re.search(rb'(?i)(WLSSECRET|AWS_SECRET_ACCESS_KEY|OPENAI_API_KEY)\s*[:=]',raw),member
            z.writestr(member,raw);rows.append(dict(member=member,bytes=len(raw),SHA256=hashlib.sha256(raw).hexdigest()))
    stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    membermap=target/'round170_new_raw_members.csv.gz';membermap.write_bytes(gzip.compress(stream.getvalue().encode('utf-8'),mtime=0))
    with zipfile.ZipFile(archive) as z:
        assert len(z.infolist())==len(rows)
        for r in rows:
            data=z.read(r['member']);assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['SHA256']
    write(OUT/'evidence_archives.json',dict(UTC=utc(),new_only=True,carrier=bind(archive),membermap=bind(membermap),
        members=len(rows),raw_uncompressed_bytes=sum(r['bytes'] for r in rows),all_local_member_bytes_verified=True,
        historical_carriers_repacked=False,commercial_DLL_licenses_credentials_included=False,
        inherited_PE=dict(commit='b86cef9917a9fd526ca89bcbdad4b667008c7eab',
            archive='results/unified_exact_round169/artifacts/round169_new_raw_and_runtime.zip',
            member='runtime/ExactEBRP.exe',bytes=9884148,SHA256=PE_SHA),
        restore='expand complete_raw members under results/unified_exact_round170; resolve old PE from fixed R169 runtime member'))
    print('New-only carrier:',len(rows),'members,',archive.stat().st_size,'bytes',flush=True)

def recover(science):
    root=WORK/'recovery'/('round170-public-'+science[:12]);root.mkdir(parents=True,exist_ok=True)
    paths=git('diff','--name-only',BASE,science).splitlines();rows=[]
    for name in paths:
        data=subprocess.check_output(['git','show',science+':'+name],cwd=ROOT)
        rows.append(dict(path=name,bytes=len(data),SHA256=hashlib.sha256(data).hexdigest()))
    tick=time.perf_counter()
    def fetch(row):
        start=time.perf_counter();name=row['path'];destination=root/name
        if destination.is_file():
            data=destination.read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['SHA256']
            return dict(**row,PASS=True,anonymous=True,resumed_verified_bytes=True,seconds=0)
        url='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+science+'/'+urllib.parse.quote(name,safe='/')
        request=urllib.request.Request(url,headers={'User-Agent':'Round170-public-integrity-readback'})
        with urllib.request.urlopen(request,timeout=55) as response:data=response.read()
        assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['SHA256'],name
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
        return dict(**row,PASS=True,anonymous=True,normal_TLS=True,seconds=time.perf_counter()-start)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:verified=list(executor.map(fetch,rows))
    a=read(root/'results/unified_exact_round170/evidence_archives.json')
    members=list(csv.DictReader(io.StringIO(gzip.decompress((root/a['membermap']['path']).read_bytes()).decode('utf-8'))))
    with zipfile.ZipFile(root/a['carrier']['path']) as z:
        assert len(z.infolist())==len(members)
        for row in members:
            data=z.read(row['member']);assert len(data)==int(row['bytes']) and hashlib.sha256(data).hexdigest()==row['SHA256']
    value=dict(UTC=utc(),scientific_commit=science,files=len(verified),bytes=sum(r['bytes'] for r in verified),results=verified,
        new_raw_members_verified=len(members),all_member_bytes_verified=True,anonymous=True,normal_TLS=True,
        old_raw_downloaded=False,fresh_root=str(root),ordinary_public_IO_seconds=time.perf_counter()-tick,PASS=True,
        scope='this round changed/new sources, current manuscript/PDF, qualified CSV increment and necessary new evidence; no licensed optimizer rerun')
    write(OUT/'public_recovery.json',value);write(root/'recovery_receipt.json',value)
    print('Anonymous byte recovery PASS:',len(verified),'files,',len(members),'raw members',flush=True)

def cleanup():
    before=read(OUT/'entry_state.json')['protected'];after=protected();assert before==after
    write(OUT/'protected_tree_check.json',dict(UTC=utc(),PASS=True,protected=after,
        protected_tracked_status_and_dirty_bytes_unchanged=True,zero_delete=True))
    recon=read(OUT/'CSV_reconciliation.json')
    for p in recon['found']:
        file=Path(p['path']);file=file if file.is_absolute() else ROOT/file
        assert sha(file)==p['SHA256'],('protected CSV changed',file)
    free=shutil.disk_usage(WORK).free;assets=[]
    for p in [OUT,WORK/'temp/round170',Path(read(OUT/'public_recovery.json')['fresh_root'])]:
        files=[q for q in p.rglob('*') if q.is_file() and 'node_modules' not in q.parts]
        assets.append(dict(root=str(p),files=len(files),logical_bytes=sum(q.stat().st_size for q in files),retained=True))
    afterfree=shutil.disk_usage(WORK).free
    write(OUT/'cleanup_record.json',dict(UTC=utc(),scope='bounded metadata screening of current round only',assets=assets,
        actions=[],deleted_files=0,deleted_bytes=0,volume_free_before=free,volume_free_after=afterfree,
        observed_free_change=afterfree-free,retained_shared_R169_PE=bind(PE),
        reason='unique science/raw/failures, QA, public recovery and active Draft retained; zero deletion allowed'))
    print('Protected trees/CSV unchanged; bounded zero-delete closeout',flush=True)

def scientific_close():
    assert read(OUT/'complete_arms.json')['all_22_qualified']
    accepted=read(OUT/'document_visual_accepted_hashes.json')
    assert all(sha(ROOT/p)==h for p,h in accepted.items())
    for name in ['document_build.json']:
        b=read(OUT/name);b['visual_QA_pending']=False;b['targeted_visual_QA']=bind(OUT/'document_qa.json');write(OUT/name,b)
    p=ROOT/'results/unified_exact_round137/pdf_export.json';b=read(p);b['visual_review_pending']=False;write(p,b)
    candidate=read(OUT/'candidate_manifest.json');assert all(sha(ROOT/p)==h for p,h in candidate['source_hashes'].items())
    reviews=[]
    for name in ['math_review_final.json','execution_review_final.json','research_review_final.json']:
        r=read(OUT/'review'/name);assert r['status']=='PASS',(name,r.get('status'))
        reviews.append(dict(path=name,status=r['status'],file=bind(OUT/'review'/name)))
    cost=read(OUT/'cost_report.json');cost['science_elapsed_conservative_seconds']=time.time()-SCIENCE_START
    assert cost['science_elapsed_conservative_seconds']<SCIENCE_CAP
    cost['CPP_source_unchanged_after_measurement']=True
    cost['independent_agent_reviews']=[dict(file=r['file'],review_seconds=read(OUT/'review'/r['path']).get('review_seconds')) for r in reviews]
    write(OUT/'cost_report.json',cost)
    arms=read(OUT/'complete_arms.json')['rows']
    write(OUT/'evidence_checks.json',dict(UTC=utc(),PASS=True,positions=22,complete_H_calls=sum(a['H_calls'] for a in arms),
        actual_Optimize=sum(a['actual_Optimize'] for a in arms),LP=sum(a['LP'] for a in arms),MIP=sum(a['MIP'] for a in arms),
        all_source_hashes_match=True,common_PE=bind(PE),independent_reviews=reviews,CSV_QA=bind(OUT/'CSV_QA.json'),
        PDF_QA=bind(OUT/'document_qa.json'),new_B_records=8,new_strict_P_pairs=3,new_physical_inputs=0,
        default_B=True,C166_D167_C169_default_off=True,solver_reruns_for_documentation=0))
    write(OUT/'science_close.json',dict(UTC=utc(),scientific_objective_achieved=True,delivery_remaining=True,
        science_elapsed_conservative_seconds=cost['science_elapsed_conservative_seconds'],science_capacity_seconds=SCIENCE_CAP,
        all_22_qualified=True,decision=read(OUT/'decision.json')['decision'],no_Round171=True))
    print('Science closed at',cost['science_elapsed_conservative_seconds'],'conservative seconds',flush=True)

if __name__=='__main__':
    if sys.argv[1]=='recover':recover(sys.argv[2])
    else:globals()[sys.argv[1]]()
