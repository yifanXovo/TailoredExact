"""Zero-Optimize mutation checks of confirmation's real admission functions.

Synthetic reference fingerprints and mocked external build identities keep this
fixture separate from research data. The original command generators are used.
Run only after the performance queue is idle; never invokes prepare or Optimize.
"""
import copy
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import round97_confirmation as runner

runner.ext.ensure_idle()
fixture=runner.ROOT/'tmp/round97_confirmation_guard_test02'
fixture.mkdir(exist_ok=False)


def fixture_write(path,value):
    path=Path(path)
    assert path.resolve().is_relative_to(fixture.resolve())
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


real_sha=runner.sha
roles=runner.read(runner.INPUTS)['roles']
runner.CAMP=fixture
references={role['id']:dict(fingerprint=100+i) for i,role in enumerate(roles)}
for role,reference in references.items():fixture_write(fixture/'reference'/role/'build.json',reference)


def fixture_sha(path):
    path=Path(path).resolve()
    return real_sha(path) if path.is_relative_to(fixture) else 'fixture-external-identity'


def rejects(action):
    try:action()
    except AssertionError:return
    raise AssertionError('Unsafe mutation was accepted')


frozen=dict(selected_operator='r83',candidate_binary_sha256='fixture-external-identity')
prereg=dict(candidate_binary=(runner.BUILD/'ExactEBRP.exe').relative_to(runner.ROOT).as_posix(),
    candidate_binary_sha256=frozen['candidate_binary_sha256'],common=runner.ext.COMMON)
identity=dict(source_hashes={},prereg=prereg,references=references,helper_hashes={},reference_bindings={})
for name in ('runner_sha256','auditor_sha256','prereg_sha256','input_manifest_sha256','recipe_sha256',
             'candidate_binary_sha256','dll_sha256','build_identity_sha256','reference_binary_sha256'):
    identity[name]='fixture-external-identity'
identity['launches']=runner.expected_launches(frozen,roles,references,prereg)


def save_identity(value,refresh_prepared=True):
    fixture_write(fixture/'identity.json',value)
    if refresh_prepared:
        fixture_write(fixture/'prepared_batch.json',dict(batch_sha256=real_sha(fixture/'identity.json'),
            candidate_freeze_sha256='fixture-external-identity',optimizer_calls=0))


with patch.object(runner,'sha',fixture_sha),patch.object(runner,'candidate',return_value=frozen),\
     patch.object(runner.campaign,'bindings',return_value={}):
    save_identity(identity)
    runner.identity_check(identity)
    changed=copy.deepcopy(identity)
    changed['launches'][5]['operator']='r96'
    changed['launches'][5]['command'][-1]='r96'
    save_identity(changed,refresh_prepared=False)
    rejects(lambda:runner.identity_check(changed))
    # Even replacing the prepared receipt cannot authorize a different operator.
    save_identity(changed)
    rejects(lambda:runner.identity_check(changed))
    changed=copy.deepcopy(identity)
    changed['launches'][3]['panel']['T_seconds']+=1
    save_identity(changed)
    rejects(lambda:runner.identity_check(changed))
    save_identity(identity)
    runner.identity_check(identity)
    queue=fixture/'queue_C1';queue.mkdir()
    batch_sha=real_sha(fixture/'identity.json')
    fixture_write(queue/'identity.json',dict(batch_sha256=batch_sha))
    evidence=fixture/'prior_audit.json';fixture_write(evidence,dict(passed=True))
    consistency=dict(passed=True,optimizer_calls=0,batch_sha256=batch_sha,
        evidence_bindings={evidence.relative_to(runner.ROOT).as_posix():real_sha(evidence)})
    fixture_write(queue/'cross_arm_consistency.json',consistency)
    status=dict(phase='role_complete_requires_root_analysis',role='C1',completed_prefix=3,
        consistency_sha256=real_sha(queue/'cross_arm_consistency.json'))

    def save_status(value):
        fixture_write(queue/'status.json',value)
        (queue/'events.jsonl').write_text(json.dumps(value)+'\n',encoding='utf-8')

    save_status(status)
    runner.completed_roles(identity,'C2')
    save_status(dict(phase='stopped_failure_no_restart',error='cross-arm contradiction'))
    # Actual run_role must reject before prefix processing or solver dispatch.
    with patch.object(runner.r90,'run_one',side_effect=AssertionError('must not dispatch')) as dispatch:
        rejects(lambda:runner.run_role('C2'))
        assert dispatch.call_count==0
    save_status(status)
    fixture_write(evidence,dict(passed=False))
    rejects(lambda:runner.completed_roles(identity,'C2'))

print('Confirmation admission rejected changed operator, command, panel, batch and failed predecessor; Optimize=0')
