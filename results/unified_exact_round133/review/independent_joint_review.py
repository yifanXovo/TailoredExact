"""Independent small finite projection/metric replay for G4; no optimizer."""
from pathlib import Path
from fractions import Fraction as Q
import hashlib, io, itertools, json, subprocess, time, zipfile

start=time.perf_counter();pin='52b02252ba47e8228b73e071d6ed692385a4f816'
member='results/unified_exact_round132/artifacts/complete_tiny_joint_study.zip'
blob=subprocess.check_output(['git','show',pin+':'+member])
assert hashlib.sha256(blob).hexdigest()=='d2e55d7ae5fcaf5bb0c9d39a489b589006f3a29eb350b167fd790ad399a0aac1'
arc=zipfile.ZipFile(io.BytesIO(blob));coefficient=Q(5404319552844595,36028797018963968)
reports={};deps=[]

def read(case,file):
    n='results/unified_exact_round132/joint/'+case+'/'+file;b=arc.read(n)
    deps.append(dict(member=n,SHA256=hashlib.sha256(b).hexdigest()))
    return json.loads(b)

def possible_fleets(horizon):
    # Distinct direct fleet enumeration: choose the unique owner and signed
    # quantity at every station first, then test all route orders per vehicle.
    b=[2,1,0,0];capacity=[1,2];choices=[]
    for stock in b:
        options=[(-1,0)]
        for k,cap in enumerate(capacity):
            options.extend((k,p) for p in range(1,min(stock,cap)+1))
            options.extend((k,-d) for d in range(1,min(2-stock,cap)+1))
        choices.append(options)
    for assignment in itertools.product(*choices):
        legal=True
        for k,cap in enumerate(capacity):
            stops=[i for i,(owner,delta) in enumerate(assignment) if owner==k]
            pickup=sum(max(0,assignment[i][1]) for i in stops)
            if 120*pickup>horizon:legal=False;break
            feasible_order=False
            for order in itertools.permutations(stops):
                load=0
                for i in order:
                    load+=assignment[i][1]
                    if load<0 or load>cap:break
                else:feasible_order=True;break
            if not feasible_order:legal=False;break
        if legal:yield assignment,[b[i]-a[1] for i,a in enumerate(assignment)]

for case,horizon,count in [('J2',240,59),('J3',360,66)]:
    fleets=list(possible_fleets(horizon));assert len(fleets)==count
    objectives=[];lhs=[]
    for a,y in fleets:
        total=sum(y);numerator=sum(abs(v-w) for i,v in enumerate(y) for w in y[i+1:])
        g=Q(numerator,4*total) if total else Q(0);p=sum(abs(v-1) for v in y)
        objectives.append(g+coefficient*p)
        lhs.append((max(0,-a[2][1]) if a[2][0]==0 else 0)+(max(0,-a[1][1]) if a[1][0]==1 else 0))
    # Positive signed quantities are pickups and contribute zero delivery.
    assert max(lhs)==1 and min(objectives)==Q(1,4)+coefficient
    mat=read(case,'B_joint_exact_matrix.json');saved=read(case,'original_objective_joint.json')
    values={n:Q(a) for n,a in saved['values'].items()}
    assert all(n in mat['bounds'] for n in values)
    for n,(low,high) in mat['bounds'].items():assert Q(low)<=values.get(n,0)<=Q(high)
    for row in mat['rows']:
        value=sum(Q(a)*values.get(n,0) for n,a in row['coefficients'].items());rhs=Q(row['RHS'])
        assert {'=':value==rhs,'<':value<=rhs,'>':value>=rhs}[row['sense']]
    obj=Q(saved['objective_constant'])+sum(Q(a)*values.get(n,0) for n,a in saved['objective_coefficients'].items())
    assert obj==coefficient
    assert all(values[f'Y_{i}']==Q(3,4) and values[f'e_{i}']==Q(1,4) for i in range(1,5))
    assert min(objectives)-obj==Q(1,4)
    reports[case]=dict(fleet_count=len(fleets),max_simple_conflict=max(lhs),IP_optimum=str(min(objectives)),
        loaded_primal_objective=str(obj),exact_gap='1/4',all_loaded_rows=len(mat['rows']),all_bounds=len(mat['bounds']))

report=dict(status='PASS',scope='independent direct fleet enumeration, all-row loaded primal replay and metric recomputation',
    parent='Round133 G4 internal independent review; not third-party replication',cases=reports,dependencies=deps,
    Optimize=0,native_modules=0,source_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    outer_seconds=time.perf_counter()-start,budget_category='E independent arithmetic; outer once')
out=Path(__file__).with_name('independent_joint_review_receipt_v2.json')
assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
