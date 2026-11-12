"""Fixed historical citations and master-table novelty reconciliation; no Optimize."""
from round163_common import *
from round163_preflight import table_read,TABLES

SOURCES={
 'physical_correspondence':['results/unified_exact_round137/paper_body.md','results/unified_exact_round137/model_and_algorithm_appendices.md'],
 'inventory_vs_service':['results/unified_exact_round133/joint_objective_gap_note.md'],
 'local_products_and_complete_cost':['results/unified_exact_round138/final_report.md','results/unified_exact_round140/final_report.md',
   'results/unified_exact_round143/mathematical_analysis.md','results/unified_exact_round145/final_report.md'],
 'GD_and_propagation':['results/unified_exact_round147/final_report.md','results/unified_exact_round150/final_report.md','results/unified_exact_round151/final_report.md'],
 'inventory_hull_and_proof_placement':['results/unified_exact_round152/final_report.md','results/unified_exact_round154/mathematical_analysis.md',
   'results/unified_exact_round154/final_report.md','results/unified_exact_round155/final_report.md','results/unified_exact_round156/mathematical_analysis.md','results/unified_exact_round156/final_report.md'],
 'integer_resources_and_physics':[f'results/unified_exact_round{n}/final_report.md' for n in range(157,161)],
 'complete_continuous_carrier':['docs/round161_native_rn.md','results/unified_exact_round161/final_report.md',
   'docs/round162_physical_completion.md','results/unified_exact_round162/final_report.md','results/unified_exact_round162/reports/complete.csv']}

def citations():
    rows={}
    for group,names in SOURCES.items():
        rows[group]=[]
        for n in names:
            commit='fb087d7d9a3eef5bbff250487639d89b6e794739' if 'round162' in n else BASE
            raw=git('show',commit+':'+n)
            rows[group].append(dict(commit=commit,path=n,SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),
                url=f'https://github.com/yifanXovo/TailoredExact/blob/{commit}/{n}',
                identity='exact pinned Git bytes; historical measured runs keep the identities inside their records'))
    write(OUT/'historical_source_map.json',dict(UTC=utc(),groups=rows,no_old_producer_or_raw_replay=True,
        source_of_new_synthesis='existing proofs/finite experiments and supplied R163 question; no new general theorem claimed'))
    print(json.dumps(dict(groups=len(rows),fixed_sources=sum(map(len,rows.values())))))

def master_novelty():
    h=read(OUT/'history_input_index.json');by={}
    for key,values in h['normalized_base_keys'].items():
        for v in values:
            if v['id']:by.setdefault(v['id'],{})[key]=v
    _,enc,rows=table_read(TABLES[0]);facts=[];new=read(OUT/'input_manifest.json')['roles']
    extra=json.loads(git('show',BASE+':results/unified_exact_round135/C_matrix_frozen.json'))
    extra={g['launch']['id']:g['launch']['panel'] for g in extra['groups']}
    for i,row in enumerate(rows,2):
        name=row['实例'];keys=by.get(name)
        if keys:
            assert all(p['normalized_base_key'] not in keys for p in new)
            facts.append(dict(csv_row=i,id=name,normalized_base_keys=sorted(keys),collision=False,
                inputs=sorted({r['input'] for r in keys.values()})))
        else:
            p=extra[name]
            # n/M/Q belongs to the required base key. This old synthetic role
            # differs from all six before any station-level comparison.
            assert all((p['V'],p['M'],sorted(p['Q_vector']))!=(q['V'],q['M'],sorted(q['Q_vector'])) for q in new)
            facts.append(dict(csv_row=i,id=name,input=p['input_path'],input_SHA256=p['input_sha256'],collision=False,
                static_separation_by_required_n_M_Q=True,old_n=p['V'],old_M=p['M'],old_Q=p['Q_vector']))
    write(OUT/'main_table_novelty.json',dict(PASS=True,UTC=utc(),primary_table_SHA256=sha(TABLES[0]),encoding=enc,
        historical_rows=len(rows),all_rows_accounted_for=True,facts=facts,
        base_input_collision=False,full_configuration_collision=False,
        reason='each old base differs, which also rules out identical full configuration; no T/lambda-only renaming',Optimize=0))
    # Strengthen the original raw-serialized key with the actual inherited
    # Parser.cpp legacy convention. This is a post-panel static readback,
    # not a changed generation rule or a reason to draw another input.
    from round163_setup import canonical
    import generate_citibike443_regional_v1 as parser
    def effective(parsed):
        p=dict(parsed);w=list(p['weights']);scale=abs(max(w[1:])-10.)<=1e-6
        if scale:w[1:]=[v/10. for v in w[1:]]
        p['weights']=[0. if v==0 else v for v in w]
        p['points']=[[0. if v==0 else v for v in pair] for pair in p['points']]
        return p,scale
    new_keys={}
    for q in new:
        parsed,scaled=effective(read(ROOT/q['input_path'].replace('instance.txt','parsed.json')))
        assert not scaled
        base,full=canonical(parsed,q);new_keys[q['id']]=dict(base=base,full=full)
    assert len({v['base'] for v in new_keys.values()})==6 and len({v['full'] for v in new_keys.values()})==6
    effective_old=[]
    paths=sorted({v['input'] for values in h['normalized_base_keys'].values() for v in values})
    for name in paths:
        raw=git('show',BASE+':'+name);local=TEMP/'novelty_inputs'/hashlib.sha256(raw).hexdigest()
        assert local.read_bytes()==raw
        parsed,scaled=effective(parser.parse_instance_mirror(local))
        base,_=canonical(parsed)
        assert all(base!=value['base'] for value in new_keys.values()),('effective parser base collision',name)
        effective_old.append(dict(input=name,input_SHA256=hashlib.sha256(raw).hexdigest(),base_key=base,
            legacy_max10_weight_downgrade=scaled))
    write(OUT/'effective_input_novelty.json',dict(PASS=True,UTC=utc(),old_inputs=len(effective_old),
        new_keys=new_keys,old=effective_old,zero_sign_canonicalized=True,
        weight_policy='actual Parser.cpp downgradeLegacyWeights: station max within 1e-6 of 10 divided by 10; no depot weight in key',
        no_base_or_full_collision=True,full_collision_excluded_by_distinct_base=True,
        audit_timing='post-panel static strengthening of pre-panel raw serialized key; no regeneration or production change',Optimize=0))
    # R57 retained metadata for six ephemeral structural pilots, not full
    # algorithm measurements. Their n/M/Q already separates all new inputs.
    import csv
    with (ROOT/'results/data_generation_citibike_round57/structural_pilot_manifest.csv').open(encoding='utf-8-sig',newline='') as f:pilots=list(csv.DictReader(f))
    pilot_facts=[];overlap=[]
    for p in pilots:
        old=(int(p['V']),int(p['M']),[int(p['Q'])]*int(p['M']))
        assert all(old!=(q['V'],q['M'],q['Q_vector']) for q in new)
        pilot_facts.append(dict(id=p['pilot_id'],n=old[0],M=old[1],Q=old[2],file_retained=p['pilot_file_retained'],
            mathematical_base_separated_by_n_M_Q=True))
        used=set(map(int,p['source_station_row_indices'].split(';')))
        for q in new:
            if q['source']=='CITI':
                chosen=set(read(ROOT/q['selection_path'])['selected_source_station_row_indices']);common=sorted(used&chosen)
                overlap.append(dict(id=q['id'],old_id=p['pilot_id'],source='CITI',overlap_rows=common,
                    overlap_count=len(common),fraction_of_new=len(common)/q['V'],old_evidence='R57 ephemeral zero-solve structural pilot; not full-method performance'))
    write(OUT/'r57_pilot_overlap.json',dict(PASS=True,pilot_facts=pilot_facts,overlap=overlap,
        source_manifest='results/data_generation_citibike_round57/structural_pilot_manifest.csv',
        source_SHA256=sha(ROOT/'results/data_generation_citibike_round57/structural_pilot_manifest.csv'),
        all_six_new_bases_separated=True,no_old_input_or_raw_reconstruction=True))
    print(json.dumps(dict(PASS=True,master_rows=len(rows),all_six_base_inputs_new=True)))

if __name__=='__main__':globals()[sys.argv[1]]()
