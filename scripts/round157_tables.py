"""Saved-evidence tables; no new optimization and no new proof by log parsing."""
import csv
from round157_common import *

def table(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fields);writer.writeheader();writer.writerows(rows)

def run():
    configure();assert not budget()['unclosed'];out=OUT/'reports';facts=[]
    sources=read(OUT/'inventory_sources.json');families=read(OUT/'inventory_families.json')
    for parent in ('fleet','resource','tour','family_floor','completion'):
        for path in sorted((OUT/parent).glob('*/family_result.json' if parent=='tour' else '*/result.json')):
            r=read(path);role=r['role'];label=path.parent.name
            script='round157_assignment_upper.py' if parent=='completion' else f'round157_{parent}.py'
            fee=next((p for p in (OUT/'fees').glob('*/receipt.json')
                      if label in read(p.parent/'launch.json')['command'] and Path(read(p.parent/'launch.json')['command'][2]).name==script),None)
            row=dict(role=role,kind=parent,label=label,classification=r.get('classification',''),
                Native_status=r.get('status',''),nodes=r.get('NodeCount',''),Work=r.get('Work',''),
                Native_Runtime=r.get('Runtime',''),outer_G1_seconds=read(fee)['G1_seconds'] if fee else '',
                required_time_native_lower=r.get('required_time_lower',''),
                required_time_guarded_lower=(r['required_time_lower']-r['margin']) if r.get('required_time_lower') is not None else '',
                resource_relaxation_upper=r.get('resource_relaxation_upper',''),
                original_J_lower=r.get('original_lower',''),physical_U=r.get('physical_U'),
                result_SHA=sha(path))
            if row['physical_U'] is None:row['physical_U']=''
            if parent=='tour':row.update(classification='AGGREGATE_NOT_EXCLUDING' if not r['family_excluded'] else 'AGGREGATE_EXCLUSION',
                aggregate_travel_lower=r['lower'],aggregate_handling_lower=r['minimum_handling'],aggregate_original_time=r['aggregate_original_time'])
            facts.append(row)
    table(out/'oracle_results.csv',facts)
    intervals=[]
    for role,s in sources.items():
        tag='rx35' if role=='R-X35-S-T2' else 'nb35'
        r=read(OUT/'resource'/f'{tag}_family4096_v1/result.json')
        non_time=OUT/'review/non_time_uppers'/f'{role}_result.json'
        true_upper=read(non_time)['true_required_time_upper'] if non_time.exists() else None
        new_lowers=[read(p)['original_lower'] for p in (OUT/'family_floor').glob('*/result.json')
                    if read(p)['role']==role and read(p)['bound_status_qualified']]
        new_uppers=[read(p)['physical_U'] for p in (OUT/'completion').glob('*/result.json')
                    if read(p)['role']==role and read(p)['physical_U'] is not None]
        intervals.append(dict(role=role,original_T=r['original_T'],best_family_members=families[role]['candidates'][0]['family_size'],
            old_inventory_lower=s['lower'],old_inventory_upper=s['upper'],
            family_minimum_Tstar_guarded_lower=r['required_time_lower']-r['margin'],
            family_minimum_Tstar_true_upper=true_upper if true_upper is not None else '',
            original_T_status='INFEASIBLE_FAMILY' if r['classification']=='RESOURCE_INFEAS' else 'UNKNOWN',
            inherited_physical_U=s['endpoint']['U'],inherited_physical_L=s['endpoint']['L'],
            new_round_physical_U=min(new_uppers) if new_uppers else '',
            new_global_physical_L=max(new_lowers) if new_lowers else ''))
    table(out/'physical_scope_intervals.csv',intervals)
    write(out/'table_manifest.json',dict(UTC=utc(),Optimize=0,source_SHA=sha(__file__),
        result_files=len(facts),facts=facts,scope_intervals=intervals,
        log_only_unfinished_calls_not_consumed=True,blank_physical_U_is_not_zero=True))
    print(json.dumps(dict(rows=len(facts),intervals=len(intervals))),flush=True)

if __name__=='__main__':run()
