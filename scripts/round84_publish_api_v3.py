"""Publish exact existing commits with inline text and verified binary blobs on nested base trees."""
import argparse
import base64
import datetime
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round84/publication_api'
TEMP=ROOT/'build/round84/publication_api'
GH='C:/Program Files/GitHub CLI/gh.exe'
REPO='repos/yifanXovo/TailoredExact'
BRANCH='codex/round84-ensc-long-protection-replication'

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)

def identity(line):
    match=re.fullmatch(r'(.+) <([^<>]+)> (\d+) ([+-]\d{4})',line)
    assert match,line
    name,email,epoch,offset=match.groups()
    minutes=int(offset[1:3])*60+int(offset[3:])
    if offset[0]=='-':minutes=-minutes
    zone=datetime.timezone(datetime.timedelta(minutes=minutes))
    date=datetime.datetime.fromtimestamp(int(epoch),zone).isoformat()
    return dict(name=name,email=email,date=date)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--head',required=True)
    parser.add_argument('--label',required=True)
    args=parser.parse_args()
    assert re.fullmatch(r'[a-z0-9_-]+',args.label)
    assert not (OUT.parent/'campaign/active_run.lock').exists(),'Close the original optimizer queue before binary-capable publication'
    target=git('rev-parse',args.head).decode().strip()
    OUT.mkdir(exist_ok=True);TEMP.mkdir(parents=True,exist_ok=True)
    ledger=OUT/(args.label+'.json');assert not ledger.exists()
    started=time.perf_counter()
    record=dict(target=target,branch=BRANCH,requests=[],optimizer_calls=0,
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='Exact blobs, tree and original commit hashes required before a non-force branch update')
    def save():
        record['wall_seconds']=time.perf_counter()-started
        ledger.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    def api(method,path,data=None,missing_ok=False):
        index=len(record['requests'])+1
        command=[GH,'api','--method',method,REPO+'/'+path]
        if data is not None:
            file=TEMP/f'{args.label}_{index}.json'
            file.write_text(json.dumps(data),encoding='utf-8')
            command+=['--input',str(file)]
        before=time.perf_counter()
        run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=120)
        result=json.loads(run.stdout) if run.returncode==0 else None
        row=dict(method=method,path=path,returncode=run.returncode,
                 wall_seconds=time.perf_counter()-before,stderr=run.stderr,
                 returned_sha=result.get('sha',result.get('object',{}).get('sha')) if result else None)
        record['requests'].append(row);save()
        if run.returncode:
            if missing_ok and method=='GET' and 'HTTP 404' in run.stderr:return None
            raise RuntimeError('GitHub API request failed; see ledger')
        return result
    try:
        existing=api('GET','git/ref/heads/'+BRANCH,missing_ok=True)
        if existing is None:
            initial='131d09280a1563243d0201e68367b26baf5079c3'
            assert subprocess.run(['git','merge-base','--is-ancestor',initial,target],cwd=ROOT).returncode==0
            assert api('GET','git/commits/'+initial)['sha']==initial
            try:
                existing=api('POST','git/refs',dict(ref='refs/heads/'+BRANCH,sha=initial))
            except RuntimeError:
                existing=api('GET','git/ref/heads/'+BRANCH)
            record['initial_branch_creation_base']=initial;save()
        current=existing['object']['sha']
        record['initial_remote_head']=current;save()
        assert subprocess.run(['git','merge-base','--is-ancestor',current,target],cwd=ROOT).returncode==0
        commits=git('rev-list','--reverse',current+'..'+target).decode().splitlines()
        record['original_commits']=commits;save()
        binary_verified=set()
        def exact_binary_blob(digest,data):
            if digest in binary_verified:return digest
            existing=api('GET','git/blobs/'+digest,missing_ok=True)
            if existing is None:
                try:
                    created=api('POST','git/blobs',dict(content=base64.b64encode(data).decode('ascii'),encoding='base64'))
                except RuntimeError:
                    created=api('GET','git/blobs/'+digest)
                    record.setdefault('recovered_uncertain_blob_creations',[]).append(digest)
                assert created['sha']==digest,'Original binary blob mismatch; no ref update'
                existing=api('GET','git/blobs/'+digest)
            assert existing['sha']==digest and existing['encoding']=='base64'
            decoded=base64.b64decode(existing['content'])
            assert decoded==data and existing['size']==len(data),'Binary readback mismatch; no ref update'
            assert hashlib.sha1(b'blob '+str(len(decoded)).encode()+b'\0'+decoded).hexdigest()==digest
            binary_verified.add(digest)
            record.setdefault('verified_binary_blobs',[]).append(dict(sha=digest,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
            save();return digest
        def exact_tree(previous,target_tree):
            if previous==target_tree:return target_tree
            assert previous is not None
            existing=api('GET','git/trees/'+target_tree,missing_ok=True)
            if existing is not None:
                assert existing['sha']==target_tree
                record.setdefault('verified_existing_trees',[]).append(target_tree);save()
                return target_tree
            # Preserve the reachable parent root and change nested file paths.
            # Text is inline; binary entries reference separately byte-verified blobs.
            # Exact resulting root hashes remain mandatory before any ref update.
            raw=git('diff-tree','--no-commit-id','--no-renames','-r','--raw','-z',previous,target_tree)
            parts=raw.split(b'\0');assert parts[-1]==b'';parts=parts[:-1]
            assert len(parts)%2==0
            elements=[]
            for i in range(0,len(parts),2):
                mode_before,mode_after,sha_before,sha_after,status=parts[i].decode().split()
                path=parts[i+1].decode('utf-8')
                if status=='D':
                    elements.append(dict(path=path,mode=mode_before[1:],type='blob',sha=None));continue
                assert status in ['A','M'] and mode_after in ['100644','100755']
                data=git('cat-file','blob',sha_after)
                assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==sha_after
                try:content=data.decode('utf-8') if b'\0' not in data else None
                except UnicodeDecodeError:content=None
                if content is None:
                    elements.append(dict(path=path,mode=mode_after,type='blob',sha=exact_binary_blob(sha_after,data)))
                else:
                    assert content.encode('utf-8')==data
                    elements.append(dict(path=path,mode=mode_after,type='blob',content=content))
            assert elements
            payload=dict(base_tree=previous,tree=elements)
            try:
                created=api('POST','git/trees',payload)
            except RuntimeError:
                created=api('GET','git/trees/'+target_tree)
                record.setdefault('recovered_uncertain_tree_creations',[]).append(target_tree)
            assert created['sha']==target_tree,'Original root tree mismatch; no ref update'
            record.setdefault('verified_exact_trees',[]).append(target_tree);save()
            return target_tree
        for commit in commits:
            raw=git('cat-file','commit',commit)
            assert hashlib.sha1(b'commit '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==commit
            header,message=raw.decode('utf-8').split('\n\n',1)
            lines=header.splitlines()
            assert all(line.split(' ',1)[0] in ['tree','parent','author','committer'] for line in lines)
            fields={key:value for key,value in (line.split(' ',1) for line in lines) if key!='parent'}
            parents=[line[7:] for line in lines if line.startswith('parent ')]
            assert len(parents)==1,'Only the existing linear publication branch is supported'
            parent=parents[0]
            base_tree=git('rev-parse',parent+'^{tree}').decode().strip()
            exact_tree(base_tree,fields['tree'])
            try:
                created=api('POST','git/commits',dict(message=message,tree=fields['tree'],parents=parents,
                    author=identity(fields['author']),committer=identity(fields['committer'])))
            except RuntimeError:
                created=api('GET','git/commits/'+commit)
                record.setdefault('recovered_uncertain_commit_creations',[]).append(commit)
            assert created['sha']==commit,'Original commit hash mismatch; no ref update'
            record.setdefault('verified_exact_commits',[]).append(commit);save()
            print(json.dumps(dict(verified_original_commit=commit)),flush=True)
        fresh=api('GET','git/ref/heads/'+BRANCH)['object']['sha']
        assert fresh==current,'Remote changed concurrently; no ref update'
        if current!=target:
            try:
                changed=api('PATCH','git/refs/heads/'+BRANCH,dict(sha=target,force=False))
            except RuntimeError:
                changed=api('GET','git/ref/heads/'+BRANCH)
                record['ref_read_after_uncertain_update']=True
            assert changed['object']['sha']==target
        final=api('GET','git/ref/heads/'+BRANCH)['object']['sha']
        assert final==target
        record.update(passed=True,final_remote_head=final,original_history_preserved=True)
        save();print(json.dumps({k:v for k,v in record.items() if k!='requests'}),flush=True)
    except Exception as exc:
        record.update(passed=False,error=repr(exc));save();raise

if __name__=='__main__':main()
