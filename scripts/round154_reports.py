"""Format sealed current evidence; report original-price and full-method units."""
import csv,re
from fractions import Fraction as F
from round154_common import *

def table(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',encoding='utf-8',newline='') as stream:
        w=csv.DictWriter(stream,fields);w.writeheader()
        for row in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})

def price_profile(folder,p):
    c=read(folder/'call.json') if (folder/'call.json').exists() else {}
    log=(folder/'native.log').read_text(encoding='utf-8',errors='replace') if (folder/'native.log').exists() else ''
    size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',log)
    root=re.search(r'Root relaxation: objective ([^,\s]+)',log)
    types=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',log)
    residual='tau_exact' in p
    guard=p['calls'][0].get('guard_original') if p['calls'] else None
    converted=guard/c['positive_S_bounds'][0] if residual and guard is not None else guard
    sb=c.get('positive_S_bounds')
    if sb is None and c.get('t_bounds'):sb=[1/c['t_bounds'][1],1/c['t_bounds'][0]]
    costs={tuple(map(int,k.split(':'))):F(v) for k,v in p['d_exact'].items()}
    lo=sum(min(costs[s['i'],y] for y in s['support']) for s in p['scope']['stations'])
    hi=sum(max(costs[s['i'],y] for y in s['support']) for s in p['scope']['stations'])
    ext=read(folder/'strengthening.json') if (folder/'strengthening.json').exists() else None
    return dict(variables=c.get('Native_vars',int(size.group(2)) if size else None),
        rows=c.get('Native_rows',int(size.group(1)) if size else None),
        nonzeros=c.get('Native_nz',int(size.group(3)) if size else None),
        Native_root_objective_printed=float(root.group(1)) if root else None,root_log_diagnostic_not_qualified_bound=True,
        guard_units='residual' if residual else 'price',guard_in_stated_units=guard,
        maximum_converted_price_guard=converted,binaries=int(types.group(3)) if types else None,
        positive_S_bounds=sb,positive_S_ratio=sb[1]/sb[0] if sb else None,
        S_bounds_source='saved direct bounds' if residual else 'saved outward reciprocal bounds',
        original_cost_Cartesian_bounds=[float(lo),float(hi)],
        written_centered_scaled_DP_cost_bounds=ext['tight_cost_bounds'] if ext else None,
        root_objective_units='scaled residual' if residual else 'scaled normalized price before anchors',
        same_price_comparisons_use_transported_return_bounds=True)

def prices():
    fees={}
    for lp in (OUT/'fees').glob('*/launch.json'):
        v=read(lp);cmd=v['command']
        for i,a in enumerate(cmd):
            if Path(a).name in ('round154_targets.py','round154_deepen.py') and cmd[i+1:i+2]==['compare']:
                args=cmd[i+2:];rp=lp.parent/'receipt.json'
                fees[tuple(args[:2]+args[3:4])]=dict(label=lp.parent.name,receipt_SHA=sha(rp) if rp.exists() else None,
                    outer_G1=read(rp)['G1_seconds'] if rp.exists() else None,
                    exit_code=read(rp)['exit_code'] if rp.exists() else None)
    rows=[]
    for path in sorted((OUT/'fixed_prices').glob('*/*/hull_result.json')):
        h=read(path);p=read(path.parent/'result.json');c=read(path.parent/'call.json') if (path.parent/'call.json').exists() else {}
        direction=next(q for q in (OUT/'directions').glob('*/direction.json') if sha(q)==h['direction_SHA'])
        d=read(direction);key=(path.parent.parent.name,h['implementation'],path.parent.name.split('_')[-1]);fee=fees.get(key)
        native=h['Native'];q=native[0] if native else {}
        rows.append(dict(role=d['role'],direction=direction.parent.name,implementation=h['implementation'],
            phase=path.parent.name,target_hull=float(F(d['zeta_exact'])),target_price=float(F(d['tau_exact'])),
            fresh_price_lower=h['fresh_raw_price_lower'],inherited_price_lower=h['inherited_price_lower'],
            effective_price_lower=h['effective_price_lower'],true_price_upper=h['true_price_upper'],
            target_proved=h['target_proved'],target_disproved=h['target_disproved'],
            fixed_certificate_lower=h['fixed_certificate_lower'],accumulated_hull_lower=h['accumulated_hull_lower'],
            fixed_certificate_ceiling=h['fixed_certificate_ceiling'],retained_full_hull_upper=h['hull_upper'],
            Native_status=q.get('Status'),Native_Runtime=q.get('Runtime'),Native_Work=q.get('Work'),nodes=q.get('nodes'),
            LP_objective=(h.get('LP') or {}).get('objective'),variables=c.get('Native_vars'),rows=c.get('Native_rows'),
            binaries=c.get('Native_binary'),nonzeros=c.get('Native_nz'),scale=q.get('scale'),
            original_guard=q.get('guard_original'),stock_records=h['stocks'],fee=fee,
            result_path=str(path.relative_to(ROOT)),result_SHA=sha(path),direction_SHA=h['direction_SHA'],
            different_directions_not_one_monotone_trajectory=True))
        rows[-1].update(price_profile(path.parent,p))
    write(OUT/'reports/pricing_results.json',dict(rows=rows));table(OUT/'reports/pricing_results.csv',rows)

def coupled():
    rows=[];phases=[]
    for rp in sorted((OUT/'coupled').glob('*/result.json')):
        data=read(rp)
        if 'implementation' not in data:continue
        phases.append(dict(role=data['role'],phase=rp.parent.name,lower=data['lower'],upper=data['upper'],width=data['upper']-data['lower'],
            columns=len(data['columns']),supports=len(data['supports']),refresh_required=data.get('refresh_required'),
            decision=data['decision'],seconds=data['seconds'],result_SHA=sha(rp),last_columns_evaluated=data.get('last_columns_evaluated')))
        for step in sorted(rp.parent.glob('iter*/result.json')):
            r=read(step);p=read(step.parent/'pricing/result.json')
            row=dict(r,role=data['role'],phase=rp.parent.name,record_SHA=sha(step),price_SHA=sha(step.parent/'pricing/result.json'),
                     direction_SHA=sha(step.parent/'direction.json'),different_directions_not_monotone_prices=True,
                     nested_pricing_seconds_not_extra_fees=True)
            row.update(price_profile(step.parent/'pricing',p));rows.append(row)
    write(OUT/'reports/coupled_iterations.json',dict(rows=rows,phases=phases));table(OUT/'reports/coupled_iterations.csv',rows)

def complete():
    matrix=read(OUT/'confirmation_matrix.json');arms=[];missing=[];mechanism=[]
    for group in matrix['groups']:
        launch=group['launch'];d=Path(launch['destination']);path=d/'round154_endpoint.json'
        if not path.exists():missing.append(group['position']);continue
        arm=read(path);close=read(d/'verification_closeout.json');identity=read(OUT/group['group']/'identity.json')
        assert close['implementation_qualified'] and close['evidence_complete'] and close['performance_eligible']
        assert arm['PE_SHA']==identity['candidate_binary_sha256'] and sha(d/'audit.json')==arm['audit_SHA']
        control=read(d/'round153_control_audit.json');root=control['root']
        arm.update(actual_cap=launch['cap_seconds'],own_floor=root['lower'] if root and root['qualified'] else None,
            helper_seconds=root['helper_process_seconds'] if root else 0.,R154_method=launch['R154_method'],
            formal_floor_rows=sum(x['floor_rows'] for x in control['models']),helper_cost_inside_T_produce=True)
        if arm['R154_method']=='E' and (d/'round154_control_audit.json').exists():
            ext=read(d/'round154_control_audit.json');ledger=ext.get('proof_ledger')
            if ledger:arm.update(raw_search_L=ledger['raw_search_L'],proof_placement=True)
        if not arm['certificate']:assert arm['T_cert'] is None
        arms.append(arm)
        ampath=d/'external/adaptive_mass_decision_ledger.csv'
        amrows=list(csv.DictReader(ampath.open(newline='',encoding='utf-8'))) if ampath.exists() else []
        events=read(d/'observations.json');calls=[r['payload'] for r in events if r['payload']['kind']=='call']
        first=calls[0] if calls else None
        mechanism.append(dict(role=launch['id'],method=launch['R154_method'],arm_id=launch['arm_id'],
            first_AM=amrows[0] if amrows else None,first_Native=first,own_root=root,
            first_AM_SHA=sha(ampath) if ampath.exists() else None,source_sha_same_domain=first['model_sha256'] if first else None))
    pairs=[]
    for role in matrix['roles']:
        by={a['R154_method']:a for a in arms if a['id']==role}
        if not {'B','E'}<=set(by):continue
        b,e=by['B'],by['E'];assert b['input_SHA']==e['input_SHA'] and b['PE_SHA']==e['PE_SHA']
        row=dict(role=role,cap=b['actual_cap'],B_U=b['U'],E_U=e['U'],E_minus_B_U=e['U']-b['U'],
            B_L=b['L'],E_L=e['L'],E_minus_B_L=e['L']-b['L'],B_gap=b['U']-b['L'],E_gap=e['U']-e['L'],
            E_minus_B_gap=(e['U']-e['L'])-(b['U']-b['L']),B_certificate=b['certificate'],E_certificate=e['certificate'],
            B_T_cert=b.get('T_cert'),E_T_cert=e.get('T_cert'),B_T_produce=b['T_produce'],E_T_produce=e['T_produce'],
            B_T_verify=b['T_verify'],E_T_verify=e['T_verify'],B_T_total=b['T_total'],E_T_total=e['T_total'],
            own_floor=e.get('own_floor'),raw_E_search_L=e.get('raw_search_L'),floor_paid=True)
        if 'J' in by:
            j=by['J'];row.update(J_U=j['U'],J_L=j['L'],J_gap=j['U']-j['L'],J_T_produce=j['T_produce'],
                                J_T_verify=j['T_verify'],J_T_cert=j.get('T_cert'),J_certificate=j['certificate'])
        pairs.append(row)
    write(OUT/'reports/complete_arms.json',dict(arms=arms,missing_positions=missing))
    write(OUT/'reports/complete_pairs.json',dict(pairs=pairs,missing_positions=missing))
    table(OUT/'reports/complete_pairs.csv',pairs);write(OUT/'reports/placement_mechanism.json',dict(arms=mechanism))

def costs():
    configure();b=budget();rows=[]
    for lp in sorted((OUT/'fees').glob('*/launch.json')):
        launch=read(lp);rp=lp.parent/'receipt.json';r=read(rp) if rp.exists() else None
        rows.append(dict(label=lp.parent.name,kind=launch['kind'],reservation=launch['reservation_seconds'],
            receipt_SHA=sha(rp) if r else None,G1=r['G1_seconds'] if r else None,
            separate_seconds=r['separately_reported_seconds'] if r else None,exit=r['exit_code'] if r else None,
            timeout=r['timeout'] if r else None,exit_observed=r['exit_observed'] if r else False))
    write(OUT/'cost_report.json',dict(UTC=utc(),budget=b,receipts=rows,
          measurement_gaps='prelaunch source/admission hashing, history reads and bookkeeping are not separately wall-clocked; pure writing/public I/O/compilation separate',
          nested_Runtime_Work_H_helper_not_added=True,not_a_claim_of_complete_wall_clock_accounting=True))
    table(OUT/'reports/costs.csv',rows)

def science():
    selected=read(OUT/'science_state.json');rows=[]
    old=read(OLD153/'reports/scientific_table.json')['rows']
    for role,spec in selected['roles'].items():
        history=next(r for r in old if r['role']==role)
        path=Path(spec['result']);data=read(path)
        lower=max(data['lower'],history['coupled_L']);upper=min(data['upper'],history['coupled_U'])
        assert lower<=upper
        rows.append(dict(role=role,reference_numerical_upper=history['direct_U'],
            R153_lower=history['coupled_L'],R153_upper=history['coupled_U'],
            lower=lower,upper=upper,width=upper-lower,lower_gain=lower-history['coupled_L'],
            upper_reduction=history['coupled_U']-upper,remaining_hull_gain_over_reference=lower-history['direct_U'],
            columns=len(data['columns']),supports=len(data['supports']),refresh_required=data.get('refresh_required',False),
            result=str(path),result_SHA=sha(path),support_result=spec.get('support_result'),
            qualified_numerical_LP_upper_not_physical=True,scope_unchanged=True,
            absolute_research_target=1e-4,target_met=upper-lower<=1e-4))
    write(OUT/'reports/scientific_table.json',dict(rows=rows));table(OUT/'reports/scientific_table.csv',rows)

if __name__=='__main__':
    globals()[sys.argv[1]]()
