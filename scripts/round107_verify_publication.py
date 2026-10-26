"""Verify the draft PR and public byte payload through GitHub's read APIs."""
from round107_common import *
import hashlib
from urllib.parse import quote

REPOSITORY='yifanXovo/TailoredExact'
BASE='codex/round106-structural-conflict-events'
BASE_COMMIT='0350dbcc60d1c68e5c499d2e9880ecc1deaf031c'
HEAD_BRANCH='codex/round107-ens-frontier-route-events'

def command(args):
    return subprocess.check_output(args,cwd=ROOT).decode('utf-8').strip()

def verify(pr_url,label):
    destination=OUT/'review'/label;destination.mkdir(parents=True,exist_ok=False)
    started=time.time();head=command(['git','rev-parse','HEAD'])
    pr=json.loads(command(['gh','pr','view',pr_url,'--json',
        'url,baseRefName,headRefName,headRefOid,state,isDraft']))
    assert pr['baseRefName']==BASE and pr['headRefName']==HEAD_BRANCH
    assert pr['headRefOid']==head and pr['state']=='OPEN' and pr['isDraft']
    refs=command(['git','ls-remote','origin','refs/heads/'+BASE,'refs/heads/'+HEAD_BRANCH])
    remote={line.split()[1]:line.split()[0] for line in refs.splitlines()}
    assert remote['refs/heads/'+BASE]==BASE_COMMIT
    assert remote['refs/heads/'+HEAD_BRANCH]==head
    # The complete inherited repository may exceed GitHub's recursive-tree limit.
    # Traverse only needed directories, each anchored by its parent's exact tree SHA.
    tree_cache={}
    def entries_for(tree_sha):
        if tree_sha not in tree_cache:
            number=len(tree_cache)+1
            args=['gh','api',f'repos/{REPOSITORY}/git/trees/{tree_sha}']
            write(destination/f'tree_{number:03d}_before.json',dict(command=args,expected_tree_SHA=tree_sha))
            tick=time.perf_counter();tree=json.loads(command(args))
            assert tree['sha']==tree_sha and not tree.get('truncated',False)
            tree_cache[tree_sha]={entry['path']:entry for entry in tree['tree']}
            write(destination/f'tree_{number:03d}_after.json',dict(response=tree,engineering_seconds=time.perf_counter()-tick,returncode=0))
        return tree_cache[tree_sha]
    def remote_entry(relative):
        components=relative.split('/');tree_sha=head
        for index,component in enumerate(components):
            entry=entries_for(tree_sha)[component]
            if index+1<len(components):
                assert entry['type']=='tree',(relative,entry)
                tree_sha=entry['sha']
        assert entry['type']=='blob',(relative,entry)
        return entry
    identity=read(OUT/'development03/identity.json')
    bindings_checked=0
    for relative,expected in identity['source_hashes'].items():
        assert sha(ROOT/relative)==expected,relative
        assert remote_entry(relative)['sha']==command(['git','rev-parse',head+':'+relative])
        bindings_checked+=1
    package=OUT/'compact_evidence';manifest=read(package/'manifest.json')
    parts=read(package/'parts_manifest.json')
    assert sha(package/'manifest.json')==parts['original_manifest_SHA']
    assert sha(ROOT/'scripts/round107_reader.py')==manifest['reader_SHA']
    assert len(parts['archive_parts'])==7
    required=[p.relative_to(ROOT).as_posix() for p in (OUT/'reports05').iterdir() if p.is_file()]
    required+=['scripts/round107_reader.py','scripts/round107_restore.py']
    required+=[(OUT/name).relative_to(ROOT).as_posix() for name in [
        'final_report.md','mathematical_algorithm.md','scope_contract.md',
        'master_retention_table.md','development_protocol.json','confirmation_protocol.json',
        'admission_decision.json','confirmation_cancellation.json','source_runtime_manifest.json',
        'reproduce.md','RESUME.md','evidence_index.md','completion_checklist.json']]
    required+=[(OUT/'review'/name).relative_to(ROOT).as_posix() for name in [
        'performance_admission.json','final_implementation_performance_review.md',
        'delivery_review.md','delivery_review.json']]
    required+=[(package/name).relative_to(ROOT).as_posix() for name in
        ['manifest.json','parts_manifest.json']+[part['path'] for part in parts['archive_parts']]]
    checked=[]
    for number,relative in enumerate(sorted(set(required)),1):
        source=ROOT/relative;expected=sha(source);size=source.stat().st_size
        entry=remote_entry(relative)
        assert entry['sha']==command(['git','rev-parse',head+':'+relative])
        assert entry['size']==size
        raw_url=f'https://raw.githubusercontent.com/{REPOSITORY}/{head}/{quote(relative,safe="/")}'
        stderr=destination/f'network_{number:03d}_stderr.log'
        tick=time.perf_counter();hasher=hashlib.sha256();length=0
        # Native curl preserves compressed bytes; gh's Windows text conversion
        # rejected the binary gzip header. TLS verification remains enabled.
        args=['curl.exe','--fail','--silent','--show-error','--location',
            '--connect-timeout','30','--max-time','300',raw_url]
        write(destination/f'network_{number:03d}_before.json',dict(command=args,path=relative,expected_SHA=expected,expected_bytes=size))
        with stderr.open('x',encoding='utf-8') as error:
            process=subprocess.Popen(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=error)
            while block:=process.stdout.read(1024*1024):
                hasher.update(block);length+=len(block)
            code=process.wait(timeout=300)
        record=dict(path=relative,github_blob_SHA=entry['sha'],bytes=length,
            sha256=hasher.hexdigest(),returncode=code,engineering_seconds=time.perf_counter()-tick,
            source_url=f'https://github.com/{REPOSITORY}/blob/{head}/{relative}',raw_download_url=raw_url)
        write(destination/f'network_{number:03d}_after.json',record)
        assert code==0 and length==size and record['sha256']==expected,(relative,record,expected,size)
        checked.append(record)
        print(json.dumps(dict(public_file_verified=relative,bytes=length)),flush=True)
    local_names=command(['git','ls-tree','-r','--name-only',head]).splitlines()
    additions=command(['git','diff','--name-only',BASE_COMMIT,head]).splitlines()
    assert 'results/unified_exact_round107/compact_evidence/evidence.tar.gz' not in local_names
    assert not any(Path(name).suffix.lower() in ['.exe','.dll','.lic','.key','.pem','.pyc','.pdb','.obj','.o'] for name in additions)
    result=dict(status='PASS_REMOTE_DRAFT_AND_EXACT_PUBLIC_PAYLOAD',PR=pr,
        verified_payload_commit=head,base_commit=BASE_COMMIT,remote_refs=remote,
        public_files=checked,public_file_count=len(checked),production_source_bindings_checked=bindings_checked,
        nonrecursive_trees_checked=len(tree_cache),
        round107_archive_SHA=manifest['archive_sha256'],reader_SHA=manifest['reader_SHA'],
        no_unsplit_archive_or_forbidden_binary_in_new_diff=True,
        Optimize_calls=0,IIS_calls=0,paid_starts=0,
        verifier_SHA=sha(__file__),started_unix=started,finished_unix=time.time(),
        metadata_followup_note='This actual verification receipt may be committed afterward; source/runtime/carrier/table payload is pinned to the verified commit above.')
    write(destination/'result.json',result)
    print(json.dumps(dict(status=result['status'],payload_commit=head,public_files=len(checked),Optimize_calls=0,IIS_calls=0)))

if __name__=='__main__':verify(sys.argv[1],sys.argv[2])
