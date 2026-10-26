"""Zero-solver finite checks of inherited Start normalization and fleet mapping."""
from pathlib import Path
import argparse, ast, copy, hashlib, json, math, re, subprocess, sys, time, traceback
from collections import Counter

ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
root=Path(a.root).resolve();dest=Path(a.out).resolve();assert dest.is_relative_to(root/'results/unified_exact_round108/review');dest.mkdir(exist_ok=False)
tick=time.perf_counter();cases=[];reads={}
def data(p):
    b=Path(p).read_bytes();reads[str(Path(p).relative_to(root))]=hashlib.sha256(b).hexdigest();return b
def sha(p):return hashlib.sha256(data(p)).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def require(b,msg):assert b,msg
def near(x,y,tol=1e-7):return math.isfinite(x) and math.isfinite(y) and abs(x-y)<=tol
source=root/'results/unified_exact_round108/review/campaign_raw_audit01.py';parser=root/'results/unified_exact_round108/review/current_qualification_audit01.py'
ns=dict(math=math,re=re,Counter=Counter,require=require,near=near)
def extract(path,names):
    tree=ast.parse(data(path));body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(body)==len(names);exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),ns)
extract(parser,{'physical'});extract(source,{'full_physics','normalize_existing_start_routes','validate_start_fleet_vector'})
normal=ns['normalize_existing_start_routes'];vector=ns['validate_start_fleet_vector'];physics=ns['full_physics']
save(dest/'launch.json',dict(actual_command=[sys.executable,*sys.argv],cwd=str(Path.cwd()),explicit_read_root=str(root),source_SHA=sha(Path(__file__)),independent_raw_source_SHA=sha(source),synthetic_only=True,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
q=dict(V=3,M=3,Q=[5,5,5],initial=[0,3,4,1],target=[0,2,2,3],capacities=[0,10,10,10],weights=[0,1.,1.,1.],points=[(0.,0.),(1.,0.),(2.,0.),(3.,0.)])
p=dict(T_seconds=3600,**{'lambda':.15},pickup_seconds=1.,drop_seconds=1.)
fleet=[dict(vehicle=0,nodes=[0,1,0],operations=[dict(station=1,pickup=1,drop=0)]),
       dict(vehicle=1,nodes=[0,0],operations=[]),
       dict(vehicle=2,nodes=[0,2,3,0],operations=[dict(station=2,pickup=2,drop=0),dict(station=3,pickup=0,drop=2)])]
normalized,mapping=normal(q,fleet);ph=physics(q,normalized,p)
v={'G':0.,'Y_1':2.,'Y_2':2.,'Y_3':3.}
for k in range(3):
    for i in range(1,4):
        for f in ['p','d','load','z','mode','ord']:v[f'{f}_{k}_{i}']=0.
    for i in range(4):
        for j in range(4):
            if i!=j:v[f'x_{k}_{i}_{j}']=v[f'conn_{k}_{i}_{j}']=0.
# Independent literal expected mapping: source 2->0, source 0->1, empty ->omit.
v.update({'p_0_2':2.,'d_0_3':2.,'z_0_2':1.,'z_0_3':1.,'mode_0_2':1.,'load_0_2':2.,'ord_0_2':1.,'ord_0_3':2.,
          'x_0_0_2':1.,'x_0_2_3':1.,'x_0_3_0':1.,'conn_0_0_2':2.,'conn_0_2_3':1.,
          'p_1_1':1.,'z_1_1':1.,'mode_1_1':1.,'load_1_1':1.,'ord_1_1':1.,'x_1_0_1':1.,'x_1_1_0':1.,'conn_1_0_1':1.})
for i in range(1,4):
    for state in range(6):v[f'state_{i}_{state}']=float(ph['final_inventories'][i]==state)
def expect(name,action,reject=False):
    try:value=action()
    except (AssertionError,KeyError,ValueError) as e:
        assert reject,(name,str(e));cases.append(dict(name=name,outcome='correctly_rejected',exception=type(e).__name__));return
    assert not reject,(name,'bad fixture accepted',value);cases.append(dict(name=name,outcome='accepted',value=value))
def mapping_case(qq,ff,expected):
    rr,mm=normal(qq,ff);assert [(x['source_vehicle'],x['normalized_vehicle']) for x in mm]==expected
    before=physics(qq,ff,p);after=physics(qq,rr,p)
    assert before['final_inventories']==after['final_inventories'] and before['U']==after['U'] and before['G']==after['G']
    bt={r['vehicle']:r for r in before['routes']};at={r['vehicle']:r for r in after['routes']}
    for item in mm:assert bt[item['source_vehicle']]['duration_seconds']==at[item['normalized_vehicle']]['duration_seconds']
    return dict(exact_mapping=expected,physical_U=after['U'],final_inventories=after['final_inventories'])
def alter(name,value):
    vv=dict(v);vv[name]=value;return vector(vv,q,normalized,ph)
history={}
try:
    commit='b5d6d83bb8fc74682de6f1f6862c2e687712f4cf'
    for name in ['src/Round61Candidates.cpp','src/GurobiBaseline.cpp']:
        command=['git','show',commit+':'+name];proc=subprocess.run(command,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert proc.returncode==0
        current=data(root/name);history[name]=dict(commit=commit,path=name,historical_file_SHA=hashlib.sha256(proc.stdout).hexdigest(),current_file_SHA=hashlib.sha256(current).hexdigest(),actual_command=command,exit_code=proc.returncode)
        if name.endswith('Round61Candidates.cpp'):
            def cpp_function(bb):
                text=bb.decode().replace('\r\n','\n');start=text.index('std::vector<RoutePlan> normalizeRound61Routes(');left=text.index('{',start);depth=0
                for i in range(left,len(text)):
                    depth+= (text[i]=='{')-(text[i]=='}')
                    if depth==0:return text[start:i+1]
                raise AssertionError('unterminated C++ function')
            old=cpp_function(proc.stdout);new=cpp_function(current);assert old==new
            (dest/'inherited_normalizeRound61Routes.cpp.txt').write_text(new+'\n',encoding='utf-8')
            history[name]['exact_function_identical_to_R100']=True;history[name]['function_comparison_line_endings']='LF canonical, all current/historical actual file byte SHA also bound';history[name]['exact_function_SHA']=hashlib.sha256(new.encode()).hexdigest()
        else:
            pattern=rb'const auto routes\s*=\s*normalizeRound61Routes\(instance,\s*options\.lambda,\s*request\.verified_start_routes\);'
            assert re.search(pattern,current) and re.search(pattern,proc.stdout)
            history[name]['prepareRound68Start_original_normalization_call_present_R100_and_current']=True
    expect('equal-Q operation-count permutation preserves exact physical fleet',lambda:mapping_case(q,fleet,[(2,0),(0,1)]))
    expect('complete submitted vector matches exact normalized fleet for all families',lambda:vector(v,q,normalized,ph))
    tie=copy.deepcopy(fleet);tie[2]=dict(vehicle=2,nodes=[0,2,0],operations=[dict(station=2,pickup=2,drop=0)])
    expect('stable ties follow ascending original vehicle ids rather than JSON list order',lambda:mapping_case(q,[tie[2],tie[1],tie[0]],[(0,0),(2,1)]))
    empties=copy.deepcopy(fleet);empties[0]=dict(vehicle=0,nodes=[0,0],operations=[])
    expect('empty vehicles omitted and used equal-Q route moved into first id',lambda:mapping_case(q,empties,[(2,0)]))
    expect('all empty fleet retains exact inventories/objective',lambda:mapping_case(q,[dict(vehicle=k,nodes=[0,0],operations=[]) for k in range(3)],[]))
    cq=copy.deepcopy(q);cq['Q']=[5,4,5]
    expect('normalization keeps unequal-Q classes separate',lambda:mapping_case(cq,fleet,[(2,0),(0,2)]))
    cn,_=normal(cq,fleet);cp=physics(cq,cn,p)
    expect('a physically feasible cross-Q label permutation is not the original exact mapping',lambda:vector(v,cq,cn,cp),True)
    noncanonical={}
    for name,value in v.items():
        parts=name.split('_')
        if parts[0] in {'x','conn','z','mode','p','d','load','ord'}:parts[1]=str({0:1,1:0,2:2}[int(parts[1])]);name='_'.join(parts)
        noncanonical[name]=value
    expect('arbitrary same-Q permutation cannot replace the inherited canonical vector',lambda:vector(noncanonical,q,normalized,ph),True)
    for name,value in [('x_0_2_3',0.),('p_0_2',3.),('d_0_3',1.),('load_0_2',1.),('z_0_2',0.),('mode_0_2',0.),('ord_0_3',1.),('conn_0_2_3',0.),('Y_2',1.),('state_2_2',0.),('G',.01)]:
        expect('altered submitted column '+name+' rejected',lambda n=name,x=value:alter(n,x),True)
    changed=copy.deepcopy(normalized);changed[0]['operations'][0]['pickup']=3;changedph=physics(q,changed,p)
    expect('different operation fleet cannot explain original vector',lambda:vector(v,q,changed,changedph),True)
    reordered=copy.deepcopy(normalized);reordered[0]['nodes']=[0,3,2,0]
    expect('different closed route order is not merely a label normalization',lambda:vector(v,q,reordered,ph),True)
    expect('duplicate source vehicle rejected',lambda:normal(q,[fleet[0],fleet[0]]),True)
    expect('out of range source vehicle rejected',lambda:normal(q,[dict(fleet[0],vehicle=3)]),True)
    invalid=[dict(vehicle=0,nodes=[0,1,0],operations=[])]+fleet[1:]
    expect('empty operation metadata cannot hide a visited station before normalization',lambda:physics(q,invalid,p),True)
    decision='ACCEPT';error=None;code=0
except Exception as e:
    decision='HOLD';error=type(e).__name__+': '+str(e);code=1;(dest/'traceback.txt').write_text(traceback.format_exc(),encoding='utf-8')
save(dest/'checks.json',dict(decision=decision,error=error,cases=cases,source_SHA=sha(Path(__file__)),independent_raw_source_SHA=sha(source),own_physical_parser_SHA=sha(parser),inherited_production_binding=history,read_bindings=reads,synthetic_only=True,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
save(dest/'receipt.json',dict(actual_command=[sys.executable,*sys.argv],explicit_read_root=str(root),source_SHA=sha(Path(__file__)),independent_raw_source_SHA=sha(source),checks_SHA=sha(dest/'checks.json'),exit_code=code,decision=decision,error=error,seconds=time.perf_counter()-tick,Optimize=0,LP_solve=0,native_environment=0,compiler=0))
print(json.dumps(dict(decision=decision,error=error,cases=len(cases),checks_SHA=sha(dest/'checks.json'))));sys.exit(code)
