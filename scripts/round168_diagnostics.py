"""Summaries and independent finished-data checks only; never imports a solver."""
from round168_common import *
from fractions import Fraction
from collections import Counter
import re,math,shutil

def parse_input(path):
    s=Path(path).read_text(encoding='utf-8-sig')
    get=lambda name:[float(x) for x in re.findall(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?',re.search(r'\b'+name+r'\s*=\s*\[(.*?)\]',s,re.S)[1])]
    b=list(map(int,get('initial')));d=list(map(int,get('target')));w=get('weights')
    if abs(max(w[1:])-10)<=1e-6:w=[x/10 for x in w]
    return b,d,w
def exact_parts(record,physical):
    _,d,w=parse_input(ROOT/record['input']['path']);y=physical['Y'];rr=[Fraction(y[i],d[i]) for i in range(1,len(d))]
    ss=sum(rr);g=sum(abs(a-b) for j,a in enumerate(rr) for b in rr[j+1:])/(len(rr)*ss) if ss else Fraction(0)
    p=sum(Fraction.from_float(w[i])*abs(rr[i-1]-1) for i in range(1,len(d)))
    f=g+Fraction.from_float(record['lambda_value'])*p
    assert abs(float(f)-physical['F'])<=1e-7
    return dict(F=float(f),G=float(g),P=float(p),F_fraction=str(f),max_original_F_difference=abs(float(f)-physical['F']))
def summarize():
    tick=time.perf_counter();data=read(OUT/'campaign/route_family_results.json');assert len(data['positions'])==11
    archive=read(OUT/'archive_manifest.json');records={r['run']:r for r in archive['records']}
    checks=[];changes=[]
    views=list(data['positions'])
    for p in data['positions']:
        raw_path=OUT/'campaign'/p['position']/'result.json'
        if raw_path.exists():
            native=read(raw_path)
            if abs(native['physical']['F']-p['physical']['F'])>1e-12:
                views.append(dict(p,position=p['position']+'__raw',physical=native['physical'],analysis_scope='raw Native witness before inclusion propagation'))
    for p in views:
        r=records[p['parent']];v=p['physical'];checks.append(dict(position=p['position'],**exact_parts(r,v)))
        before=r['historical_physical'];by={op['station']:(route['vehicle'],op['pickup']-op['drop']) for route in before['routes'] for op in route['operations']}
        ay={op['station']:(route['vehicle'],op['pickup']-op['drop']) for route in v['routes'] for op in route['operations']}
        stock=[dict(station=i,before=before['Y'][i],after=v['Y'][i],delta=v['Y'][i]-before['Y'][i]) for i in range(1,len(v['Y'])) if v['Y'][i]!=before['Y'][i]]
        oldseq={route['vehicle']:[i for i in route['nodes'] if i] for route in before['routes']}
        newseq={route['vehicle']:[i for i in route['nodes'] if i] for route in v['routes']}
        reordered=[]
        for k in oldseq:
            common=set(oldseq[k])&set(newseq[k]);o=[i for i in oldseq[k] if i in common];a=[i for i in newseq[k] if i in common]
            if o!=a:reordered.append(dict(vehicle=k,old_common_order=o,new_common_order=a))
        changes.append(dict(position=p['position'],new_fleet=v['F']<p['parent_F']-1e-7,F_change=v['F']-p['parent_F'],
            G_change=v['G']-before['G'],P_change=v['P']-before['P'],stock_changes=stock,
            deleted=sorted(set(by)-set(ay)),activated=sorted(set(ay)-set(by)),
            flipped=[i for i in by.keys()&ay.keys() if by[i][1]*ay[i][1]<0],
            owner_changes=[dict(station=i,before=by[i][0],after=ay[i][0]) for i in by.keys()&ay.keys() if by[i][0]!=ay[i][0]],
            reordered=reordered,vehicles=v['routes'],interpretation='witness description only; no Native causal attribution'))
    write(OUT/'fleet_changes.json',dict(UTC=utc(),records=changes))
    write(OUT/'independent_objective_readback.json',dict(UTC=utc(),arithmetic='rational stock/target; exact binary64 lambda and normalized input weights; no Optimize',checks=checks,PASS=True,seconds=time.perf_counter()-tick))
    calls=[]
    for directory,kind in [(OUT/'tiny_qualification','tiny'),(OUT/'campaign','substantive')]:
        for p in sorted(directory.glob('*/Optimize.jsonl')):
            ledger=[json.loads(l) for l in p.read_text().splitlines()];assert len(ledger)==2 and ledger[0]['phase']=='begin' and ledger[1]['phase']=='end'
            assert ledger[0]['call_id']==ledger[1]['call_id'] and ledger[1]['api_return']==0
            d=read(p.parent/'result.json');params=read(p.parent/'parameters.json');assert params['Threads']==1 and params['Seed']==0 and params['MIPGap']==params['MIPGapAbs']==0
            assert params['FeasibilityTol']==params['OptimalityTol']==1e-6 and params['IntFeasTol']==1e-5
            assert d['model_SHA256']==sha(p.parent/'model.lp') and ledger[0]['model_SHA256']==d['model_SHA256']
            st=read(p.parent/'start_check.json');assert st['complete'] and st['max_row_bound_type_residual']<=1e-7
            calls.append(dict(kind=kind,path=p.parent.relative_to(ROOT).as_posix(),**d,parameters=params,ledger=ledger))
    ids=[c['call_id'] for c in calls];assert len(ids)==len(set(ids));tiny=[c for c in calls if c['kind']=='tiny'];sub=[c for c in calls if c['kind']=='substantive']
    assert len(tiny)==6 and len(sub)<=9 and len(calls)<=19
    end=time.time();begin=float((OUT/'diagnostic_epoch.txt').read_text());assert end-begin<5400
    cost=dict(UTC=utc(),actual_Optimize=len(calls),tiny_Optimize=len(tiny),substantive_Optimize=len(sub),max_Optimize=19,
        unused_tiny_repair_calls=4,unused_substantive_calls=9-len(sub),Native_Runtime_seconds=sum(c['Native_Runtime'] for c in calls),
        tiny_Native_Runtime_seconds=sum(c['Native_Runtime'] for c in tiny),substantive_Native_Runtime_seconds=sum(c['Native_Runtime'] for c in sub),
        Native_Work=sum(c['Native_Work'] for c in calls),recorded_call_outer_seconds=sum(c['outer_seconds'] for c in calls),
        diagnostic_enclosing_start_epoch=begin,diagnostic_enclosing_end_epoch=end,diagnostic_enclosing_seconds=end-begin,
        diagnostic_enclosing_includes='qualification models/Start/membership, Native, all substantive build/read/check, interleaved audit and management; conservative wall window',
        diagnostic_outer_cap_seconds=5400,Native_nested_not_added_to_outer=True,
        archive_recovery_IO_seconds=archive['extraction_seconds'],archive_physical_math_science_not_IO=True,
        science_elapsed_seconds=end-datetime.fromisoformat(read(OUT/'entry_state.json')['work_start_UTC']).timestamp(),science_cap_seconds=28800,
        public_Git_IO='separately recorded during delivery',no_complete_algorithm_performance_run=True)
    write(OUT/'calls.json',dict(UTC=utc(),calls=calls));write(OUT/'cost_report.json',cost)
    bycall={c['call_id']:c for c in calls}
    for p in data['positions']:
        c=bycall.get(p['solve_id']);p['bound_qualified']=bool(c and c['bound_qualified'])
        p['raw_safe_L_basis']='qualified Native lower minus outward 1e-7 guard' if p['bound_qualified'] else 'nonnegative original objective L=0; Native lower unqualified or no call'
        p['numeric_policy']='target +1e-7; outward lower guard1e-7; physical time1e-7; inherited Native tolerances; details family_manifest.json'
        p['Native_Runtime']=c['Native_Runtime'] if c else 0;p['Native_Work']=c['Native_Work'] if c else 0;p['outer_seconds']=c['outer_seconds'] if c else 0
        p['columns']=c['columns'] if c else 0;p['rows']=c['rows'] if c else 0
        p['bound_qualification_reason']='PASS' if p['bound_qualified'] else ('available incumbent matrix/Native residual exceeds frozen1e-7 gate' if c else 'no Optimize; archive physical HIT')
    write(OUT/'route_family_results.json',data)
    with (OUT/'campaign/route_family_results.csv').open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    for row,p in zip(rows,data['positions']):
        assert row['parent_run']==p['parent'] and row['family']==p['scope']
        row.update(bound_qualified=p['bound_qualified'],raw_safe_L_basis=p['raw_safe_L_basis'],numeric_policy=p['numeric_policy'],bound_qualification_reason=p['bound_qualification_reason'])
    with (OUT/'route_family_results.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    frozen=read(OUT/'family_manifest.json');assert len(frozen['positions'])==11
    assert sha(WORK/'build-cache/round168/Round168RouteFamily.exe')==read(OUT/'candidate_manifest.json')['executable']['SHA256']
    assert sha(ROOT/'src/round168_route_family.cpp')==read(OUT/'candidate_manifest.json')['source']['SHA256']
    unchanged=['src/CplexBaseline.cpp','src/GurobiBaseline.cpp','src/MipStartMapping.cpp','src/IntervalRowFactory.cpp','include/Round166Research.hpp','include/Round167ConditionalState.hpp','config/gi_tbc_round137.json','config/gi_tbc_c166_round166.json']
    assert not git('diff',BASE,'--',*unchanged)
    write(OUT/'evidence_checks.json',dict(UTC=utc(),PASS=True,actual_calls=len(calls),actual_tiny=len(tiny),actual_substantive=len(sub),
        unique_position_ids=len({p['position'] for p in data['positions']}),verdicts=dict(Counter(p['verdict'] for p in data['positions'])),
        final_PE_and_CPP_match_frozen_candidate=True,all_actual_models_ledger_Start_parameters_checked=True,
        core_default_sources_unchanged=unchanged,master_new_rows=0,new_complete_method_runs=0,
        target_and_family_manifest=bind(OUT/'target_manifest.json'),positions=bind(OUT/'route_family_results.csv'),
        independent_objective_check=bind(OUT/'independent_objective_readback.json')))
    print(json.dumps(dict(verdicts=dict(Counter(p['verdict'] for p in data['positions'])),calls=len(calls),Native=cost['Native_Runtime_seconds'],diagnostic_outer=cost['diagnostic_enclosing_seconds']),indent=2))
if __name__=='__main__':globals()[sys.argv[1]]()
