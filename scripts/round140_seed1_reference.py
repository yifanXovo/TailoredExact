"""Reuse two qualified fixed R138 Seed1 references; no solve or old public replay."""
from round140_common import *
import shutil,zipfile

PIN='1b19897ab5819ab3b7485ddc978954b45225f361'


def prepare():
    assert not budget()['unclosed']
    old=ROOT/'results/unified_exact_round138';matrix=read(old/'seed1_matrix_frozen.json')
    report_path=old/'reports/seed1.json';report=read(report_path)
    for path in [report_path,old/'seed1_matrix_frozen.json',old/'carrier_manifest.json']:
        pinned=git('show',PIN+':'+path.relative_to(ROOT).as_posix())
        assert hashlib.sha256(pinned).hexdigest()==sha(path),path
    planned=read(OUT/'seed1_matrix.json')['groups'][0]['launch'];p=planned['panel']
    own=read(Path(read(OUT/'incremental_matrix.json')['groups'][1]['launch']['destination'])/'round135_endpoint.json')
    dest=OUT/'inherited/seed1_reference_metadata';dest.mkdir(parents=True,exist_ok=False)
    refs=[];archives=read(old/'carrier_manifest.json')['carriers']
    wanted=['round135_endpoint.json','audit.json','verification_closeout.json','producer_receipt.json','producer_seal.json',
        'round137_control_audit.json','round137_parameters.json','round138_control_audit.json','round138_parameters.json',
        'affinity.json','launch.json','result.json']
    for g in matrix['groups']:
        l=g['launch']
        if l['id']!=p['id']:continue
        r=next(a for a in report['arms'] if a['role']==p['id'] and a['method']==l['method'])
        d=Path(l['destination']);identity=old/g['group']/'identity.json'
        assert sha(identity)==g['identity_SHA']
        assert sha(d/'round135_endpoint.json')==r['endpoint_SHA'] and sha(d/'audit.json')==r['audit_SHA']
        endpoint=read(d/'round135_endpoint.json');assert read(d/'audit.json')['passed']
        assert read(d/'verification_closeout.json')['necessary_verification_complete']
        assert r['performance_eligible'] and r['native_proof_qualified'] and r['seed']==1
        for k in ['input_SHA','cap','lambda_value','T']:
            expected={'input_SHA':p['input_sha256'],'cap':p['cap_seconds'],'lambda_value':p['lambda'],'T':p['T_seconds']}[k]
            assert r[k]==expected,(l['method'],k)
        for k in ['H_complete','H_semantic_SHA','H_fleet_SHA']:assert endpoint[k]==own[k]
        carrier=next(a for a in archives if Path(a['path']).stem==g['group'].replace('/','_'))
        archive=ROOT/carrier['path'];assert sha(archive)==carrier['SHA256']
        target=dest/l['method'];target.mkdir();copied=[]
        with zipfile.ZipFile(archive) as z:
            index=json.loads(z.read('__round138_member_index__.json'))
            sources=[identity]+[d/n for n in wanted if (d/n).is_file()]
            for source in sources:
                relative=source.relative_to(ROOT).as_posix();record=index[relative]
                assert record['SHA256']==sha(source) and record['bytes']==source.stat().st_size
                name='identity.json' if source==identity else source.name
                shutil.copyfile(source,target/name)
                copied.append(dict(original_path=relative,new_path=(target/name).relative_to(ROOT).as_posix(),**record))
        refs.append(dict(**r,original_group=g['group'],identity_SHA=g['identity_SHA'],original_launch=l,
            fixed_science_commit=PIN,archive=carrier,copied_metadata=copied,H_semantic_SHA=endpoint['H_semantic_SHA'],
            H_fleet_SHA=endpoint['H_fleet_SHA'],original_measured_PE_and_source_retained=True))
    assert len(refs)==2 and {r['method'] for r in refs}=={'BASE','STOCK'}
    write(OUT/'seed1_reference_reuse.json',dict(UTC=utc(),fixed_science_commit=PIN,
        matrix_path=(old/'seed1_matrix_frozen.json').relative_to(ROOT).as_posix(),matrix_SHA=sha(old/'seed1_matrix_frozen.json'),
        report_path=report_path.relative_to(ROOT).as_posix(),report_SHA=sha(report_path),references=refs,
        original_costs_retained_without_new_experiment_charge=True,small_necessary_metadata_only=True,
        no_old_public_recovery_reopened=True,Optimize=0,vendor_DLL_loads=0))
    print('Two matched accepted Seed1 references pinned and small metadata copied; zero Optimize')


def report():
    assert not budget()['unclosed']
    full=read(OUT/'reports/full.json');assert full['complete']
    reuse=read(OUT/'seed1_reference_reuse.json')
    selected=[a for a in full['new_arms'] if a['seed']==1]
    assert len(selected)==1 and selected[0]['role']=='R-B35-S-T2' and selected[0]['method']=='TC_STOCK'
    new=selected[0];arms=[];pairs=[]
    fields=['role','method','seed','certificate','T_cert','T_produce','T_verify','T_total','U','L',
        'signed_gap','relative_gap','PE_SHA','source_commit','input_SHA','cap','lambda_value',
        'H_complete','H_semantic_SHA','H_fleet_SHA','native_proof_qualified','performance_eligible']
    for ref in reuse['references']:
        assert ref['input_SHA']==new['input_SHA'] and ref['cap']==new['cap']
        assert ref['T']==new['physical_T'] and ref['lambda_value']==new['lambda_value']
        for k in ['H_complete','H_semantic_SHA','H_fleet_SHA']:assert ref[k]==new[k]
        row={k:ref[k] for k in fields};row.update(reused=True,physical_T=ref['T'])
        arms.append(row)
        pairs.append(dict(role=new['role'],Seed=1,reference=ref['method'],candidate='TC_STOCK',
            reference_U=ref['U'],candidate_U=new['U'],delta_U=new['U']-ref['U'],
            reference_L=ref['L'],candidate_L=new['L'],delta_L=new['L']-ref['L'],
            reference_T_cert=ref['T_cert'],candidate_T_cert=new['T_cert'],
            identical_initial_H_semantics_and_fleet=True,same_PE_intervention=False,
            reference_source=ref['source_commit'],reference_PE=ref['PE_SHA'],
            candidate_source=new['source_commit'],candidate_PE=new['PE_SHA']))
    arms.append(dict(**{k:new[k] for k in fields},reused=False,physical_T=new['physical_T']))
    value=dict(UTC=utc(),arms=arms,pairs=pairs,Optimize=0,
        selection_rationale='One result-selected RB35-T2 confirmation: the matched accepted STOCK Seed1 already approaches TC_STOCK Seed0, so the largest repair may be Seed-sensitive and can affect the next uniform research priority. No new reference solve or second role is added.',
        discussion='The fresh current-PE TC_STOCK Seed1 is paired with already qualified R138 BASE/STOCK Seed1. References retain their original measured source, PE and complete clocks; this is not a same-PE causal intervention. All Seed0 certified-time and endpoint regressions remain visible. One selected confirmation is not an unseen validation panel.',
        source_full_report_SHA=sha(OUT/'reports/full.json'),reference_reuse_SHA=sha(OUT/'seed1_reference_reuse.json'),
        new_complete_positions=1,reused_reference_positions=2,original_costs_not_newly_charged=True)
    write(OUT/'reports/seed1.json',value)
    from round138_analyze import csv_write
    csv_write(OUT/'reports/seed1_arms.csv',arms);csv_write(OUT/'reports/seed1_pairs.csv',pairs)
    print(json.dumps(pairs))


if __name__=='__main__':globals()[sys.argv[1]]()
