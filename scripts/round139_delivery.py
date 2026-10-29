"""Finite Round139 evidence packaging and additive local checks. Never Optimize."""
from round139_common import *
import types,zipfile,collections,gzip
import round138_delivery as prior

INDEX='__round139_member_index__.json'
BANNED=prior.BANNED
make_zip=types.FunctionType(prior.make_zip.__code__,dict(vars(prior),ROOT=ROOT,OUT=OUT,INDEX=INDEX,sha=sha))

def groups():
    return [g for p in sorted(OUT.glob('*_matrix.json')) for g in read(p)['groups']]

def dependencies():
    """Select old members from existing local indexes; do not redo public recovery."""
    assert not budget()['unclosed'];bindings=[];metadata=[]
    m138=read(ROOT/'results/unified_exact_round138/matrix_frozen.json')
    old1=read(ROOT/'results/unified_exact_round138/seed1_matrix_frozen.json')
    selections=[]
    for b in read(OUT/'baseline_reuse.json')['positions']:
        for method,key,round_no,position,pin in [('base','base',137,b['base_position'],'e735c3447eb1443713c700942d873de1783a4a26'),
            ('both','both',138,b['both_position'],'1b19897ab5819ab3b7485ddc978954b45225f361')]:
            selections.append((b['role'],method,round_no,f'campaign_{position:03}.zip',Path(b[key]['destination']),pin))
    for g in old1['groups']:
        l=g['launch'];selections.append((l['id'],l['method']+' Seed1',138,
            g['group'].replace('/','_')+'.zip',Path(l['destination']),'1b19897ab5819ab3b7485ddc978954b45225f361'))
    manifest_names={137:'raw_archive_manifest.json',138:'carrier_manifest.json'}
    carriers={137:[dict(path=f'results/unified_exact_round137/artifacts/{c["name"]}',SHA256=c['SHA256'],external_index=c['member_index'])
        for c in read(ROOT/'results/unified_exact_round137/raw_archive_manifest.json')['archives']],
        138:read(ROOT/'results/unified_exact_round138/carrier_manifest.json')['carriers']}
    for role,method,n,archive_name,d,pin in selections:
        carrier=next(c for c in carriers[n] if Path(c['path']).name==archive_name)
        if n==137:
            record=carrier['external_index'];assert sha(ROOT/record['path'])==record['SHA256']
            with gzip.open(ROOT/record['path'],'rt',encoding='utf-8') as f:
                index={r['path']:{'SHA256':r['SHA256'],'bytes':r['bytes']} for r in json.load(f)}
        else:
            with zipfile.ZipFile(ROOT/carrier['path']) as z:
                raw=z.read(carrier['member_index']);assert hashlib.sha256(raw).hexdigest()==carrier['member_index_SHA']
                index=json.loads(raw)
        paths=[d.parent.parent/'identity.json',d/'round135_endpoint.json',d/'audit.json',d/'producer_receipt.json',d/'producer_seal.json',
            d/'external/initial_witness.json',d/'external/paper_optimize_ledger.csv',d/'external/adaptive_mass_decision_ledger.csv']
        if role in ['K-15-S','K-20-S','K-35-U','R-B35-S-T2'] and 'Seed1' not in method:
            obs=read(d/'observations.json');paths.append(d/'observations.json')
            for r in obs:
                c=r['payload']
                if c['kind']=='call':paths.append(Path(c['model_path']))
            paths += list((d/'external/native_logs').glob('*mip.gurobi.log'))
            paths += list((d/'external/native_logs').glob('*.round68.start.json'))
            paths += list((d/'external/native_logs').glob('*.round68.start.values.csv'))
        members=[]
        for p in sorted(set(paths)):
            name=p.relative_to(ROOT).as_posix();record=index[name];assert sha(p)==record['SHA256']
            members.append(dict(member=name,**record))
        bindings.append(dict(role=role,method=method,commit=pin,archive=carrier['path'],archive_SHA=carrier['SHA256'],
            selected_members=members,original_manifest_SHA=sha(ROOT/f'results/unified_exact_round{n}'/manifest_names[n])))
    for n,pin,names in [(137,'e735c3447eb1443713c700942d873de1783a4a26',['matrix_frozen.json','candidate_manifest.json','candidate_build.json','reports/arms.csv']),
        (138,'1b19897ab5819ab3b7485ddc978954b45225f361',['matrix_frozen.json','candidate_manifest.json','candidate_repair_manifest.json',
        'baseline_reuse.json','reports/new_arms.csv','reports/seed1.json','seed1_matrix_frozen.json','repair/primary_native_bridge.json'])]:
        for name in names:
            p=ROOT/f'results/unified_exact_round{n}'/name;metadata.append(dict(commit=pin,path=p.relative_to(ROOT).as_posix(),SHA=sha(p)))
    write(OUT/'inherited_dependencies.json',dict(UTC=utc(),archives=bindings,metadata_files=metadata,Optimize=0,
        scope='Only required existing local old member indexes and selected file bytes; old public acceptance is inherited, not rerun. No old archive transfer/restore, native asset load or full old semantic replay.'))
    print(f'{len(bindings)} fixed old carrier dependencies with exact selected members; no old public check repeated')

def local_check():
    assert not budget()['unclosed']
    from round139_qualify import exact_matrix
    from round135_read import validate_event_lifecycle,expected_settings
    import round108_reader as core
    tick=time.perf_counter();facts=[]
    for g in groups():
        l=g['launch'];d=Path(l['destination']);p=l['panel']
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        c=read(d/'verification_closeout.json');a=read(d/'audit.json');e=read(d/'round135_endpoint.json')
        assert c['necessary_verification_complete'] and c['evidence_complete'] and a['passed']
        assert c['audit_SHA']==sha(d/'audit.json') and e['performance_eligible'] and e['native_proof_qualified']
        seal=read(d/'producer_seal.json');producer=read(d/'producer_receipt.json')
        assert producer['producer_seal_SHA']==sha(d/'producer_seal.json') and producer['native_stopped_no_reentry']
        for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest,(d,name)
        physical=core.full_fleet(ROOT,p,read(d/'result.json'));assert abs(physical['F']-e['U'])<=1e-7
        observations=read(d/'observations.json');payloads=[r['payload'] for r in observations]
        lifecycle=validate_event_lifecycle(payloads,True);control=read(d/'round139_control_audit.json');assert control['PASS']
        checked=[]
        for call in (r for r in payloads if r['kind']=='call'):
            for name,value in expected_settings(l).items():assert call['settings'][name]==value
            path=core.portable(ROOT,call['model_path']);assert sha(path)==call['model_sha256']
            enabled=control['model_stock'][call['model_sha256']];fact,model=exact_matrix(path,p,enabled,False);checked.append(fact)
        facts.append(dict(arm_id=l['arm_id'],placement=l['placement'],seed=l['seed'],certificate=e['certificate'],
            U=e['U'],L=e['L'],audit_SHA=sha(d/'audit.json'),closeout_SHA=sha(d/'verification_closeout.json'),
            physical_return_loads=physical['return_loads'],lifecycle=lifecycle,models=checked))
    assert 'gurobipy' not in sys.modules
    write(OUT/'local_semantic_check.json',dict(PASS=True,UTC=utc(),positions=facts,seconds=time.perf_counter()-tick,
        Optimize=0,vendor_DLL_loads=0,scope='Additive pure physical fleet, seal, lifecycle, exact stock multiplicity, parameter and immutable model replay; original full H/Start/proof readers remain separate authorities'))
    print(f'{len(facts)} entered new positions pass additive local semantic checks')

def accounting():
    assert not budget()['unclosed'];b=budget();paths=sorted((OUT/'ordinary_steps').glob('*/receipt.json'))
    records=[read(p) for p in paths]
    write(OUT/'cost_report.json',dict(UTC=utc(),experiment=b,fee_ordinary_seconds=b['separately_reported_seconds'],
        additional_disjoint_ordinary_seconds=sum(r['seconds'] for r in records),
        ordinary_steps=[dict(label=p.parent.name,SHA=sha(p),receipt=r) for p,r in zip(paths,records)],
        reused_BASE_BOTH_positions_have_no_new_charge=True,all_qualification_and_failures_charged=True,
        complete_outer_cost_without_nested_H_LP_MIP_Work_double_count=True,
        precision_scope='Measured build/verification and explicit ordinary commands only; interactive reading/editing/review/Git/tool time not exhaustively metered or assigned invented precision'))
    print(json.dumps(dict(charged_seconds=b['G1_seconds'],hours=b['G1_seconds']/3600,remaining=b['remaining_G1_seconds'])))

def archive():
    assert not budget()['unclosed'] and read(OUT/'candidate_decision.json')['study_complete']
    assert read(OUT/'local_semantic_check.json')['PASS'];tick=time.perf_counter();records=[]
    for g in groups():
        folder=OUT/g['group'];records.append(make_zip(folder.relative_to(OUT).as_posix().replace('/','_'),[p for p in folder.rglob('*') if p.is_file()]))
    diagnostics=[p for name in ['qualification','fees','infra','cost_segments'] for p in (OUT/name).rglob('*') if p.is_file()]
    diagnostics += [p for receipt in (OUT/'ordinary_steps').glob('*/receipt.json') for p in receipt.parent.rglob('*') if p.is_file()]
    records.append(make_zip('qualification_and_failures',diagnostics))
    manifest=read(OUT/'candidate_manifest.json');helpers={}
    for path in OUT.glob('*_matrix.json'):
        for name,digest in read(path)['helpers'].items():
            assert sha(ROOT/name)==digest,name
            if name in helpers:assert helpers[name]==digest,name
            helpers[name]=digest
    sources=set(manifest['source_hashes'])|set(helpers)|{'.gitattributes','CMakeLists.txt','WORKSPACE_POLICY.md','scripts/round126_export.py','scripts/round138_documents.py','scripts/round138_pdf_qa.py',
        'scripts/round138_delivery.py','scripts/round138_public_read.py','scripts/round138_common.py','scripts/round138_repair.py',
        'scripts/round138_setup.py','scripts/round138_analyze.py','scripts/paper_s2.py','scripts/paper_s2_stock_rlt.py','scripts/paper_s2_stock_placement.py'}
    sources.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('round139*') if p.is_file())
    for name,digest in manifest['source_hashes'].items():assert sha(ROOT/name)==digest,name
    source=make_zip('source_and_helpers',[ROOT/n for n in sources]);records.append(source)
    inputs={g['launch']['panel']['input_path'] for g in groups()}
    configs=['config/gi_tbc_round137.json','config/paper_s2.json','config/gi_tbc_stock_rlt_round138.json','config/gi_tbc_stock_placement_round139.json']
    write(OUT/'source_publication.json',dict(UTC=utc(),production_source_commit=manifest['source_commit'],
        production_PE_SHA=manifest['production_PE_SHA'],production_DLL_SHA=manifest['DLL_SHA'],source_bundle=source,
        actual_source_hashes=manifest['source_hashes'],frozen_helpers=helpers,
        additional_source_and_supporting_files={n:sha(ROOT/n) for n in sources if n not in helpers and n not in manifest['source_hashes']},
        inputs={n:sha(ROOT/n) for n in inputs},configuration_files={n:sha(ROOT/n) for n in configs},
        inherited_science=dict(R137='e735c3447eb1443713c700942d873de1783a4a26',R138='1b19897ab5819ab3b7485ddc978954b45225f361',
            R138_delivery=BASE,R138_primary_stays_V1=True,V2_writer_unchanged=True),
        commercial_assets_published=False,Optimize=0))
    meta=[p for p in OUT.iterdir() if p.is_file() and p.suffix.lower() in {'.json','.md','.bib','.pdf'}
          and p.name not in {'carrier_manifest.json','publication_pin.json','public_restore_receipt.json'}]
    meta += [p for folder in ['reports','review','figures'] for p in (OUT/folder).rglob('*') if p.is_file()]
    meta += [ROOT/n for n in inputs]+[ROOT/n for n in configs]
    meta += [ROOT/n for n in ['docs/round139_research.md','docs/current_mainline.md','docs/unified_exact_research_index.md']]
    records.append(make_zip('science_and_paper',meta))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),carriers=records,source_bundle=source,new_round_only=True,
        all_entered_adverse_open_and_failures_retained=True,unique_science_retained=True,seconds=time.perf_counter()-tick,
        Optimize=0,public_check='Finite anonymous fixed-commit archive and member byte checks; no solver/build/vendor loading'))
    print(json.dumps(dict(carriers=len(records),bytes=sum(r['bytes'] for r in records),members=sum(r['members'] for r in records))))

if __name__=='__main__':globals()[sys.argv[1]]()
