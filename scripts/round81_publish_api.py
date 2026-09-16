"""Publish exact existing Git objects through authenticated gh, without rewriting history."""
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
OUT=ROOT/'results/unified_exact_round81/publication_api'
TEMP=ROOT/'build/round81/publication_api'
GH='C:/Program Files/GitHub CLI/gh.exe'
REPO='repos/yifanXovo/TailoredExact'
BRANCH='codex/round81-bdsc-long-protection-replication'

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
    def api(method,path,data=None):
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
        if run.returncode:raise RuntimeError('GitHub API request failed; see ledger')
        return result
    try:
        current=api('GET','git/ref/heads/'+BRANCH)['object']['sha']
        record['initial_remote_head']=current;save()
        assert subprocess.run(['git','merge-base','--is-ancestor',current,target],cwd=ROOT).returncode==0
        commits=git('rev-list','--reverse',current+'..'+target).decode().splitlines()
        record['original_commits']=commits;save()
        uploaded=set()
        for older in OUT.glob('*.json'):
            previous=json.loads(older.read_text(encoding='utf-8'))
            for request in previous.get('requests',[]):
                if request['path']=='git/blobs' and request['returncode']==0:
                    uploaded.add(request['returned_sha'])
        def tree_entries(tree):
            if tree is None:return {}
            entries={}
            for row in git('ls-tree','-z',tree).split(b'\0'):
                if not row:continue
                meta,path=row.split(b'\t',1)
                mode,kind,digest=meta.decode().split()
                name=path.decode('utf-8')
                assert '/' not in name and kind in ['blob','tree']
                entries[name]=dict(path=name,mode=mode,type=kind,sha=digest)
            return entries
        def exact_tree(previous,target_tree):
            if previous==target_tree:return target_tree
            old=tree_entries(previous);new=tree_entries(target_tree)
            for name,entry in new.items():
                before=old.get(name)
                if before==entry:continue
                digest=entry['sha']
                if entry['type']=='tree':
                    exact_tree(before['sha'] if before and before['type']=='tree' else None,digest)
                elif digest not in uploaded:
                    data=git('cat-file','blob',digest)
                    response=api('POST','git/blobs',dict(content=base64.b64encode(data).decode(),encoding='base64'))
                    assert response['sha']==digest,'Uploaded blob is not byte-identical'
                    uploaded.add(digest)
            # Publish only immediate directory entries. Referencing unchanged
            # child trees avoids the API's recursive base-tree expansion timeout.
            created=api('POST','git/trees',dict(tree=list(new.values())))
            assert created['sha']==target_tree,'Original subtree hash mismatch; no ref update'
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
            created=api('POST','git/commits',dict(message=message,tree=fields['tree'],parents=parents,
                author=identity(fields['author']),committer=identity(fields['committer'])))
            assert created['sha']==commit,'Original commit hash mismatch; no ref update'
            record.setdefault('verified_exact_commits',[]).append(commit);save()
            print(json.dumps(dict(verified_original_commit=commit)),flush=True)
        fresh=api('GET','git/ref/heads/'+BRANCH)['object']['sha']
        assert fresh==current,'Remote changed concurrently; no ref update'
        if current!=target:
            changed=api('PATCH','git/refs/heads/'+BRANCH,dict(sha=target,force=False))
            assert changed['object']['sha']==target
        final=api('GET','git/ref/heads/'+BRANCH)['object']['sha']
        assert final==target
        record.update(passed=True,final_remote_head=final,original_history_preserved=True)
        save();print(json.dumps({k:v for k,v in record.items() if k!='requests'}),flush=True)
    except Exception as exc:
        record.update(passed=False,error=repr(exc));save();raise

if __name__=='__main__':main()
