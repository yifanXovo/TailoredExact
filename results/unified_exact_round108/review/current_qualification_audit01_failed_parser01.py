"""Independent read-only stdlib audit. No project imports, native loads or solving.

Only writes this review directory. All LP arithmetic comes from the saved bytes;
physical objectives come from independent parsing of the original input/routes.
"""
from pathlib import Path
from collections import Counter
import ast, csv, difflib, hashlib, json, math, re, sys, time

ROOT = Path('E:/codes/ExactEBRP-round108')
OUT = ROOT/'results/unified_exact_round108'
REVIEW = OUT/'review'
DEST = REVIEW/'current_qualification_audit01'
PE = ROOT/'build/research/round108-frozen-mb-v1/ExactEBRP.exe'
DLL = Path('D:/gurobi1302/win64/bin/gurobi130.dll')
reads = {}
checks = []

def data(p):
    p=Path(p); raw=p.read_bytes(); reads[str(p)] = hashlib.sha256(raw).hexdigest(); return raw
def sha(p): return hashlib.sha256(data(p)).hexdigest()
def txt(p): return data(p).decode('utf-8-sig')
def obj(p): return json.loads(txt(p))
def rows(p): return list(csv.DictReader(txt(p).splitlines()))
def require(b, message):
    if not b: raise AssertionError(message)
    checks.append(message)
def near(a,b,tol=1e-7): return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol
def save(p,v):
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def input_file(p):
    t=txt(p); h=t.splitlines()[0]; m=re.fullmatch(r'(\d+)\s+(\d+)\s+(\[.*\])',h)
    require(m is not None,'input header independently parsed '+str(p))
    q={'V':int(m[1]),'M':int(m[2]),'Q':ast.literal_eval(m[3])}
    for k in ['capacities','initial','target','weights','min_ratio','points']:
        line=next(x for x in t.splitlines() if re.match(k+r'\s*=',x))
        q[k]=ast.literal_eval(line.split('=',1)[1].strip())
        require(len(q[k])==q['V']+1,'input vector length includes depot '+k+' '+str(p))
    require(len(q['Q'])==q['M'],'input capacity vector '+str(p))
    # Parser.cpp retained legacy max-10 rule, although no qualification input uses it.
    if abs(max(q['weights'][1:])-10)<=1e-6:q['weights']=[x/10 for x in q['weights']]
    require(all(q['target'][i]>0 and q['weights'][i]>=0 and math.isfinite(q['weights'][i]) for i in range(1,q['V']+1)), 'positive station targets and nonnegative finite weights '+str(p))
    return q

def physical(q, routes, T, lam=.15, pickup=60, drop=60):
    inventory=list(q['initial']); seen=set(); vehicles=set(); route_results=[]
    for r in routes:
        k=r['vehicle']; ns=r['nodes']; ops=r['operations']
        require(k not in vehicles and 0<=k<q['M'],'unique valid vehicle '+str(k)); vehicles.add(k)
        require(ns[0]==ns[-1]==0 and 0 not in ns[1:-1] and len(ns)==len(ops)+2,'depot round trip and one operation per visited node '+str(k))
        load=0; profile=[0]; pu=dr=0
        for node, op in zip(ns[1:-1],ops):
            i=op['station']; p=op['pickup']; d=op['drop']
            require(i==node and 1<=i<=q['V'] and i not in seen,'unique matching station '+str(i)); seen.add(i)
            require(all(isinstance(x,(int,float)) and math.isfinite(x) and abs(x-round(x))<=1e-5 and x>=0 for x in [p,d]),'integer finite nonnegative handling at '+str(i))
            require((p==0 or d==0) and p+d>=1,'one direction and nonzero visited service '+str(i))
            require(p<=q['initial'][i] and d<=q['capacities'][i]-q['initial'][i],'station handling upper bounds '+str(i))
            load+=p-d;profile.append(load); pu+=p;dr+=d;inventory[i]+=d-p
            require(0<=load<=q['Q'][k],'prefix vehicle capacity '+str(k)+' '+str(i))
        travel=sum(math.sqrt((q['points'][a][0]-q['points'][b][0])**2+(q['points'][a][1]-q['points'][b][1])**2)/1.5 for a,b in zip(ns,ns[1:]))
        handling=pickup*pu+drop*(dr+load)
        require(near(handling,(pickup+drop)*pu) and travel+handling<=T+1e-6,'return depot unload and total route duration '+str(k))
        route_results.append(dict(vehicle=k,travel_seconds=travel,handling_seconds=handling,duration_seconds=travel+handling,prefix_loads=profile,return_load=load,total_pickup=pu,total_station_drop=dr))
    require(len(vehicles)==q['M'],'all vehicles independently represented')
    require(all(0<=inventory[i]<=q['capacities'][i] for i in range(1,q['V']+1)),'final station bounds independently checked')
    rr=[inventory[i]/q['target'][i] for i in range(1,q['V']+1)]
    S=sum(rr); H=sum(abs(a-b) for i,a in enumerate(rr) for b in rr[i+1:]); G=H/(q['V']*S) if S>0 else 0
    P=sum(q['weights'][i]*abs(rr[i-1]-1) for i in range(1,q['V']+1))
    return dict(U=G+lam*P,G=G,P=P,S=S,H=H,final_inventories=inventory,routes=route_results)

NUM=r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
VAR=r'[A-Za-z_][A-Za-z_0-9]*'
def terms(s):
    # These writer files have a strict linear grammar and explicit section/row lines.
    result={}; pattern=re.compile(r'\s*([+-]?)\s*(?:('+NUM+r')\s+)?('+VAR+r')')
    at=0
    while at<len(s.strip()):
        m=pattern.match(s,at)
        if not m:raise AssertionError('unparsed LP term '+s[at:])
        coef=(-1 if m[1]=='-' else 1)*(float(m[2]) if m[2] else 1.0)
        result[m[3]]=result.get(m[3],0)+coef;at=m.end()
    return tuple(sorted((k,v) for k,v in result.items() if v))

def lp(p):
    sec=None; bounds={}; types={}; row=[]; objective=None; names=[]
    for line in txt(p).splitlines():
        s=line.strip()
        if not s or s.startswith('\\'):continue
        if s in ['Minimize','Subject To','Bounds','Generals','Binaries','End']:sec=s;continue
        if sec=='Minimize':objective=terms(s.split(':',1)[1].strip())
        elif sec=='Subject To':
            lhs=s.split(':',1)[1].strip();m=re.fullmatch(r'(.*?)\s*(<=|>=|=)\s*([+-]?'+NUM+r')',lhs)
            require(m is not None,'linear row independently parsed')
            row.append(({'<=':'<','>=':'>','=':'='}[m[2]],float(m[3]),terms(m[1].strip())))
        elif sec=='Bounds':
            m=re.fullmatch(r'([+-]?'+NUM+r')\s*<=\s*('+VAR+r')\s*<=\s*([+-]?'+NUM+r')',s)
            if not m:raise AssertionError('unparsed LP bound '+s)
            require(m[2] not in bounds,'unique LP column bound')
            bounds[m[2]]=(float(m[1]),float(m[3]));names.append(m[2]);types[m[2]]='C'
        elif sec in ['Generals','Binaries']:
            require(s in bounds,'declared variable in bounds '+s);types[s]='I' if sec=='Generals' else 'B'
        else:raise AssertionError('unexpected LP line '+s)
    return dict(bounds=bounds,types=types,rows=row,objective=dict(objective),names=names)

def norm_native(r):return (r['sense'],r['rhs'],tuple(tuple(x) for x in r['terms']))
def matrix():
    d=OUT/'qualification/fixed_F2_models'; ns=obj(d/'native_models.json'); parsed={k:lp(d/(k+'.lp')) for k in ['ENS-C','M-B']}
    for k,n in ns.items():
        p=parsed[k]
        require(n['SHA']==sha(d/(k+'.lp')),'native saved-model SHA '+k)
        require(Counter(map(norm_native,n['rows']))==Counter(p['rows']),'raw writer rows equal all native numeric readback rows '+k)
        require(len(p['bounds'])==n['column_count'] and len(p['rows'])==n['row_count'],'raw/native row-column counts '+k)
        for c in n['columns']:
            require(p['bounds'][c['name']]==(c['lower'],c['upper']) and p['types'][c['name']]==c['type'] and p['objective'].get(c['name'],0)==c['objective'],'raw/native column bounds type objective '+k+' '+c['name'])
    a,b=ns['ENS-C'],ns['M-B']; ca,cb=a['columns'],b['columns']
    require([{k:v for k,v in c.items() if k!='type'} for c in ca]==[{k:v for k,v in c.items() if k!='type'} for c in cb],'ordered columns/bounds/objective exactly equal')
    require(a['objective_constant']==b['objective_constant']==0 and a['objective_sense']==b['objective_sense']==1,'same objective sense and zero constant')
    changed=[(x['name'],x['type'],y['type']) for x,y in zip(ca,cb) if x['type']!=y['type']]
    require(len(changed)==80 and all(n.startswith(('p_','d_')) and (x,y)==('I','C') for n,x,y in changed),'only 80 original p/d I to C')
    require(all(x['type']==y['type'] for x,y in zip(ca,cb) if not x['name'].startswith(('p_','d_'))),'all nonquantity native types retained including load/state/m/x/z')
    old,new=Counter(map(norm_native,a['rows'])),Counter(map(norm_native,b['rows']))
    require(not old-new,'no original numeric row removed')
    inp=input_file(ROOT/'reference/round86_unadapted_confirmation/F2.txt');names=set(parsed['M-B']['bounds']); expected=[]
    for i in range(1,21):
        motion=[(f'{v}_{k}_{i}',1.0) for k in range(2) for v in ['p','d']]
        for n in names:
            m=re.fullmatch('state_'+str(i)+r'_(\d+)',n)
            if m and int(m[1])!=inp['initial'][i]:motion.append((n,-float(abs(inp['initial'][i]-int(m[1])))))
        visit=[(f'z_{k}_{i}',1.0) for k in range(2)]
        s=f"state_{i}_{inp['initial'][i]}"
        if s in names:visit.append((s,1.0))
        expected.extend([('=',0.,tuple(sorted(motion))),('=',1.,tuple(sorted(visit)))])
    require(new-old==Counter(expected),'exact 20 A plus 20 B equations on actual state columns')
    require((a['row_count'],b['row_count'],a['column_count'],b['column_count'])==(9269,9309,3488,3488),'frozen F2 scope 9269/9309 rows and 3488 columns')
    return dict(ENS_C_rows=a['row_count'],M_B_rows=b['row_count'],columns=3488,changed_types=changed,removed_rows=0,added_rows=40,native_readback_SHA=sha(d/'native_models.json'),raw_lp_agrees_with_every_native_numeric_row_column=True,Optimize_calls_by_reviewer=0)

SETTINGS={'Threads':1,'Seed':0,'Presolve':-1,'MIPGap':0,'MIPGapAbs':0,'FeasibilityTol':1e-6,'IntFeasTol':1e-5,'OptimalityTol':1e-6}
def argv_map(cmd):
    f={}; flags={'--plain-baseline','--round100-continuous-quantities'};i=1
    while i<len(cmd):
        key=cmd[i];require(key.startswith('--') and key not in f,'unique CLI option '+key)
        if key in flags:f[key]=True;i+=1
        else:require(i+1<len(cmd),'CLI option argument exists '+key);f[key]=cmd[i+1];i+=2
    return f

def qualification():
    qi=obj(OUT/'qualification/identity.json'); ci=obj(OUT/'qualification/cli01/identity.json')
    inp=input_file(ROOT/'reference/round100_confirmation/H100.txt');results=[]
    require(not qi['fallback_triggered'] and qi['primary_actual_MIP_reached']==[True,True],'known H100 actual MIP reached without fallback')
    for launch,cmd in zip(ci['launches'],qi['qualified_argv']):
        d=Path(launch['destination']); raw=obj(d/'result.json'); comp=obj(d/'completion.json');actual=obj(d/'launch.json');am=argv_map(cmd)
        require(actual['command']==launch['command']==cmd,'actual complete qualification argv '+launch['arm'])
        require(comp['returncode']==0 and comp['stop_reason']=='normal_return' and comp['within_cap'] and comp['fully_observed_end_to_end_seconds']<=120,'normal qualified termination within 120 seconds '+launch['arm'])
        require(am['--input']=='reference/round100_confirmation/H100.txt','qualification uses known H100 only '+launch['arm'])
        events=[]
        for p in sorted((d/'journal').glob('event_*.json'),key=lambda x:int(x.stem.split('_')[1])):
            e=obj(p);commit=p.with_suffix('.commit')
            require(commit.is_file(),'journal committed '+p.name);data(commit);events.append(e)
        ident=next(e for e in events if e['kind']=='identity')
        require(ident['input_sha256']==sha(ROOT/am['--input']),'journal actual input SHA '+launch['arm'])
        calls=[e for e in events if e['kind']=='call'];returns=[e for e in events if e['kind']=='returned']
        require(set(e['call'] for e in calls)==set(e['call'] for e in returns) and all(e['return_code']==0 for e in returns),'all actual native calls returned '+launch['arm'])
        for c in calls:
            require(all(c['settings'][k]==v for k,v in SETTINGS.items()),'actual native settings '+launch['arm']+' '+str(c['call']))
            require(sha(c['model_path'])==c['model_sha256'],'actual native model bytes '+launch['arm']+' '+str(c['call']))
        ph=physical(inp,raw['routes'],5100)
        require(near(ph['U'],raw['objective']) and ph['final_inventories']==raw['final_inventories'],'independent physical final objective/inventory '+launch['arm'])
        for e in events:
            if e['kind']=='witness':require(near(physical(inp,e['routes'],5100)['U'],e['objective']),'independent committed native witness '+launch['arm']+' '+str(e['sequence']))
        starts=[]; cover=None; L=raw['lower_bound']; certified=False
        if launch['arm']=='P-GRB':
            require(len(calls)==1 and raw['native_mip_mipopt_count']==1 and raw['native_mip_status_text']=='TIME_LIMIT','plain cold P real complete compact MIP normally timed out')
            require(raw['native_mip_lifecycle_valid'] and raw['native_mip_problem_freed'] and raw['native_mip_environment_closed'],'P model/environment finalization')
            native=txt(d/'native.log');require('Loaded user MIP start' not in native,'P has no user MIP Start')
            require(raw['native_mip_best_bound_available'] and near(L,raw['native_mip_best_bound']),'P finite native complete-model lower bound')
        else:
            ledger=rows(d/'external/paper_optimize_ledger.csv');leaf=rows(d/'external/paper_leaf_ledger.csv');trace=rows(d/'external/global_bound_trace.csv')
            require(len(ledger)==len(calls)==5 and [r['solve_kind'] for r in ledger]==['LP','LP','LP','CHILD_BOUND_TARGET_MIP','MIP'],'three LPs and original target/terminal MIP actually called '+launch['arm'])
            initial=obj(d/'external/initial_witness.json'); init=physical(inp,initial['routes'],5100)
            require(len(leaf)==1 and leaf[0]['leaf_id']=='L0' and leaf[0]['parent_id']=='' and leaf[0]['status']=='closed' and leaf[0]['closure_source']=='native_terminal_mip_optimal','complete root leaf closed by native terminal optimal '+launch['arm'])
            require(near(float(leaf[0]['gamma_L']),0) and near(float(leaf[0]['gamma_U']),init['U']),'root [0,same-run physical U0] covers all potentially improving solutions '+launch['arm'])
            require(ledger[-1]['native_status']=='OPTIMAL' and ledger[-1]['optimize_return_code']=='0','native terminal Optimal successful return '+launch['arm'])
            require(calls[-1]['native_preconditions']==1 and calls[-1]['leaf']=='L0' and calls[-1]['model_scope']=='complete_original_compact_milp_intersected_with_static_gini_interval','native root complete model scope '+launch['arm'])
            L=float(leaf[0]['lower_bound']);require(near(L,raw['lower_bound']),'independent final-cover lower bound '+launch['arm'])
            require(all(float(b['valid_global_lower_bound'])+1e-7>=float(a['valid_global_lower_bound']) for a,b in zip(trace,trace[1:])),'valid global lower bound trace monotone '+launch['arm'])
            require(trace[-1]['open_relevant_leaf_count']=='0' and trace[-1]['closed_relevant_leaf_count']=='1' and near(float(trace[-1]['valid_global_lower_bound']),L),'complete cover no open relevant leaf '+launch['arm'])
            rootlp=lp(calls[-1]['model_path']); counts=Counter(rootlp['types'].values());log=txt(ledger[-1]['native_log'])
            m=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',log)
            require(m is not None and (int(m[1]),int(m[2]),int(m[3]))==(counts['C'],counts['I']+counts['B'],counts['B']),'actual terminal native types restored to writer domain '+launch['arm'])
            require('Optimal solution found (tolerance 0.00e+00)' in log,'zero requested MIP gap terminal optimum '+launch['arm'])
            for sp in (d/'external/native_logs').glob('*.start.values.csv'):
                sr=rows(sp); val={s['variable']:float(s['value']) for s in sr};meta=obj(sp.with_name(sp.name.replace('.values.csv','.json')))
                require(len(val)==len(sr)==len(rootlp['bounds']) and set(val)==set(rootlp['bounds']),'complete Start vector column set '+launch['arm'])
                require(all(s['type']==rootlp['types'][s['variable']] and near(float(s['value']),float(s['readback']),1e-12) for s in sr),'Start exact actual native readback/type '+launch['arm'])
                require(all(math.isfinite(v) and rootlp['bounds'][n][0]-1e-6<=v<=rootlp['bounds'][n][1]+1e-6 and (rootlp['types'][n]=='C' or abs(v-round(v))<=1e-5) for n,v in val.items()),'all Start columns finite bounds/integer valid '+launch['arm'])
                violations=[]
                for sense,rhs,ts in rootlp['rows']:
                    lhs=sum(val[n]*v for n,v in ts)
                    violations.append(abs(lhs-rhs) if sense=='=' else max(0,lhs-rhs) if sense=='<' else max(0,rhs-lhs))
                require(max(violations)<=1e-6,'every Start numeric model row independently holds '+launch['arm'])
                start_w=obj(d/'external'/ (meta['source']+'_witness.json')); sw=physical(inp,start_w['routes'],5100)
                modelobj=sum(val[n]*v for n,v in rootlp['objective'].items())
                require(near(modelobj,sw['U']) and near(modelobj,meta['objective']),'Start objective agrees with independent physical witness '+launch['arm'])
                op={(r['vehicle'],o['station']):(o['pickup'],o['drop']) for r in start_w['routes'] for o in r['operations']}
                for k in range(inp['M']):
                    for i in range(1,inp['V']+1):
                        p,v=op.get((k,i),(0,0));require(near(val[f'p_{k}_{i}'],p,1e-5) and near(val[f'd_{k}_{i}'],v,1e-5),'all visited and unvisited Start quantities match physical routes '+launch['arm'])
                starts.append(dict(path=str(sp),columns=len(val),rows_checked=len(violations),max_row_violation=max(violations),native_type_counts=dict(Counter(s['type'] for s in sr)),physical_U=sw['U']))
            require(len(starts)==2,'both original target and terminal Start independently checked '+launch['arm'])
            require(raw['algorithm_preset']==('research-round83-vds-equal-net-exchange' if launch['arm']=='ENS-C' else 'research-round99-ensc-discrete-structure-m-binary'),'actual effective preset identity '+launch['arm'])
            require(L<=ph['U']+1e-7 and ph['U']-L<=1e-7,'independent physical U/full-cover L closure '+launch['arm']);certified=True
            cover=dict(gamma_L=0,gamma_U=init['U'],same_run_initial_U=init['U'],leaf_ids=['L0'],root_terminal_model_SHA=calls[-1]['model_sha256'],native_terminal_type_counts=dict(counts),closed_relevant_leaves=1,open_relevant_leaves=0,outside_root_lower_bound=init['U'])
        require(math.isfinite(L) and L<=ph['U']+1e-7,'own bound contradiction gate '+launch['arm'])
        results.append(dict(arm=launch['arm'],independent_physics=ph,independent_L=L,signed_gap=ph['U']-L,relative_gap=(ph['U']-L)/abs(ph['U']) if abs(ph['U'])>1e-12 else None,certificate_qualified=True,certified=certified,actual_native_calls=len(calls),termination=comp,starts=starts,cover=cover,actual_full_argv=cmd))
    require(len(results)==3,'complete actual P ENS M-B qualification')
    return results

def binding_and_protocol():
    candidate=obj(OUT/'candidate_identity.json'); qual=obj(OUT/'qualification/identity.json');dev=obj(OUT/'development_protocol.json');con=obj(OUT/'confirmation_protocol.json');manifest=obj(OUT/'input_manifest.json')
    pe,dll=sha(PE),sha(DLL)
    require(candidate['production_PE_SHA']==qual['production_PE_SHA']==pe,'current actual PE SHA same frozen candidate and qualification')
    require(candidate['DLL_SHA']==qual['DLL_SHA']==dll,'current actual installed DLL SHA same candidate and qualification')
    for p,s in candidate['source_bindings'].items():require(sha(ROOT/p)==s,'current frozen source bytes '+p)
    require(candidate['source_bindings']==qual['source_bindings'],'qualified source bindings exactly candidate')
    for p,s in candidate['helpers'].items():require(sha(ROOT/p)==s,'final frozen helper bytes '+p)
    require(candidate['decision_reader_SHA']==sha(ROOT/'scripts/round108_decisions.py'),'frozen decision reader bytes')
    require(candidate['actual_CLI_qualification_SHA']==sha(OUT/'qualification/identity.json'),'candidate qualification SHA')
    require(candidate['development_protocol_SHA']==sha(OUT/'development_protocol.json') and candidate['confirmation_protocol_SHA']==sha(OUT/'confirmation_protocol.json') and candidate['input_manifest_SHA']==sha(OUT/'input_manifest.json'),'candidate actual full protocols and input manifest SHAs')
    require(dev['common_parameters']==con['common_parameters'],'all 21 arms same numerical/process parameters')
    common=dev['common_parameters'];require(common==dict(threads=1,mip_threads=1,gurobi_seed=0,gurobi_presolve=-1,gurobi_version='13.0.2',affinity_mask=4,native_limit_offset_seconds=6,hard_stop_offset_seconds=2,shutdown_margin_seconds=30,requested_mip_gap=0,requested_mip_gap_abs=0,FeasibilityTol=1e-6,OptimalityTol=1e-6,IntFeasTol=1e-5),'complete frozen numerical process settings')
    identities={};launches=[];reference_results=[]
    for name,protocol in [('bridge01',dev),('confirmation01',con)]:
        identity=obj(OUT/name/'identity.json');identities[name]=identity
        require(identity['source_hashes']==candidate['source_bindings'] and identity['helpers']==candidate['helpers'],'final full source/helper bindings '+name)
        require(identity['candidate_binary_sha256']==pe and identity['dll_sha256']==dll and identity['prereg_sha256']==sha(OUT/('development_protocol.json' if name=='bridge01' else 'confirmation_protocol.json')),'prepared actual identity matches current PE DLL protocol '+name)
        require(identity['runner_sha256']==sha(ROOT/'scripts/round108_campaign.py') and identity['final_wrapper_receipt_source_SHA']==identity['runner_sha256'],'final whole-arm timing wrapper frozen '+name)
        require([l['command'] for l in identity['launches']]==candidate['full_argv'][name],'all complete future argv frozen '+name)
        expected=[(r['id'],a) for r in protocol['roles'] for a in r['method_order']]
        require([(l['id'],l['arm']) for l in identity['launches']]==expected,'complete frozen arm order '+name)
        require(not (OUT/name/'summary.jsonl').exists(),'no formal summary/arm before independent admission '+name)
        for role in protocol['roles']:
            inp=input_file(ROOT/role['input_path']);require(sha(ROOT/role['input_path'])==role['input_sha256'] and (inp['V'],inp['M'],inp['Q'])==(role['V'],role['M'],role['Q_vector']),'actual role input bytes and V/M/Q '+role['id'])
            build=obj(OUT/name/'reference'/role['id']/'build.json');complete=obj(OUT/name/'reference'/role['id']/'completion.json')
            require(complete['returncode']==0,'pure reference export normal return '+role['id'])
            require(build['optimizer_calls']==0,'reference export calls no Optimize '+role['id'])
            ref_lp=lp(OUT/name/'reference'/role['id']/'original.lp');reference_results.append(dict(id=role['id'],columns=len(ref_lp['bounds']),rows=len(ref_lp['rows']),reference=identity['references'][role['id']]))
        for l in identity['launches']:
            cmd=l['command'];am=argv_map(cmd);r=l['panel'];cap=l['cap_seconds'];require(Path(cmd[0])==PE,'same final production PE in all arm argv')
            expectedvals={'--input':r['input_path'],'--lambda':'0.15','--T':str(r['T_seconds']),'--pickup-time':'60','--drop-time':'60','--time-limit':str(cap-6),'--process-wall-time-limit':str(cap),'--process-shutdown-margin':'30','--threads':'1','--mip-threads':'1','--gurobi-seed':'0','--gurobi-presolve':'-1'}
            require(all(am[k]==v for k,v in expectedvals.items()),'exact role/numeric budget argv '+r['id']+' '+l['arm'])
            require(not Path(l['destination']).exists(),'each formal destination unstarted and exclusive '+r['id']+' '+l['arm'])
            require('--round100-continuous-quantities' not in am,'ENS-Q flag absent '+r['id']+' '+l['arm'])
            if l['arm']=='P-GRB':require(am['--method']=='gurobi' and am['--plain-baseline'] is True and '--algorithm-preset' not in am and '--round98-state-service' not in am,'P original cold compact argv '+r['id'])
            else:
                require(am['--method']=='gcap-frontier' and am['--algorithm-preset']=='research-round83-vds-equal-net-exchange' and am['--round90-lp-g-split']=='false' and am['--round61-candidate-mode']=='off','ENS original full startup/search argv '+r['id']+' '+l['arm'])
                require(am.get('--round98-state-service')==('m-binary' if l['arm']=='M-B' else None),'only frozen M-B option differs '+r['id']+' '+l['arm'])
                require(not any(re.match(r'--round(?:9[567]|10[1-7])-',k) for k in am),'all later optional mechanism flags absent '+r['id']+' '+l['arm'])
            launches.append(l)
    require(len(launches)==21 and sum(l['cap_seconds'] for l in launches)==54900,'exact 21 arms and 54900 nominal seconds')
    require([(r['id'],r['cap_seconds']) for r in dev['roles']+con['roles']]==[('F2',1200),('C2',1800),('S12',900),('B24',1800),('L48',1800),('F5',5400),('N36',5400)],'exact seven roles and prescribed caps')
    before=OUT/'engineering/wrapper_time_receipt01/round108_campaign_before.py';after=ROOT/'scripts/round108_campaign.py'
    diff=''.join(difflib.unified_diff(txt(before).splitlines(True),txt(after).splitlines(True),fromfile=str(before),tofile=str(after)))
    require(all(obj(OUT/'engineering/wrapper_time_receipt01'/f'{n}_identity_before.json')['launches']==identities[n+'01']['launches'] for n in ['bridge','confirmation']),'wrapper receipt edit preserves every arm/argv')
    launch_fees=[];starts=0;secs=0
    for p in sorted((OUT/'fees').glob('*/launch.json')):
        f=obj(p);rec=obj(p.parent/'receipt.json');require(rec['exit_code']==0 and rec['stop_reason']=='normal_return' and f['conservative_process_starts']==rec['conservative_process_starts'],'all existing paid work receipts closed '+p.parent.name)
        starts+=f['conservative_process_starts'];secs+=rec['outer_seconds'];launch_fees.append(dict(path=str(p),starts=f['conservative_process_starts'],seconds=rec['outer_seconds']))
    require(starts==17 and starts+7+20==candidate['planned_total_conservative_starts']==44 and secs+54900+6*120<80000,'independent conservative full planned budget within 48 starts/80000 seconds')
    return dict(production_PE_SHA=pe,DLL_SHA=dll,source_bindings=candidate['source_bindings'],helper_bindings=candidate['helpers'],qualification_identity_SHA=sha(OUT/'qualification/identity.json'),development_protocol_SHA=sha(OUT/'development_protocol.json'),confirmation_protocol_SHA=sha(OUT/'confirmation_protocol.json'),candidate_identity_SHA=sha(OUT/'candidate_identity.json'),input_manifest_SHA=sha(OUT/'input_manifest.json'),decision_reader_SHA=sha(ROOT/'scripts/round108_decisions.py'),bridge_identity_SHA=sha(OUT/'bridge01/identity.json'),confirmation_identity_SHA=sha(OUT/'confirmation01/identity.json'),bridge_full_argv=candidate['full_argv']['bridge01'],confirmation_full_argv=candidate['full_argv']['confirmation01'],qualified_full_argv=candidate['full_argv']['qualification/cli01'],references=reference_results,paid_fees=launch_fees,paid_starts=starts,paid_outer_seconds=secs,planned_max_starts=44,wrapper_diff=diff)

def main():
    DEST.mkdir(exist_ok=False);tick=time.perf_counter();audit={};decision='HOLD';error=None
    try:
        audit['bindings']=binding_and_protocol();audit['fixed_F2_matrix']=matrix();audit['actual_H100_qualification']=qualification()
        guards=txt(ROOT/'tests/round100_quantity_tests.cpp');proof=txt(OUT/'fees/qualification_prepare01/stdout.log')
        require('ENS-Q fixtures=4 all-column guards passed Optimize=0' in proof,'actual current compiled all-column guards fixture passed with zero Optimize')
        require(all(x in guards for x in ['unvisited zero vector','invalid unvisited pickup accepted','missing column accepted','zero cap accepted','singleton/absent initial','empty domain']),'fixture covers missing/nonfinite/fractional/unvisited/zero-cap and absent/empty states')
        audit['guard_fixture']=dict(source_SHA=sha(ROOT/'tests/round100_quantity_tests.cpp'),stdout_SHA=sha(OUT/'fees/qualification_prepare01/stdout.log'),actual_guard_exit_code=0,Optimize_calls=0)
        audit['inheritance_audit_SHA']=sha(REVIEW/'inheritance_audit01/audit.json');audit['inheritance_review_SHA']=sha(REVIEW/'inheritance_review01.md')
        decision='ACCEPT'
    except Exception as e:
        error=type(e).__name__+': '+str(e)
    audit.update(decision=decision,error=error,completed_checks=len(checks),checks=checks,read_bindings=reads,reviewer_script_SHA=sha(Path(__file__)),reviewer_calls=dict(Optimize=0,IIS=0,LP_solve=0,native_environment=0,compiler=0,production_edits=0),engineering_elapsed_seconds=time.perf_counter()-tick)
    save(DEST/'audit.json',audit)
    save(DEST/'receipt.json',dict(decision=decision,error=error,audit_SHA=sha(DEST/'audit.json'),script_SHA=sha(Path(__file__)),Optimize_calls=0,IIS_calls=0,LP_solve_calls=0,native_environment_calls=0,compiler_calls=0,elapsed_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(decision=decision,error=error,completed_checks=len(checks),audit_SHA=sha(DEST/'audit.json')),ensure_ascii=False))
    if decision!='ACCEPT':sys.exit(1)

if __name__=='__main__':main()
