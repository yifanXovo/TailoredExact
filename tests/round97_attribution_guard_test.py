"""Exercise manifest mutation between queue admission and dispatch, without Optimize."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import round97_operator_attribution as runner

runner.ext.ensure_idle()
fixture=runner.ROOT/'tmp/round97_attribution_guard_test01'
fixture.mkdir(exist_ok=False)
identity=dict(launches=[dict(number=1,id='fixture',arm='OLD-FEEDBACK',
                            destination=str(fixture/'must_not_launch'))])
runner.write(fixture/'identity.json',identity)
runner.CAMP=fixture
runner.check=lambda value: None
runner.prefix=lambda value,count: []
original_write=runner.write
calls=[]


def mutate_after_queue_freeze(path,value):
    original_write(path,value)
    if Path(path)==fixture/'queue/identity.json':
        changed=dict(identity,mutation='changed after queue freeze')
        (fixture/'identity.json').write_text(json.dumps(changed),encoding='utf-8')


def forbidden_dispatch(*args):
    calls.append(args)
    raise RuntimeError('Dispatcher reached despite changed manifest')


runner.write=mutate_after_queue_freeze
runner.campaign.run=forbidden_dispatch
try:
    runner.run_all()
except AssertionError as error:
    assert 'batch changed after queue freeze' in str(error)
else:
    raise AssertionError('Mutated manifest was accepted')
assert calls==[]
assert runner.read(fixture/'queue/status.json')['phase']=='stopped_failure_no_restart'
print('Actual queue rejected changed manifest before dispatcher; original experiment files untouched; Optimize=0')
