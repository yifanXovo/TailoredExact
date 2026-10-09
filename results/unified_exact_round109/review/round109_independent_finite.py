"""Finite zero-solve checks of only R109's added scope and decision boundaries."""
from pathlib import Path
from collections import Counter
import copy, hashlib, json, sys, time, traceback
import round109_independent_decision as dec
import round109_independent_parser as parser

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    root=Path(sys.argv[1]).resolve();dest=root/'results/unified_exact_round109/review/finite01';dest.mkdir(exist_ok=False)
    started=time.perf_counter();checks=[];error=None
    save(dest/'launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),explicit_root=str(root),source_SHA=sha(__file__),Optimize=0,native_environment=0,started_unix=time.time()))
    def check(condition,label):
        if not condition:raise AssertionError(label)
        checks.append(label)
    def arm(role,method,seed=0,U=1.,L=.5,certificate=False,seconds=100.):
        return dict(id=role,seed=seed,arm=method,U=U,L=L,gap=U-L,certificate=certificate,complete_seconds=seconds,
            numbers_qualified=True,certificate_qualified=True,PE_SHA='frozenPE',DLL_SHA='frozenDLL')
    try:
        check(len(dec.PANEL)==12 and Counter(r[1] for r in dec.PANEL)=={20:4,50:4,100:4},'exact12 real V20/V50/V100 strata')
        check(Counter(r[3] for r in dec.PANEL)=={'compact':6,'regional':6} and Counter(r[5] for r in dec.PANEL)=={'shortage':4,'balanced':4,'surplus':4},'exact geometry and inventory coverage')
        check(Counter(r[9] for r in dec.PANEL).values()=={2}.values() if False else all(n==2 for n in Counter(r[9] for r in dec.PANEL).values()) and len(Counter(r[9] for r in dec.PANEL))==6,'six orders each exactly twice')
        check(sum(3*r[8] for r in dec.PANEL)==75600 and sum(2*c for _,c,_ in dec.SEED_CHECKS)==12600,'distinct main75600 and seed12600 nominal')
        check(dec.pair(arm('r','M-B',certificate=True,seconds=70),arm('r','P-GRB',certificate=True))['classification']=='WIN','dual certificate exact30s threshold is inclusive')
        check(dec.pair(arm('r','M-B',certificate=True,seconds=70.0000001),arm('r','P-GRB',certificate=True))['classification']=='TIE','dual certificate below30s floor remains tie')
        check(dec.pair(arm('r','M-B',certificate=True,seconds=240),arm('r','P-GRB',certificate=True,seconds=120))['severe_regression'],'dual certificate severe exact2x and120s is inclusive')
        check(not dec.pair(arm('r','M-B',certificate=True,seconds=238),arm('r','P-GRB',certificate=True,seconds=119))['severe_regression'],'dual certificate severe needs both2x and120s')
        check(dec.pair(arm('r','M-B',U=2,L=1.9995),arm('r','P-GRB',U=1,L=.5))['classification']=='MIXED','UB harm and gap gain is mixed without best-of masking')
        tiny=arm('r','M-B',U=1,L=1+1e-10,certificate=True)
        check(dec.good_numbers(tiny) and tiny['gap']<0 and dec.pair(tiny,arm('r','P-GRB',U=1,L=1,certificate=True))['gap_ratio'] is None,'signed tiny negative retained with no percentage ratio')
        missing=arm('r','M-B');missing.update(U=None,L=None,gap=None,numbers_qualified=False)
        check(dec.pair(missing,arm('r','P-GRB'))['classification']=='UNEVALUABLE','missing finite uncertified values are unevaluable')
        zeroq=dict(V=2,M=2,Q=[6,6],capacities=[50000,20,20],initial=[50000,0,0],target=[50000,10,10],weights=[0,1,1],min_ratio=[0,1,1],points=[(0,0)]*3)
        z=parser.physical(zeroq,[dict(vehicle=k,nodes=[0,0],operations=[]) for k in range(2)],3600)
        check(z['G']==0 and z['P']==2 and z['U']==.3 and z['final_inventories']==zeroq['initial'],'zero stock denominator keeps penalty; min_ratio introduces no artificial lower bound')
        q100=dict(V=100,M=8,Q=[30]*8,capacities=[50000]+[20]*100,initial=[50000]+[10]*100,target=[50000]+[10]*100,weights=[0]+[1]*100,min_ratio=[0]+[1]*100,points=[(0,0)]*101)
        z100=parser.physical(q100,[dict(vehicle=k,nodes=[0,0],operations=[]) for k in range(8)],7200)
        check(z100['U']==0 and len(z100['final_inventories'])==101 and len(z100['routes'])==8,'actual100station full8vehicle zero objective remains legal')
        pickupq=dict(V=3,M=1,Q=[6],capacities=[50000,6,6,6],initial=[50000,6,0,6],target=[50000,6,6,6],weights=[0,1,1,1],points=[(0,0)]*4)
        repeated=parser.physical(pickupq,[dict(vehicle=0,nodes=[0,1,2,3,0],operations=[dict(station=1,pickup=6,drop=0),dict(station=2,pickup=0,drop=6),dict(station=3,pickup=6,drop=0)])],18000)
        check(repeated['routes'][0]['total_pickup']==12 and repeated['routes'][0]['return_load']==6 and repeated['routes'][0]['handling_seconds']==1440,'cumulative pickup above Q and loaded return validated by original physics')
        arms=[]
        for r in dec.PANEL:
            arms.extend([arm(r[0],m,U=.5,L=.5,certificate=True) if m=='M-B' else arm(r[0],m) for m in ('P-GRB','ENS-C','M-B')])
        for role,_,methods in dec.SEED_CHECKS:
            arms.extend([arm(role,m,seed=1,U=.9,L=.5) if m=='M-B' else arm(role,m,seed=1) for m in methods])
        eligibility={r[0]:True for r in dec.PANEL};supported=dec.selection(arms,eligibility)
        check(supported['stage']=='BROAD_PANEL_SUPPORT' and supported['main_WIN']==12 and supported['exact_main_denominator']==12 and supported['completed_formal_arms']==42,'support requires full42 with main12 and separate seed3')
        mutated=copy.deepcopy(arms);a=next(a for a in mutated if a['id']=='G20-C2' and a['seed']==1 and a['arm']=='M-B');a.update(U=1.02,L=.5,gap=.52)
        flipped=dec.selection(mutated,eligibility)
        check(flipped['stage']=='BROAD_PANEL_NOT_SUPPORTED' and flipped['seed0_WIN_to_seed1_LOSS']==['G20-C2'] and not flipped['seed1_severe_regressions'] and flipped['seed1_nonLOSS']==2,'nonsevere WIN to LOSS seed flip independently vetoes support')
        duplicated=arms+[copy.deepcopy(arms[0])]
        check(dec.selection(duplicated,eligibility)['stage']=='BLOCKED','duplicate arm cannot inflate42 or mainWIN denominator')
        check(dec.selection(arms[:-1],eligibility)['stage']=='BLOCKED','41valid arms cannot produce normal negative or positive final decision')
        mutated=copy.deepcopy(arms)
        for a in mutated:
            if a['seed']==0 and a['arm']=='M-B' and a['id'].startswith('G100'):
                a.update(U=1.,L=.5,gap=.5,certificate=False)
        result=dec.selection(mutated,eligibility)
        check(result['stage']=='BROAD_PANEL_NOT_SUPPORTED' and result['main_WIN']==8 and result['stratum_WIN']['100']==0 and 'MISSING_STRATUM_GAIN' in result['reason_codes'],'eight mainWIN cannot hide missing V100 gain')
        mutated=copy.deepcopy(arms)
        for a in mutated:
            if a['seed']==0 and a['arm']=='ENS-C':a.update(U=.5,L=.5,gap=0,certificate=True,complete_seconds=1.)
        check(dec.selection(mutated,eligibility)['stage']=='BROAD_PANEL_SUPPORT','ENS losses remain published without hidden ENS support veto')
        groups=[(r[8],r[9]) for r in dec.PANEL]+[(c,ms) for _,c,ms in dec.SEED_CHECKS]
        budget=dec.remaining_budget(8,1200,groups)
        check(budget['remaining_formal_starts']==57 and budget['remaining_nominal_seconds']==88200 and budget['passed'],'8qualification plus57formal starts65 and88200nominal independently counted')
        check(not dec.remaining_budget(16,1200,groups)['passed'],'more than15paid starts prevents fullremaining57 under72')
        check(not dec.remaining_budget(8,11800.001,groups)['passed'],'already paid fee plus allremaining nominal cannot exceed100000')
        check(dec.remaining_budget(8,11800,groups)['passed'],'outer fee100000 equality is inclusive without unknown savings')
    except Exception:
        error=traceback.format_exc()
    elapsed=time.perf_counter()-started
    value=dict(decision='ACCEPT' if error is None else 'HOLD',checks=checks,error=error,Optimize=0,LP_solve=0,native_environment=0,compiler=0,production_edits=0,
        elapsed_engineering_seconds=elapsed,parser_SHA=sha(parser.__file__),decision_SHA=sha(dec.__file__),source_SHA=sha(__file__))
    save(dest/'audit.json',value);save(dest/'receipt.json',dict(exit_code=int(error is not None),audit_SHA=sha(dest/'audit.json'),source_SHA=sha(__file__),elapsed_engineering_seconds=elapsed,cwd=str(Path.cwd())))
    print(json.dumps(dict(decision=value['decision'],checks=len(checks),error=error),ensure_ascii=False))
    if error:sys.exit(1)
if __name__=='__main__':main()
