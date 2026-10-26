"""Compare completed primary publication only to an already executed own audit."""
from pathlib import Path
import argparse,csv,hashlib,json,math,sys,time,traceback
ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--own-audit',required=True);ap.add_argument('--reports',required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
ROOT=Path(args.root).resolve();DEST=Path(args.out).resolve();assert DEST.is_relative_to(ROOT/'results/unified_exact_round109/review');DEST.mkdir(exist_ok=False);tick=time.perf_counter();reads={};error=None
def source(p):
    p=Path(p).resolve();assert p.is_relative_to(ROOT);data=p.read_bytes();reads[str(p)]=hashlib.sha256(data).hexdigest();return data
def sha(p):return hashlib.sha256(source(p)).hexdigest()
def path(p):
    p=Path(p);return p.resolve() if p.is_absolute() else (ROOT/p).resolve()
def obj(p):return json.loads(source(p).decode('utf-8-sig'))
def rows(p):return list(csv.DictReader(source(p).decode('utf-8-sig').splitlines()))
def save(name,value):
    with (DEST/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
save('launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),explicit_read_root=str(ROOT),source_SHA=sha(__file__),Optimize=0,native_environment=0));(DEST/'source_at_execution.py').write_bytes(source(__file__))
try:
    ownpath=path(args.own_audit);own=obj(ownpath);receipt=obj(ownpath.parent/'receipt.json');assert own['decision']=='ACCEPT_INDEPENDENT_BLOCKED' and receipt['exit_code']==0 and receipt['audit_SHA']==sha(ownpath) and own['stage']=='BLOCKED'
    reports=path(args.reports);published=rows(reports/'arms.csv');pp=rows(reports/'pairs.csv');ps=obj(reports/'selection_decision.json');summary=obj(reports/'summary.json');arms=own['own_actual_arms'];pairs=own['science']['own_pairs'];selection=own['selection']
    assert len(published)==len(arms)==24 and summary['formal_arms']==24 and summary['failed_formal_arms']==1 and summary['conservative_starts']==51 and summary['outer_solver_fee_seconds']==own['fees']['paid_outer_seconds']
    endpoint_checks=[]
    for a in arms:
        b=next(v for v in published if (v['id'],int(v['seed']),v['arm'])==(a['id'],a['seed'],a['arm']));assert abs(float(b['U'])-a['U'])<=1e-7 and abs(float(b['L'])-a['L'])<=1e-7 and abs(float(b['gap'])-a['gap'])<=1e-7 and (b['certificate']=='True')==a['certificate']
        assert (b['complete_seconds']=='' if a['complete_seconds'] is None else abs(float(b['complete_seconds'])-a['complete_seconds'])<=1e-9)
        if a['complete_seconds'] is None:assert json.loads(b['complete_seconds_interval'])==a['complete_seconds_interval']
        endpoint_checks.append(dict(id=a['id'],arm=a['arm'],seed=a['seed'],U=a['U'],L=a['L'],gap=a['gap'],certificate=a['certificate'],complete_seconds=a['complete_seconds'],complete_seconds_interval=a.get('complete_seconds_interval')))
    assert len(pp)==len(pairs)==24
    for p in pairs:
        b=next(v for v in pp if (v['id'],int(v['seed']),v['candidate'],v['control'])==(p['id'],p['seed'],p['candidate'],p['control']));assert b['classification']==p['classification'] and (b['severe_regression']=='True')==(p['severe_regression'] is True)
        if p.get('certified_time_ratio_interval') is not None:assert b['certified_time_ratio']=='' and json.loads(b['certified_time_ratio_interval'])==p['certified_time_ratio_interval']
    for field in ['stage','main_WIN','main_LOSS','main_severe_P_regressions','stratum_WIN','seed1_nonLOSS','seed1_severe_regressions','seed0_WIN_to_seed1_LOSS']:assert ps[field]==selection[field],field
    assert ps['completed_formal_seed1_arms']==0 and ps['formal_seed_sensitivity_assessed'] is False and ps['reason_codes']==selection['reason_codes']
    assert [int(v['number']) for v in rows(reports/'failures.csv')]==[25] and [int(v['number']) for v in rows(reports/'unstarted.csv') if v['campaign']=='campaign']==list(range(26,43))
    combined=own['own_qualification']+arms;native=rows(reports/'native_calls.csv');expected_calls=sum(len(a['native_records']) for a in combined);assert len(native)==summary['actual_Optimize']==expected_calls
    assert summary['independently_proved_actual_native_returns_without_journal']==1 and summary['actual_native_returns_including_independent_rc_sources']==expected_calls and summary['Optimize_returned']==expected_calls-1
    for a in combined:
        for call in a['native_records']:
            b=next(v for v in native if (v['id'],int(v['seed']),v['arm'],int(v['call']))==(a['id'],a['seed'],a['arm'],call['call']));assert b['model_SHA']==call['model_SHA'] and b['actual_Optimize']=='True'
            if (a['id'],a['arm'])==('G50-C2','P-GRB'):assert b['returned']=='False' and b['returned_journal_missing']=='True' and b['actual_normal_return_from_independent_rc_source']=='True' and b['native_bounds_mathematically_qualified']=='False'
            else:assert b['returned']=='True'
    mechanisms=rows(reports/'mechanism_summary.csv');models=rows(reports/'models.csv')
    for a,m in zip(arms,own['mechanism']):
        b=next(v for v in mechanisms if v['campaign']=='campaign' and (v['id'],int(v['seed']),v['arm'])==(a['id'],a['seed'],a['arm']));kinds=m['solve_kinds'];assert int(b['actual_native_Optimize'])==m['actual_Optimize'] and int(b['LP_calls'])==kinds.get('LP',0) and int(b['terminal_MIP_calls'])==kinds.get('MIP',0) and int(b['child_bound_target_MIP_calls'])==kinds.get('CHILD_BOUND_TARGET_MIP',0) and int(b['next_leaf_target_MIP_calls'])==kinds.get('NEXT_LEAF_TARGET_MIP',0)
        assert json.loads(b['AM_action_counts'])==m['AM_actions']
        if m['maximum_observed_open_relevant_leaf_count'] is not None:assert int(b['maximum_open_relevant_leaves'])==m['maximum_observed_open_relevant_leaf_count']
        for model in a['model_contracts']:
            b=next(v for v in models if v['campaign']=='campaign' and (v['id'],int(v['seed']),v['arm'],v['SHA'])==(a['id'],a['seed'],a['arm'],model['SHA']));assert int(b['rows'])==model['rows'] and int(b['columns'])==model['columns'] and int(b['quantity_columns'])==model['quantity_columns'] and b['quantity_type']==('C' if a['arm']=='M-B' else 'I') and int(b['frozen_A_B_rows_checked'])==model['AB_exact_rows']
    fleets=rows(reports/'physical_fleets.csv')
    for a in arms:
        b=next(v for v in fleets if v['campaign']=='campaign' and (v['id'],int(v['seed']),v['arm'])==(a['id'],a['seed'],a['arm']));ph=a['physical'];assert abs(float(b['F'])-ph['U'])<=1e-7 and abs(float(b['G'])-ph['G'])<=1e-7 and abs(float(b['P'])-ph['P'])<=1e-7 and json.loads(b['Y'])==ph['final_inventories'] and int(b['complete_fleet_vehicles'])==len(ph['routes']) and int(b['total_return_load'])==sum(r['return_load'] for r in ph['routes'])
    fb=rows(reports/'fees.csv');assert sum(int(v['conservative_process_starts']) for v in fb)==51 and abs(sum(float(v['outer_seconds']) for v in fb)-own['fees']['paid_outer_seconds'])<=1e-9 and len(fb)==len(own['fees']['records'])
    floors=rows(reports/'analytical_full_domain_bounds.csv');assert len(floors)==2 and {(v['id'],v['arm']) for v in floors}=={('G50-C1','P-GRB'),('G50-C2','P-GRB')} and all(float(v['L'])==0 and v['native_bound']=='False' and v['borrowed_ENS_bound_or_certificate']=='False' for v in floors)
    value=dict(decision='ACCEPT_INDEPENDENT_BLOCKED_PUBLICATION',stage='BLOCKED',resumption_allowed=False,own_raw_audit_SHA=sha(ownpath),own_raw_receipt_SHA=sha(ownpath.parent/'receipt.json'),own_completed_checks=own['completed_checks'],own_pair_counts=own['science']['own_pair_counts'],all24_endpoints_and_24pairs_agree=True,all_models_native_calls_AM_and_physical_final_fleets_agree=True,actual_Optimize=expected_calls,journal_returned=expected_calls-1,independently_proved_rc0_without_returned=1,failed25_not_endpoint=True,unstarted17_not_0_or_TIE=True,formal_Seed1_sensitivity_not_assessed=True,V100_performance_not_assessed=True,original_stage_gate_placeholders_not_observed_failures=True,exact_bounded_clocks_and_ratio_remain_null=True,fees_starts=51,fees_outer_seconds=own['fees']['paid_outer_seconds'],endpoints=endpoint_checks,primary_table_SHA={p.name:sha(p) for p in reports.glob('*.csv')},primary_selection_SHA=sha(reports/'selection_decision.json'),primary_summary_SHA=sha(reports/'summary.json'),read_bindings=reads,Optimize=0,native_environment=0,production_edits=0)
    save('audit.json',value);print(json.dumps(dict(decision=value['decision'],actual_Optimize=expected_calls,counts=value['own_pair_counts'])),flush=True)
except Exception:
    error=traceback.format_exc();save('audit.json',dict(decision='HOLD',error=error));print(error,file=sys.stderr,flush=True)
save('receipt.json',dict(exit_code=int(error is not None),engineering_elapsed_seconds=time.perf_counter()-tick,source_SHA=sha(__file__),audit_SHA=sha(DEST/'audit.json'),Optimize=0,native_environment=0,cwd=str(Path.cwd()),explicit_read_root=str(ROOT)))
if error:sys.exit(1)
