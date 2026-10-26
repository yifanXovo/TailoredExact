"""Verify an actual published Round108 draft and public bytes; no mutation."""
import argparse, base64, csv, hashlib, io, json, subprocess, sys, time
from pathlib import Path

REPO = 'yifanXovo/TailoredExact'
BASE = 'b5db3f038f64215766a54498d8acc82e384de733'
BRANCH = 'codex/round108-frozen-mb-validation'
BASE_BRANCH = 'codex/round107-ens-frontier-route-events'
ROUND = 'results/unified_exact_round108'
GH = 'C:/Program Files/GitHub CLI/gh.exe'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')

def run(root, pr_number, head, label, isolated_review):
    root = Path(root).resolve()
    here = Path(__file__).resolve().parent / label
    here.mkdir(exist_ok=False)
    commands = []
    begin = time.perf_counter()

    def command(args):
        started = time.perf_counter()
        child = subprocess.run(args, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        commands.append(dict(command=args, exit_code=child.returncode,
            seconds=time.perf_counter()-started,
            stdout_SHA=hashlib.sha256(child.stdout).hexdigest(),
            stderr_SHA=hashlib.sha256(child.stderr).hexdigest()))
        assert child.returncode == 0, (args, child.returncode, child.stderr.decode(errors='replace'))
        return child.stdout

    def api(endpoint):
        return json.loads(command([GH, 'api', endpoint]))

    def blob_oid(path):
        return command(['git', 'rev-parse', head+':'+path]).decode().strip()

    launch = dict(command=[sys.executable, str(Path(__file__).resolve()), '--root', str(root),
        '--pr-number', str(pr_number), '--head', head, '--label', label, '--isolated-review', isolated_review],
        read_root=str(root), source_SHA=sha(__file__), engineering=True, Optimize=0, IIS=0)
    write(here/'launch.json', launch)
    assert command(['git','rev-parse','HEAD']).decode().strip() == head
    remote = command(['git', 'ls-remote', 'origin', 'refs/heads/'+BRANCH, 'refs/heads/'+BASE_BRANCH]).decode()
    remote_refs = dict((line.split()[1], line.split()[0]) for line in remote.splitlines())
    assert remote_refs['refs/heads/'+BRANCH] == head
    assert remote_refs['refs/heads/'+BASE_BRANCH] == BASE
    pr = api(f'repos/{REPO}/pulls/{pr_number}')
    prior = api(f'repos/{REPO}/pulls/169')
    assert pr['head']['sha'] == head and pr['head']['ref'] == BRANCH
    assert pr['base']['sha'] == BASE and pr['base']['ref'] == BASE_BRANCH
    assert pr['draft'] is True and pr['state'] == 'open'
    assert prior['head']['sha'] == BASE and prior['head']['ref'] == BASE_BRANCH
    assert prior['draft'] is True and prior['state'] == 'open'
    prepared = (root/ROUND/'engineering/public_pr_body01/body.md').read_text(encoding='utf-8')
    assert pr['body'] == prepared
    report = (root/ROUND/'final_report.md').read_text(encoding='utf-8')
    assert pr['body'].startswith(report)
    write(here/'pr_metadata.json', dict(url=pr['html_url'], number=pr['number'], title=pr['title'],
        head=pr['head']['sha'], base=pr['base']['sha'], head_ref=pr['head']['ref'],
        base_ref=pr['base']['ref'], isDraft=pr['draft'], state=pr['state'], body=pr['body']))
    write(here/'R107_metadata.json', dict(url=prior['html_url'], head=prior['head']['sha'],
        head_ref=prior['head']['ref'], base_ref=prior['base']['ref'], isDraft=prior['draft'],
        state=prior['state'], updated_at=prior['updated_at']))
    candidate = read(root/ROUND/'candidate_identity.json')
    assert all(sha(root/p)==h for p,h in candidate['source_bindings'].items())
    assert all(sha(root/p)==h for p,h in candidate['helpers'].items())
    assert command(['git','diff','--name-only',BASE,head,'--','src','include','tests','CMakeLists.txt']).strip()==b''
    baseline = read(root/ROUND/'baseline.json')
    assert all(sha(Path(baseline['original_checkout'])/p)==h for p,h in baseline['user_tracked_changes'].items())
    manifest = read(root/ROUND/'compact_evidence/manifest.json')
    critical = ['final_report.md','research_decision.md','candidate_identity.json','representation_contract.md',
        'development_protocol.json','confirmation_protocol.json','input_manifest.json',
        'admission_decision.json','selection_decision.json','reproduce.md','RESUME.md',
        'public_pack_receipt.json','public_export_receipt.json','public_restore_receipt.json',
        'public_comparison_receipt.json','reports_final/summary.json','reports_final/arms.csv',
        'reports_final/pairs.csv','reports_final/worst_losses.csv','reports_final/candidate_evidence_gap.csv',
        'reports_final/stopped_mechanism_families.csv','review/final_local_review01.json',
        'review/packaging_exact_parts_review01.json',isolated_review.removeprefix(ROUND+'/')]
    checks = []
    for name in critical:
        path = ROUND+'/'+name
        response = api(f'repos/{REPO}/contents/{path}?ref={head}')
        assert response['type']=='file' and response['encoding']=='base64'
        data = base64.b64decode(response['content'])
        assert data == (root/path).read_bytes()
        assert response['sha'] == blob_oid(path)
        checks.append(dict(path=path, bytes=len(data), SHA256=hashlib.sha256(data).hexdigest(),
            remote_Git_blob=response['sha'], remote_content_read=True, exact_local_bytes=True))
    folder = api(f'repos/{REPO}/contents/{ROUND}/compact_evidence?ref={head}')
    expected = {'manifest.json'} | {p['path'] for p in manifest['parts']}
    if not manifest['parts']: expected.add(manifest['archive_path'])
    assert {p['name'] for p in folder} == expected
    combined = hashlib.sha256()
    for item in sorted(folder, key=lambda r:r['name']):
        path=item['path']
        assert item['type']=='file' and item['sha']==blob_oid(path)
        assert item['size']==(root/path).stat().st_size
        assert item['download_url'].startswith('https://raw.githubusercontent.com/')
        digest=hashlib.sha256(); size=0
        download_command=[GH,'api',f'repos/{REPO}/contents/{path}?ref={head}','-H','Accept: application/vnd.github.raw+json']
        download_begin=time.perf_counter();download_stderr=here/('download_'+item['name']+'.stderr.log')
        with download_stderr.open('xb') as errors:
            process=subprocess.Popen(download_command,cwd=root,stdout=subprocess.PIPE,stderr=errors)
            while block:=process.stdout.read(1024*1024):
                digest.update(block);size+=len(block)
                if item['name']!='manifest.json':combined.update(block)
            code=process.wait(timeout=120)
        commands.append(dict(command=download_command,exit_code=code,seconds=time.perf_counter()-download_begin,
            stdout_SHA=digest.hexdigest(),stdout_bytes=size,stderr_SHA=sha(download_stderr),
            raw_streamed=True,TLS_verification_not_disabled=True))
        assert code==0,(download_command,code,download_stderr.read_text(errors='replace'))
        assert size==item['size'] and digest.hexdigest()==sha(root/path)
        checks.append(dict(path=path,bytes=size,SHA256=digest.hexdigest(),remote_Git_blob=item['sha'],
            remote_content_read=True,exact_local_bytes=True))
    assert combined.hexdigest()==manifest['archive_sha256']
    write(here/'file_checks.json',checks)
    receipt=dict(**launch, exit_code=0, seconds=time.perf_counter()-begin,
        checked_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        remote_head=head,remote_base=BASE,remote_draft=True,R107_latest_unchanged=True,
        PR_body_exact_prepared_text=True,PR_tables_exact_final_report=True,
        required_public_files_readable=True,public_carrier_files_exact=True,
        combined_remote_archive_SHA=combined.hexdigest(),remote_carrier_part_count=len(manifest['parts']),
        production_and_helpers_unchanged=True,original_user_changes_preserved=True,
        file_checks_SHA=sha(here/'file_checks.json'),remote_files_checked=len(checks),
        pr_metadata_SHA=sha(here/'pr_metadata.json'),commands=commands,
        conservative_solver_starts=0,route_oracle=0)
    write(here/'receipt.json',receipt)
    print(json.dumps({k:receipt[k] for k in ['exit_code','seconds','remote_head','remote_base',
        'remote_draft','R107_latest_unchanged','remote_files_checked','combined_remote_archive_SHA']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for flag in ['root','head','label','isolated-review']:parser.add_argument('--'+flag,required=True)
    parser.add_argument('--pr-number',type=int,required=True)
    args=parser.parse_args()
    run(args.root,args.pr_number,args.head,args.label,args.isolated_review)
