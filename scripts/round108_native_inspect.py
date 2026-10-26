"""Actual installed-DLL model/readback qualification. Never calls Optimize/IIS."""
import ctypes as ct
import collections, json, math
from round108_common import *
import generate_citibike443_regional_v1 as parser

def models(paths):
    dll=ct.WinDLL(str(DLL))
    P=ct.c_void_p;I=ct.c_int;D=ct.c_double;C=ct.c_char;S=ct.c_char_p
    signatures={
      'loadenv':([ct.POINTER(P),S],I),'readmodel':([P,S,ct.POINTER(P)],I),
      'getintattr':([P,S,ct.POINTER(I)],I),'getdblattr':([P,S,ct.POINTER(D)],I),
      'getstrattrelement':([P,S,I,ct.POINTER(S)],I),
      'getdblattrarray':([P,S,I,I,ct.POINTER(D)],I),'getcharattrarray':([P,S,I,I,ct.POINTER(C)],I),
      'getconstrs':([P,ct.POINTER(I),ct.POINTER(I),ct.POINTER(I),ct.POINTER(D),I,I],I),
      'setintparam':([P,S,I],I),'freemodel':([P],None),'freeenv':([P],None),
      'version':([ct.POINTER(I),ct.POINTER(I),ct.POINTER(I)],None)}
    for name,(args,ret) in signatures.items():
        fun=getattr(dll,'GRB'+name);fun.argtypes=args;fun.restype=ret
    def ok(x):assert x==0,('native API error',x)
    version=[I(),I(),I()];dll.GRBversion(*(ct.byref(x) for x in version))
    assert [x.value for x in version]==[13,0,2]
    e=P();ok(dll.GRBloadenv(ct.byref(e),None));ok(dll.GRBsetintparam(e,b'OutputFlag',0));result={}
    try:
        for key,path in paths.items():
            m=P();ok(dll.GRBreadmodel(e,str(path).encode(),ct.byref(m)))
            try:
                nv=I();nr=I();nz=I();sense=I();off=D()
                for attr,v in [(b'NumVars',nv),(b'NumConstrs',nr),(b'NumNZs',nz),(b'ModelSense',sense)]:ok(dll.GRBgetintattr(m,attr,ct.byref(v)))
                ok(dll.GRBgetdblattr(m,b'ObjCon',ct.byref(off)))
                n=nv.value;r=nr.value;types=(C*n)();ok(dll.GRBgetcharattrarray(m,b'VType',0,n,types))
                arrays={}
                for attr in ['LB','UB','Obj']:
                    a=(D*n)();ok(dll.GRBgetdblattrarray(m,attr.encode(),0,n,a));arrays[attr]=list(a)
                names=[]
                for j in range(n):v=S();ok(dll.GRBgetstrattrelement(m,b'VarName',j,ct.byref(v)));names.append(v.value.decode())
                senses=(C*r)();rhs=(D*r)();ok(dll.GRBgetcharattrarray(m,b'Sense',0,r,senses));ok(dll.GRBgetdblattrarray(m,b'RHS',0,r,rhs))
                total=I();ok(dll.GRBgetconstrs(m,ct.byref(total),None,None,None,0,r))
                beg=(I*r)();ind=(I*total.value)();val=(D*total.value)()
                ok(dll.GRBgetconstrs(m,ct.byref(total),beg,ind,val,0,r))
                rows=[]
                for j in range(r):
                    end=beg[j+1] if j+1<r else total.value
                    terms=sorted((names[ind[k]],val[k]) for k in range(beg[j],end) if val[k])
                    rows.append(dict(sense=senses[j].decode(),rhs=rhs[j],terms=terms))
                result[key]=dict(path=str(path),SHA=sha(path),columns=[dict(name=names[j],type=types[j].decode(),
                    lower=arrays['LB'][j],upper=arrays['UB'][j],objective=arrays['Obj'][j]) for j in range(n)],
                    rows=rows,row_count=r,column_count=n,nonzeros=total.value,objective_sense=sense.value,objective_constant=off.value)
            finally:dll.GRBfreemodel(m)
    finally:dll.GRBfreeenv(e)
    return result

def matrix(destination):
    d=Path(destination);native=models({a:d/(a+'.lp') for a in ['ENS-C','M-B']})
    a,b=native['ENS-C'],native['M-B']
    numeric=lambda q:[{k:v for k,v in c.items() if k!='type'} for c in q['columns']]
    assert numeric(a)==numeric(b) and a['objective_sense']==b['objective_sense'] and a['objective_constant']==b['objective_constant']
    changed=[x['name'] for x,y in zip(a['columns'],b['columns']) if x['type']!=y['type']]
    quantities=[x['name'] for x in a['columns'] if x['name'].startswith(('p_','d_'))]
    assert changed==quantities and len(changed)==80
    for x,y in zip(a['columns'],b['columns']):
        if x['name'] in quantities:assert x['type']=='I' and y['type']=='C'
        elif x['name'].startswith(('x_','load_','Y_','state_','z_','mode_')):
            assert x['type']==y['type']
    normalize=lambda row:(row['sense'],row['rhs'],tuple(tuple(t) for t in row['terms']))
    old=collections.Counter(map(normalize,a['rows']));new=collections.Counter(map(normalize,b['rows']))
    assert not old-new;added=new-old
    assert a['row_count']==9269 and b['row_count']==9309 and a['column_count']==b['column_count']==3488
    initial=parser.parse_instance_mirror(ROOT/'reference/round86_unadapted_confirmation/F2.txt')['initial']
    actual_names={x['name'] for x in b['columns']};expected=[]
    for i in range(1,21):
        terms=[(f'{q}_{k}_{i}',1.) for k in range(2) for q in ['p','d']]
        for name in actual_names:
            if name.startswith(f'state_{i}_'):
                suffix=name[len(f'state_{i}_'):]
                if suffix.isdigit() and abs(initial[i]-int(suffix)):
                    terms.append((name,-float(abs(initial[i]-int(suffix)))))
        expected.append(('=',0.,tuple(sorted(terms))))
        terms=[(f'z_{k}_{i}',1.) for k in range(2)]
        if f'state_{i}_{initial[i]}' in actual_names:terms.append((f'state_{i}_{initial[i]}',1.))
        expected.append(('=',1.,tuple(sorted(terms))))
    assert added==collections.Counter(expected),'actual A/B semantics differ'
    write(d/'native_models.json',native)
    value=dict(passed=True,Optimize_calls=0,IIS_calls=0,installed_DLL_SHA=sha(DLL),native_version=[13,0,2],
        ordered_numeric_columns_bounds_objective_equal=True,removed_original_rows=0,added_AB_rows=40,
        changed_quantity_types=changed,ENS_C_rows=9269,M_B_rows=9309,columns=3488,
        native_readback_SHA=sha(d/'native_models.json'),historical_scope_only=True,
        no_diagnostic_witness_in_formal_Start=True)
    write(d/'matrix_comparison.json',value)
    return value
