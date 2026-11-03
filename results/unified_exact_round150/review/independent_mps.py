"""Read the actual MPS with no solver dependency and compare old semantics."""
from pathlib import Path
import collections, hashlib, json, sys, time

def read_mps(path):
    section=None; rows={}; cols={}; rhs={}; bounds={}; ranges={}; sense='MIN'
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('*'):continue
        parts=line.split()
        if not line.startswith(' ') and parts[0] in {'NAME','ROWS','COLUMNS','RHS','BOUNDS','RANGES','ENDATA','OBJSENSE','OBJNAME'}:
            section=parts[0];continue
        if section=='ROWS':
            kind,name=parts;assert name not in rows;rows[name]=kind
        elif section=='COLUMNS':
            if 'MARKER' in parts[1].strip("'"): continue
            name=parts[0];terms=cols.setdefault(name,{})
            for r,x in zip(parts[1::2],parts[2::2]):
                assert r not in terms,(name,r);terms[r]=float(x)
        elif section=='RHS':
            for r,x in zip(parts[1::2],parts[2::2]):
                assert r not in rhs;rhs[r]=float(x)
        elif section=='RANGES':
            for r,x in zip(parts[1::2],parts[2::2]):ranges[r]=float(x)
        elif section=='BOUNDS':
            kind,vector,name=parts[:3];value=float(parts[3]) if len(parts)>3 else None
            bounds.setdefault(name,[]).append((kind,value))
        elif section=='OBJSENSE':sense=parts[0]
        elif section in {'NAME','ENDATA','OBJNAME'}:pass
        else:raise AssertionError((section,line))
    return dict(rows=rows,columns=cols,rhs=rhs,bounds=bounds,ranges=ranges,sense=sense)

def compare(before_path,after_path,prefix='r150_CPF_'):
    start=time.perf_counter();before=read_mps(before_path);after=read_mps(after_path)
    added={name for name in after['rows'] if name.startswith(prefix)}
    assert added
    stripped=dict(after)
    stripped['rows']={k:v for k,v in after['rows'].items() if k not in added}
    stripped['rhs']={k:v for k,v in after['rhs'].items() if k not in added}
    stripped['ranges']={k:v for k,v in after['ranges'].items() if k not in added}
    stripped['columns']={k:{r:x for r,x in terms.items() if r not in added} for k,terms in after['columns'].items()}
    assert before==stripped, 'Old MPS semantics changed after deleting CPF rows'
    actual={name:dict(sense=after['rows'][name],rhs=after['rhs'].get(name,0.),terms={}) for name in added}
    for variable,terms in after['columns'].items():
        for row,value in terms.items():
            if row in actual:actual[row]['terms'][variable]=value
    return dict(PASS=True,Native_load=0,Optimize=0,added_rows=len(added),
        added_nonzeros=sum(len(row['terms']) for row in actual.values()),
        before_rows=len(before['rows']),after_rows=len(after['rows']),columns=len(before['columns']),
        actual_rows=actual,elapsed_seconds=time.perf_counter()-start)

if __name__=='__main__':
    result=compare(*sys.argv[1:3],sys.argv[3] if len(sys.argv)>3 else 'r150_CPF_')
    print(json.dumps({k:v for k,v in result.items() if k!='actual_rows'}))
