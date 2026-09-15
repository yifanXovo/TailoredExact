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
OUT=ROOT/'results/unified_exact_round79/publication_api'
TEMP=ROOT/'build/round79/publication_api'
GH='C:/Program Files/GitHub CLI/gh.exe'
REPO='repos/yifanXovo/TailoredExact'
BRANCH='codex/round79-bdsc-small-validation'

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
        for commit in commits:
            raw=git('cat-file','commit',commit)
            assert hashlib.sha1(b'commit '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==commit
            header,message=raw.decode('utf-8').split('\n\n',1)
            lines=header.splitlines()
            assert all(line.split(' ',1)[0] in ['tree','parent','author','committer'] for line in lines)
            fields={key:value for key,value in (line.split(' ',1) for line in lines) if key!='parent'}
            parents=[line[7:] for line in lines if line.startswith('parent ')]
            assert len(parents)==1,'Only the existing linear publication branch is supported'
            parent=parents[0];elements=[]
            paths=git('diff-tree','--name-only','-r','--no-commit-id','--no-renames','-z',parent,commit).split(b'\0')
            for rawpath in paths:
                if not rawpath:continue
                path=rawpath.decode('utf-8')
                entry=git('ls-tree','-z',commit,'--',path)
                if not entry:
                    elements.append(dict(path=path,mode='100644',type='blob',sha=None));continue
                meta,actual_path=entry[:-1].split(b'\t',1)
                assert actual_path==rawpath
                mode,kind,sha=meta.decode().split()
                assert kind=='blob','Unexpected non-blob publication change'
                if sha not in uploaded:
                    data=git('cat-file','blob',sha)
                    response=api('POST','git/blobs',dict(content=base64.b64encode(data).decode(),encoding='base64'))
                    assert response['sha']==sha,'Uploaded blob is not byte-identical'
                    uploaded.add(sha)
                elements.append(dict(path=path,mode=mode,type=kind,sha=sha))
            base_tree=git('rev-parse',parent+'^{tree}').decode().strip()
            tree=api('POST','git/trees',dict(base_tree=base_tree,tree=elements))
            assert tree['sha']==fields['tree'],'Complete tree hash mismatch; no ref update'
            created=api('POST','git/commits',dict(message=message,tree=tree['sha'],parents=parents,
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
