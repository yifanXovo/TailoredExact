"""Finite new-round carriers and additive local semantic checks; never Optimize."""
from round138_common import *
import zipfile
import collections

INDEX='__round138_member_index__.json'
BANNED={'.exe','.dll','.o','.obj','.a','.lib','.lic','.ttf','.otf'}

def groups():
    out=list(read(OUT/'matrix_frozen.json')['groups'])
    second=OUT/'seed1_matrix_frozen.json'
    if second.exists():out+=read(second)['groups']
    return out

def local_check():
    assert not budget()['unclosed']
    import round138_read as reader
    from round138_scaled_read import ArmModels as ScaledArmModels
    from round138_repair import scaled_rows
    from round135_read import validate_event_lifecycle,expected_settings
    import round108_reader as core
    tick=time.perf_counter();checks=[];models=reader.ArmModels();scaled_models=ScaledArmModels()
    for group in groups():
        launch=group['launch'];p=launch['panel'];d=Path(launch['destination'])
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        closeout=read(d/'verification_closeout.json');audit=read(d/'audit.json')
        endpoint=read(d/'round135_endpoint.json');control=read(d/'round138_control_audit.json')
        assert closeout['necessary_verification_complete'] and closeout['evidence_complete'] and audit['passed']
        assert control['PASS'] and control['Seed']==launch['seed'] and control['stock_rlt']==p['round138_stock_rlt']
        assert closeout['audit_SHA']==sha(d/'audit.json')
        producer=read(d/'producer_receipt.json');seal=read(d/'producer_seal.json')
        assert producer['producer_seal_SHA']==sha(d/'producer_seal.json') and producer['native_stopped_no_reentry']
        for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest,(d,name)
        physical=core.full_fleet(ROOT,p,read(d/'result.json'))
        assert abs(physical['F']-endpoint['U'])<=1e-7 and endpoint['performance_eligible']
        assert endpoint['T_cert'] is not None if endpoint['certificate'] else endpoint['T_cert'] is None
        observations=read(d/'observations.json');payloads=[r['payload'] for r in observations]
        lifecycle=validate_event_lifecycle(payloads,True);used=[]
        for call in (r for r in payloads if r['kind']=='call'):
            path=core.portable(ROOT,call['model_path']);assert sha(path)==call['model_sha256']
            for name,value in expected_settings(launch).items():assert call['settings'][name]==value
            v2=launch.get('stock_row_transport')=='power-of-two-v2'
            fact,m=(scaled_models if v2 else models).model_contract(ROOT,p,path,launch['arm'])
            if p['round138_stock_rlt']:
                row=fact['stock_RLT']
                make_rows=scaled_rows if v2 else reader.stock_rows
                expected=collections.Counter(make_rows(p['V'],row['actual_alpha'],row['actual_beta'],row['Bminus'],row['B']))
                counts=collections.Counter(m['rows'])
                assert all(counts[r]==n for r,n in expected.items()),('Repeated stock row emission',path)
            used.append(fact['stock_RLT'])
        checks.append(dict(arm_id=launch['arm_id'],method=launch['method'],seed=launch['seed'],
            certificate=endpoint['certificate'],U=endpoint['U'],L=endpoint['L'],
            physical_return_loads=physical['return_loads'],models=used,lifecycle=lifecycle,
            audit_SHA=sha(d/'audit.json'),closeout_SHA=sha(d/'verification_closeout.json')))
    assert 'gurobipy' not in sys.modules
    write(OUT/'local_semantic_check.json',dict(PASS=True,UTC=utc(),arms=checks,seconds=time.perf_counter()-tick,
        Optimize=0,vendor_DLL_loads=0,scope='Additive pure replay of physical fleets, modern lifecycle/parameters, seals and every used model stock row; complete H/Start/proof qualification is retained from each original full postproduction reader, not relabelled as a new independent full semantic replay'))
    print(f'{len(checks)} sealed new positions: additive local semantic checks pass; zero Optimize/DLL')

def make_zip(label,paths):
    target=OUT/'artifacts'/f'{label}.zip';target.parent.mkdir(parents=True,exist_ok=True)
    assert not target.exists(),('immutable carrier already exists; inspect/resume without replacing it',target)
    entries={}
    with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for path in sorted(set(Path(p) for p in paths)):
            assert path.is_file() and path.suffix.lower() not in BANNED,path
            name=path.relative_to(ROOT).as_posix();assert '..' not in Path(name).parts
            raw=path.read_bytes();entries[name]=dict(SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
            z.writestr(name,raw)
        index=json.dumps(entries,sort_keys=True,separators=(',',':')).encode('utf-8')
        z.writestr(INDEX,index)
    return dict(path=target.relative_to(ROOT).as_posix(),SHA256=sha(target),bytes=target.stat().st_size,
        members=len(entries),member_index=INDEX,member_index_SHA=hashlib.sha256(index).hexdigest())

def archive():
    assert not budget()['unclosed'] and read(OUT/'candidate_decision.json')['study_complete']
    assert read(OUT/'local_semantic_check.json')['PASS']
    tick=time.perf_counter();old_source=read(OUT/'repair/source_v1_archive.json');old_carrier=old_source['carrier']
    assert sha(ROOT/old_carrier['path'])==old_carrier['SHA256']
    records=[old_carrier]
    for g in groups():
        folder=OUT/g['group'];label=folder.relative_to(OUT).as_posix().replace('/','_')
        records.append(make_zip(label,[p for p in folder.rglob('*') if p.is_file()]))
    diagnostics=[p for name in ['roots','qualification','fees','infra','repair','cost_segments'] for p in (OUT/name).rglob('*') if p.is_file()]
    # Late archive/public/cleanup costs are committed as metadata deltas. Never
    # capture this archive operation's still-open own stdout/receipt recursively.
    diagnostics += [p for receipt in (OUT/'ordinary_steps').glob('*/receipt.json')
                    for p in receipt.parent.rglob('*') if p.is_file()]
    records.append(make_zip('diagnostics_and_failures',diagnostics))
    primary=read(OUT/'candidate_manifest.json');candidate=read(OUT/'candidate_repair_manifest.json');helpers=dict(read(OUT/'matrix_frozen.json')['helpers'])
    amendment=read(OUT/'review/reader_amendment.json')
    for name,r in amendment['helper_replacements'].items():helpers[name]=r['new_SHA']
    # Ordinary imports only: include the existing exact-math helper graph as
    # well as the already frozen full-reader graph, without vendor runtimes.
    import round138_math,round138_tiny_read,round138_offline_products
    sources=set(candidate['source_hashes'])|set(helpers)|{'scripts/round126_export.py','scripts/paper_s2_stock_rlt.py'}
    sources.update(Path(m.__file__).resolve().relative_to(ROOT).as_posix() for m in list(sys.modules.values())
                   if getattr(m,'__file__',None) and str(m.__file__).endswith('.py')
                   and Path(m.__file__).resolve().parent==ROOT/'scripts')
    sources.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('round138*') if p.is_file())
    for name,digest in candidate['source_hashes'].items():assert sha(ROOT/name)==digest,name
    for name,digest in helpers.items():assert sha(ROOT/name)==digest,name
    source=make_zip('source_and_helpers',[ROOT/p for p in sources]);records.append(source)
    inputs={g['launch']['panel']['input_path'] for g in groups()}
    write(OUT/'source_publication.json',dict(UTC=utc(),production_source_commit=candidate['source_commit'],
        production_version='Delivered/Seed1 V2 exact coefficient transport',production_PE_SHA=candidate['production_PE_SHA'],
        primary_measured_source_commit=primary['source_commit'],primary_measured_PE_SHA=primary['production_PE_SHA'],
        primary_source_bundle=old_carrier,primary_native_bridge_SHA=sha(OUT/'repair/primary_native_bridge.json'),
        primary_results_not_retagged_as_V2=True,
        publication_parent_before_science_commit=git('rev-parse','HEAD').decode().strip(),source_bundle=source,
        actual_source_hashes=candidate['source_hashes'],frozen_helpers_with_reviewed_amendment=helpers,
        baseline_source_commit='779713ad9a0b01edc538ecb64df9438739127be3',
        new_standalone_helpers={n:sha(ROOT/n) for n in sources if n not in helpers and n not in candidate['source_hashes']},
        commercial_assets_published=False,inputs={p:sha(ROOT/p) for p in inputs},
        required_configuration_files={p:sha(ROOT/p) for p in ['config/gi_tbc_round137.json','config/paper_s2.json',
            'config/gi_tbc_stock_rlt_round138.json','scripts/paper_s2.py','scripts/paper_s2_stock_rlt.py']},Optimize=0))
    meta=[p for p in OUT.iterdir() if p.is_file() and p.suffix.lower() in {'.json','.md','.bib','.pdf'}
          and p.name not in {'carrier_manifest.json','public_restore_receipt.json','publication_pin.json'}]
    meta += [p for folder in ['reports','review','math','figures'] for p in (OUT/folder).rglob('*') if p.is_file()]
    meta += [ROOT/p for p in inputs]+[ROOT/p for p in ['config/gi_tbc_round137.json','config/paper_s2.json',
             'config/gi_tbc_stock_rlt_round138.json','scripts/paper_s2.py','scripts/paper_s2_stock_rlt.py']]
    records.append(make_zip('science_and_paper',meta))
    write(OUT/'carrier_manifest.json',dict(UTC=utc(),carriers=records,source_bundle=source,
        new_round_only=True,old_dependencies_are_fixed_pins_and_selected_members=True,
        unique_science_and_failures_retained=True,Optimize=0,seconds=time.perf_counter()-tick,
        public_check='Anonymous fixed-commit read, archive and member hashes only; no native asset, build or Optimize'))
    print(json.dumps(dict(archives=len(records),bytes=sum(r['bytes'] for r in records),members=sum(r['members'] for r in records))))

if __name__=='__main__':globals()[sys.argv[1]]()
