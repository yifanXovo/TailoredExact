"""Finite artificial physical/vector checks through actual writers; Optimize=0."""
from round127_common import *
import round108_reader as core
import math,re,copy

def physical_point(p,w,model):
    a=core.evidence.instance(ROOT,p);Y=list(a['b']);direct={}
    for route in w['routes']:
        k=route['vehicle'];load=0;ops={o['station']:o for o in route['operations']}
        for pos,(i,j) in enumerate(zip(route['nodes'],route['nodes'][1:]),1):
            direct[f'x_{k}_{i}_{j}']=1.;direct[f'conn_{k}_{i}_{j}']=len(route['nodes'])-1-pos
        for pos,i in enumerate(route['nodes'][1:-1],1):
            o=ops[i];load+=o['pickup']-o['drop'];Y[i]+=o['drop']-o['pickup']
            for n,x in [('z',1),('mode',int(o['pickup']>0)),('p',o['pickup']),('d',o['drop']),('ord',pos),('load',load)]:direct[f'{n}_{k}_{i}']=x
    obj=core.evidence.objective(a,Y,.15);r={i:Y[i]/a['D'][i] for i in range(1,p['V']+1)};values={}
    for name in model['order']:
        if name in direct:x=direct[name]
        elif name=='G':x=obj['G']
        elif name=='W_SP':x=sum(r.values())*obj['P']
        elif name=='r_min':x=min(r.values())
        elif name=='r_max':x=max(r.values())
        elif (m:=re.fullmatch(r'h_(\d+)_(\d+)',name)):x=abs(r[int(m[1])]-r[int(m[2])])
        elif (m:=re.fullmatch(r'(Y|r|e|zprod)_(\d+)',name)):
            i=int(m[2]);x={'Y':Y[i],'r':r[i],'e':abs(r[i]-1),'zprod':obj['G']*Y[i]}[m[1]]
        elif (m:=re.fullmatch(r'(state_g|state)_(\d+)_(\d+)',name)):
            i,y=int(m[2]),int(m[3]);x=int(Y[i]==y)*(obj['G'] if m[1]=='state_g' else 1)
        elif re.fullmatch(r'(x|conn)_\d+_\d+_\d+|(z|mode|p|d|ord|load)_\d+_\d+',name):x=0
        else:raise AssertionError(('unmapped actual column',name))
        values[name]=x
    bad=[]
    for index,(terms,sense,rhs) in enumerate(model['rows']):
        lhs=math.fsum(c*values[n] for n,c in terms)
        residual=abs(lhs-rhs) if sense=='=' else max(0,lhs-rhs) if sense=='<=' else max(0,rhs-lhs)
        if residual>1e-6:bad.append(dict(row=index+1,terms=terms,sense=sense,rhs=rhs,lhs=lhs,residual=residual))
    for n,x in values.items():
        lo,hi=model['bounds'][n]
        if x<lo-1e-6 or x>hi+1e-6:bad.append(dict(column=n,value=x,lower=lo,upper=hi))
    return dict(objective=obj,violations=bad,actual_columns_checked=len(values),all_remaining_rows_checked=len(model['rows']))
def case(id,b,D,Q,T):
    d=OUT/'qualification/boundaries'/id;d.mkdir(parents=True,exist_ok=True);path=d/'input.txt';n=len(b);M=len(Q)
    text=f'{n} {M} {json.dumps(Q)}\n'+''.join(k+' = '+repr(v)+'\n' for k,v in [
        ('capacities',[1000]+[max(2,x,y) for x,y in zip(b,D)]),('initial',[500]+b),('target',[0]+D),
        ('weights',[0]+[1]*n),('min_ratio',[0]*(n+1)),('points',[(0,0)]*(n+1))])
    if path.exists():assert path.read_text()==text
    else:path.write_text(text,encoding='utf-8')
    return dict(id=id,V=n,M=M,Q_vector=Q,T_seconds=T,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},input_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path))
def run():
    records=[]
    cases=[case('zero_S_duration60',[0,0],[1,1],[1],60),case('zero_S_duration3600',[0,0],[1,1],[1],3600),
        case('shared_midpoint',[4,0],[2,2],[1],3600),case('homogeneous',[2,0,2,0],[1,1,1,1],[1,1],3600),
        case('heterogeneous',[2,0,2,0],[1,1,1,1],[1,2],3600)]
    for p in cases:
        a=core.evidence.instance(ROOT,p);U0=core.evidence.objective(a,a['b'],.15)['F'];hi=min(U0,(p['V']-1)/p['V'])
        witnesses=[dict(label='zero_service',routes=[],F=U0)]
        if p['id']=='shared_midpoint':
            for label,nodes,ops in [('shared_midpoint',[0,1,2,0],[(1,1,0),(2,0,1)]),('loaded_return',[0,1,0],[(1,1,0)])]:
                w=dict(label=label,routes=[dict(vehicle=0,nodes=nodes,operations=[dict(station=i,pickup=x,drop=y) for i,x,y in ops])])
                Y=list(a['b'])
                for i,x,y in ops:Y[i]+=y-x
                w['F']=core.evidence.objective(a,Y,.15)['F'];witnesses.append(w)
        if p['id'] in ['homogeneous','heterogeneous']:
            witnesses.append(dict(label='pickup_total_exceeds_Q',F=0,routes=[dict(vehicle=0,nodes=[0,1,2,3,4,0],
                operations=[dict(station=i,pickup=int(i%2==1),drop=int(i%2==0)) for i in range(1,5)])]))
        for w in witnesses:core.full_fleet(ROOT,p,w)
        scopes=[('root',0,hi)]
        if p['id']=='shared_midpoint':scopes += [('left',0,hi/2),('right',hi/2,hi)]
        for scope,lo,upper in scopes:
            for mode in ['mb','mr','mg','ms2']:
                dest=OUT/'qualification/boundaries'/p['id']/scope/mode
                label=f'boundary_{p["id"]}_{scope}_{mode}'
                if not (dest/'build.json').exists():
                    assert metered(label,'qualification',[BUILD/'Round127ExportE1.exe',ROOT/p['input_path'],p['T_seconds'],lo,upper,U0,mode,dest])==0
                model=core.lp_model(dest/'original.lp')
                for w in witnesses:
                    ph=core.full_fleet(ROOT,p,w)
                    if not lo-1e-12<=ph['G']<=upper+1e-12 or ph['F']>U0+1e-12:continue
                    records.append(dict(id=p['id'],scope=scope,mode=mode,witness=w['label'],U0=U0,
                        physical=ph,model_SHA=sha(dest/'original.lp'),**physical_point(p,w,model)))
    write(OUT/'qualification/boundary_vectors.json',dict(UTC=utc(),Optimize=0,records=records,
        all_violations_preserved=True,no_changes_to_penalty_closure_or_production=True))
    print(json.dumps(dict(checks=len(records),violating=[dict(id=r['id'],scope=r['scope'],mode=r['mode'],violations=r['violations']) for r in records if r['violations']])))
if __name__=='__main__':run()
