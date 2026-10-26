"""Independent interval threshold arithmetic vs actual compatibility subject."""
from pathlib import Path
from fractions import Fraction
import copy,hashlib,itertools,json,math,runpy,sys,time,traceback
ROOT=Path(sys.argv[1]).resolve();OUT=ROOT/'results/unified_exact_round109';DEST=Path(sys.argv[2]).resolve();assert DEST.is_relative_to(OUT/'review');DEST.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
tick=time.perf_counter();error=None;cases=[]
save(DEST/'launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=sha(__file__),Optimize=0,native_environment=0));(DEST/'source_at_execution.py').write_bytes(Path(__file__).read_bytes())
try:
    sys.path.insert(0,str(ROOT/'scripts'));import round109_interval_pairs as subject
    own=runpy.run_path(str(OUT/'review/round109_independent_decision.py'))['pair']
    def make(interval,role):
        lo,hi=interval;a=dict(id='finite',seed=0,arm=role,U=0.,L=0.,gap=0.,certificate=True,certificate_qualified=True,numbers_qualified=True,cap_seconds=max(1800.,hi+1))
        if lo==hi:a['complete_seconds']=lo
        else:a.update(complete_seconds=None,complete_seconds_interval=[lo,hi],original_whole_clock_unknown=True,numerical_reader_recovery='known_finite_subject')
        return a
    intervals=[(100.,(50.,70.)),(100.,(70.,70.000001)),(200.,(230.,250.)),(200.,(399.,401.)),(120.,(239.999999,240.)),(50.,(150.,169.999999)),(50.,(170.,170.000001))]
    rectangles=[(a,(c,c)) for c,a in intervals]+[((269.,271.),(299.,301.)),((200.,201.),(300.,600.)),((643.7820000000065,645.352919),(112.51700630004052,112.51700630004052)),((112.51700630004052,112.51700630004052),(643.7820000000065,645.352919))]
    for ix,(ia,ic) in enumerate(rectangles):
        a=make(ia,'M-B');c=make(ic,'P-GRB');corners=[]
        for x,y in itertools.product(ia,ic):
            corners.append(own(dict(a,complete_seconds=x),dict(c,complete_seconds=y)))
        classes={v['classification'] for v in corners};severity={v['severe_regression'] for v in corners};invariant=len(classes)==len(severity)==1
        result=subject.pair(a,c);assert result['classification']==(next(iter(classes)) if invariant else 'UNEVALUABLE')
        assert result['severe_regression']==(next(iter(severity)) if invariant else None)
        assert result['candidate_seconds']==a['complete_seconds'] and result['control_seconds']==c['complete_seconds'] and result['certified_time_ratio'] is None and result['time_improvement'] is None
        lr,hr=result['certified_time_ratio_interval'];assert Fraction(lr)<=Fraction(ia[0])/Fraction(ic[1]) and Fraction(hr)>=Fraction(ia[1])/Fraction(ic[0])
        # Independent full rectangle sample verifies corner-monotonicity,
        # including the 30/.1 threshold kink and2x/120 severe boundary.
        if invariant:
            for u,v in itertools.product([0.,.1,.25,.5,.75,.9,1.],repeat=2):
                ar=dict(a,complete_seconds=ia[0]+u*(ia[1]-ia[0]));cr=dict(c,complete_seconds=ic[0]+v*(ic[1]-ic[0]));inside=own(ar,cr)
                assert inside['classification']==result['classification'] and inside['severe_regression']==result['severe_regression']
        cases.append(dict(case=ix,candidate_interval=ia,control_interval=ic,independent_corners=[dict(classification=v['classification'],severe_regression=v['severe_regression']) for v in corners],actual_result=result,independent_invariant=invariant))
    rejected=[]
    for label,change in [('missing_fault_provenance',{'numerical_reader_recovery':None}),('missing_unknown_flag',{'original_whole_clock_unknown':False}),('reversed_interval',{'complete_seconds_interval':[700.,600.]}),('nonpositive_interval',{'complete_seconds_interval':[0.,1.]}),('nonfinite_interval',{'complete_seconds_interval':[600.,float('inf')]}),('at_or_over_cap',{'complete_seconds_interval':[600.,1800.]})]:
        a=make((600.,650.),'M-B');a.update(change)
        try:subject.pair(a,make((100.,100.),'P-GRB'))
        except (AssertionError,ValueError,KeyError):rejected.append(label)
        else:raise AssertionError('accepted invalidclock '+label)
    save(DEST/'audit.json',dict(decision='ACCEPT',source_SHA=sha(__file__),subject_SHA=sha(ROOT/'scripts/round109_interval_pairs.py'),independent_rules_SHA=sha(OUT/'review/round109_independent_decision.py'),rectangle_cases=cases,rejected_invalid_clocks=rejected,checks=len(cases)+len(rejected),Optimize=0,native_environment=0))
    print(json.dumps(dict(decision='ACCEPT',rectangle_cases=len(cases),invalid_clocks_rejected=len(rejected))),flush=True)
except Exception:
    error=traceback.format_exc();save(DEST/'audit.json',dict(decision='HOLD',error=error));print(error,file=sys.stderr,flush=True)
save(DEST/'receipt.json',dict(exit_code=int(error is not None),elapsed_engineering_seconds=time.perf_counter()-tick,source_SHA=sha(__file__),audit_SHA=sha(DEST/'audit.json'),Optimize=0,native_environment=0))
if error:sys.exit(1)
