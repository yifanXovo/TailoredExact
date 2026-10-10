"""Bounded current E14 context and P15 signed proof review; zero native."""
from pathlib import Path
import hashlib, json, sys, time
from round110_independent_core import Audit, ROUND

root = Path(sys.argv[1]).resolve()
dest = root/ROUND/'review/current_cold15_context01'
dest.mkdir(exist_ok=False)
source = Path(__file__).read_bytes()
(dest/'source_at_execution.py').write_bytes(source)
start = time.perf_counter()
def save(name, value):
    with (dest/name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')
save('launch.json', dict(argv=[sys.executable, *sys.argv], cwd=str(Path.cwd()),
                        source_SHA=hashlib.sha256(source).hexdigest(), Optimize=0, native_environment=0))
campaign_path = root/ROUND/'campaign/identity.json'
campaign = json.loads(campaign_path.read_text(encoding='utf-8-sig'))
a = Audit(root, dest, campaign['candidate_binary_sha256'])
admission = a.obj(a.out/'review/performance_admission.json')
a.require(admission['decision'] == 'ACCEPT' and admission['campaign_identity_SHA'] == a.sha(campaign_path),
          'actual pause retains previously admitted exact current campaign')
a.require(a.sha(a.local(campaign['prereg']['candidate_binary'])) == admission['production_PE_SHA'],
          'actual current PE bytes unchanged')
a.require(all(not a.local(l['destination']).exists() for l in campaign['launches'][15:]),
          'no formal arm16 or later started before explicit current-proof admission')
launch = campaign['launches'][13]
a.require((launch['number'], launch['id'], launch['arm'], launch['seed']) == (14, 'G50-C1', 'ENS-C', 0),
          'current E14 cross-arm diagnostic context')
arm, models, q = a.arm(launch, campaign, True)
a.require(arm['U'] == arm['L'] == arm['physical']['G'] == arm['physical']['P'] == 0 and arm['certificate'],
          'current E14 own complete physical exact zero independently certified')
a.require([record['solve_kind'] for record in arm['native_records']] == ['LP', 'LP', 'LP', 'MIP'],
          'current ENS three LP plus one terminal MIP mechanism retained')
proof_path = a.out/'review/current_cold15_01/audit.json'
proof = a.obj(proof_path)
a.require(proof['decision'] == 'ACCEPT_CURRENT_CALL_REJECTION' and
          proof['current_key'] == [15, 'G50-C1', 0, 'P-GRB'] and proof['own_U'] > 0 and
          not proof['certificate_from_own_exact_zero'] and proof['complete_seconds'] is None,
          'current P15 proof retains own positive open U and missing exact whole clock')
value = dict(decision='ACCEPT_CURRENT_P15_CONTEXT', current_E14=arm,
             current_P15_proof_SHA=a.sha(proof_path), current_P15_own_U=proof['own_U'],
             current_P15_qualified_L=0., current_P15_certificate=False,
             complete_seconds=None, complete_seconds_interval=proof['complete_seconds_interval'],
             no_cross_arm_UB_Start_or_search_transfer=True,
             E14_used_only_to_explain_detected_contradiction=True,
             source_SHA=hashlib.sha256(source).hexdigest(), read_bindings=a.reads,
             module_bindings=a.module_bindings, completed_checks=a.checks,
             Optimize=0, native_environment=0)
save('audit.json', value)
save('receipt.json', dict(exit_code=0, engineering_elapsed_seconds=time.perf_counter()-start,
                         source_SHA=hashlib.sha256(source).hexdigest(), audit_SHA=a.sha(dest/'audit.json'),
                         Optimize=0, native_environment=0))
print(json.dumps(dict(decision=value['decision'], completed_checks=a.checks,
                      current_P15_proof_SHA=value['current_P15_proof_SHA'])))
