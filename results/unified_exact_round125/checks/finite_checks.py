"""Finite formula/decision/replay checks. Standard library only; no solver/search.
Default is portable: reads only the compact saved excerpts next to this script.
--extract reads one named existing LP as text and copies a small fixed trace set.
It never imports production code, runs an exporter, generates routes or optimizes.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations, permutations, product
import ast,csv,hashlib,json,math,re,sys,time
ROOT=Path(__file__).resolve().parents[1]
EV=ROOT/'evidence'
def dump(p,x): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def instance(path):
    lines=path.read_text().splitlines(); n,m,*_=lines[0].split();d={'n':int(n),'m':int(m),'Q':ast.literal_eval(lines[0][lines[0].index('['):]),'T':10800,'h':120,'lambda':.15}
    for s in lines[1:]:
        if '=' in s:
            k,v=s.split('=',1);d[k.strip()]=ast.literal_eval(v.strip())
    pts=d['points'];d['dist']=[[math.hypot(x-u,y-v)/1.5 for u,v in pts] for x,y in pts]
    return d
def expr(s):
    ts=s.split();out={};sign=1.;j=0
    while j<len(ts):
        if ts[j] in ('+','-'):sign=1. if ts[j]=='+' else -1.;j+=1
        try:coef=float(ts[j]);j+=1
        except ValueError:coef=1.
        var=ts[j];j+=1;out[var]=out.get(var,0.)+sign*coef;sign=1.
    return {k:v for k,v in out.items() if v!=0}
def rowparse(line):
    name,s=line.split(':',1);left,sense,right=re.split(r'\s+(<=|>=|=)\s+',s.strip());return {'name':name.strip(),'coef':expr(left),'sense':sense,'rhs':float(right)}
def expected(d,alpha,beta,U):
    n,m=d['n'],d['m'];C=d['capacities'];b=d['initial'];D=d['target'];w=d['weights'];dist=d['dist'];T=d['T'];h=d['h'];lam=d['lambda']
    yl=[0]*(n+1);yu=C.copy();budget=(U-alpha)/lam
    for i in range(1,n+1):
        if w[i]>1e-12 and budget>=-1e-10:
            rad=max(0,budget/w[i]);yl[i]=max(0,math.ceil(D[i]*(1-rad)-1e-9));yu[i]=min(C[i],math.floor(D[i]*(1+rad)+1e-9))
        reach=[min(q,math.floor((T-dist[0][i]-dist[i][0])/h+1e-9)) if T+1e-9>=dist[0][i]+dist[i][0] else 0 for q in d['Q']]
        yl[i]=max(yl[i],b[i]-max(min(b[i],q,a) for q,a in zip(d['Q'],reach)))
        yu[i]=min(yu[i],b[i]+max(min(C[i]-b[i],q,a) for q,a in zip(d['Q'],reach)))
        if yl[i]>yu[i]:yl[i],yu[i]=0,C[i]
    sl=sum(yl[i]/D[i] for i in range(1,n+1));su=sum(yu[i]/D[i] for i in range(1,n+1))
    el=[max(0,1-yu[i]/D[i],yl[i]/D[i]-1) for i in range(1,n+1)]
    eu=[max(abs(yl[i]/D[i]-1),abs(yu[i]/D[i]-1)) for i in range(1,n+1)]
    pl=sum(w[i]*el[i-1] for i in range(1,n+1));pu=sum(w[i]*eu[i-1] for i in range(1,n+1))
    out={}
    def add(key,coef,sense,rhs):out[key]={'coef':{k:v for k,v in coef.items() if abs(v)>1e-14},'sense':sense,'rhs':rhs}
    hh={f'h_{i}_{j}':1 for i in range(1,n+1) for j in range(i+1,n+1)};rr={f'r_{i}':1 for i in range(1,n+1)};ee={f'e_{i}':w[i] for i in range(1,n+1)}
    def mix(*items):
        z={}
        for co,scale in items:
            for k,v in co.items():z[k]=z.get(k,0)+v*scale
        return z
    # One literal representative of each active original physical/flow template.
    add('depot_balance',{**{f'x_0_0_{j}':1 for j in range(1,n+1)},**{f'x_0_{j}_0':-1 for j in range(1,n+1)}},'=',0)
    add('depot_at_most_one',{f'x_0_0_{j}':1 for j in range(1,n+1)},'<=',1)
    add('station_in',{**{f'x_0_{j}_1':1 for j in range(n+1) if j!=1},'z_0_1':-1},'=',0)
    add('station_out',{**{f'x_0_1_{j}':1 for j in range(n+1) if j!=1},'z_0_1':-1},'=',0)
    add('unique_service',{f'z_{k}_1':1 for k in range(m)},'<=',1)
    add('rank_lower',{'ord_0_1':1,'z_0_1':-1},'>=',0)
    add('rank_upper',{'ord_0_1':1,'z_0_1':-n},'<=',0)
    add('MTZ',{'ord_0_1':1,'ord_0_2':-1,'x_0_1_2':n},'<=',n-1)
    add('F0_link',{'conn_0_0_1':1,'x_0_0_1':-n},'<=',0)
    add('F0_station',{**{f'conn_0_{j}_1':1 for j in range(n+1) if j!=1},**{f'conn_0_1_{j}':-1 for j in range(n+1) if j!=1},'z_0_1':-1},'=',0)
    add('F0_depot',{**{f'conn_0_0_{j}':1 for j in range(1,n+1)},**{f'conn_0_{j}_0':-1 for j in range(1,n+1)},**{f'z_0_{j}':-1 for j in range(1,n+1)}},'=',0)
    for sign,sense in [(1,'<='),(-1,'>=')]:
        add('load_depot_'+str(sign),{'load_0_1':1,'p_0_1':-1,'d_0_1':1,'x_0_0_1':sign*d['Q'][0]},sense,sign*d['Q'][0])
        add('load_internal_'+str(sign),{'load_0_2':1,'load_0_1':-1,'p_0_2':-1,'d_0_2':1,'x_0_1_2':sign*d['Q'][0]},sense,sign*d['Q'][0])
    add('nonnegative_return',{**{f'p_0_{i}':1 for i in range(1,n+1)},**{f'd_0_{i}':-1 for i in range(1,n+1)}},'>=',0)
    add('vehicle_duration',{**{f'x_0_{i}_{j}':dist[i][j] for i in range(n+1) for j in range(n+1) if i!=j},**{f'p_0_{i}':h for i in range(1,n+1)}},'<=',T)
    add('gini_cap',mix((hh,1),(rr,-n*beta)),'<=',0);add('gini_floor',mix((hh,1),(rr,-n*alpha)),'>=',0)
    add('H_spread',mix(({'h_1_2':n-1},1),(rr,-n*beta)),'<=',0)
    for sign in (1,-1):
        diff={'r_1':sign,'r_2':-sign};add('fixed_center_'+str(sign),diff,'<=',n*beta*su/(n-1));add('variable_center_'+str(sign),mix((diff,n-1),(rr,-n*beta)),'<=',0)
    add('original_cutoff',mix(({'G':1},1),(ee,lam)),'<=',U);add('penalty_floor',ee,'>=',pl)
    add('e_budget',{'e_1':1},'<=',max(0,budget/w[1]));add('scalar_estimator',mix((hh,1),(ee,n*su*lam)),'<=',n*su*U)
    for key,s,p,sense in [('ll',sl,pl,'>='),('uu',su,pu,'>='),('ul',su,pl,'<='),('lu',sl,pu,'<=')]:add('SP_'+key,mix(({'W_SP':1},1),(ee,-s),(rr,-p)),sense,-s*p)
    add('SP_lift',mix((hh,1),({'W_SP':n*lam},1),(rr,-n*U)),'<=',0)
    yi={f'Y_{i}':1 for i in range(1,n+1)};total=sum(b[1:]);add('stock_upper',yi,'<=',total);add('stock_lower',yi,'>=',total-sum(d['Q']))
    add('handling',{f'p_{k}_{i}':h for k in range(m) for i in range(1,n+1)},'<=',m*T)
    i=1;k=0;pm=min(b[i],d['Q'][k]);dm=min(C[i]-b[i],d['Q'][k])
    add('visit_stock_upper',{'Y_1':1,**{f'z_{k}_1':-(C[1]-b[1]) for k in range(m)}},'<=',b[1]);add('visit_stock_lower',{'Y_1':-1,**{f'z_{k}_1':-b[1] for k in range(m)}},'<=',-b[1])
    add('pickup_visit',{'p_0_1':1,'z_0_1':-pm},'<=',0);add('drop_visit',{'d_0_1':1,'z_0_1':-dm},'<=',0)
    add('mode_visit',{'mode_0_1':1,'z_0_1':-1},'<=',0);add('pickup_mode',{'p_0_1':1,'mode_0_1':-pm},'<=',0);add('drop_mode',{'d_0_1':1,'z_0_1':-dm,'mode_0_1':dm},'<=',0)
    add('nonzero_service',{'p_0_1':1,'d_0_1':1,'z_0_1':-1},'>=',0);add('load_visit',{'load_0_1':1,'z_0_1':-d['Q'][0]},'<=',0)
    add('inventory_balance',{'Y_1':1,**{f'p_{k}_1':1 for k in range(m)},**{f'd_{k}_1':-1 for k in range(m)}},'=',b[1])
    add('A_movement',{**{f'p_{k}_1':1 for k in range(m)},**{f'd_{k}_1':1 for k in range(m)},**{f'state_1_{y}':-abs(b[1]-y) for y in range(yl[1],yu[1]+1)}},'=',0)
    add('B_visit',{**{f'z_{k}_1':1 for k in range(m)},**({f'state_1_{b[1]}':1} if yl[1]<=b[1]<=yu[1] else {})},'=',1)
    add('state_sum',{f'state_1_{y}':1 for y in range(yl[1],yu[1]+1)},'=',1)
    add('state_inventory',{'Y_1':1,**{f'state_1_{y}':-y for y in range(yl[1],yu[1]+1)}},'=',0)
    add('state_g_sum',{'G':-1,**{f'state_g_1_{y}':1 for y in range(yl[1],yu[1]+1)}},'=',0)
    # Paper Z_i is the serialized zprod_i column.
    add('state_product',{'zprod_1':1,**{f'state_g_1_{y}':-y for y in range(yl[1],yu[1]+1)}},'=',0)
    y=yl[1];add('state_g_lower',{f'state_g_1_{y}':1,f'state_1_{y}':-alpha},'>=',0);add('state_g_upper',{f'state_g_1_{y}':1,f'state_1_{y}':-beta},'<=',0)
    add('ratio',{'r_1':1,'Y_1':-1/D[1]},'=',0);add('deviation_pos',{'e_1':1,'r_1':-1},'>=',-1);add('deviation_neg',{'e_1':1,'r_1':1},'>=',1)
    add('H_pos',{'h_1_2':1,'r_1':-1,'r_2':1},'>=',0);add('H_neg',{'h_1_2':1,'r_1':1,'r_2':-1},'>=',0)
    add('gini_product',mix(({f'zprod_{i}':n/D[i] for i in range(1,n+1)},1),(hh,-1)),'>=',0)
    add('transfer_j1',{'d_0_1':1,**{f'p_0_{i}':-1 for i in range(2,n+1) if dist[0][i]+dist[i][1]+dist[1][0]+h<=T+1e-9}},'<=',0)
    for size in (2,3):
        W=tuple(range(1,size+1));tau=min(sum(dist[a][b] for a,b in zip((0,)+q,q+(0,))) for q in permutations(W));big=T+tau+h*max(1,sum(min(b[i],d['Q'][0]) for i in W))
        if tau+h*((size+1)//2)>T+1e-9:add(f'support_{size}_cover',{f'z_0_{i}':1 for i in W},'<=',size-1)
        else:add(f'support_{size}_conditional',{**{f'p_0_{i}':h for i in W},**{f'z_0_{i}':big for i in W}},'<=',T-tau+big*size)
    if len(set(d['Q']))==1 and m>1:add('symmetry',{**{f'z_0_{i}':1 for i in range(1,n+1)},**{f'z_1_{i}':-1 for i in range(1,n+1)}},'>=',0)
    for i in range(1,n+1):
        if yl[i]>b[i]:add('required_drop',{**{f'd_{k}_{i}':1 for k in range(m)},**{f'p_{k}_{i}':-1 for k in range(m)}},'>=',yl[i]-b[i]);break
    for i in range(1,n+1):
        if yu[i]<b[i]:add('required_pick',{**{f'p_{k}_{i}':1 for k in range(m)},**{f'd_{k}_{i}':-1 for k in range(m)}},'>=',b[i]-yu[i]);break
    return out,{'yl':yl,'yu':yu,'S':[sl,su],'P':[pl,pu],'W':[max(0,sl*pl),max(max(0,sl*pl),su*pu)]}
def near(a,b):return abs(a-b)<=2e-10*max(1,abs(a),abs(b))
def same(a,b):return a['sense']==b['sense'] and set(a['coef'])==set(b['coef']) and near(a['rhs'],b['rhs']) and all(near(a['coef'][k],b['coef'][k]) for k in a['coef'])
def extract():
    src=Path('E:/codes/ExactEBRP-work/worktrees/round123/results/unified_exact_round123/campaign/group01/raw/02_PB-C50-S_S0_M-B')
    EV.mkdir(exist_ok=True)
    copies={'input.txt':ROOT.parent/'unified_exact_round124/authorities/PB-C50-S.txt','joint.csv':src/'hga.csv.joint.csv','descent.csv':src/'hga.csv.descent.csv','block_events.jsonl':src/'hga.csv.exchange/events.jsonl','before_neutral.json':src/'hga.csv.exchange/closure_0.csv.final.json','after_neutral.json':src/'hga.csv.exchange/neutral_0.json','closure.csv':src/'hga.csv.exchange/closure_1.csv','am.csv':src/'external/adaptive_mass_decision_ledger.csv','cover_events.csv':src/'external/paper_tree_events.csv','native_targets.csv':src/'external/native_target_ledger.csv'}
    provenance=[]
    for name,p in copies.items():(EV/name).write_bytes(p.read_bytes());provenance.append({'selected':name,'source':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
    lp=src/'external/models/L0.0.0.0_epoch_0_generation_6.lp';d=instance(EV/'input.txt');alpha=0.;beta=.046542721937380925;U=.3723417754990474
    exp,domains=expected(d,alpha,beta,U);found={};keys={frozenset(v['coef']) for v in exp.values()};bounds={};types={};section=''
    with lp.open() as f:
        for line in f:
            st=line.strip()
            if st in ('Bounds','Generals','Binaries','End'):section=st;continue
            if section=='Bounds':
                ma=re.fullmatch(r'(\S+) <= (\S+) <= (\S+)',st)
                if ma:bounds[ma[2]]=[float(ma[1]),float(ma[3])]
            elif section in ('Generals','Binaries'):
                for x in st.split():types[x]='I' if section=='Generals' else 'B'
            elif st.startswith('c') and ':' in st:
                row=rowparse(st)
                if frozenset(row['coef']) in keys:
                    for key,v in exp.items():
                        if key not in found and same(row,v):found[key]=row
    sample={'source':str(lp),'source_sha256':sha(lp),'source_bytes':lp.stat().st_size,'alpha':alpha,'beta':beta,'cutoff':U,'rows':found,'missing_expected':sorted(set(exp)-set(found)),'domains':domains,'selected_bounds':{x:bounds.get(x) for x in ['G','W_SP','Y_1','e_1','p_0_1','d_0_1']},'types':{x:types.get(x,'C') for x in ['Y_1','p_0_1','d_0_1','mode_0_1','load_0_1','state_1_0']}}
    dump(EV/'matrix_samples.json',sample);dump(EV/'provenance.json',provenance)
    print('extracted matrix templates',len(found),'missing',sample['missing_expected'])
def arithmetic():
    checks=[]
    def record(name,ok,detail):assert ok,name;checks.append({'name':name,'passed':bool(ok),'detail':detail})
    count=0
    for n in (2,3,4):
        for r in product([F(0),F(1,3),F(1),F(2)],repeat=n):
            S=sum(r);A=sum(abs(r[i]-r[j]) for i,j in combinations(range(n),2));beta=A/(n*S) if S else F(0)
            for i,j in combinations(range(n),2):
                assert A>=(n-1)*abs(r[i]-r[j]);assert (n-1)*abs(r[i]-r[j])<=n*beta*S;assert abs(r[i]-r[j])<=n*beta*(S+1)/(n-1)
            count+=1
    record('rational Gini spread to variable and fixed centering',True,{'vectors':count,'includes_S0':True})
    for S,P in product([F(0),F(1,2),F(2)],repeat=2):
        sl, su, pl, pu=F(0),F(2),F(0),F(2);W=S*P
        assert W>=sl*P+pl*S-sl*pl and W>=su*P+pu*S-su*pu
        assert W<=su*P+pl*S-su*pl and W<=sl*P+pu*S-sl*pu
    record('SP four products and zero boundary',True,'9 fixed rectangle points; exact Fraction arithmetic')
    G,lam,c,weight=F(1,10),F(1,5),F(1),F(1,2)
    B=(c-G)/lam; y=3;D=2;P=weight*abs(F(y,D)-1);S=F(y,D);A=2*G*S
    record('cutoff budget and scalar/lifted estimator',lam*P+G<=c and weight*abs(F(y,D)-1)<=B and A+2*lam*S*P<=2*c*S and A+2*(S+1)*lam*P<=2*(S+1)*c,'specified rational feasible objective, no route search')
    record('S0 cross multiplication loses penalty',F(0)<=0 and F(1,5)*10>1,'S=A=W=0,P=10,lambda=1/5,c=1: lifted passes, original cutoff fails')
    record('support integer lower bound',all(math.ceil(s/2)<=p for s,p,d in [(2,1,1),(3,2,1),(3,2,2),(4,2,2)]),'declared aggregate service scenarios; total pickup, not support pickup')
    for T,tau,h,B,s,served in [(10,12,2,3,3,2),(10,4,0,0,2,1),(0,0,0,0,2,0),(10,2,3,4,3,0)]:
        M=T+tau+h*max(1,B);assert h*B+M*served<=T-tau+M*s
    record('support Big-M inactive cases',True,'zero h/stock; empty route; tau>T; fixed algebra points')
    record('implicit integrality and A/B',all((abs(b-y)==(b-y if b>=y else y-b)) and ((y!=b)==(abs(b-y)>0)) for b,y in [(0,0),(2,0),(2,4),(2,2)]),'four declared states; missing initial selector forces visit')
    record('counterexample without unique service',F(1,2)+F(1,2)==1,'two serving vehicles pickup 1/2 each give integer net1')
    record('counterexample without direction',F(3,2)-F(1,2)==1,'p=3/2,d=1/2; integer net does not imply either integer')
    record('counterexample without integer inventory',F(2)-F(3,2)==F(1,2),'single one-way pickup1/2 leaves Y=3/2')
    ops=[2,-1,-1];loads=[sum(ops[:j]) for j in range(1,4)]
    record('counterexample to support-local pickup lower bound',min(loads)>=0 and sum(max(0,a) for a in ops[1:])<math.ceil(2/2) and sum(max(0,a) for a in ops)==2,'declared route outside source +2, then W deliveries -1,-1')
    record('counterexample without integer nonzero service',F(1,5)<1,'two served stops pickup=drop=1/5 have total pickup below ceil(2/2)')
    record('counterexample to cumulative pickup<=Q',max([2,0,2])==2 and sum([2,2])>2,'fixed operations +2,-2,+2, Q2, return2, cumulative4')
    initial_load=1;delivery=1;pickup=0
    record('counterexample without empty departure',initial_load+pickup-delivery==0 and delivery>pickup,'preload1 and deliver1, no pickup; transfer upper bound0 fails')
    record('heterogeneous capacity relabelling boundary',2<=2 and 2>1,'route +2,-2 feasible for Q2, cannot relabel to Q1')
    record('inflated native H not physical completion',2*F(1,2)*2>=1 and 1>0,'r=(1,1),g=.5,H=1: original epigraph permits it; true-G0 cap excludes it')
    record('numerical penalty closure counterexample',F(1)-F(1,2*10**9)>=F(1)-F(1,10**9),'F=c-5e-10 meets nonstrict cutoff but >=c-1e-9 closure guard')
    return checks
def next_action(b,other,milestone=False,eps=1e-7):
    if not all(math.isfinite(x) for x in [b]+other):return 'ERROR',None
    if any(x+eps<b for x in other):return 'REQUEUE',None
    if milestone:return 'LOOKAHEAD',None
    higher=[x for x in other if x>b+eps]
    return ('NEXT',min(higher)) if higher else ('LOOKAHEAD',None)
def am(b,U,l,r,eps=1e-7):
    gap=max(U-b,max(eps,1e-12));v=[max(0,min(1,(x-b)/gap)) for x in (l,r)];score=min(v)*sum(v)/2;scale=max(1,abs(b),abs(U),abs(l),abs(r));tol=min(1,max(eps,32*2**-52*scale)/gap+32*2**-52)
    return {'action':'TERMINAL' if min(l,r)<=b+eps else 'SPLIT' if score+tol>=.08 else 'CHILD','target':min(l,r),'score':score,'score_tolerance':tol}
def decisions():
    assert next_action(.2,[.2,.35,.6])==('NEXT',.35)
    assert next_action(.35,[.2,.6],True)[0]=='REQUEUE'
    assert next_action(.35,[.4,.6],True)[0]=='LOOKAHEAD'
    out=[am(.2,1,.21,.3),am(.2,1,.2,.9),am(.2,1,.5,.6)];assert [x['action'] for x in out]==['CHILD','TERMINAL','SPLIT']
    actual=next(csv.DictReader((EV/'am.csv').open()));calc=am(*[float(actual[k]) for k in ['B_p','U','B_L','B_R']]);assert calc['action']=='SPLIT' and near(calc['score'],float(actual['S_AM'])) and near(calc['score_tolerance'],float(actual['score_tolerance']))
    # Atomic replacement checked as interval geometry and union minimum.
    parent=[0,F(1,2)];children=[[0,F(1,4),F(1,2)],[F(1,4),F(1,2),F(3,5)]]
    assert children[0][0]==parent[0] and children[0][1]==children[1][0] and children[1][1]==parent[1]
    assert min(F(1,4),*(x[2] for x in children))==F(1,4)
    # Independent bounded state adapter from Algorithms 2-3. It actually consumes
    # returns; it is not production execution or a full controller simulator.
    def transition(cover,event):
        result=json.loads(json.dumps(cover));p=result[0]
        if not event.get('qualified',True) or event['kind'] in ('UNKNOWN','native_error','deadline','missing_Start'):return result
        if event['kind']=='split':
            ch=event['children']
            if len(ch)!=2 or ch[0]['domain'][0]!=p['domain'][0] or ch[0]['domain'][1]!=ch[1]['domain'][0] or ch[1]['domain'][1]!=p['domain'][1]:return result
            return [{**x,'lb':max(p['lb'],x['lb'])} for x in ch]+result[1:]
        if 'bound' in event:p['lb']=max(p['lb'],event['bound'])
        if event['kind'] in ('INFEASIBLE','OPTIMAL'):p['status']='Closed';p['lb']=max(p['lb'],event['cutoff']) if event['kind']=='INFEASIBLE' else p['lb']
        return result
    cover=[{'domain':[0,1],'status':'Open','lb':.2}]
    for reason in ['UNKNOWN','missing_Start','native_error','deadline']:
        assert transition(cover,{'kind':reason})==cover
    partial=transition(cover,{'kind':'TimeLimit','bound':.205});assert partial[0]['status']=='Open' and partial[0]['lb']==.205
    assert transition(cover,{'kind':'INFEASIBLE','qualified':False,'cutoff':1})==cover
    children=[{'domain':[0,.5],'status':'Empty','lb':1},{'domain':[.5,1],'status':'Open','lb':.3}]
    committed=transition(cover,{'kind':'split','children':children});assert len(committed)==2 and min(x['lb'] for x in committed)==.3
    both_empty=transition(cover,{'kind':'split','children':[{**x,'status':'Empty','lb':1} for x in children]});assert len(both_empty)==2
    assert transition(cover,{'kind':'split','children':children[:1]})==cover
    assert transition(cover,{'kind':'target_return','bound':.25})[0]['status']=='Open'
    # Current schedulable competitors exclude Closed/Empty/Fathomed, irrespective of their floors.
    units=[{'status':'Closed','lb':.4},{'status':'Open','lb':1.1}]
    eligible=[x['lb'] for x in units if x['status'] in ('Open','Invalid') and x['lb']<1-1e-7]
    assert next_action(.2,eligible)==('LOOKAHEAD',None)
    return {'teaching':out,'R123_actual_AM':calc,'atomic_union_minimum':.25,'nonproof_returns_preserve_parent':True,'bounded_transition_adapter':True,'scope':'finite independent rule computations plus source review; no execution/compilation of production decision code or native solve'}
def physical(d,routes):
    y=d['initial'].copy();dur=[0.]*d['m'];seen=set()
    for r in routes:
        k=r['vehicle'];op={int(a):int(p)-int(q) for a,p,q in r['operations']};load=0;P=0
        for i in r['nodes'][1:-1]:
            assert i not in seen and i in op and op[i]!=0;seen.add(i);load+=op[i];P+=max(0,op[i]);y[i]-=op[i];assert 0<=load<=d['Q'][k] and 0<=y[i]<=d['capacities'][i]
        travel=sum(d['dist'][i][j] for i,j in zip(r['nodes'],r['nodes'][1:]));dur[k]=travel+d['h']*P;assert dur[k]<=d['T']+1e-7
    ratios=[F(y[i],d['target'][i]) for i in range(1,d['n']+1)];S=sum(ratios);A=sum(abs(a-b) for a,b in combinations(ratios,2));G=A/(d['n']*S) if S else F(0);P=sum(F(str(d['weights'][i]))*abs(ratios[i-1]-1) for i in range(1,d['n']+1));return y,dur,G+F(3,20)*P
def replay():
    d=instance(EV/'input.txt');rows=list(csv.DictReader((EV/'joint.csv').open()));routes={};checks=[]
    for row in rows[1:4]: # exactly three already-declared accepted insertions
        k=int(row['vehicle']);p=int(row['pickup']);q=int(row['drop']);amount=int(row['quantity']);a=int(row['pickup_leg']);b=int(row['drop_leg']);old=routes.get(k,{'vehicle':k,'nodes':[0,0],'operations':[]});nodes=[0]
        for leg,to in enumerate(old['nodes'][1:]):
            if leg==a and p:nodes.append(p)
            if leg==b and q:nodes.append(q)
            nodes.append(to)
        routes[k]={'vehicle':k,'nodes':nodes,'operations':old['operations']+([[p,amount,0]] if p else [])+([[q,0,amount]] if q else [])};y,dur,Fval=physical(d,list(routes.values()));assert near(float(Fval),float(row['objective']));checks.append({'step':row['step'],'objective_replayed':float(Fval),'feasible':True})
    before=json.loads((EV/'before_neutral.json').read_text());after=json.loads((EV/'after_neutral.json').read_text());event=json.loads((EV/'block_events.jsonl').read_text().splitlines()[0]);assert event['kind']==0
    actual={r['vehicle']:r for r in before['routes']};s=actual[event['source']];t=actual[event['target']];block=s['nodes'][1:-1][event['first']:event['last']];ops={a:p-q for a,p,q in s['operations']};assert sum(ops[i] for i in block)==0
    predicted={k:list(r['nodes'][1:-1]) for k,r in actual.items()};del predicted[event['source']][event['first']:event['last']];predicted[event['target']][event['target_first']:event['target_first']]=block
    assert all(predicted[r['vehicle']]==r['nodes'][1:-1] for r in after['routes'])
    y0,d0,f0=physical(d,before['routes']);y1,d1,f1=physical(d,after['routes']);assert y0==y1 and f0==f1 and sorted(d1,reverse=True)<sorted(d0,reverse=True)
    descent=list(csv.DictReader((EV/'descent.csv').open()));first=descent[:3];end=next(r for r in descent if r['exhausted']=='1')
    assert all(float(r['fitness_after'])>float(r['fitness_before'])+1e-12 for r in first);assert end['accepted']=='0' and end['decoded_checks']==end['neighbors'] and end['interrupted']=='0'
    return {'declared_joint_moves':checks,'neutral_relocation':{'same_inventory':True,'exact_rational_objective_unchanged':True,'duration_tuple_before':sorted(d0,reverse=True),'duration_tuple_after':sorted(d1,reverse=True)},'descent_first3_acceptance':True,'first_exhaustion_pass':end['pass'],'scope':'replayed three saved insertion choices and one saved neutral choice; inspected saved acceptance/exhaustion fields; no neighbor search or new H solution'}
def main():
    started=time.perf_counter()
    if '--extract' in sys.argv:extract()
    sample=json.loads((EV/'matrix_samples.json').read_text());exp,dom=expected(instance(EV/'input.txt'),sample['alpha'],sample['beta'],sample['cutoff'])
    assert not sample['missing_expected'],sample['missing_expected']
    assert set(sample['rows'])==set(exp),'changed template set requires re-extraction'
    for k,row in sample['rows'].items():assert same(row,exp[k]),k
    for k,v in [('G',[sample['alpha'],sample['beta']]),('W_SP',dom['W']),('Y_1',[dom['yl'][1],dom['yu'][1]])]:assert all(near(x,y) for x,y in zip(sample['selected_bounds'][k],v)),k
    assert sample['types']['p_0_1']==sample['types']['d_0_1']=='C' and sample['types']['mode_0_1']=='B' and sample['types']['Y_1']==sample['types']['load_0_1']=='I'
    result={'arithmetic':arithmetic(),'matrix':{'matched_templates':len(sample['rows']),'missing':sample['missing_expected'],'scope':'one sample per algebra template where present; source generation map is broader; no full-matrix reproduction','source_sha256':sample['source_sha256']},'decisions':decisions(),'H_saved_trace':replay(),'optimizer_calls':0,'solver_launches':0,'production_compilations':0,'elapsed_seconds':time.perf_counter()-started}
    dump(ROOT/'checks/finite_results.json',result)
    with (ROOT/'checks/template_coverage.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['template','sample_status','saved_row']);w.writerows([k,'matched' if k in sample['rows'] else 'not_matched',sample['rows'].get(k,{}).get('name','')] for k in exp)
        w.writerows([[k,'source-only; absent trigger in selected open-leaf matrix',source] for k,source in [
            ('singleton_unreachable','CplexBaseline.cpp:1713-1728; A23 z<=0'),
            ('pair_support_cover','CplexBaseline.cpp:2049-2108; A27 sum(z)<=1'),
            ('triple_support_cover','CplexBaseline.cpp:2049-2108; A27 sum(z)<=2'),
            ('required_drop_conditional','IntervalRowFactory.cpp:634-650; A31'),
            ('required_pick_conditional','IntervalRowFactory.cpp:634-650; A31'),
            ('domain_infeasible','IntervalRowFactory.cpp domain reset/flag; A19-A20; 0<=-1'),
            ('numerical_penalty_closure','IntervalRowFactory.cpp:745-751; A32; 0<=-1')]])
    print(json.dumps({'arithmetic_groups':len(result['arithmetic']),'matrix_templates':len(sample['rows']),'missing':sample['missing_expected'],'saved_H_replay':'passed','optimizer_calls':0}))
if __name__=='__main__':main()
