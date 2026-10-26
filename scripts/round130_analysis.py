"""All fixed observations and five typed comparisons; no new native work."""
from round130_common import *
from round127_analysis import qualified,pair as inherited_pair,statistics_pairs,root
from round129_qualify import support_family
from compare_round112_startup import reconstruct as H
import round108_reader as core
import collections,math

def difference(a,b):
    """Post-formal summary: support rows must use a single vehicle.

    The frozen qualification's row-shape-only descriptive counter also counted
    two-vehicle unique-service rows as pair covers. Full model equality was
    unaffected; retain that historical report and disclose the count correction.
    """
    x,y=core.lp_model(a),core.lp_model(b)
    for k in ['objective','order','types','bounds']:assert x[k]==y[k],k
    removed=collections.Counter(x['rows'])-collections.Counter(y['rows'])
    added=collections.Counter(y['rows'])-collections.Counter(x['rows'])
    assert not added and set(removed)<={((),'<=',-1.)}
    families=collections.Counter(support_family(r) for r in y['rows'])
    assert families['cover_3']==families['conditional_3']==0
    return dict(removed_semantic_sentinel_rows=sum(removed.values()),all_other_rows_columns_types_bounds_objective_identical=True,
        pair_cover=families['cover_2'],pair_conditional=families['conditional_2'],ordered_supply=families['ordered_supply'],
        triple_rows=0,other_root_rows_retained=True)

def comparison(id,a,b,seed):
    q=inherited_pair(id,a,b,kind='R130_known_role_attribution',seed=seed)
    q.pop('legacy_materiality',None)
    q.update(materiality=None,material_threshold_seconds=None)
    if q['classification']=='BOTH_CERTIFIED':
        faster=min(a['T_cert'],b['T_cert']);threshold=max(10.,.1*faster)
        dt=a['T_cert']-b['T_cert']
        q.update(material_threshold_seconds=threshold,
            materiality='LEFT_MATERIALLY_FASTER' if -dt>=threshold else 'RIGHT_MATERIALLY_FASTER' if dt>=threshold else 'TIME_CLOSE')
    return q

def phase_value(rows,event,status):
    values=[float(r['process_seconds']) for r in rows if r['event']==event and r['status']==status]
    return values[0] if len(values)==1 else None

def run():
    manifest=read(OUT/'experiment_manifest.json');arms=[];pairs=[];costs=[];diffs=[];H_facts=[];closure=[]
    for number,g in enumerate(manifest['groups'],1):
        camp=OUT/g['name'];i=read(camp/'identity.json');aa=read(camp/'reconstructed.json')['arms']
        assert [a['method'] for a in aa]==g['methods'] and len(aa)==4
        by={a['method']:a for a in aa};models={};calls={};hs={};local={}
        for a,l in zip(aa,i['launches']):
            d=Path(l['destination']);r=read(d/'result.json');p=l['panel'];method=l['method']
            assert a['PE_SHA']==read(OUT/'E3_frozen.json')['PE_SHA'] and a['binary_layer']=='E3'
            assert a['T_cert']==(a['T_produce'] if qualified(a) and a['certificate'] else None)
            a.update(group=number,signed_gap=a['U']-a['L'],absolute_gap=abs(a['U']-a['L']))
            arms.append(a)
            if method!='P':hs[method]=H(ROOT,p,d)
            ledger=core.rows(d/'external/paper_optimize_ledger.csv') if (d/'external/paper_optimize_ledger.csv').exists() else []
            lp=core.rows(d/'external/lp_status_ledger.csv') if ledger else []
            root_lp=next((x for x in lp if x['leaf_id']=='L0'),None)
            if method in ['S2','S2R']:m,c=root(d)
            else:
                m=core.lp_model(d/'compact.lp') if (d/'compact.lp').exists() else None
                c=next((e['payload'] for e in read(d/'observations.json') if e['payload']['kind']=='call'),None)
            models[method]=m;calls[method]=c
            families=collections.Counter(support_family(row) for row in m['rows']) if m else collections.Counter()
            starts=[read(x) for x in (d/'external/native_logs').glob('*.round68.start.json')]
            prelp=[x for x in starts if x.get('source')=='round128_own_U0_pre_lp']
            if (d/'native.log.round112.start.json').exists():starts.append(read(d/'native.log.round112.start.json'))
            phases=core.rows(d/'phases.csv');h_start=phase_value(phases,'hga_start','start')
            h_end=phase_value(phases,'decoded_descent_complete','complete')
            exact=phase_value(phases,'exact_phase_start','start') if method in ['S2','S2R'] else phase_value(phases,'round112_ENS_H','complete') if method=='PS' else None
            mapping_start=phase_value(phases,'round112_compact_start','start');mapping_end=phase_value(phases,'round112_compact_start','complete')
            compact_native_launch=phase_value(phases,'plain_gurobi_optimize_launch','start')
            compact_preparation_begin=phase_value(phases,'round112_ENS_H','complete') if method=='PS' else phase_value(phases,'instance_parsing_complete','complete') if method=='P' else None
            compact_preparation_end=mapping_start if method=='PS' else compact_native_launch if method=='P' else None
            start_subclocks=[x.get('mapping_validation_submission_seconds') for x in starts]
            ind=read(d/'independent_evidence.json');witnesses=[w for w in ind.get('witnesses',[]) if abs(w['F']-a['U'])<=1e-7 and 'available' in w]
            cost=dict(group=number,id=a['id'],seed=a['seed'],method=method,
                H_complete=hs[method]['complete'] if method in hs else None,initial_own_U=hs[method]['physical']['F'] if method in hs else None,
                H_logged_descent_seconds=h_end-h_start if h_start is not None and h_end is not None else None,
                admission_and_H_until_backend_seconds=exact,
                PS_mapping_validation_submission_phase_seconds=mapping_end-mapping_start if mapping_start is not None and mapping_end is not None else None,
                compact_pre_Optimize_logged_process_seconds=compact_native_launch,
                compact_build_read_and_admission_phase_seconds=compact_preparation_end-compact_preparation_begin if compact_preparation_begin is not None and compact_preparation_end is not None else None,
                compact_preparation_phase_scope='logged aggregate before Start/Optimize; includes original model build/read/export and admission; no separately logged pure model-build subclock' if method in ['P','PS'] else None,
                root_scope=[c['lower_g'],c['upper_g']] if c else None,root_cutoff=c.get('cutoff') if c else None,
                root_rows=len(m['rows']) if m else None,root_columns=len(m['order']) if m else None,
                root_nonzeros=sum(len(t) for t,s,b in m['rows']) if m else None,
                root_sentinel_rows=sum(not t and s=='<=' and b==-1 for t,s,b in m['rows']) if m else None,
                support_pair_rows=families['cover_2']+families['conditional_2'],support_triple_rows=families['cover_3']+families['conditional_3'],
                ordered_supply_rows=families['ordered_supply'],actual_native_calls=a['native_Optimize'],
                solve_kinds=dict(collections.Counter(x['solve_kind'] for x in ledger)) if ledger else {'complete_original_compact_milp':a['native_Optimize']},
                root_LP_calls=sum(x['solve_kind']=='LP' and x['leaf_id']=='L0' for x in ledger),
                child_LP_calls=sum(x['solve_kind']=='LP' and x['leaf_id']!='L0' for x in ledger),
                terminal_MIP_calls=sum(x['solve_kind']=='MIP' for x in ledger),
                root_LP_bound=float(root_lp['lower_bound']) if root_lp and root_lp['bound_available']=='1' else None,
                LP_native_seconds=sum(float(x['solver_runtime']) for x in ledger if x['solve_kind']=='LP'),
                MIP_native_seconds=sum(float(x['solver_runtime']) for x in ledger if x['solve_kind']!='LP') if ledger else r.get('gurobi_runtime'),
                LP_native_work=sum(float(x['work']) for x in ledger if x['solve_kind']=='LP'),
                MIP_native_work=sum(float(x['work']) for x in ledger if x['solve_kind']!='LP') if ledger else r.get('gurobi_work'),
                native_nodes=sum(float(x['nodes']) for x in ledger) if ledger else r.get('gurobi_node_count'),
                model_generation_seconds=r.get('external_gini_tree_model_build_seconds') if ledger else r.get('gurobi_model_build_seconds'),
                native_model_read_seconds=r.get('external_gini_tree_model_read_seconds') if ledger else r.get('gurobi_model_read_seconds'),
                Start_check_submission_seconds=sum(start_subclocks) if all(x is not None for x in start_subclocks) else None,
                actual_submitted_Starts=sum(bool(x['submitted']) for x in starts),pre_LP_Start_audit_receipts=len(prelp),
                split_count=r.get('external_gini_tree_split_count',0),target_reached_events=r.get('external_gini_tree_partial_mip_target_reached_count',0),
                partial_target_calls=r.get('external_gini_tree_partial_mip_optimize_count',0),
                native_statuses=[x['native_status'] for x in ledger] if ledger else [r.get('gurobi_status_text')],
                final_own_U_first_logged_available=min(w['available'] for w in witnesses) if witnesses else None,
                final_U_witness_match_tolerance=1e-7,
                witness_time_scope='first retained own physical witness matching final U within the declared 1e-7 comparison; logged availability, not an inferred exact native discovery time',
                native_Start_incumbent_adoption=read(d/'native.log.round112.native.json') if method=='PS' and (d/'native.log.round112.native.json').exists() else None,
                T_produce=a['T_produce'],T_verify=a['T_verify'],T_total=a['T_total'],T_cert=a['T_cert'],certificate=a['certificate'])
            if method in ['S2','S2R'] and m is not None:assert cost['support_triple_rows']==0
            if method=='S2R' and hs[method]['physical']['F']>1e-7:
                assert [x['solve_kind'] for x in ledger]==['LP','MIP'] and all(x['leaf_id']=='L0' for x in ledger)
                assert cost['split_count']==cost['partial_target_calls']==0 and cost['actual_submitted_Starts']==1
            costs.append(cost);local[method]=cost
            seen=set()
            for event in read(d/'observations.json'):
                q=event['payload']
                if q['kind']!='call' or q['model_sha256'] in seen or q['full_original']:continue
                seen.add(q['model_sha256']);cm=core.lp_model(core.portable(ROOT,q['model_path']))
                sentinel=sum(not t and s=='<=' and b==-1 for t,s,b in cm['rows'])
                penalties=[rhs for terms,sense,rhs in cm['rows'] if sense=='>=' and len(terms)==p['V'] and all(n.startswith('e_') for n,v in terms)]
                La=q['lower_g']+.15*max(penalties) if penalties else None
                closure.append(dict(group=number,id=l['id'],seed=l['seed'],method=method,leaf=q['leaf'],model_SHA=q['model_sha256'],
                    scope=[q['lower_g'],q['upper_g']],cutoff=q['cutoff'],sentinel_rows=sentinel,
                    analytic_region_lower=La,analytic_minus_cutoff=La-q['cutoff'] if La is not None else None,
                    interpretation='semantic improving-domain proof closure; not inclusive physical infeasibility' if sentinel else 'no semantic pseudo-infeasibility row'))
        for left,right in g['pairs']:
            pairs.append(dict(comparison(g['role']['id'],by[left],by[right],g['seed']),group=number))
        ps=hs['PS']
        for method in ['S2','S2R']:
            h=hs[method];same=ps['complete'] and h['complete'] and ps['fleet']==h['fleet'] and ps['semantic_traces']==h['semantic_traces'] and ps['physical']['Y']==h['physical']['Y']
            H_facts.append(dict(group=number,id=g['role']['id'],seed=g['seed'],left=method,right='PS',same_complete_H=bool(same),
                left_H_complete=h['complete'],PS_H_complete=ps['complete'],capacity_assigned_fleet_equal=ps['fleet']==h['fleet'],
                full_semantic_actions_equal=ps['semantic_traces']==h['semantic_traces'],initial_inventory_equal=ps['physical']['Y']==h['physical']['Y'],
                initial_U_values=[h['physical']['F'],ps['physical']['F']],backend_exposed=by[method]['native_Optimize']>0 and by['PS']['native_Optimize']>0))
        compact_equal=models['P'] is not None and models['PS'] is not None and models['P']==models['PS']
        if models['PS'] is not None:assert compact_equal
        cp,cps=calls['P'],calls['PS'];compact_parameters_equal=cp is not None and cps is not None and cp['settings']==cps['settings']
        h0,h1=hs['S2'],hs['S2R'];c0,c1=calls['S2'],calls['S2R']
        sameH=h0['complete'] and h1['complete'] and h0['fleet']==h1['fleet'] and h0['semantic_traces']==h1['semantic_traces'] and h0['physical']['Y']==h1['physical']['Y']
        same_scope=c0 is not None and c1 is not None and all(c0[k]==c1[k] for k in ['lower_g','upper_g','cutoff'])
        same_parameters=c0 is not None and c1 is not None and c0['settings']==c1['settings']
        delta=difference(core.portable(ROOT,c0['model_path']),core.portable(ROOT,c1['model_path'])) if same_scope else None
        pure=bool(sameH and same_scope and same_parameters and delta and not local['S2']['root_sentinel_rows'])
        diffs.append(dict(group=number,id=g['role']['id'],seed=g['seed'],P_PS_complete_original_compact_equal=bool(compact_equal),
            P_PS_fixed_native_parameters_equal=bool(compact_parameters_equal),P_PS_native_TimeLimit='same full deadline policy; own already-paid preparation deducted',
            S2_S2R_complete_H_equal=bool(sameH),S2_S2R_scope_cutoff_equal=bool(same_scope),S2_S2R_root_settings_equal=bool(same_parameters),
            actual_root_difference=delta,pure_outer_package_attribution_eligible=pure,S2_splits=local['S2']['split_count'],S2R_splits=local['S2R']['split_count'],
            attribution_scope='entire exposed probing/targets/domain-dependent strengthening/scheduling/split package' if pure else 'complete-method result; unmatched H/root or semantic preprocessing difference disclosed'))
    assert len(arms)==24 and len(pairs)==30 and len({a['input_SHA'] for a in arms})==3
    consistency=[]
    for id in [p['id'] for p in read(OUT/'input_manifest.json')['roles']]:
        rows=[a for a in arms if a['id']==id and qualified(a)]
        assert len({a['input_SHA'] for a in rows})<=1
        best=min((a['U'] for a in rows),default=None)
        violations=[dict(method=a['method'],seed=a['seed'],own_L=a['L'],other_verified_U=best)
                    for a in rows if a['L']>best+1e-7]
        consistency.append(dict(id=id,qualified_own_observations=len(rows),
            minimum_verified_physical_U_for_contradiction_only=best,violations=violations,
            own_U_values_or_bounds_or_certificates_transferred=False))
    write(OUT/'cross_arm_bound_consistency.json',dict(status='PASS' if not any(x['violations'] for x in consistency) else 'PROOF_CONTRADICTION_REQUIRES_DECISION',
        records=consistency,comparison_tolerance=1e-7,scope='Same-input physical witnesses can revoke a contradictory global bound only; no arm is given another arm\'s U, solution or certificate',Optimize=0))
    assert not any(x['violations'] for x in consistency),consistency
    for n,rows in [('arms',arms),('pairs',pairs),('mechanism_costs',costs),('same_H',H_facts),('closure_sources',closure)]:core.table(OUT/(n+'.csv'),rows)
    write(OUT/'actual_method_differences.json',dict(records=diffs,Optimize=0,all_actual_initial_roots_checked=True))
    write(OUT/'observations.json',dict(arms=arms,pairs=pairs,costs=costs,same_H=H_facts,differences=diffs,closure_sources=closure))
    summary=dict(execution='COMPLETE' if all(qualified(a) for a in arms) and all(q['classification']!='UNEVALUABLE' for q in pairs) else 'PARTIAL',
        actual_formal_arms=24,typed_shared_comparisons=30,distinct_inputs=3,Seed_repeats_are_not_new_problems=True,
        by_comparison={f'{a}/{b}':statistics_pairs([q for q in pairs if q['left']==a and q['right']==b]) for a,b in manifest['pairs']},
        all_actual_same_H=all(x['same_complete_H'] for x in H_facts),all_actual_same_effective_root=all(x['pure_outer_package_attribution_eligible'] for x in diffs),
        no_extra_Optimize=True,no_open_time_imputation=True,no_best_Seed=True)
    write(OUT/'stratified_summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':run()
