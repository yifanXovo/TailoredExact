"""Accepted physical/lifecycle checks; first actual Native SHA; PF/Shared-S off."""
import types
import round147_read as inherited
from round149_context import root_context
from round149_read import pf_contract
from round150_common import *


def verify(launch, identity):
    configure()
    destination = Path(launch['destination'])
    assert not (destination/'verification_closeout.json').exists(), 'Closed verification is immutable'
    command = launch['command']
    assert command.count('--round149-penalty-feedback') == 1
    assert command[command.index('--round149-penalty-feedback')+1] == 'off'
    assert all(f not in command for f in ['--round138-stock-rlt', '--round148-shared-s', '--round135-ap'])
    off = types.FunctionType(pf_contract.__code__, dict(pf_contract.__globals__, ROOT=ROOT, OUT=OUT))
    off(destination, False)
    return types.FunctionType(inherited.verify.__code__, dict(vars(inherited),
        ROOT=ROOT, OUT=OUT, configure=configure, root_context=root_context))(launch, identity)
