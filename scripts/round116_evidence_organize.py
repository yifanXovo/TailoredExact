"""Expose existing evidence and separately measure final cohort engineering cost.

No native/route generation, new lower bound, or sealed receipt modification.
The extra reconciliation cost is contemporary; the original reader's per-group
elapsed cost was not instrumented and is explicitly unknown.
"""
import argparse, json, re, time
from pathlib import Path
import round108_reader as core
import read_round116 as reader

def run(root):
    tick=time.perf_counter();root=Path(root).resolve();out=root/reader.ROUND
    data=core.read(out/'reports_final/current_core.json');fixed=core.read(out/'fixed_manifest.json')
    lookup={(a['id'],a['arm']):a for a in data['arms']}
    previous=core.read(out/'reports_final/cohort_reconciliation.json');costs=[];source=[];fleets=[];starts=[]
    for group in fixed['groups']:
        begin=time.perf_counter();claims=[];witnesses=[]
        launches=[l for l in fixed['launches'] if l['group_number']==group['group_number']]
        for l in launches:
            a=lookup[l['id'],l['arm']]
            if not a['formal_protocol_qualified']:continue
            d=reader.portable(root,l['destination']);ind=core.read(d/'independent_evidence.json')
            claims+=core.read(d/'native_claims.json');witnesses+=ind['witnesses']
            source.append(dict(id=l['id'],arm=l['arm'],counts=ind['counts'],
                proof_evidence=a['proof_evidence'],native_proof_qualified=a['native_proof_qualified'],
                result_SHA=ind['result_SHA'],producer_receipt_SHA=a['producer_receipt_SHA']))
            fleets.append(dict(id=l['id'],arm=l['arm'],**ind['physical'],own_exact_zero=ind['own_exact_zero'],
                already_recomputed_by_current_reader=True,new_route_constructed=False))
            if l['arm']=='P-S':starts.append(dict(id=l['id'],**core.read(d/'audit.json')['Start']))
        load_seconds=time.perf_counter()-begin
        reconcile_tick=time.perf_counter();final=reader.reconcile(claims,witnesses)
        assert final==reader.reconcile(list(reversed(claims)),list(reversed(witnesses)))
        stored=next(p for p in previous if p['formal'] and p['id']==group['id'])
        assert final=={k:stored[k] for k in final}
        costs.append(dict(id=group['id'],group_number=group['group_number'],
            load_own_evidence_seconds=load_seconds,
            reconciliation_and_reverse_order_check_seconds=time.perf_counter()-reconcile_tick,
            group_outer_engineering_seconds=time.perf_counter()-begin,
            original_reader_per_group_seconds='unknown_not_instrumented',
            actual_recheck_unix=time.time(),unchanged_final_reconciliation=True,
            own_witnesses=len(witnesses),claims=len(claims),
            completed_qualified_arms=sum(lookup[l['id'],l['arm']]['formal_protocol_qualified'] for l in launches),
            pending_failed_arm_excluded=True,Optimize=0,native_starts=0))
    coeff=[]
    for call in core.rows(out/'reports_final/native_calls.csv'):
        if 'path' not in call or not call['path']:continue
        p=root/call['path'];assert core.sha(p)==call['SHA'];content=p.read_text(encoding='utf-8')
        stats={}
        for label in ['Matrix','Objective','Bounds','RHS']:
            match=re.search(r'\b'+label+r' range\s+\[([^,]+),\s*([^\]]+)\]',content)
            stats[label.lower()+'_printed_range']=list(match.groups()) if match else 'unknown'
        coeff.append(dict(id=call['id'],arm=call['arm'],call=call['call'],model_SHA=call['model_SHA'],
            rows=call.get('rows','unknown'),columns=call.get('columns','unknown'),
            native_log_path=call['path'],native_log_SHA=call['SHA'],**stats,
            ranges_are_printed_native_precision=True,new_solver_query=False))
    core.table(out/'reports_final/group_reconciliation_costs.csv',costs)
    core.table(out/'reports_final/native_coefficient_ranges.csv',coeff)
    core.write(out/'physical_completion.json',dict(qualified_fleets=fleets,qualified_arms=len(fleets),
        failed_arm_physical_components='objective_structure_analysis.json: offline only, formal endpoint remains UNVERIFIABLE',
        unstarted_arms=6,Optimize=0,new_routes=0,no_certificate_backfill=True))
    core.write(out/'formal_compact_Start.json',dict(current_qualified_Starts=starts,current_qualified_PS=4,
        missing_PS_positions=['E100-C1','E100-R2'],Start_not_resubmitted=True,Optimize=0))
    core.write(out/'current_source_qualification.json',dict(qualified_arms=source,
        numerical_reliability_SHA=core.sha(out/'reports_final/numerical_reliability.csv'),
        cohort_reconciliation_SHA=core.sha(out/'reports_final/cohort_reconciliation.json'),
        unqualified_positions=7,failed_arm_return_audit='execution_stop.json',engine_repaired=False,Optimize=0))
    core.write(out/'severe_loss_summary.json',dict(assessed_pair_positions=sum(p['evaluable'] for p in data['pairs']),
        unassessed_pair_positions=sum(not p['evaluable'] for p in data['pairs']),
        severe_losses=[p for p in data['pairs'] if p['severe_regression'] is True],
        unassessed_severity='unknown',primary_clock='T_produce',secondary_T_total_disclosed=True))
    value=dict(Optimize=0,native_starts=0,new_routes=0,qualified_fleets=len(fleets),Start_rows=len(starts),
        coefficient_range_rows=len(coeff),groups_with_separately_instrumented_reconciliation=6,
        original_reader_group_cost_not_backfilled=True,seconds=time.perf_counter()-tick,script_SHA=core.sha(__file__))
    core.write(out/'engineering/evidence_organization_receipt.json',value);print(json.dumps(value),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);run(parser.parse_args().root)
