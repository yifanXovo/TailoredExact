"""Declared finite current-production qualification; never touches sealed inputs with Optimize."""
from round108_common import *
import round108_campaign as campaign
import round108_native_inspect as inspect
from round100_idle import ensure_idle

def prepare():
    ensure_idle()
    d=OUT/'qualification';d.mkdir(exist_ok=False)
    plan=dict(production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),DLL_SHA=sha(DLL),source_bindings=bindings(),
        declarations='R100 implicit-integrality/all-quantity guards; exact F2 frozen-scope native matrix load; no LP reoptimization',
        diagnostic_F2=dict(input_path='reference/round86_unadapted_confirmation/F2.txt',gamma_L=0,
            gamma_U=.8853483009345782,cutoff=.8853483009345782,scope='diagnostic-only old legal U, never formal Start'),
        CLI_primary='known H100 P, ENS-C, M-B, cap120 each; original full argv/startup',
        CLI_fallback='only if primary startup avoids actual original MIP: preregistered F2 ENS-C/M-B cap120 each',
        confirmation_inputs_never_qualification=True,
        conservative_preparation_children=10,declared_CLI_children_max=5,maximum_CLI_nominal_seconds=600,
        no_performance_interpretation=True,Optimize_calls_in_this_preparation=0)
    write(d/'plan.json',plan)
    subprocess.run([str(BUILD/'Round100QuantityTests.exe'),str(d/'quantity_guards')],cwd=ROOT,env=env(),check=True,timeout=30)
    subprocess.run(list(map(str,[BUILD/'Round100ModelExport.exe','reference/round86_unadapted_confirmation/F2.txt',
        3600,60,60,.15,0,.8853483009345782,.8853483009345782,d/'fixed_F2_models'])),cwd=ROOT,env=env(),check=True,timeout=60)
    matrix=inspect.matrix(d/'fixed_F2_models')
    h=dict(read(ROOT/'results/unified_exact_round100/holdout_protocol01.json')['roles'][0])
    h.update(cap_seconds=120,method_order=['P-GRB','ENS-C','M-B'],role_identity='known_qualification_only')
    write(d/'CLI_protocol.json',dict(roles=[h],functional_only=True,per_arm_cap=120,fallback_F2_registered=True))
    campaign.prepare('qualification/cli01',d/'CLI_protocol.json')
    campaign.prepare('bridge01',OUT/'development_protocol.json')
    campaign.prepare('confirmation01',OUT/'confirmation_protocol.json')
    write(d/'preparation.json',dict(passed=True,source_bindings=bindings(),production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),
        DLL_SHA=sha(DLL),fixture_PE_SHA=sha(BUILD/'Round100QuantityTests.exe'),
        exporter_PE_SHA=sha(BUILD/'Round100ModelExport.exe'),reference_PE_SHA=sha(BUILD/'Round65ReferenceBuild.exe'),
        helper_bindings=campaign.helpers(),native_matrix=matrix,Optimize_calls=0,
        planned_actual_reference_children=8,planned_quantity_guard_children=1,planned_export_children=1))
    print('zero-solve preparation passed; actual reference children=8; other writer children=2',flush=True)

def cli():
    ensure_idle()
    records=[]
    for n in range(1,4):records.append(campaign.run('qualification/cli01',n,True))
    mids=[r for r in records if r['arm'] in ['ENS-C','M-B']]
    reached=all(read(Path(r['destination'])/'result.json').get('external_gini_tree_mip_count',
        read(Path(r['destination'])/'result.json').get('external_gini_tree_terminal_mip_calls',0))>0 for r in mids)
    # The durable original Optimize ledger is authoritative for actual backend reach.
    import csv
    actual=[]
    for r in mids:
        ledger=Path(r['destination'])/'external/paper_optimize_ledger.csv'
        with ledger.open(newline='') as f:rr=list(csv.DictReader(f))
        actual.append(any(x['solve_kind']!='LP' for x in rr))
    reached=all(actual)
    fallback=[]
    if not reached:
        p=dict(read(OUT/'input_manifest.json')['roles'][0]);p.update(cap_seconds=120,method_order=['ENS-C','M-B'])
        write(OUT/'qualification/F2_fallback_protocol.json',dict(roles=[p],functional_only=True,preregistered=True))
        # Reuse the already-paid identical actual F2 reference; no additional builder process.
        camp=OUT/'qualification/fallback01';camp.mkdir(exist_ok=False)
        q=read(OUT/'bridge01/identity.json');launches=[]
        for arm in p['method_order']:
            src=next(x for x in q['launches'] if x['id']=='F2' and x['arm']==arm)
            item=dict(src['panel']);item.update(cap_seconds=120,method_order=p['method_order'])
            d=camp/'raw'/f'{len(launches)+1:02d}_F2_{arm}'
            cmd=campaign.r90.command_for(q['prereg'],item,'ENS-C',d)
            if arm=='M-B':cmd+=['--round98-state-service','m-binary']
            launches.append(dict(src,number=len(launches)+1,panel=item,destination=str(d),stage='functional_fallback',
                cap_seconds=120,hard_stop_seconds=118,command=cmd))
        q.update(launches=launches,prereg_sha256=sha(OUT/'qualification/F2_fallback_protocol.json'),
                 protocol_path=str(OUT/'qualification/F2_fallback_protocol.json'))
        write(camp/'identity.json',q)
        for n in range(1,3):fallback.append(campaign.run('qualification/fallback01',n,True))
    write(OUT/'qualification/identity.json',dict(passed=all(r['audit_passed'] for r in records+fallback),
        actual_production_CLI=True,production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),DLL_SHA=sha(DLL),source_bindings=bindings(),
        preparation_SHA=sha(OUT/'qualification/preparation.json'),primary_identity_SHA=sha(OUT/'qualification/cli01/identity.json'),
        primary_actual_MIP_reached=actual,fallback_triggered=not reached,
        complete_legal_terminations=len(records+fallback),certified_qualifications=sum(bool(r['endpoint']['certificate']) for r in records+fallback),
        qualified_argv=[read(Path(r['destination'])/'launch.json')['command'] for r in records+fallback],
        current_CLI_records=records+fallback,not_performance=True))
    print('actual CLI qualification identity saved',flush=True)

if __name__=='__main__':{'prepare':prepare,'cli':cli}[sys.argv[1]]()
