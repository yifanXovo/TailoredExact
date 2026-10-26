"""Copy only the five preregistered input bytes from their pinned commits."""
from round133_common import *

def main():
    rows=[]
    for name in ('D_matrix_draft.json','D3_matrix_draft.json'):
        plan=read(OUT/'plans'/name)
        for arm in plan['arms']:
            source=arm['input'];target=Path(source['planned_staged_path'])
            assert target.parent==OUT/'inputs' and target.name==source['filename']
            data=git('show',source['source_public_commit']+':'+source['source_repository_path'])
            assert len(data)==source['bytes'] and hashlib.sha256(data).hexdigest()==source['SHA256']
            if target.exists():assert target.read_bytes()==data
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('xb') as stream:stream.write(data)
            row=dict(path=target.relative_to(ROOT).as_posix(),SHA=sha(target),bytes=len(data),
                     source_commit=source['source_public_commit'],source_path=source['source_repository_path'])
            if row not in rows:rows.append(row)
    assert len({r['path'] for r in rows})==5
    write(OUT/'infra/staged_inputs.json',dict(inputs=rows,Optimize=0,generated_inputs=0,
          no_historical_raw_or_solution_read=True,source_drafts_unchanged=True))
    print(json.dumps(dict(input_files=5,bytes=sum(r['bytes'] for r in rows),Optimize=0)))

if __name__=='__main__':main()
