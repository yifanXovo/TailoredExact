"""Read-only initial admission of the real frozen confirmation; zero Optimize."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import round97_confirmation as runner

runner.ext.ensure_idle()
identity=runner.read(runner.CAMP/'identity.json')
runner.identity_check(identity)
assert runner.prefix(identity,0)==[]
runner.completed_roles(identity,'C1')
assert runner.read(runner.FREEZE)['selected_operator']=='r83'
assert identity['optimizer_calls_in_preparation']==0
assert len(identity['launches'])==9 and sum(r['cap_seconds'] for r in identity['launches'])==18900
for launch in identity['launches']:
    assert not Path(launch['destination']).exists()
    panel=launch['panel'];command=launch['command']
    assert runner.sha(runner.ROOT/panel['input_path'])==panel['input_sha256']
    reference=runner.CAMP/'reference'/launch['id']
    built=runner.read(reference/'build.json')
    assert built['optimizer_calls']==0 and built['canonical_sha256']==runner.sha(reference/'original.lp')
    assert runner.read(reference/'completion.json')['returncode']==0
    if launch['arm']=='P-GRB':
        assert '--plain-baseline' in command
        assert '--algorithm-preset' not in command and '--round97-native-closure' not in command
        assert command[command.index('--round24-expected-gurobi-model-fingerprint')+1]==str(built['fingerprint'])
    else:
        assert launch['operator']=='r83'
        assert command[command.index('--round97-native-closure')+1]==('feedback' if launch['arm']=='FEEDBACK' else 'observe')
    for option,value in [('--threads','1'),('--mip-threads','1'),('--gurobi-seed','0'),('--gurobi-presolve','-1')]:
        assert command[command.index(option)+1]==value
print('Actual frozen nine-arm confirmation identity, zero-Optimize original references, P isolation, uniform candidate, inputs and original settings passed; no arm launched.')
