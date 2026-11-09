"""New-only indexed carrier and one anonymous fixed-commit public recovery."""
import shutil,urllib.request,zipfile
from pathlib import PurePosixPath
from round159_common import *

HEAVY={'inputs','inputs_v2','runs','deepening','fees','engineering','infra','review','qualification_dp'}
MUTABLE={'public_manifest.json','carrier_manifest.json','public_restore_receipt.json','publication.json',
         'cleanup_record.json','RESUME.md','pr_body.md','stage_paths.json','stage_verification.json','delivery_audit.json'}

def safe(name):
    p=PurePosixPath(name)
    assert name and not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name

def protect():
    facts=[]
    for tree in read(OUT/'infra/protected_initial.json')['trees']:
        for name,entry in tree['tracked_dirty'].items():
            actual=sha(Path(tree['tree'])/name);assert actual==entry['SHA256'],(tree['tree'],name)
            facts.append(dict(tree=tree['tree'],path=name,SHA256=actual))
    return facts

def costs():
    configure();state=budget();assert not state['unclosed'],state
    receipts=[]
    for p in sorted((OUT/'fees').glob('*/receipt.json')):
        r=read(p);receipts.append(dict(label=p.parent.name,**r))
    write(OUT/'cost_report.json',dict(UTC=utc(),TOTAL=TOTAL,**state,outer_receipts=receipts,
        R158_prior_cost_excluded=True,compilation_and_public_IO_separate=True,reservations_not_actual_fees=True))

def pack():
    configure();assert not budget()['unclosed'];protected=protect()
    assert read(OUT/'final_review.json')['PASS'];assert read(OUT/'final_decision.json')['study_complete']
    art=OUT/'artifacts';art.mkdir(exist_ok=True);carrier=art/'new_evidence.zip';assert not carrier.exists()
    members=[]
    with zipfile.ZipFile(carrier,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for group in sorted(HEAVY):
            for p in sorted((OUT/group).rglob('*')):
                if not p.is_file():continue
                rel=p.relative_to(OUT).as_posix()
                if rel.startswith('infra/history/'):continue # only fixed-commit/hash references to old source reads
                name=p.relative_to(ROOT).as_posix();safe(name);content=p.read_bytes();z.writestr(name,content)
                members.append(dict(member=name,bytes=len(content),SHA256=hashlib.sha256(content).hexdigest()))
        # The one new research executable is a necessary measured artifact.
        # Old production executables, DLLs and historical carriers stay references.
        name='results/unified_exact_round159/runtime/Round159Research.exe';content=PE.read_bytes()
        assert hashlib.sha256(content).hexdigest()==read(OUT/'build_manifest.json')['PE_SHA']
        z.writestr(name,content);members.append(dict(member=name,bytes=len(content),SHA256=hashlib.sha256(content).hexdigest()))
    index=art/'new_evidence.members.json.gz';save_gz(index,members)
    assert carrier.stat().st_size<40*1024*1024,'split new-only carrier before staging'
    archive=dict(path=carrier.relative_to(ROOT).as_posix(),SHA256=sha(carrier),bytes=carrier.stat().st_size,
        index=dict(path=index.relative_to(ROOT).as_posix(),SHA256=sha(index),bytes=index.stat().st_size),
        members=len(members),uncompressed_bytes=sum(r['bytes'] for r in members))
    thin=[p for p in OUT.rglob('*') if p.is_file() and p.relative_to(OUT).parts[0] not in HEAVY|{'artifacts'} and p.name not in MUTABLE]
    thin+=list((ROOT/'scripts').glob('round159_*.py'))
    thin+=[ROOT/p for p in ['src/Round159JointResource.cpp','src/round159_research_main.cpp','include/Round159JointResource.hpp',
        'CMakeLists.txt','.gitattributes','.gitignore','docs/round159_research.md','docs/unified_exact_research_index.md','docs/current_mainline.md','docs/paper_review.md']]
    files=[]
    for p in sorted(set(thin)):
        name=p.relative_to(ROOT).as_posix();safe(name);files.append(dict(path=name,SHA256=sha(p),bytes=p.stat().st_size))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),archives=[archive],old_carriers_repacked=0,old_source_copies_excluded='infra/history',
        unique_science_failures_retained=True))
    write(OUT/'public_manifest.json',dict(schema='round159-new-only-v1',UTC=utc(),files=files,archives=[archive],
        fixed_dependency_base=BASE,reference_index='results/unified_exact_round159/history_sources.json',
        current_only_recovery=True,scientific_recomputation_not_claimed=True,protected_dirty_files=len(protected)))
    paths=[r['path'] for r in files]+[archive['path'],archive['index']['path']]+[
        'results/unified_exact_round159/'+name for name in ['carrier_manifest.json','public_manifest.json','RESUME.md']]
    write(OUT/'stage_paths.json',paths)
    print(json.dumps(dict(thin=len(files),raw_members=len(members),compressed_bytes=archive['bytes'])))

def stage():
    paths=read(OUT/'stage_paths.json')+['results/unified_exact_round159/stage_paths.json'];facts=[]
    for no in range(0,len(paths),30):subprocess.run(['git','add','--sparse','--force','--',*paths[no:no+30]],cwd=ROOT,check=True)
    for name in paths:
        content=subprocess.check_output(['git','show',':'+name],cwd=ROOT);assert content==(ROOT/name).read_bytes(),name
        facts.append(dict(path=name,SHA256=sha(ROOT/name)))
    write(OUT/'stage_verification.json',dict(UTC=utc(),PASS=True,files=facts,index_bytes_equal_actual=True))

def recover(commit):
    assert len(commit)==40 and all(c in '0123456789abcdef' for c in commit)
    tick=time.perf_counter();dest=WORK/'restore'/f'round159-public-{commit[:12]}-attempt01'
    assert not dest.exists();dest.mkdir(parents=True)
    prefix=f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{commit}/'
    downloaded=[]
    def fetch(name):
        safe(name);path=dest.joinpath(*PurePosixPath(name).parts)
        assert path.resolve().is_relative_to(dest.resolve()) and not path.exists()
        path.parent.mkdir(parents=True,exist_ok=True)
        request=urllib.request.Request(prefix+name,headers={'User-Agent':'Round159-public-recovery'})
        with urllib.request.urlopen(request,timeout=60) as response:content=response.read()
        path.write_bytes(content);downloaded.append(dict(path=name,SHA256=sha(path),bytes=len(content)));return path
    manifest=read(fetch('results/unified_exact_round159/public_manifest.json'))
    for row in manifest['files']:
        path=fetch(row['path']);assert sha(path)==row['SHA256'] and path.stat().st_size==row['bytes']
    members_checked=0;rawbytes=0
    for archive in manifest['archives']:
        path=fetch(archive['path']);assert sha(path)==archive['SHA256'] and path.stat().st_size==archive['bytes']
        idx=fetch(archive['index']['path']);assert sha(idx)==archive['index']['SHA256']
        expected=load_gz(idx)
        with zipfile.ZipFile(path) as z:
            assert sorted(z.namelist())==sorted(r['member'] for r in expected)
            for row in expected:
                name=row['member'];safe(name);content=z.read(name);assert len(content)==row['bytes'] and hashlib.sha256(content).hexdigest()==row['SHA256']
                target=dest.joinpath(*PurePosixPath(name).parts);assert target.resolve().is_relative_to(dest.resolve()) and not target.exists()
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content);members_checked+=1;rawbytes+=len(content)
    write(OUT/'public_restore_receipt.json',dict(UTC=utc(),PASS=True,science_commit=commit,destination=str(dest),
        anonymous=True,downloaded=downloaded,members_checked=members_checked,uncompressed_bytes=rawbytes,
        IO_seconds=time.perf_counter()-tick,Optimize=0,compile=0,old_carriers_downloaded=0,scientific_recomputation=False))
    print(json.dumps(dict(PASS=True,files=len(downloaded),members=members_checked,seconds=time.perf_counter()-tick)))

def cleanup():
    assert read(OUT/'public_restore_receipt.json')['PASS'];assert read(OUT/'publication.json')['draft']
    assert not budget()['unclosed'];protected=protect();disk=shutil.disk_usage(WORK)
    screening=[]
    for path in [BUILD,OUT/'runs',OUT/'deepening',WORK/'temp/round159',Path(read(OUT/'public_restore_receipt.json')['destination']),ROOT]:
        # Bounded metadata only. No old-round enumeration or deletion.
        if path==ROOT:
            screening.append(dict(path=str(path),decision='retain active worktree',bytes=None));continue
        files=list(path.rglob('*')) if path.exists() else []
        screening.append(dict(path=str(path),files=sum(p.is_file() for p in files),bytes=sum(p.stat().st_size for p in files if p.is_file()),
            decision='retain reproducibility/runtime/failure or accepted recovery; no necessary duplicate selected'))
    after=shutil.disk_usage(WORK)
    write(OUT/'cleanup_record.json',dict(UTC=utc(),policy='WORKSPACE_POLICY and R122 bounded current-round authorization',
        screening=screening,deleted_files=0,deleted_bytes=0,retained_unique_science=True,protected_dirty_files=len(protected),
        volume_free_before=disk.free,volume_free_after=after.free,observed_free_change=after.free-disk.free,
        old_rounds_screened_for_deletion=False,zero_deletion_is_accepted=True))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
