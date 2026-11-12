"""Preproduction reconciliation; no solver or old producer is executed."""
from round163_common import *
import csv, io, shutil
from round163_setup import canonical

TABLES=[Path('C:/Users/Administrator/Desktop/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'),
        Path('C:/Users/Administrator/Desktop/Research/docs/tempfiles/GI_TBC_vs_P_GRB_All_Tested_Instances.csv')]

def table_read(path):
    raw=path.read_bytes()
    for enc in ['utf-8-sig','utf-16','gb18030']:
        try:
            text=raw.decode(enc)
            rows=list(csv.DictReader(io.StringIO(text,newline='')))
            if rows and '实例' in rows[0]:return raw,enc,rows
        except (UnicodeError,csv.Error):pass
    raise ValueError(('unrecognized table encoding',path))

def run():
    # Charge a conservative enclosing preparation interval for the initial
    # unmetered metadata/history I/O. It includes ordinary time; it is not
    # misreported as exact Optimize cost or added nested solver Runtime.
    external=OUT/'infra/external_costs.json'
    if not external.exists():
        start=float(git('show','-s','--format=%ct','9d8836101').decode().strip())
        end=(OUT/'history_input_index.json').stat().st_mtime
        write(external,dict(processes=[dict(label='initial_history_preparation_enclosing_wall',kind='qualification',outer_seconds=max(0,end-start),
            measurement='file close wall time minus preceding recipe-commit wall second; conservative enclosing preparation interval, not per-process precision',
            pure_metadata_and_static_input_reads=True,Optimize=0,failed_premature_generate_seconds=.3578002)],
            conservative_charge_includes_ordinary_preparation=True))
    h=read(OUT/'history_input_index.json');names={r['input'] for values in h['normalized_base_keys'].values() for r in values}
    digest_to_input={}
    for name in names:
        raw=git('show',BASE+':'+name)
        digest_to_input[hashlib.sha256(raw).hexdigest()]=name
    small=read(ROOT/'results/unified_exact_round162/small_input_manifest.json')
    def walk(x):
        if isinstance(x,dict):
            yield x
            for q in x.values():yield from walk(q)
        elif isinstance(x,list):
            for q in x:yield from walk(q)
    aliases=[]
    unresolved={r['path'] for r in h['unresolved']}
    for p in walk(small):
        if p.get('input_path') in unresolved:
            assert p['input_sha256'] in digest_to_input
            aliases.append(dict(missing_raw_alias=p['input_path'],same_input_SHA256=p['input_sha256'],
                resolved_input=digest_to_input[p['input_sha256']],no_old_raw_recovery=True))
    assert {r['missing_raw_alias'] for r in aliases}==unresolved
    write(OUT/'novelty_alias_resolution.json',dict(PASS=True,aliases=aliases,all_unresolved_manifest_inputs_accounted_for=True))
    snapshots=[]
    for i,path in enumerate(TABLES):
        raw,enc,rows=table_read(path)
        snapshot=TEMP/f'main_table_before_{i}.csv';snapshot.write_bytes(raw)
        snapshots.append(dict(path=str(path),SHA256=sha(path),bytes=len(raw),encoding=enc,columns=list(rows[0]),rows=len(rows),
            local_backup=str(snapshot),last_instance=rows[-1]['实例'],last_data_round=rows[-1].get('数据轮次'),
            status_labels=sorted(set(r['GI_TBC_状态'] for r in rows)),classification_labels=sorted(set(r['对比结果'] for r in rows))))
        for p in read(OUT/'input_manifest.json')['roles']:
            assert all(r['实例']!=p['id'] for r in rows),('already registered prospective ID',p['id'])
    write(OUT/'main_table_discovery.json',dict(UTC=utc(),tables=snapshots,primary_path=str(TABLES[0]),
        replicas_equal=snapshots[0]['SHA256']==snapshots[1]['SHA256'],preserve_existing_bytes_and_encoding=True,
        classification_policy='Do not infer unconfirmed Win/Lose thresholds; leave new classification blank and state certificate/U/L facts',
        prospective_ids_absent=True))
    from round163_campaign import tokens,command
    m=read(OUT/'matrix_frozen.json');facts=[]
    for g in m['groups']:
        l=g['launch'];c=tokens(l['command']);method=l['R163_method'];p=l['panel']
        assert sha(ROOT/p['input_path'])==p['input_sha256'] and sha(l['command'][0])==PE_SHA
        assert float(c['--lambda'])==p['lambda'] and float(c['--T'])==p['T_seconds']
        assert c['--threads']==c['--mip-threads']=='1' and c['--gurobi-seed']=='0'
        assert '--round112-ens-start-compact' not in c and '--round138-stock-rlt' not in c
        assert l['command']==command(p,method,Path(l['destination']))
        assert not Path(l['destination']).exists()
        assert sha(OUT/g['group']/'identity.json')==g['identity_SHA256']
        facts.append(dict(position=g['position'],id=p['id'],method=method,cap=l['cap_seconds'],lambda_decimal=c['--lambda'],
            own_input=True,independent_lifecycle=True,Native_NodeLimit_unlimited=True))
    assert len(facts)==18 and sum(f['cap'] for f in facts)==32400
    smoke=read(OUT/'qualification/smoke_result.json');assert smoke['PASS']
    write(OUT/'pre_panel_admission.json',dict(PASS=True,UTC=utc(),matrix_SHA256=sha(OUT/'matrix_frozen.json'),facts=facts,
        fixture_smoke_SHA256=sha(OUT/'qualification/smoke_result.json'),PE_SHA256=sha(PE),DLL_SHA256=sha(DLL),
        external_preparation_cost_disclosed=True,preserved_workspace=check_protected(),
        no_result_aware_redraw_or_ranking=True,no_adverse_stop=True,all_six_triplets_required=True,
        independent_person_review=False,qualification='single implementing agent risk-focused qualification; final independent agents still required'))
    print(json.dumps(dict(PASS=True,positions=18,main_tables=snapshots,scientific_budget=budget()),ensure_ascii=False))

if __name__=='__main__':run()
