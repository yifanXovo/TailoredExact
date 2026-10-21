"""Read sealed observations; retain every fixed comparison and raw signed gap."""
from round128_common import *
from round127_analysis import qualified,pair,root,row_family,statistics_pairs
from round128_qualify import root_diff
from round127_qualify import compare
from compare_round112_startup import reconstruct as H
import round108_reader as core
import collections,math

def analyze():
    manifest=read(OUT/'experiment_manifest.json');arms=[];pairs=[];costs=[];differences=[];support=[]
    for g in manifest['groups']:
        camp=OUT/g['name'];i=read(camp/'identity.json');aa=read(camp/'reconstructed.json')['arms']
        assert [a['method'] for a in aa]==g['methods'] and len(aa)==len(i['launches'])
        by={a['method']:a for a in aa};hs={};models={};calls={};local_costs={}
        for a,l in zip(aa,i['launches']):
            assert a['PE_SHA']==read(OUT/'E2_frozen.json')['PE_SHA'] and a['binary_layer']=='E2'
            a.update(group=g['number'],signed_gap=a['U']-a['L'],absolute_gap=abs(a['U']-a['L']))
            assert a['T_cert']==(a['T_produce'] if qualified(a) and a['certificate'] else None)
            arms.append(a);d=Path(l['destination']);r=read(d/'result.json');p=l['panel']
            ledger=core.rows(d/'external/paper_optimize_ledger.csv') if a['method']!='P' else []
            if a['method']!='P':
                hs[a['method']]=H(ROOT,p,d);m,c=root(d);models[a['method']]=m;calls[a['method']]=c
            else:m,c=core.lp_model(d/'compact.lp'),None
            families=collections.Counter(row_family(row) for row in m['rows'])
            LPS=sum(float(x['solver_runtime']) for x in ledger if x['solve_kind']=='LP')
            MIPS=sum(float(x['solver_runtime']) for x in ledger if x['solve_kind']!='LP') if ledger else r.get('gurobi_runtime',0.)
            starts=[read(s) for s in (d/'external/native_logs').glob('*.round68.start.json')] if ledger else []
            ind=read(d/'independent_evidence.json');ws=[w for w in ind.get('witnesses',[]) if abs(w['F']-a['U'])<=1e-7 and 'available' in w]
            h=hs.get(a['method']);Hcost=r.get('process_elapsed_at_exact_phase_start_seconds',0.) if h else 0.
            cost=dict(group=g['number'],id=a['id'],seed=a['seed'],method=a['method'],binary_layer='E2',
                H_complete=h['complete'] if h else None,initial_own_U=h['physical']['F'] if h else None,
                initial_fleet_SHA=hashlib.sha256(json.dumps(h['fleet'],sort_keys=True).encode()).hexdigest() if h else None,
                root_rows=len(m['rows']),root_columns=len(m['order']),root_nonzeros=sum(len(x[0]) for x in m['rows']),
                root_cutoff=c['cutoff'] if c else None,root_scope=[c['lower_g'],c['upper_g']] if c else None,
                root_sentinel_rows=sum(1 for t,s,b in m['rows'] if not t and s=='<=' and b==-1),
                actual_native_calls=a['native_Optimize'],root_LP_calls=sum(x['solve_kind']=='LP' and x['leaf_id']=='L0' for x in ledger),
                child_LP_calls=sum(x['solve_kind']=='LP' and x['leaf_id']!='L0' for x in ledger),
                terminal_calls=sum(x['solve_kind']=='MIP' for x in ledger),partial_target_calls=r.get('external_gini_tree_partial_mip_optimize_count',0),
                target_reached_events=r.get('external_gini_tree_partial_mip_target_reached_count',0),split_count=r.get('external_gini_tree_split_count',0),
                LP_native_seconds=LPS,MIP_native_seconds=MIPS,native_nodes=sum(float(x['nodes']) for x in ledger) if ledger else r.get('gurobi_node_count'),
                H_plus_admission_seconds=Hcost,Start_precheck_submission_seconds=sum(s['mapping_validation_submission_seconds'] for s in starts),
                actual_submitted_Starts=sum(bool(s['submitted']) for s in starts),
                other_production_seconds=a['T_produce']-Hcost-LPS-MIPS,T_produce=a['T_produce'],T_verify=a['T_verify'],T_total=a['T_total'],
                certificate=a['certificate'],T_cert=a['T_cert'],native_statuses=[x['native_status'] for x in ledger] if ledger else [r.get('gurobi_status')],
                support_pair_rows=families['cover_2']+families['conditional_2'],support_triple_rows=families['cover_3']+families['conditional_3'],
                ordered_supply_rows=families['ordered_supply'],
                final_own_U_first_logged_available=min(w['available'] for w in ws) if ws else None,
                witness_time_scope='first retained same-run physical witness matching final U; logged availability, not exact native discovery',
                remainder_scope='modeling, Start, output, wrapper work and clock differences; nested native Runtime is not certification time')
            costs.append(cost);local_costs[a['method']]=cost
        for left,right in g['pairs']:
            q=pair(g['role']['id'],by.get(left),by.get(right),kind='E2_core' if g['number']<=3 else 'E2_support_seed1',seed=g['seed'])
            q.update(group=g['number'],left=left,right=right);pairs.append(q)
            if [left,right]==['MB','MS2']:support.append(dict(q,MB_T_cert=by['MB']['T_cert'],MS2_T_cert=by['MS2']['T_cert'],
                MS2_saving_seconds=by['MB']['T_cert']-by['MS2']['T_cert'] if by['MB']['T_cert'] is not None and by['MS2']['T_cert'] is not None else None))
        for method in ['MD-R','MS2']:
            if method not in hs:continue
            h0,h1=hs['MB'],hs[method];c0,c1=calls['MB'],calls[method]
            sameH=h0['complete'] and h1['complete'] and h0['fleet']==h1['fleet'] and h0['semantic_traces']==h1['semantic_traces']
            sameScope=all(c0[k]==c1[k] for k in ['lower_g','upper_g','cutoff'])
            record=dict(group=g['number'],id=g['role']['id'],seed=g['seed'],comparison='MB/'+method,
                complete_H_actions_fleet_equal=bool(sameH),initial_root_scope_U_equal=sameScope,
                MB_sentinel_rows=local_costs['MB']['root_sentinel_rows'],MB_actual_splits=local_costs['MB']['split_count'])
            if sameH and sameScope:
                pa,pb=core.portable(ROOT,c0['model_path']),core.portable(ROOT,c1['model_path'])
                record['actual_root_difference']=root_diff(pa,pb) if method=='MD-R' else compare(pa,pb,'ms2',g['role']['V'],g['role']['M'])
                record['component_interpretation_eligible']=method=='MS2' or record['MB_sentinel_rows']==0
            else:record['component_interpretation_eligible']=False
            record['interpretation']='exposed preprobe/target/scheduling package, with no observed multi-leaf split' if method=='MD-R' and not local_costs['MB']['split_count'] else 'only actual declared triple-support deletion' if method=='MS2' else 'actual exposed outer control'
            differences.append(record)
    assert len(arms)==16 and len(pairs)==17 and len({a['input_SHA'] for a in arms})==3
    for name,rr in [('arms',arms),('pairs',pairs),('mechanism_costs',costs),('support_two_seeds',support)]:core.table(OUT/(name+'.csv'),rr)
    write(OUT/'actual_method_differences.json',dict(records=differences,extra_Optimize=0,source='actual own-H initial root for every formal group'))
    summary=dict(execution='COMPLETE' if all(qualified(a) for a in arms) else 'PARTIAL',actual_formal_arms=16,typed_pairs=17,distinct_inputs=3,
        same_build_E2_PE_SHA=read(OUT/'E2_frozen.json')['PE_SHA'],
        comparisons={f'{a}/{b}':statistics_pairs([p for p in pairs if p['left']==a and p['right']==b]) for a,b in manifest['groups'][0]['pairs']},
        all_observed_arms_qualified=all(qualified(a) for a in arms),
        unique_problem_count_not_increased_by_Seed_repeats=True,
        support_comparisons=5,core_comparisons=15,support_additional_Seed_comparisons=2,
        fees=budget(),R127_unchanged_partial_MD_unstarted=3)
    write(OUT/'stratified_summary.json',summary)
    print(json.dumps(summary))

if __name__=='__main__':analyze()
