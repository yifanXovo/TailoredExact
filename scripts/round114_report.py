"""Finite engineering checks and evidence-bound reporting after the fixed stop."""
import argparse,csv,difflib,json,sys,time
from pathlib import Path
import read_round114 as reader
from read_round113 import clock as inherited_clock

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def rows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def text(p,s):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:f.write(s)

def main(root):
    begin=time.perf_counter();root=Path(root).resolve();out=root/reader.ROUND;rep=out/'reports_final'
    summary=read(rep/'summary.json');candidate=read(out/'candidate_identity.json');eng=out/'engineering/offline_reader_repair01'
    assert summary['execution_status']=='BLOCKED' and summary['new_qualified_measurements']==1
    assert summary['evaluable_pairs']==21 and summary['total_qualified_measurements']==16
    assert summary['formal_native_children_executed']==2 and summary['formal_actual_Optimize']==5
    assert summary['conservative_starts']==11 and summary['qualification_starts']==6 and not summary['current_reader_fee_pending']
    for field in ['source_bindings','helpers']:
        for name,h in candidate[field].items():assert reader.sha(root/name)==h,name
    original=eng/'original_reader.py';assert reader.sha(original)==candidate['offline_reader_SHA']
    old=original.read_text(encoding='utf-8-sig').splitlines(keepends=True)
    new=(root/'scripts/read_round114.py').read_text(encoding='utf-8-sig').splitlines(keepends=True)
    text(eng/'reader.diff',''.join(difflib.unified_diff(old,new,fromfile='admitted/read_round114.py',tofile='reported/read_round114.py')))
    current=rows(rep/'new_arms.csv');lookup={q['arm']:q for q in current};assert len(current)==4
    assert lookup['P-GRB']['formal_protocol_qualified']=='True'
    assert lookup['ENS-C']['formal_protocol_qualified']=='False' and lookup['ENS-C']['U']=='' and lookup['ENS-C']['L']==''
    assert lookup['ENS-C']['failure_reason']=='WHOLE_ARM_CAP_EXCEEDED'
    assert all(lookup[m]['status']=='UNSTARTED' for m in ['P-S','M-B'])
    assert all(q['classification']=='UNEVALUABLE' and q['dU']==q['dL']==q['dGap']=='' for q in rows(rep/'new_pairs.csv'))
    physical=[];clocks=[]
    for campaign in ['qualification/cli01','campaign']:
        ident=read(out/campaign/'identity.json')
        for l in ident['launches']:
            d=reader.portable(root,l['destination'])
            if not (d/'launch.json').exists():
                assert campaign=='campaign' and l['arm'] in ['P-S','M-B'];continue
            c=reader.clock_evidence(d,l);clocks.append(dict(campaign=campaign,arm=l['arm'],**c))
            if c['within_cap']:assert inherited_clock(d,l,campaign=='campaign')==c['complete_seconds']
            else:
                assert campaign=='campaign' and l['arm']=='ENS-C'
                try:inherited_clock(d,l,True)
                except AssertionError:pass
                else:raise AssertionError('original cap gate must reject actual excess')
            if campaign!='campaign':continue
            ind=read(d/'independent_evidence.json');p=ind['physical'];instance=reader.core.evidence.instance(root,l['panel'])
            delta=[dict(station=k,D=instance['D'][k],Y=p['Y'][k],Y_minus_D=p['Y'][k]-instance['D'][k])
                for k in range(1,l['panel']['V']+1) if p['Y'][k]!=instance['D'][k]]
            candidates=[q for q in ind['witnesses'] if 'sequence' in q and abs(q['F']-ind['own_U'])<1e-12]
            first=min(candidates,key=lambda q:q['available']) if candidates else None
            offset=read(d/'native_end_receipt.json')['complete_seconds_until_native_end']-read(d/'completion.json')['fully_observed_end_to_end_seconds']
            physical.append(dict(arm=l['arm'],input_SHA=l['panel']['input_sha256'],result_SHA=ind['result_SHA'],
                own_U=ind['own_U'],G=p['G'],P=p['P'],Y=p['Y'],D=instance['D'],own_exact_zero=ind['own_exact_zero'],
                different_stations=delta,absolute_bike_difference=sum(abs(v['Y_minus_D']) for v in delta),
                maximum_duration=p['maximum_duration'],physical_T=l['panel']['T_seconds'],return_loads=p['return_loads'],
                complete_fleet_vehicles=p['complete_fleet_vehicles'],all_physical_constraints_rechecked_by_reader=True,
                earliest_best_committed_sequence=first['sequence'] if first else None,
                earliest_best_committed_availability_upper_seconds=first['available']+max(0.,offset) if first else None,
                true_native_first_discovery='unknown',formal_clock_qualified=c['within_cap'],diagnostic_only=not c['within_cap']))
    old_qual=rows(out/'qualification/post01/reports/qualification_arms.csv');new_qual=rows(rep/'qualification_arms.csv')
    for a,b in zip(old_qual,new_qual):
        for k in ['arm','U','L','gap','certificate','complete_seconds','native_Optimize','formal_protocol_qualified']:assert a[k]==b[k],k
    inherited=rows(rep/'inherited_arms.csv');authoritative=rows(out/'inherited_r113/reports_final/arms.csv')
    for a in inherited:
        b=next(q for q in authoritative if (q['id'],q['arm'])==(a['id'],a['arm']))
        for k in ['U','L','gap','certificate','complete_seconds','formal_protocol_qualified','origin_round']:assert a[k]==b[k],k
    for a in rows(rep/'inherited_pairs.csv'):
        b=next(q for q in rows(out/'inherited_r113/reports_final/pairs.csv') if (q['id'],q['candidate'],q['control'])==(a['id'],a['candidate'],a['control']))
        for k in ['classification','evaluable','severe_regression','dU','dL','dGap']:assert a[k]==b[k],k
    write(out/'physical_completion.json',dict(G100_zero_optimum_known=False,own_strict_zero_observed=False,arms=physical))
    write(eng/'targeted_checks.json',dict(passed=True,actual_overshoot_rejected=True,formal_overshoot_numbers_null=True,
        healthy_P_and_two_actual_CLI_original_clock_rules_unchanged=True,qualification_endpoints_unchanged=True,
        historical15_endpoints21_pairs_unchanged=True,new6_pairs_unevaluable=True,original_reader_SHA=reader.sha(original),
        final_reader_SHA=reader.sha(root/'scripts/read_round114.py'),frozen206_source47_helpers_unchanged=True,
        clocks=clocks,Optimize=0,engineering_seconds=time.perf_counter()-begin))
    text(out/'reader_delta.md',f'''# Offline report correction after the actual whole-cap stop

The admitted reader ({reader.sha(original)}) failed at its inherited clock assertion on the actual ENS-C whole of 3605.688342700014 seconds. The original bytes, actual traceback and measured failure receipt remain in engineering/offline_reader_repair01.

Only read_round114.py changed after formal execution stopped. The scoped clock reader retains every inherited chronology, normal-return, metrics/publication and digest check. It reports the actual cap predicate separately and passes false to the frozen endpoint qualification function. ENS-C keeps its real whole and raw native/physical diagnostics, while formal U/L/gap/certificate are null. Six new pairs remain UNEVALUABLE. Historical endpoints and the two qualification CLI are unchanged. Missing same-H evidence is explicit.

Final reader SHA: {reader.sha(root/'scripts/read_round114.py')}. The candidate and admission continue to bind their original reader and frozen performance bytes; they have not been rewritten. reader.diff and targeted_checks.json disclose and verify this offline-only correction. No production source, performance helper, numeric threshold, model, clock or native raw changed; no solver was rerun.
''')
    print(json.dumps(dict(passed=True,physical=[{k:v for k,v in p.items() if k not in ['Y','D']} for p in physical],engineering_seconds=time.perf_counter()-begin)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();main(a.root)
