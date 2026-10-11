"""Observe current GitHub Draft identity and actual manifest/carrier Git objects."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO='yifanXovo/TailoredExact';ROUND='results/unified_exact_round113'
BASE='9165e69bf41d1eb323fd52b8cb4a8230dcb4edd4'
HEAD_BRANCH='codex/round113-geographic-attribution-completion'
BASE_BRANCH='codex/round112-paid-start-backend-attribution'
def command(args):return subprocess.check_output(args,cwd=ROOT)
def api(path):return json.loads(command(['gh','api','repos/'+REPO+'/'+path]))
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def byte_hashes(raw):
    size=len(raw)
    return size,hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest(),hashlib.sha256(raw).hexdigest()
def committed_blobs(local,names):
    names=sorted(names)
    data=command_with_input(['git','cat-file','--batch'],b''.join(local[n]['oid'].encode()+b'\n' for n in names))
    offset=0;blobs={}
    for name in names:
        end=data.index(b'\n',offset);oid,kind,size=data[offset:end].split();size=int(size);offset=end+1
        assert oid.decode()==local[name]['oid'] and kind==b'blob',name
        blobs[name]=data[offset:offset+size];offset+=size
        assert data[offset:offset+1]==b'\n',name
        offset+=1
    assert offset==len(data)
    return blobs
def command_with_input(args,data):return subprocess.check_output(args,cwd=ROOT,input=data)
def main(pr,head,destination):
    t=time.perf_counter();p=json.loads(command(['gh','pr','view',str(pr),'--repo',REPO,'--json','number,url,state,isDraft,headRefName,headRefOid,baseRefName']))
    assert p['state']=='OPEN' and p['isDraft'] and p['headRefOid']==head
    assert p['headRefName']==HEAD_BRANCH and p['baseRefName']==BASE_BRANCH
    base=api('git/ref/heads/'+BASE_BRANCH);ref=api('git/ref/heads/'+HEAD_BRANCH)
    assert base['object']['sha']==BASE and ref['object']['sha']==head
    command(['git','fetch','origin',HEAD_BRANCH]);assert command(['git','rev-parse','FETCH_HEAD']).decode().strip()==head
    changed=command(['git','diff','--name-only',BASE,head]).decode().splitlines()
    assert all(n.startswith(('scripts/',ROUND+'/')) for n in changed)
    candidate=json.loads(command(['git','show',head+':'+ROUND+'/candidate_identity.json']))
    manifest=json.loads(command(['git','show',head+':'+ROUND+'/compact_evidence/manifest.json']))
    manifest_files={v['path']:v for v in manifest['files']}
    required=set(changed)|set(candidate['source_bindings'])|set(candidate['helpers'])
    carrier_names=[v['path'] for v in manifest['parts']] or [manifest['archive_path']]
    required.update(ROUND+'/compact_evidence/'+n for n in carrier_names)
    required.add(ROUND+'/compact_evidence/manifest.json')
    local={}
    raw=command(['git','ls-tree','-rz',head,'--','scripts','src','include','tests','CMakeLists.txt',ROUND])
    for record in raw.split(b'\0'):
        if not record:continue
        left,name=record.split(b'\t',1);mode,kind,oid=left.decode().split();local[name.decode()]=dict(mode=mode,kind=kind,oid=oid)
    root=api('git/trees/'+head);assert not root['truncated'];top={v['path']:v for v in root['tree']};remote={}
    for prefix in sorted({n.split('/')[0] for n in required if not n.startswith('results/')}):
        entry=top[prefix]
        if entry['type']=='blob':remote[prefix]=entry;continue
        tree=api('git/trees/'+entry['sha']+'?recursive=1');assert not tree['truncated']
        remote.update({prefix+'/'+v['path']:v for v in tree['tree'] if v['type']=='blob'})
    results=api('git/trees/'+top['results']['sha']);assert not results['truncated']
    round_entry=next(v for v in results['tree'] if v['path']=='unified_exact_round113')
    tree=api('git/trees/'+round_entry['sha']+'?recursive=1');assert not tree['truncated']
    remote.update({ROUND+'/'+v['path']:v for v in tree['tree'] if v['type']=='blob'})
    blobs=committed_blobs(local,required);checks=[];normalized=[];tool_deltas=[]
    for name in sorted(required):
        size,oid,digest=byte_hashes(blobs[name]);working=(ROOT/name).read_bytes();raw_size,raw_oid,raw_digest=byte_hashes(working)
        assert local[name]['kind']=='blob' and local[name]['mode']=='100644'
        assert oid==local[name]['oid']==remote[name]['sha'] and size==remote[name]['size'] and remote[name]['mode']=='100644',name
        frozen=candidate['source_bindings'].get(name,candidate['helpers'].get(name))
        relation='EXACT_WORKING_AND_COMMITTED_BYTES'
        if frozen is not None:
            assert raw_digest==frozen==manifest_files[name]['sha256'] and raw_size==manifest_files[name]['bytes'],name
            if working!=blobs[name]:
                assert working.replace(b'\r\n',b'\n')==blobs[name],name
                relation='HISTORICAL_GIT_CRLF_TO_LF_RAW_BYTES_PRESERVED_IN_CARRIER';normalized.append(name)
        elif working!=blobs[name]:
            # A verifier fixed after scientific sealing is explicitly outside the observed scientific commit.
            assert name=='scripts/verify_round113_publication.py',name
            relation='POST_SCIENCE_PUBLICATION_VERIFIER_WORKING_DELTA';tool_deltas.append(name)
        checks.append(dict(path=name,committed_bytes=size,Git_blob_oid=oid,committed_SHA256=digest,
            working_bytes=raw_size,working_SHA256=raw_digest,byte_relation=relation,remote_Git_object_matches=True,
            frozen_raw_identity_matches_manifest=frozen is not None))
    for v in manifest['parts'] or [dict(path=manifest['archive_path'],bytes=manifest['archive_bytes'],sha256=manifest['archive_sha256'])]:
        check=next(r for r in checks if r['path']==ROUND+'/compact_evidence/'+v['path'])
        assert check['committed_bytes']==check['working_bytes']==v['bytes'] and check['committed_SHA256']==check['working_SHA256']==v['sha256']
    assert all((ROOT/ROUND/'compact_evidence'/n).stat().st_size<manifest['single_blob_limit_bytes'] for n in carrier_names)
    receipt=dict(passed=True,observed_PR=p,observed_head=head,verified_base_commit=BASE,required_objects=checks,
        carrier_archive_SHA=manifest['archive_sha256'],carrier_archive_bytes=manifest['archive_bytes'],actual_carrier_parts=len(manifest['parts']),
        remote_checks='GitHub PR/ref APIs, actual untruncated tree blob OIDs/sizes, fetched remote HEAD and hashed committed blob bytes; frozen raw source/helper bytes checked separately against exact manifest members',
        historical_Git_CRLF_to_LF_paths=normalized,post_science_verifier_working_delta=tool_deltas,
        verifier_execution_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        frozen_raw_sources_checked=len(candidate['source_bindings']),frozen_raw_helpers_checked=len(candidate['helpers']),
        receipt_not_in_observed_commit=True,no_future_commit_claim=True,engineering=True,seconds=time.perf_counter()-t,Optimize=0)
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(passed=True,PR=p['url'],head=head,objects=len(checks),archive_bytes=manifest['archive_bytes'],parts=len(manifest['parts']))))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pr',required=True,type=int);p.add_argument('--head',required=True);p.add_argument('--receipt',required=True);a=p.parse_args();main(a.pr,a.head,a.receipt)
