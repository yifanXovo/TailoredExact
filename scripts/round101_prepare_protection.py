"""Archive qualified final source and preregister a fresh F2 three-arm group.
No Optimize; the ordinary campaign prepares and bills its fresh P reference.
"""
import shutil,subprocess
from round100_idle import ensure_idle
from round101_budget import account
from round101_common import *

if __name__=='__main__':
    ensure_idle();guard=read(OUT/'numeric_guard_revision.json')
    assert guard['after_source_hashes']==bindings()
    for label in ['pure05','numeric_replay01','matrix_guards01']:
        assert read(OUT/'qualification'/label/'receipt.json')['exit_code']==0
    assert read(OUT/'diagnostics/numeric_replay01/summary.json')['source_hashes']==bindings()
    assert read(OUT/'diagnostics/matrix_guards01/summary.json')['passed']
    budget=account();assert not budget['reserved'] and budget['within_limits']
    assert budget['remaining_after_current_plan_seconds']>=54000+3600+600
    stage=OUT/'builds/final_numeric_guards';stage.mkdir(exist_ok=False)
    files=['ExactEBRP.exe','Round101FleetDiagnostic.exe','Round101FleetTests.exe','Round65ReferenceBuild.exe']
    for filename in files:shutil.copy2(BUILD/filename,stage/filename)
    write(stage/'manifest.json',dict(source_hashes=bindings(),
        tests_sha256=sha(ROOT/'tests/round101_fleet_tests.cpp'),
        binary_sha256={f:sha(stage/f) for f in files},
        dll_sha256=sha('D:/gurobi1302/win64/bin/gurobi130.dll'),native_version='13.0.2',
        source_delivery_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        numeric_guard_revision_sha256=sha(OUT/'numeric_guard_revision.json'),
        build_receipt_sha256=sha(OUT/'engineering/build06/receipt.json'),
        frozen_for='Fresh F2 final-source protection followed by uniform candidate freeze and confirmation/long windows'))
    fleet=read(OUT/'development_protocol01.json')['fleet_arm']
    p=dict(read(OUT/'development_inputs.json')['roles'][0]);assert p['id']=='F2'
    p['cap_seconds']=1200;p['method_order']=['P-GRB','ENS-C',fleet]
    write(OUT/'protection_protocol01.json',dict(roles=[p],phase='fleet development',
        reference_billing='one_finite_batch',maximum_optimize_calls_per_arm=2048,
        planning_call_envelope_not_production_gate=True,maximum_formal_starts=3,maximum_formal_seconds=3600,
        archived_build_manifest_sha256=sha(stage/'manifest.json'),
        question='Final-source guard repair protection; fresh P/ENS/uniform ROOT under common1200 cap. Keep prior build05 results under their original identities; no guard benefit attributed to cuts.',
        future_long_and_confirmation_reserve_seconds=54000))
    print(json.dumps(dict(archived=True,fleet=fleet,formal_starts=3,formal_cap_seconds=3600,Optimize=0)))
