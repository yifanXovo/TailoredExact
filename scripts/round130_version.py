"""Adopt the selected version without relabelling predecessor measurements."""
from round130_common import *
import csv,io

def run():
    seal=read(OUT/'E3_frozen.json')
    write(OUT/'paper_version_manifest.json',dict(version='Round130',sole_proposed_method='GI-TBC (uniform pair-support implementation, MS2)',
        table_short_name='S2',algorithm_identity='original E2 --round127-mode ms2',predecessor_full_MB='original E2 --round127-mode mb',
        repository_default='ENS-C (unchanged)',paper_reproduction_entry=['--method','gcap-frontier','--algorithm-preset','research-round83-vds-equal-net-exchange','--round98-state-service','m-binary','--round90-lp-g-split','false','--round127-mode','ms2'],
        E2_PE_SHA=E2_SHA,E3_PE_SHA=seal['PE_SHA'],DLL_SHA=DLL_SHA,E3_is_not_E2_binary=True,
        support='pair cover and conditional rows only; no triple support on any input',
        unchanged=['complete H','representation','support enumeration and budget','ordered supply','C_G','A/B','Gini interval controller','AM thresholds','numeric tolerances','native defaults'],
        current_main_benchmark='cold P-GRB',controls=dict(PS='own paid H -> original compact full Start',S2R='pair-only inclusive fixed root LP + MIP; outer control disabled'),
        inherited_verified_zero_startup_scope_preserved=True,
        zero_backend_exposure_rule='A qualified original startup-zero branch has no native backend exposure; no new shortcut or free backend attribution',
        evidence_layers=dict(R127_R128_MS2='development / known roles',R129_new_four='prospective at selection time',R129_protection='separate known protection input',R130='three already-known attribution roles; not independent new validation'),
        manuscript_performance_policy='Only qualified actual MS2 observations directly support current main-method performance. Older full-MB/ENS observations retain their names and serve predecessor/background evidence.',
        larger_roles='Historical V35/V50/V60 observations do not establish final MS2 performance at those sizes; no historical rerun authorized',
        negative_results_preserved=['R112-R115 paid-start mixed outcomes','R127 q2 P-tuned holdout 0/3 versus default P1/3','R128 timing reversal and no-split roles','R129 C15/B30 open at both Seeds and B30 endpoint reversal'],
        selection_is_settled='All five R129 conditions passed; the user adopts MS2. This round is not another candidate selection.',
        formal_results_pending=not (OUT/'arms.csv').exists()))
    config=read(ROOT/'results/unified_exact_round129/paper_method_config.json')
    config.update(name='GI-TBC (uniform pair-support implementation, MS2)',table_short_name='S2',
        production_source=read(OUT/'preformal_source_provenance.json')['source_commit'],PE_SHA256=seal['PE_SHA'],predecessor_E2_SHA256=E2_SHA,
        static_strengthening='R125 formulas, with only pair support active; all triple support disabled uniformly',
        additional_flags=['--round98-state-service','m-binary','--round90-lp-g-split','false','--round127-mode','ms2'],
        exact_reproduction_commands=[dict(id=l['id'],seed=l['seed'],command=l['command']) for p in read(OUT/'argv_freeze.json')['full_plans'] for l in p['launches'] if l['method']=='S2'])
    config['native'].update(gurobi_seed='per-group frozen 0/1; never per-call redraw',MIPFocus=0,Cuts=-1)
    config['algorithm_identity']='original E2 --round127-mode ms2; not a new third algorithm'
    config['frozen_core_archive_source']=SOURCE
    config['repository_default_unchanged']='ENS-C'
    write(OUT/'paper_method_config.json',config)
    spec=list(csv.DictReader((ROOT/'results/unified_exact_round129/method_spec_matrix.csv').open(encoding='utf-8-sig')))
    for r in spec:
        for k in ['actual_activation','generation_update']:
            r[k]=r[k].replace('M-B','S2')
        item=r['item']
        if r['category'] in ['physical extension','representation','variable declaration','static strengthening','static physical row','domain tightening','static interval/cutoff row']:
            r['actual_activation']='S2/S2R strengthened package: '+r['actual_activation']
        if item=='physical_core':r['actual_activation']='P/PS original compact; S2/S2R strengthened representation; same physical contract'
        elif item in ['support_cover','support_conditional']:
            r.update(actual_activation='S2 and S2R only; pairs enabled, triples uniformly disabled',generation_update='unchanged k then pair enumeration and shared50000 budget; triple emission predicate false')
        elif item=='numerical_penalty_closure':r['actual_activation']='S2 original semantic proof shortcut only; disabled in S2R, not a valid inclusive physical row'
        elif r['category']=='heuristic':r['actual_activation']='independently paid identical full H in PS/S2/S2R; absent in P'
        elif item in ['NEXT','AM','selection','epoch_cache']:r['actual_activation']='S2 outer control only; off in S2R/PS/P'
        elif item=='Start':r['actual_activation']='PS complete original-compact own Start; S2 scoped own Starts; S2R own pre-LP validation and one root-MIP Start; cold P none'
        elif item=='native_return':r['actual_activation']='all actual calls; S2R additionally requires complete native optimal root-MIP return for certification'
        elif item=='cover':r['actual_activation']='S2 interval union; S2R fixed root plus cutoff complement; P/PS full original domain'
        elif item=='Gurobi_native':r['actual_activation']='all four methods; frozen per-group Seed0/1, one thread, PresolveAuto, MIPFocus0, Cuts-1, requested zero gaps and original tolerances'
        r['review_status']='R125 validity retained; R130 finite source/matrix/native qualification in qualification/ and review/; no blanket rational proof'
    with (OUT/'method_spec_matrix.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(spec[0]));w.writeheader();w.writerows(spec)
    rows=[]
    historical_argv={}
    for round_no in [122,123]:
        path=f'results/unified_exact_round{round_no}/argv_freeze.json'
        p=ROOT/path
        historical_argv[round_no]=read(p) if p.is_file() else json.loads(git('show',BASE+':'+path))
    specs=[(122,f'reconstruction/group{k:02d}/arms.csv','predecessor benchmark') for k in range(1,9)]
    specs += [(123,'reconstruction/final/arms.csv','predecessor proof-limit benchmark'),
        (126,'arms.csv','predecessor small-instance confirmation'),(127,'main_arms.csv','predecessor Seed1 confirmation'),
        (127,'core_arms.csv','development / known-role component diagnostics'),(128,'arms.csv','known-role inclusive-root and MS2 development'),
        (129,'arms.csv','prospective new four / separate protection'),(130,'arms.csv','known-role attribution diagnostics')]
    for round_no,filename,layer in specs:
        path=f'results/unified_exact_round{round_no}/{filename}'
        p=ROOT/path
        if p.exists():data=p.read_text(encoding='utf-8-sig')
        elif round_no!=130:
            try:data=git('show',BASE+':'+path).decode('utf-8-sig')
            except subprocess.CalledProcessError:continue
        else:continue
        for a in csv.DictReader(io.StringIO(data)):
            method=a.get('method') or a.get('arm') or 'unknown'
            seed=a.get('seed')
            seed_authority=path+' (seed field)'
            if seed in [None,''] and round_no in historical_argv:
                wanted='campaign/'+filename.split('/')[1] if round_no==122 else None
                matches=[launch for plan in historical_argv[round_no]['plans']
                         if wanted is None or plan['name']==wanted
                         for launch in plan['launches']
                         if launch['id']==a['id'] and (launch.get('method') or launch.get('arm'))==method]
                assert len(matches)==1,(round_no,filename,a['id'],method)
                seed=matches[0]['seed']
                seed_authority=f'results/unified_exact_round{round_no}/argv_freeze.json'
            current=method in ['S2','MS2'];config='uniform pair-support MS2' if current else 'full three-station M-B' if method in ['M-B','MB','MD-R'] else 'as named in original authority'
            if method=='MD-R':config='full three-station inclusive-root MD-R control'
            if method=='S2R':config='pair-only inclusive-root s2-root control'
            if method in ['MR','MG','MD']:config='R127 three-station predecessor diagnostic '+method
            if round_no==129:role='protection' if a.get('id')=='PB-C20-B' else 'prospective at R129 selection'
            elif round_no==130:role='known-role attribution diagnostic'
            else:role=layer
            qualification_keys=['formal_protocol_qualified','numbers_qualified','certificate_qualified']
            eligibility=(all(str(a[k]).lower()=='true' for k in qualification_keys) and str(a.get('source_reduced','false')).lower()!='true') if all(a.get(k) not in [None,''] for k in qualification_keys) else None
            rows.append(dict(round=round_no,id=a.get('id'),seed=seed if seed is not None else 'unknown',seed_authority=seed_authority,method=method,actual_configuration=config,
                source_native_configuration=a.get('configuration','not a separate field in source table'),
                evidence_role=role,PE_SHA=a.get('PE_SHA','unknown'),DLL_SHA=a.get('DLL_SHA','unknown'),input_SHA=a.get('input_SHA','unknown'),
                source_recorded_commit=a.get('source_commit','unknown'),
                software_binding_authority={E0_SHA:'results/unified_exact_round122/production_identity.json',E1_SHA:'results/unified_exact_round127/E1_frozen.json',E2_SHA:'results/unified_exact_round128/E2_frozen.json',seal['PE_SHA']:'results/unified_exact_round130/E3_frozen.json'}.get(a.get('PE_SHA'),'original source authority'),
                actual_new_E3_source_commit=read(OUT/'preformal_source_provenance.json')['source_commit'] if round_no==130 else '',
                V=a.get('V','unknown'),M=a.get('M','unknown'),Q_vector=a.get('Q_vector','unknown'),T_seconds=a.get('T_seconds','unknown'),cap_seconds=a.get('cap_seconds','unknown'),
                numerical_policy='original source/return/coverage policy; raw signed gaps retained; no new tolerance',
                clock='Original endpoint-study clocks/classification retained; no certification-speedup conversion' if round_no in [122,123] else 'source T_produce/T_verify/T_total unchanged; T_cert only if qualified',
                T_produce=a.get('T_produce','unknown'),T_verify=a.get('T_verify','unknown'),T_total=a.get('T_total','unknown'),
                certificate=a.get('certificate','unknown'),T_cert=a.get('T_cert','unknown'),source_authority=path,
                source_qualification_fields_pass=eligibility,
                qualification_field_scope='original named fields only; unavailable stays unknown; no new blanket historical revalidation',
                direct_current_method_performance=bool(current and eligibility),predecessor_numbers_relabelled=False))
    if rows:
        with (OUT/'evidence_migration.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/'method_matrix.md').write_text('''# Round130 fixed method matrix

The sole proposed method is **GI-TBC (uniform pair-support implementation, MS2)**, table ID **S2**. The selected E2 `ms2` algorithm is unchanged in E3. Historical full M-B and ENS-C measurements keep their original identity. The repository default remains ENS-C; paper reproduction explicitly selects `ms2`.

| ID | Independently paid startup | Actual mathematical backend | Role |
| --- | --- | --- | --- |
| P | no H or external Start | original cold compact, one complete native MIP, defaults | sole primary benchmark |
| PS | full same H; own fully mapped and read-back Start | same original compact as P; normal nonzero path has one native MIP; no project cutoff, strengthening or root LP | same-start control |
| S2 | full same H | unchanged pair support, R, ordered supply, C_G, A/B, Gini interval control | sole paper method |
| S2R | full same H | inclusive `[0,min(U0,(n-1)/n)]`, `F_model<=U0`, pair-only strengthened root; complete LP then MIP, own full Start | outer-control package deletion control |

PS uses the existing `--round112-ens-start-compact` entry with research mode off. S2R uses exactly one `--round127-mode s2-root`; sequential conflicting old mode flags are forbidden by the frozen argv. Only the semantic interval-no-improver proof row is suppressed in S2R. Ordinary MS2 and full MD-R retain their old behavior.

All methods use one frozen E3, original DLL, original physical/numerical settings and complete 1200-second cap. H, mapping, validation, LP/MIP, output and shutdown share the deadline. P receives no other arm's solution. PS and S2R receive no extra budget. The fixed comparison types are S2/P, PS/P, S2/PS, S2/S2R and S2R/PS.

The original declared verified-zero startup scope is retained. A qualified startup-zero branch has no backend exposure and supplies no pure backend attribution. No new zero shortcut is added. Nonzero S2R requires its complete LP+MIP chain; all formal roles here have nonzero own H.

S2/PS measures the complete backend, representation and control increment after matched own H. S2/S2R measures the entire exposed outer control package only when actual H, initial scope, settings and effective root agree. S2R/PS also changes representation, preprocessing and cutoff domain; it is not a pure-cuts experiment. Splits alone do not prove a net benefit.
''',encoding='utf-8')
    print('PAPER_VERSION_ADOPTED; predecessor evidence retains original labels')
if __name__=='__main__':run()
