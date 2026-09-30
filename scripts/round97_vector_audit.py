"""Independent saved-vector audit of actual Gurobi model rows, zero Optimize.

Run only while no solver/build is active. Uses fsum, native loaded matrix and
saved CSV, not the C++ route mapper or its residual implementation.
"""
import csv, ctypes as c, json, math, sys, time
from pathlib import Path
from round96_prepare import read, write, sha
from round97_build import ROOT, OUT
import round96_external as ext

def check(destination, label):
    ext.ensure_idle();started=time.perf_counter();dest=Path(destination)
    if not dest.is_absolute():dest=ROOT/dest
    folder=dest/'external/round97'
    events=[json.loads(s) for s in (folder/'events.jsonl').read_text().splitlines()]
    events=[e for e in events if e['kind']=='solution']
    files={sha(p):p for p in (dest/'external/models').glob('*.lp')}
    api=c.CDLL('D:/gurobi1302/win64/bin/gurobi130.dll')
    ptr=c.c_void_p;ip=c.POINTER(c.c_int);dp=c.POINTER(c.c_double)
    def bind(name,args):
        f=getattr(api,name);f.argtypes=args;f.restype=c.c_int;return f
    empty=bind('GRBemptyenv',[c.POINTER(ptr)])
    start=bind('GRBstartenv',[ptr]);setint=bind('GRBsetintparam',[ptr,c.c_char_p,c.c_int])
    load=bind('GRBreadmodel',[ptr,c.c_char_p,c.POINTER(ptr)])
    geti=bind('GRBgetintattr',[ptr,c.c_char_p,ip]);getd=bind('GRBgetdblattr',[ptr,c.c_char_p,dp])
    getda=bind('GRBgetdblattrarray',[ptr,c.c_char_p,c.c_int,c.c_int,dp])
    getca=bind('GRBgetcharattrarray',[ptr,c.c_char_p,c.c_int,c.c_int,c.c_char_p])
    getsa=bind('GRBgetstrattrarray',[ptr,c.c_char_p,c.c_int,c.c_int,c.POINTER(c.c_char_p)])
    rows=bind('GRBgetconstrs',[ptr,ip,ip,ip,dp,c.c_int,c.c_int])
    api.GRBfreemodel.argtypes=[ptr];api.GRBfreeenv.argtypes=[ptr]
    def ok(code):assert code==0,code
    def integer(m,name):v=c.c_int();ok(geti(m,name.encode(),c.byref(v)));return v.value
    def scalar(m,name):v=c.c_double();ok(getd(m,name.encode(),c.byref(v)));return v.value
    def doubles(m,name,n):a=(c.c_double*n)();ok(getda(m,name.encode(),0,n,a));return a
    env=ptr();ok(empty(c.byref(env)));ok(setint(env,b'OutputFlag',0));ok(start(env))
    audit=[];seen=set()
    try:
        for h in sorted({e['model_sha256'] for e in events}):
            related=[e for e in events if e['model_sha256']==h]
            vectors=[]
            for e in related:
                source=folder/f'vector_{e["event"]}.csv'
                if source.exists():vectors.append((e,source,'input',e['model_objective']))
                if e.get('mapped_vector'):vectors.append((e,folder/e['mapped_vector'],'mapped',e['model_objective_candidate']))
            if not vectors:continue
            assert h in files,('missing immutable actual model',h)
            m=ptr();ok(load(env,str(files[h]).encode(),c.byref(m)))
            try:
                n=integer(m,'NumVars');r=integer(m,'NumConstrs')
                assert integer(m,'NumQNZs')==integer(m,'NumQConstrs')==integer(m,'NumGenConstrs')==0
                assert integer(m,'ModelSense')==1
                names=(c.c_char_p*n)();ok(getsa(m,b'VarName',0,n,names));names=[x.decode() for x in names]
                lb=doubles(m,'LB',n);ub=doubles(m,'UB',n);obj=doubles(m,'Obj',n);rhs=doubles(m,'RHS',r)
                types=c.create_string_buffer(n);senses=c.create_string_buffer(r)
                ok(getca(m,b'VType',0,n,types));ok(getca(m,b'Sense',0,r,senses))
                nnz=c.c_int();ok(rows(m,c.byref(nnz),None,None,None,0,r))
                begins=(c.c_int*r)();idx=(c.c_int*nnz.value)();coef=(c.c_double*nnz.value)()
                ok(rows(m,c.byref(nnz),begins,idx,coef,0,r));starts=list(begins)+[nnz.value]
                for e,path,kind,expected in vectors:
                    with path.open(newline='') as f:table=list(csv.DictReader(f))
                    assert [v['name'] for v in table]==names
                    values=[float(v['value']) for v in table];assert all(math.isfinite(v) for v in values)
                    bt=1e-6 if kind=='input' else 1e-7;it=1e-5 if kind=='input' else 1e-7
                    for j,x in enumerate(values):
                        assert lb[j]-bt<=x<=ub[j]+bt,(path,names[j],'bounds')
                        if types[j] in (b'I',b'B'):assert abs(x-round(x))<=it,(path,names[j],'integer')
                    maximum=0
                    for row in range(r):
                        a=math.fsum(coef[k]*values[idx[k]] for k in range(starts[row],starts[row+1]))
                        sense=senses[row];violation=(a-rhs[row] if sense==b'<' else rhs[row]-a if sense==b'>' else abs(a-rhs[row]))
                        maximum=max(maximum,violation)
                        assert violation<=bt*max(1,abs(a),abs(rhs[row])),(path,row,violation)
                    objective=scalar(m,'ObjCon')+math.fsum(obj[j]*values[j] for j in range(n))
                    assert abs(objective-expected)<=1e-6,(path,objective,expected)
                    audit.append(dict(event=e['event'],kind=kind,path=path.relative_to(ROOT).as_posix(),sha256=sha(path),
                        model_sha256=h,columns=n,rows=r,maximum_absolute_residual=maximum,objective=objective))
                    seen.add(path)
            finally:api.GRBfreemodel(m)
    finally:api.GRBfreeenv(env)
    write(OUT/(label+'.json'),dict(passed=True,optimizer_calls=0,wall_seconds=time.perf_counter()-started,
        vectors=audit,source_sha256=sha(__file__),scope='Every retained source/mapped CSV against its exact actual canonical linear model; numerical, not rational certificate.'))
    print(json.dumps(dict(passed=True,vectors=len(audit),optimizer_calls=0)))

if __name__=='__main__':check(sys.argv[1],sys.argv[2])
