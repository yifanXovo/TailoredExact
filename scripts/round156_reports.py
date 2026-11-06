"""Actual fees and original-price trajectories, separate from nested Work."""
import csv
from fractions import Fraction as F
from round156_common import *

def table(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def oracle():
    summaries=[];curves={};details=[]
    for endpoint in sorted((OUT/'oracle').glob('*/*/result.json')):
        arm=read(endpoint);base=endpoint.parent
        label='rx35_'+arm['label'];fee=read(OUT/'fees'/label/'receipt.json')
        assert fee['exit_code']==0 and not fee['timeout']
        total=fee['G1_seconds'];overhead=total-arm['arm_seconds'];assert overhead>=0
        row={k:arm[k] for k in ('role','method','label','initial_lower','initial_upper','lower','upper','qualified_gap','resolved','oracle_construct_seconds','arm_seconds')}
        row.update(fee_label=label,outer_seconds=total,non_body_overhead=overhead,
            lower_gain=arm['lower']-arm['initial_lower'],upper_decrease=arm['initial_upper']-arm['upper'],
            stop=arm.get('stop','original_price_precision' if arm['resolved'] else 'node_or_gap_return'),
            result_SHA=sha(endpoint))
        paths=[base/'pricing'] if arm['method']=='RN' else sorted(base.glob('price_*'))
        calls=[c for path in paths for c in read(path/'result.json')['calls']]
        row.update(nodes=sum(c['nodes'] for c in calls),Native_Runtime=sum(c['Runtime'] for c in calls),Native_Work=sum(c['Work'] for c in calls),calls=len(calls))
        summaries.append(row)
        events=[]
        for line in (base/'events.jsonl').read_text().splitlines():
            e=json.loads(line)
            # The outer fee contains every event plus non-body setup/teardown.
            # Moving ALL that nonnegative overhead before each event gives a
            # conservative availability bound, not an invented exact timestamp.
            event=dict(available_no_later_than=e['elapsed']+overhead,driver_elapsed=e['elapsed'],kind=e['kind'])
            if e['kind']=='bound':event['L']=e['lower']
            else:event['U']=e['price']
            events.append(event)
        for r in arm.get('records',[]):events.append(dict(available_no_later_than=r['elapsed']+overhead,kind='qualified_call_return',L=r['lower'],U=r['upper']))
        events.append(dict(available_no_later_than=total,kind='outer_return',L=arm['lower'],U=arm['upper']))
        events.sort(key=lambda e:e['available_no_later_than'])
        L=arm['initial_lower'];U=arm['initial_upper'];curve=[]
        for e in events:
            L=max(L,e.get('L',L));U=min(U,e.get('U',U));assert L<=U
            curve.append(dict(**e,lower=L,upper=U,gap=U-L))
        curves[arm['method']]=curve
        save_gz(OUT/'reports/oracle_time_chains'/f'{arm["method"]}.json.gz',curve)
        if arm['method']!='RN':
            c=read(paths[0]/'call.json');lp=read(paths[0]/'LP.json')
            a,b=c['cost_bounds'];old_b=c['original_cost_upper']
            details.append(dict(method=arm['method'],first_target=float(F(c['tau_exact'])),actual_D_lower=a,
                actual_D_upper=b,old_actual_D_upper=old_b,width_fraction=(b-a)/(old_b-a),
                LP_scaled_residual=lp['objective'],LP_converted_guarded_lower=lp['converted_guarded_lower'],
                LP_seconds=lp['Runtime'],LP_Work=lp['Work'],
                first_target_proved=read(paths[0]/'result.json')['target_proved']))
    assert len(summaries)==3
    checkpoints=sorted(set([30.,60.,120.]+[r['outer_seconds'] for r in summaries]));common=[]
    initial=read(OUT/'starting_inventory.json')['R-X35-S-T2']
    for t in checkpoints:
        for method,curve in curves.items():
            past=[r for r in curve if r['available_no_later_than']<=t]
            last=past[-1] if past else dict(lower=initial['lower'],upper=initial['upper'],gap=initial['upper']-initial['lower'])
            common.append(dict(actual_outer_cost_position=t,method=method,lower=last['lower'],upper=last['upper'],gap=last['gap'],
                conservative_all_nonbody_overhead_prepaid=True,not_exact_callback_wall_timestamp=True))
    write(OUT/'reports/oracle_comparison.json',dict(rows=summaries,product_comparison=details,common_cost=common,
        same_scope_and_initial_information=True,rebuild_paid=True,no_inherited_branch_bound_tree=True,
        actual_outer_fees_include_all_runtime_and_driver_IO=True,posthoc_validation_fees_separate=True))
    table(OUT/'reports/oracle_comparison.csv',summaries);table(OUT/'reports/oracle_common_cost.csv',common)
    print(json.dumps(dict(rows=summaries,product=details)),flush=True)

def select():
    audit=read(OUT/'review/actual_oracle_v1/result.json');assert audit['PASS']
    report=read(OUT/'reports/oracle_comparison.json');rn=next(r for r in report['rows'] if r['method']=='RN')
    assert rn['resolved'] and rn['lower_gain']>1e-3 and rn['nodes']<16384
    assert all(r['outer_seconds']>rn['outer_seconds'] for r in report['rows'] if r['method']!='RN')
    target=OUT/'candidate_decision.json';assert not target.exists()
    write(target,dict(UTC=utc(),stage='frozen_producer_selection_before_complete_panel',selected='RN16384_original_gap',
        node_limit=16384,original_price_gap=1e-4,beta=1,d='exact original h',
        fixed_initial_RN_capacity=True,old_4096_restart=False,instance_identity_conditions=False,
        time_based_component_switch=False,Seed=0,Threads=1,only_whole_method_deadline=True,
        lower_gain=rn['lower_gain'],matched_RN_interval=[rn['lower'],rn['upper']],matched_RN_outer_seconds=rn['outer_seconds'],
        reason='RN closes the original price interval below 1e-4 before either residual arm; a larger 65536 tier has no remaining precision need.',
        depth_capacity_not_required_to_be_spent=True,residual_finite_negative_for_efficiency=True,
        original_inventory_upper_is_not_physical=True,proof_only_consumer_unchanged=True,
        preliminary_full_panel_admission_requires=['fresh helper checks including preselected K20','same-PE B/E/Eplus smoke','frozen argv audit'],
        complete_panel_results_not_yet_available=True,stable_GI_TBC_default_unchanged=True,
        source_report_SHA=sha(OUT/'reports/oracle_comparison.json'),source_audit_SHA=sha(OUT/'review/actual_oracle_v1/result.json')))
    print(json.dumps(read(target)),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
