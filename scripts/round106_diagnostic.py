"""Freeze exact repeated historical C2 Y; diagnostic never feeds formal arms."""
from round106_common import *
import ast,math,re

def values(p):
    out={}
    for line in Path(p).read_text().splitlines():
        if not line or line.startswith('#'):continue
        n,x=line.split();out[n]=float(x)
    return out
def prepare():
    root=Path('E:/r106-recovery/r105-02');old=root/'results/unified_exact_round105'
    identity=read(old/'control01/identity.json');a=next(a for a in identity['launches'] if a['id']=='R98-C2' and a['arm']=='IR-CORE')
    folder=root/'results'/Path(a['destination'].replace('\\','/').split('/results/',1)[1])/'external/round105'
    sources=[];common=None;ownership=set()
    for n in range(1,5):
        p=folder/f'master_{n}.lp.sol';v=values(p);Y=[round(v.get(f'Y_{i}',0)) for i in range(1,31)]
        assert all(abs(v.get(f'Y_{i}',0)-Y[i-1])<=1e-5 and abs(v.get(f'state_{i}_{Y[i-1]}',0)-1)<=1e-5 for i in range(1,31))
        if common is None:common=Y
        assert Y==common
        ownership.add(tuple(round(v.get(f'z_{k}_{i}',0)) for k in range(3) for i in range(1,31)))
        sources.append(dict(candidate=p.relative_to(root).as_posix(),SHA=sha(p),iteration=n))
    assert len(ownership)==4
    panel=a['panel'];assert sha(ROOT/panel['input_path'])==panel['input_sha256']
    text=(ROOT/panel['input_path']).read_text()
    def vector(name):return ast.literal_eval(re.search(r'^\s*'+name+r'\s*=\s*(\[[^\n]*\])',text,re.M)[1])
    D=vector('target');w=vector('weights');w=[x/10 for x in w] if abs(max(w[1:])-10)<1e-6 else w
    r=[common[i-1]/D[i] for i in range(1,31)];G=sum(abs(r[i]-r[j]) for i in range(30) for j in range(i+1,30))/(30*sum(r)) if sum(r)>0 else 0
    F=G+.15*sum(w[i]*abs(r[i-1]-1) for i in range(1,31));assert abs(F-.19293317528184106)<1e-12
    d=OUT/'fixed_Y';d.mkdir(exist_ok=False);yp=d/'inventory.txt'
    with yp.open('x') as f:f.write(' '.join(map(str,common))+'\n')
    command=list(map(str,[BUILD/'Round106Research.exe','fleet',ROOT/panel['input_path'],7200,60,60,.15,d/'native',1200,yp]))
    write(d/'protocol.json',dict(status='FROZEN_SINGLE_DIAGNOSTIC',cap_seconds=1200,reserve_seconds=30,Y=common,Ftrue=F,
        distinct_historical_candidates=4,distinct_historical_Y=1,distinct_ownership=4,sources=sources,
        input_path=panel['input_path'],input_SHA=panel['input_sha256'],command=command,
        research_PE_SHA=sha(BUILD/'Round106Research.exe'),production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),DLL_SHA=sha(DLL),
        source_bindings=bindings(),objective='zero feasibility with original T bound',
        equivalence='R61 full integer fleet template, all vehicles/arcs/service/order choices; fixed Y and Tstar<=originalT; zero objective. No Gini/cutoff and no free expanded physical time.',
        production_handoff=False,no_extension_after_UNKNOWN=True))
    print(json.dumps(dict(Y=common,Ftrue=F,command=command)))
def qualification_identity():
    q=OUT/'qualification';paths=[p for p in q.rglob('*') if p.is_file() and p.suffix in ['.json','.jsonl','.csv']]
    tiny=q/'native02/full/round106';inf=values(tiny/'candidate_2.sol')
    write(q/'identity.json',dict(production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),test_PE_SHA=sha(BUILD/'Round106Tests.exe'),
        research_PE_SHA=sha(BUILD/'Round106Research.exe'),header_SHA=sha('D:/gurobi1302/win64/include/gurobi_c.h'),DLL_SHA=sha(DLL),
        source_bindings=bindings(),tests_SHA={p.relative_to(ROOT).as_posix():sha(p) for p in [ROOT/'tests/round106_tests.cpp',ROOT/'tests/round105_tests.cpp']},
        retained_evidence_SHA={p.relative_to(ROOT).as_posix():sha(p) for p in paths},
        scripted_INF_proof_binding=dict(candidate_SHA=sha(tiny/'candidate_2.sol'),native_ledger_SHA=sha(tiny/'inner/calls.csv'),
            native_INF_model_SHA=sha(tiny/'event_2_k0/full.lp'),native_INF_log_SHA=sha(tiny/'event_2_k0/full.lp.log'),
            meaning='Actual native full-mode INF from same tiny run, subsequently injected only into zero-Optimize scripted contract test; not a new proof'),
        C2_scripted_INF_proof_scope='Caller-supplied historical native proof, audited vector; current scripted replay is not native re-proof',
        native_B='native02/native_B: new actual MIPSOL->B_EXACT+B_THRESHOLD lazy->same master continuation->physical UB and certificate',
        native_A='replay01/C2_A: historical candidate seeded into retained master; actual A lazy plus continuation; offline qualification, never formal evidence',
        actual_inner_deadline='replay01/inner_deadline: core IIS actual cancellation at12s, outer terminated after retained full-proof lazy, UB retained LB0, not certified',
        no_formal_performance_yet=True))
    print(json.dumps(dict(identity=sha(q/'identity.json'))))
if __name__=='__main__':{'prepare':prepare,'identity':qualification_identity}[sys.argv[1]]()
