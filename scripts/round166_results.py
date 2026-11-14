"""Read sealed Round166 arms; no producer/native imports or optimization calls."""
from round166_common import *
import argparse,csv,re
from collections import Counter

def rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def csvout(path,values):
    assert values
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(values[0]));writer.writeheader();writer.writerows(values)

def size(log):
    text=Path(log).read_text(encoding='utf-8',errors='strict')
    m=re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',text)
    assert m,log
    return dict(rows=int(m[1]),columns=int(m[2]),nonzeros=int(m[3]))

def mip_root(log):
    text=Path(log).read_text(encoding='utf-8')
    p=re.search(r'Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros',text)
    r=re.search(r'Root relaxation: objective ([-+\deE.]+), ([\d,]+) iterations, ([\d.]+) seconds',text)
    return dict(log=bind(Path(log)),original_model=size(log),
        presolved_model=dict(rows=int(p[1]),columns=int(p[2]),nonzeros=int(p[3])) if p else None,
        root_relaxation=dict(objective=float(r[1]),iterations=int(r[2].replace(',','')),seconds=float(r[3])) if r else None,
        precision='Values transcribed from the printed Native log, not full-precision qualified endpoint sources.',
        absent_root_detail_reason=None if r else 'Native log has no separate root-relaxation line; retained without inference.')

def collect(partial=False):
    tick=time.perf_counter();matrix=read(OUT/'matrix_frozen.json');arms=[];metrics=[];calls=[];fees=[]
    for group in matrix['groups']:
        launch=group['launch'];d=Path(launch['destination']);p=launch['panel']
        fee=OUT/'fees'/f'{group["position"]:03}.json'
        if fee.exists():fees.append(read(fee))
        endpoint=d/'round166_endpoint.json'
        if not endpoint.exists():
            assert partial,('formal position has no qualified endpoint',group['position'])
            arms.append(dict(position=group['position'],id=group['input_id'],method=group['method'],
                state='RUNNING' if fee.exists() else 'NOT_STARTED',endpoint=None))
            continue
        arm=read(endpoint)
        assert arm['method']==group['method'] and arm['id']==group['input_id']
        assert arm['seed']==0 and arm['H_complete'] and arm['formal_protocol_qualified']
        assert arm['implementation_qualified'] and arm['numbers_qualified'] and arm['evidence_complete']
        assert arm['source_build']==matrix['source_commit'] and arm['PE_SHA']==matrix['PE_SHA']
        assert arm['DLL_SHA']==matrix['DLL_SHA'] and arm['input_SHA']==p['input_sha256']
        assert arm['performance_eligible'] and arm['performance_evidence_eligible']
        assert (arm['T_cert'] is not None)==bool(arm['certificate'])
        assert arm['T_produce']<=p['cap_seconds']
        a=read(d/'audit.json');r=read(d/'result.json');ledger=rows(d/'external/paper_optimize_ledger.csv')
        assert a['passed'] and a['raw_bytes_unchanged']
        assert len(ledger)==arm['native_Optimize']==arm['declared_calls']==arm['returned_calls']
        assert all(c['optimize_return_code']=='0' for c in ledger)
        assert all(c['integer_domain_restored']=='1' for c in ledger if c['solve_kind']=='LP')
        for i,call in enumerate(ledger,1):calls.append(dict(position=group['position'],id=arm['id'],method=arm['method'],call=i,**call))
        native=[dict(kind=kind,calls=sum(c['solve_kind']==kind for c in ledger),
            runtime=sum(float(c['solver_runtime']) for c in ledger if c['solve_kind']==kind),
            work=sum(float(c['work']) for c in ledger if c['solve_kind']==kind),
            nodes=sum(float(c['nodes']) for c in ledger if c['solve_kind']==kind))
            for kind in sorted({c['solve_kind'] for c in ledger})]
        first=size(ledger[0]['native_log']);first_contract=a['model_contracts'][0]['model']
        assert first['rows']==first_contract['rows'] and first['columns']==first_contract['columns']
        lp=rows(d/'external/lp_status_ledger.csv')[0]
        am=rows(d/'external/adaptive_mass_decision_ledger.csv')
        first_mip=next((c for c in ledger if c['solve_kind']!='LP'),None)
        metric=dict(position=group['position'],id=arm['id'],method=arm['method'],state=arm['state'],
            T_produce=arm['T_produce'],T_verify=arm['T_verify'],T_total=arm['T_total'],
            H_seconds=r['hga_wall_time_seconds'],
            writer_build_seconds=r['external_gini_tree_model_build_seconds'],
            native_model_read_seconds=r['external_gini_tree_model_read_seconds'],
            native_runtime=sum(float(c['solver_runtime']) for c in ledger),
            native_work=sum(float(c['work']) for c in ledger),native_nodes=sum(float(c['nodes']) for c in ledger),
            native_calls=len(ledger),first_raw_model=first,
            first_LP_lower=float(lp['lower_bound']),first_LP_work=float(lp['work']),
            first_MIP=mip_root(first_mip['native_log']) if first_mip else None,
            AM_action_sequence=[c['selected_action'] for c in am],
            AM_action_counts=dict(Counter(c['selected_action'] for c in am)),
            native_by_kind=native,models_checked=len(a['model_contracts']),Starts_checked=len(a['Start_checks']),
            max_Start_residual=max((c['maximum_absolute_residual'] for c in a['Start_checks']),default=0),
            endpoint=bind(endpoint),audit=bind(d/'audit.json'),result=bind(d/'result.json'),ledger=bind(d/'external/paper_optimize_ledger.csv'))
        metrics.append(metric)
        arms.append(dict(position=group['position'],**arm,endpoint=bind(endpoint)))
    done=[a for a in arms if a['endpoint'] is not None];pairs=[]
    for id in dict.fromkeys(g['input_id'] for g in matrix['groups']):
        available={a['method']:a for a in done if a['id']==id}
        if len(available)!=2:continue
        b,c=available['B'],available['C166'];joint=b['certificate'] and c['certificate']
        assert b['input_SHA']==c['input_SHA'] and b['H_semantic_SHA']==c['H_semantic_SHA'] and b['H_fleet_SHA']==c['H_fleet_SHA']
        faster=min(b['T_cert'],c['T_cert']) if joint else None
        threshold=max(10,.1*faster) if joint else None
        difference=c['T_cert']-b['T_cert'] if joint else None
        substantive=abs(difference)>=threshold if joint else None
        pairs.append(dict(id=id,B_state=b['state'],C166_state=c['state'],B_U=b['U'],C166_U=c['U'],
            delta_U_C166_minus_B=c['U']-b['U'],B_L=b['L'],C166_L=c['L'],delta_L_C166_minus_B=c['L']-b['L'],
            B_T_cert=b['T_cert'],C166_T_cert=c['T_cert'],C166_over_B_T_cert=c['T_cert']/b['T_cert'] if joint else None,
            joint_CERT=joint,T_cert_difference_C166_minus_B=difference,substantive_threshold_seconds=threshold,
            substantive_difference=substantive,
            certificate_time_winner=('C166' if difference<0 else 'B') if substantive else None,
            same_own_H_semantics_and_fleet=True,
            B_T_produce=b['T_produce'],C166_T_produce=c['T_produce'],B_T_verify=b['T_verify'],C166_T_verify=c['T_verify']))
    summary=dict(UTC=utc(),complete=len(done)==12,positions=12,executed_and_qualified=len(done),paired_inputs=len(pairs),
        CERT={method:sum(a['certificate'] for a in done if a['method']==method) for method in ['B','C166']},
        OPEN={method:sum(not a['certificate'] for a in done if a['method']==method) for method in ['B','C166']},
        joint_CERT_pairs=sum(p['joint_CERT'] for p in pairs),
        substantive_certificate_time_wins={method:sum(p['certificate_time_winner']==method for p in pairs) for method in ['B','C166']},
        method_produce_seconds={method:sum(a['T_produce'] for a in done if a['method']==method) for method in ['B','C166']},
        method_verify_seconds={method:sum(a['T_verify'] for a in done if a['method']==method) for method in ['B','C166']},
        total_native_Optimize=sum(a['native_Optimize'] for a in done),
        formal_nominal_caps=21600,formal_reservation=25200,
        actual_wrapper_outer_seconds=sum(f['seconds'] for f in fees if f['status']=='COMPLETE'),
        actual_produce_plus_verify=sum(a['T_total'] for a in done),
        new_independent_physical_inputs=0,new_Seed_values=0,new_strict_B_P_pairs=0,
        exposed=True,Seed=0,replications_per_input_method=1,
        source_commit=matrix['source_commit'],PE_SHA=matrix['PE_SHA'],DLL_SHA=matrix['DLL_SHA'],
        matrix=bind(OUT/'matrix_frozen.json'),analysis_Optimize=0,
        timing_policy='T_produce includes own H/import/models/native/online qualification/close; T_verify is necessary post-production verification. Native/H counters are nested explanatory costs, not additive fees.',
        schema_note='Legacy raw arm=M-B and method=S2 are service/schema fields. R166_method and qualified endpoint method identify B versus C166. Legacy formal_performance=false is superseded by the explicit qualified protocol/performance eligibility fields, all checked here.')
    folder=OUT/'reports';folder.mkdir(exist_ok=True)
    write(folder/'complete_arms.json',arms);write(folder/'pairs.json',pairs);write(folder/'runtime_metrics.json',metrics)
    write(folder/'summary.json',summary)
    if done:
        csvout(folder/'complete_arms.csv',[{k:a[k] for k in ['position','id','method','state','U','L','signed_gap','relative_gap','T_cert','T_produce','T_verify','T_total','native_Optimize','input_SHA','source_commit','PE_SHA','DLL_SHA']} for a in done])
        csvout(folder/'native_calls.csv',calls)
    if pairs:csvout(folder/'pairs.csv',pairs)
    lp=read(OUT/'qualification/LP_pairs.json');size_rows=[]
    for q in lp:
        b,c=q['B'],q['C166'];size_rows.append(dict(id=q['id'],B_LP=b['objective'],C166_LP=c['objective'],signed_LP_delta=q['signed_LP_delta'],
            **{method+'_'+key:q[method][key] for method in ['B','C166'] for key in ['rows','columns','nonzeros','binaries','integers','build_seconds','runtime','outer_seconds']},
            **{'delta_'+key:c[key]-b[key] for key in ['rows','columns','nonzeros','binaries','build_seconds']}))
    csvout(folder/'qualified_LP_sizes.csv',size_rows)
    write(folder/'aggregation_receipt.json',dict(UTC=utc(),seconds=time.perf_counter()-tick,Optimize=0,
        complete=summary['complete'],reader=bind(Path(__file__)),outputs=[bind(folder/n) for n in ['complete_arms.json','pairs.json','runtime_metrics.json','summary.json','qualified_LP_sizes.csv']]))
    print(json.dumps(summary,ensure_ascii=True,indent=2))
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--partial',action='store_true');args=parser.parse_args();collect(args.partial)
