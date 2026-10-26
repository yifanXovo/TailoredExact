"""One positive-objective D2 unit fixture, not a new performance input.

prepare writes only input/oracle/argv/identity metadata. run can launch only
inside the primary agent's D/repair meter after independent small admission
and a frozen D1 matrix. It reuses the full original producer and current reader.
No native or test is started at import. No C result, incumbent or cache is read.
"""
from fractions import Fraction as F
from round133_common import *
import collections, copy
import round133_campaign as campaign
import round133_read as current_reader

NAME='small_native01'
FIXTURE=OUT/'qualification'/NAME
MANIFEST=FIXTURE/'fixture_manifest.json'
GATE=OUT/'review/D2_small_native_admission.json'
CAP=45
INPUT_TEXT='''2 1 [1]
capacities = [100000,2,2]
initial = [50000,1,0]
target = [0,1,1]
weights = [0,1,1]
min_ratio = [0,0,0]
points = [(0,0),(0,0),(0,0)]
'''

def inventory_oracle():
    """Independent exact inventory relaxation and its attainable no-op bound."""
    records=[]
    # Empty departure/loaded return give tau=1-R, R in[0,1]. This
    # supersets every original route inventory; no service oracle is assumed.
    for y0 in range(3):
        for y1 in range(3):
            tau=y0+y1
            if tau>1:continue
            g=F(abs(y0-y1),2*tau) if tau else F(0)
            penalty=abs(y0-1)+abs(y1-1)
            records.append(dict(Y=[y0,y1],tau=tau,G=str(g),P=penalty,F=str(g+penalty)))
    optimum=min(F(row['F']) for row in records)
    assert optimum==F(3,2)
    return dict(schema='round133-D2-two-station-independent-inventory-oracle-v1',
        initial=[1,0],targets=[1,1],capacities=[2,2],weights=[1,1],Q=[1],lambda_value='1',
        original_integer_inventories=records,possible_total_inventory=[0,1],
        exact_original_optimum=str(optimum),attaining_no_op_inventory=[1,0],
        no_op_route_duration_seconds=0,loaded_return_inventory=[0,0],
        loaded_return_route_duration_seconds=120,loaded_return_objective='2',
        physical_horizon_seconds=240,positive_min_ratio_imposed=False,
        root_relaxation_inventory=[str(F(1,2)),str(F(1,2))],
        root_relaxation_objective_candidate='1',
        independent_no_op_upper_and_inventory_lower_match=True,
        Optimize=0,enumerated_inventory_vectors=len(records),
        new_performance_inputs=0,not_lambda_sensitivity=True,
        not_supplied_as_Start_incumbent_cutoff_bound_or_cache=True)

def _set(command,flag,value):
    assert command.count(flag)==1,(flag,'missing/duplicate inherited flag')
    command[command.index(flag)+1]=str(value)

def prepare(candidate_path,d1_matrix=None):
    """Pure one-time preparation; no reference exporter or native dependency."""
    candidate_path=Path(candidate_path)
    d1_matrix=Path(d1_matrix or OUT/'plans/D1_matrix_frozen.json')
    assert d1_matrix.is_file(),'freeze D1 before admitting this unit fixture'
    matrix=read(d1_matrix);candidate=campaign._candidate(candidate_path)
    assert matrix['stage']=='D1' and matrix['full_arm_count']==14 and matrix['full_arm_cap_sum_seconds']==15600
    assert matrix['candidate_manifest_SHA']==sha(candidate_path)
    template=next(group for group in matrix['groups'] if group['launch']['id']=='K-15-S'
                  and group['launch']['method']=='S2' and group['launch']['seed']==1)
    source=template['launch']
    assert source['version']=='candidate' and source['command'][source['command'].index('--round127-mode')+1]=='ms2'
    assert not FIXTURE.exists(),'unit preparation/evidence is immutable; inspect an existing attempt'
    FIXTURE.mkdir(parents=True,exist_ok=False)
    inp=FIXTURE/'input.txt';inp.write_text(INPUT_TEXT,encoding='utf-8',newline='\n')
    destination=FIXTURE/'raw'/'01_D2_TWO_STATION_S1_S2'
    command=[arg.replace(source['destination'],str(destination)) for arg in source['command']]
    command[0]=candidate['production_PE']
    for flag,value in (('--input',inp),('--lambda',1),('--T',240),('--pickup-time',60),('--drop-time',60),
                       ('--time-limit',39),('--process-wall-time-limit',45),('--process-shutdown-margin',30),
                       ('--gurobi-seed',1),('--threads',1),('--mip-threads',1)):
        _set(command,flag,value)
    assert command[command.index('--round127-mode')+1]=='ms2'
    assert '--round112-ens-start-compact' not in command and '--round132-expression' not in command
    panel=dict(id='D2-TWO-STATION-POSITIVE',layer='D2 semantic unit fixture',source='mathematical correctness fixture',
        V=2,M=1,inventory='shortage',geometry='coincident',Q_vector=[1],T_seconds=240,cap_seconds=CAP,
        pickup_seconds=60,drop_seconds=60,**{'lambda':1.},gurobi_seed=1,
        input_path=str(inp),instance_path=str(inp),input_sha256=sha(inp),input_bytes=inp.stat().st_size,
        panel_kind='Round133_D2_semantic_unit_fixture',total_initial=1,total_target=2,total_capacity=4,
        Omega=2,rho=2,new_performance_input=False,
        reference=dict(optimizer_calls=0,full_original_compact_reference_not_applicable=True,
            reason='S2 interval calls are checked against their own complete actual models; no reference Optimize/export'))
    expected=copy.deepcopy(source['expected_configuration']);expected.update(gurobi_seed=1,requested_native_seed=1)
    launch=dict(number=1,group_number=0,global_launch_number=0,id=panel['id'],arm='M-B',method='S2',seed=1,repeat=1,
        binary_layer='Round133-production',version='candidate',panel=panel,panel_kind=panel['panel_kind'],
        destination=str(destination),cap_seconds=CAP,hard_stop_seconds=43,command=command,
        configuration=copy.deepcopy(expected['configuration']),expected_configuration=expected,
        arm_id='D2_TWO_STATION_S1_S2',formal_performance=False)
    source_identity=read(OUT/template['group']/'identity.json')
    assert sha(OUT/template['group']/'identity.json')==template['identity_SHA']
    assert source_identity['launches']==[source]
    common=copy.deepcopy(source_identity['prereg']['common']);common['gurobi_seed']=1
    oracle=inventory_oracle();write(FIXTURE/'inventory_oracle.json',oracle)
    protocol=dict(schema='round133-D2-one-unit-protocol-v1',UTC=utc(),launch=launch,
        source_K15_template_group=template['group'],source_template_identity_SHA=template['identity_SHA'],
        registered_changes=['two-station mathematical unit input','lambda1 positive semantic fixture',
            'physical horizon240','own45-second complete cap/native39/hard43','own raw paths'],
        original_H_and_Start_semantics_unchanged=True,no_C_information=True,
        no_old_solution_Start_or_bound=True,independent_oracle_SHA=sha(FIXTURE/'inventory_oracle.json'),
        not_performance=True,not_lambda_sensitivity=True,D14_positions_unchanged=True,D3_positions_unchanged=True,
        force_split_NEXT_or_extra_Optimize=False,Optimize=0)
    write(FIXTURE/'protocol.json',protocol)
    identity=dict(schema='round133-own-complete-lifecycle-v1',prereg=dict(common=common,
        candidate_binary=candidate['production_PE'],candidate_binary_sha256=candidate['production_PE_SHA']),
        prereg_sha256=sha(FIXTURE/'protocol.json'),runner_sha256=sha(__file__),source_hashes=candidate['source_hashes'],
        candidate_binary_sha256=candidate['production_PE_SHA'],dll_sha256=DLL_SHA,
        measured_source_commit=candidate['source_commit'],delivery_base_commit=BASE,launches=[launch],
        references={panel['id']:panel['reference']},candidate_manifest_path=str(candidate_path),
        candidate_manifest_SHA=sha(candidate_path),no_cross_arm_information=True,raw_schema=1,stage='D2-unit')
    write(FIXTURE/'identity.json',identity)
    manifest=dict(schema='round133-D2-single-native-fixture-v1',UTC=utc(),fixture=NAME,
        protocol_SHA=sha(FIXTURE/'protocol.json'),identity_SHA=sha(FIXTURE/'identity.json'),
        input_SHA=sha(inp),oracle_SHA=sha(FIXTURE/'inventory_oracle.json'),
        candidate_manifest_path=str(candidate_path),candidate_manifest_SHA=sha(candidate_path),
        D1_matrix_path=str(d1_matrix),D1_matrix_SHA=sha(d1_matrix),
        helpers=campaign.helper_bindings(),complete_process_cap_seconds=CAP,
        native_processes=1,threads=1,native_serial=True,budget_category='D2 within D18000',
        formal_performance=False,new_performance_inputs=0,D14_unchanged=True,D3_unchanged=True,
        expected_positive_optimum='3/2',requested_native_seed=1,Optimize=0)
    write(MANIFEST,manifest)
    print(json.dumps(dict(prepared=str(MANIFEST),SHA=sha(MANIFEST),cap=CAP,Optimize=0)),flush=True)
    return manifest

def admission():
    manifest=read(MANIFEST);gate=read(GATE)
    assert gate['decision']=='ACCEPT' and gate['fixture_manifest_SHA']==sha(MANIFEST)
    assert gate['candidate_manifest_SHA']==manifest['candidate_manifest_SHA']
    assert gate['D1_matrix_SHA']==manifest['D1_matrix_SHA']
    assert sha(manifest['candidate_manifest_path'])==manifest['candidate_manifest_SHA']
    assert sha(manifest['D1_matrix_path'])==manifest['D1_matrix_SHA']
    campaign._candidate(manifest['candidate_manifest_path'])
    assert sha(FIXTURE/'protocol.json')==manifest['protocol_SHA']
    assert sha(FIXTURE/'identity.json')==manifest['identity_SHA']
    assert sha(FIXTURE/'input.txt')==manifest['input_SHA'] and sha(FIXTURE/'inventory_oracle.json')==manifest['oracle_SHA']
    for name,digest in manifest['helpers'].items():assert sha(ROOT/name)==digest,name
    return manifest

def run():
    """Primary-agent meter only; no nested meter, automatic retry or new probe."""
    manifest=admission()
    label=os.environ.get('ROUND133_METERED_PARENT_LABEL')
    assert label,'run must be launched by the primary agent through round133_common.metered'
    meter=read(OUT/'fees'/label/'launch.json')
    assert meter['kind'] in ('D','repair') and meter['reservation_seconds']>=CAP
    identity=read(FIXTURE/'identity.json');launch=identity['launches'][0];d=Path(launch['destination'])
    assert not d.exists(),'started or sealed unit fixture is immutable; inspect/analyze it, never auto-rerun'
    tick,creation=campaign.inherited.process_origin()
    campaign.supervised(launch,identity,tick)
    campaign.finish_producer(launch,tick,creation)
    started=time.perf_counter()
    try:value=current_reader.verify(launch,identity)
    finally:
        write(OUT/'cost_segments'/label/'D2_unit_verification.json',dict(
            kind='non-native postproduction D2 unit audit, including retained failures',
            seconds=time.perf_counter()-started,native_Optimize=0))
    write(FIXTURE/'run_receipt.json',dict(UTC=utc(),fixture_manifest_SHA=sha(MANIFEST),
        endpoint_SHA=sha(d/'round133_endpoint.json'),producer_receipt_SHA=sha(d/'producer_receipt.json'),
        verification_closeout_SHA=sha(d/'verification_closeout.json'),meter_label=label,
        native_reentry=False,not_performance=True))
    print(json.dumps(dict(unit=NAME,endpoint=value['arm'],not_performance=True)),flush=True)
    return value

def analyze():
    """Read the one sealed fixture and compare with the preregistered oracle."""
    manifest=read(MANIFEST);identity=read(FIXTURE/'identity.json');launch=identity['launches'][0]
    d=Path(launch['destination']);oracle=read(FIXTURE/'inventory_oracle.json')
    assert oracle==inventory_oracle() and sha(FIXTURE/'inventory_oracle.json')==manifest['oracle_SHA']
    arm=read(d/'round133_endpoint.json');close=read(d/'verification_closeout.json')
    assert close['implementation_qualified'] and arm['implementation_qualified']
    assert arm['audit_SHA']==close['audit_SHA']==sha(d/'audit.json')
    assert arm['verification_closeout_SHA']==sha(d/'verification_closeout.json')
    assert arm['arm_total_receipt_SHA']==sha(d/'arm_total_receipt.json')
    optimum=F(oracle['exact_original_optimum'])
    assert arm['L']<=float(optimum)+1e-7,'qualified lower bound contradicted by exact original unit optimum'
    assert abs(arm['U']-float(optimum))<=1e-7,'own H must retain the no-op optimum on this unit input'
    assert arm['T_produce']<=CAP
    assert arm['T_cert'] is None or arm['certificate']
    controller=current_reader.core.evidence.controller_tables(d,read(d/'result.json'))
    native=controller['controller_native'];kinds=collections.Counter(row['solve_kind'] for row in native)
    # These independent postproduction witnesses test loaded-return and S=0;
    # neither is passed to the solver or to any formal D/D3 arm.
    witnesses=[dict(objective=1.5,routes=[dict(vehicle=0,nodes=[0,0],operations=[])]),
        dict(objective=2.,routes=[dict(vehicle=0,nodes=[0,1,0],operations=[dict(station=1,pickup=1,drop=0)])])]
    physical=[current_reader.core.full_fleet(ROOT,launch['panel'],w) for w in witnesses]
    assert physical[0]['F']==1.5 and physical[1]['F']==2 and physical[1]['G']==0
    assert physical[1]['return_loads']==[1] and physical[1]['maximum_duration']==120
    result=dict(schema='round133-D2-one-unit-analysis-v1',UTC=utc(),fixture_manifest_SHA=sha(MANIFEST),
        passed=True,implementation_qualified=True,exact_independent_original_optimum=str(optimum),
        own_U=arm['U'],qualified_L=arm['L'],signed_gap=arm['U']-arm['L'],certificate=arm['certificate'],
        native_source_qualified=arm['native_proof_qualified'],performance_evidence_eligible=False,
        source_rejection_handling_observed=arm['source_reduced'],
        normal_positive_certificate_observed=bool(arm['certificate'] and arm['L']>0),
        LP_calls=kinds['LP'],MIP_calls=sum(v for k,v in kinds.items() if k!='LP'),
        MIP_exposed=any(row['solve_kind']!='LP' for row in native),
        actual_solve_kind_counts=dict(kinds),
        actual_splits=sum(row['event']=='atomic_split' for row in controller['controller_events']),
        actual_target_or_NEXT_calls=[row['solve_kind'] for row in native if 'TARGET' in row['solve_kind']],
        actual_LP_status=controller['controller_LP_status'],
        no_MIP_does_not_trigger_extra_probe=True,force_split_or_NEXT=False,
        independent_no_op_loaded_return_S0_checks=physical,
        T_produce=arm['T_produce'],T_verify=arm['T_verify'],T_total=arm['T_total'],T_cert=arm['T_cert'],
        cost_scope='the single 45s complete D2 process cap; nested H/LP/MIP not added; verification separately recorded',
        not_performance=True,new_performance_inputs=0,D14_positions_unchanged=True,D3_positions_unchanged=True,
        no_C_evidence_or_cross_arm_solution_transferred=True,extra_Optimize=0)
    write(FIXTURE/'analysis.json',result)
    print(json.dumps({k:result[k] for k in ('passed','own_U','qualified_L','certificate','LP_calls','MIP_calls','MIP_exposed','not_performance')}),flush=True)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--candidate-manifest',type=Path,required=True);prep.add_argument('--D1-matrix',type=Path)
    sub.add_parser('run');sub.add_parser('analyze')
    args=parser.parse_args()
    if args.action=='prepare':prepare(args.candidate_manifest,args.D1_matrix)
    elif args.action=='run':run()
    else:analyze()
