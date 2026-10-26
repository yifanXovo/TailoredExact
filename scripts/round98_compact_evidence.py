"""After all runs exit: compact original evidence and physical routes, zero Optimize.

This is an executor-side extraction, not an independent solver reproduction.
Original receipts, failed audits and journal bytes remain untouched.
"""
import csv
import json
import sys
from round98_common import *
import analyze_round61 as physical

def run(label):
    target=OUT/label;target.mkdir(exist_ok=False)
    physical.ROOT=ROOT
    witnesses=[];artifacts={};cost_receipts=[]
    def bind(path,kind):
        path=Path(path).resolve();assert path.is_file(),path
        key=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        if key not in artifacts:
            artifacts[key]=dict(path=key,kind=kind,bytes=path.stat().st_size,sha256=sha(path))
        return artifacts[key]['sha256']
    for name in ['development02','revision01','confirmation01']:
        camp=OUT/name;q=read(camp/'identity.json')
        bind(camp/'identity.json','frozen_campaign_identity')
        bind(ROOT/q['prereg']['candidate_binary'],'production_binary')
        summaries=[json.loads(s) for s in (camp/'summary.jsonl').read_text().splitlines()]
        for record in summaries:
            launch=q['launches'][record['number']-1];dest=Path(record['destination'])
            panel=launch['panel'];result=read(dest/'result.json');original_audit=read(dest/'audit.json')
            audit=original_audit;recovery=None
            if name=='development02' and record['number']==14:
                recovery_path=OUT/'recovered_models/C3_R1/qualified_recovery.json'
                recovery=read(recovery_path);audit=recovery['audit']
                assert sha(recovery_path)=='96edc767b6f971f295c28b0ebdeec15ff692a64d27ff92d22016327abf20f2cb'
                observations=read(OUT/'recovered_models/C3_R1/replay_observations.json')
            else:observations=read(dest/'observations.json')
            assert audit['passed'] and record['completion']['stop_reason']=='normal_return'
            assert bind(ROOT/panel['input_path'],'input')==panel['input_sha256']
            witness=dict(F=result['upper_bound'],routes=result['routes'])
            checked=physical.physical(panel,witness)
            assert checked['original_T_feasible'] and abs(checked['F']-audit['endpoint']['U'])<1e-7
            if 'final_inventories' in result:
                assert result['final_inventories'][1:]==result['verification']['final_inventories'][1:]
            witness.update(inventory=result['final_inventories'],G=checked['G'],P=checked['P'])
            source_hashes={f:bind(dest/f,'original_run_evidence') for f in
                ['launch.json','result.json','audit.json','completion.json','observations.json']}
            models=[]
            for o in observations:
                event=o['payload']
                if event['kind']!='call':continue
                assert bind(event['model_path'],'actual_native_matrix')==event['model_sha256']
                models.append(dict(call=event['call'],model_path=event['model_path'],sha256=event['model_sha256'],
                    full_original=event['full_original'],native_preconditions=event['native_preconditions'],
                    lower_g=event['lower_g'],upper_g=event['upper_g'],cutoff=event['cutoff'],settings=event['settings']))
            ledger=dest/'external/paper_optimize_ledger.csv'
            optimizer_ledger=[]
            if ledger.exists():
                bind(ledger,'native_optimize_ledger')
                with ledger.open(newline='',encoding='utf-8') as f:optimizer_ledger=list(csv.DictReader(f))
                assert len(optimizer_ledger)==audit['native_calls_started']
            key=f'{name}_{record["number"]:02d}_{record["id"]}_{record["arm"]}'
            bundle=dict(schema='round98-compact-original-evidence-v1',campaign=name,number=record['number'],
                role=record['id'],arm=record['arm'],panel=panel,binary_sha256=q['candidate_binary_sha256'],
                original_source_hashes=source_hashes,original_summary=record,original_audit=original_audit,
                exact_recovery=recovery,qualified_endpoint=audit['endpoint'],models=models,optimizer_ledger=optimizer_ledger,
                physical_witness=witness,executor_physical_recheck=checked,
                scope='Original complete-run endpoint and original physical routes; no fresh Optimize, no rational certificate.')
            path=target/'runs'/(key+'.json');write(path,bundle)
            witnesses.append(dict(campaign=name,number=record['number'],role=record['id'],arm=record['arm'],
                input_sha256=panel['input_sha256'],bundle=path.relative_to(ROOT).as_posix(),bundle_sha256=sha(path),
                **checked))
    with (OUT/'complete_results/cost_failures.csv').open(newline='',encoding='utf-8') as f:cost=list(csv.DictReader(f))
    for row in cost:
        category,label=row['category'],row['label']
        if category=='retired_paid_qualification':
            arm=label.rsplit('/',1)[1]
            sources=list((OUT/'development01/raw').glob('*_'+arm+'/completion.json'))
            assert len(sources)==1;source=sources[0]
        elif category.startswith('full_'):
            campaign,number,role,arm=label.split('/')
            source=OUT/campaign/'raw'/f'{int(number):02d}_{role}_{arm}'/'completion.json'
        elif category=='diagnostic':source=OUT/'diagnostic_receipts'/label/'receipt.json'
        elif category=='qualification':source=OUT/'qualification'/label/'receipt.json'
        elif category in ['native_ctest_qualification_correction','zero_optimize_diagnostic']:
            source=OUT/'engineering'/label/'receipt.json'
        elif category=='plain_matrix_qualification_batch':
            source=OUT/label.split('/')[0]/'reference_batch_receipt.json'
        else:source=OUT/label/'completion.json'
        cost_receipts.append(dict(cost=row,source_path=source.relative_to(ROOT).as_posix(),
            source_sha256=bind(source,'paid_receipt'),original_receipt=read(source)))
    write(target/'paid_receipts.json',cost_receipts)
    # Bind retained large diagnostics and actual ordered Start vectors. Never
    # parse or optimize them here; the qualification records describe that scope.
    for dirname in ['exports','diagnostics','recovered_models']:
        for path in (OUT/dirname).rglob('*'):
            if path.is_file() and (path.suffix=='.lp' or ('values' in path.name and path.suffix in ['.json','.gz','.csv'])):
                bind(path,'retained_diagnostic_model_or_vector')
    for name in ['development02','revision01','confirmation01']:
        for path in (OUT/name/'raw').rglob('*.round68.start.values.csv'):bind(path,'actual_ordered_start_vector')
    for build_name in ['round98-state-service-v1','round98-state-service-v2','round98-state-service-v3']:
        for filename in ['ExactEBRP.exe','Round98ModelExport.exe','Round65ReferenceBuild.exe']:
            path=ROOT/'build/research'/build_name/filename
            if path.exists():bind(path,'retained_binary')
    bind('D:/gurobi1302/win64/bin/gurobi130.dll','gurobi_runtime')
    for filename,rows in [('witness_index.csv',witnesses),('local_artifacts.csv',list(artifacts.values()))]:
        with (target/filename).open('x',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    write(target/'summary.json',dict(formal_runs=len(witnesses),physical_rechecks_passed=len(witnesses),
        paid_receipts=len(cost_receipts),local_artifacts=len(artifacts),optimizer_calls=0,
        original_files_modified=False,extractor_sha256=sha(__file__),independent_reproduction=False))
    print(json.dumps(read(target/'summary.json')),flush=True)

if __name__=='__main__':run(sys.argv[1])
