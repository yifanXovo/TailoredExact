"""R154 proof-only consumer audit with an explicit uniform producer identity."""
import inspect,types
import round153_read as old
import round154_read as reader
from round156_common import *

def floor_contract(destination,enabled,launch,identity):
    # Old E/B continue through the exact old contract. Eplus changes only
    # the allowed node capacity and the bound helper entry, not its algebra.
    floor_source=inspect.getsource(old.floor_contract)
    entry=identity.get('inventory_helper_entry','scripts/round153_online.py')
    nodes=identity.get('inventory_node_limit',4096)
    assert (entry,nodes) in [('scripts/round153_online.py',4096),('scripts/round156_online.py',16384)]
    assert launch.get('R156_method','E')!='Eplus' or nodes==16384
    if nodes==16384:
        assert floor_source.count('==4096')==3
        floor_source=floor_source.replace('==4096','==16384')
        floor_source=floor_source.replace("deps['scripts/round153_online.py']","deps['scripts/round156_online.py']")
    # R154's proof-placement amendment is applied to this explicit producer
    # contract. No old module/file is patched and original callers retain 4096.
    source=inspect.getsource(reader.floor_contract)
    needle='source=inspect.getsource(old.floor_contract)';assert source.count(needle)==1
    source=source.replace(needle,'source=_producer_floor_source')
    ns=dict(vars(reader),ROOT=ROOT,OUT=OUT,_producer_floor_source=floor_source)
    exec(compile(source,__file__+'::producer_floor_contract','exec'),ns)
    value=ns['floor_contract'](destination,enabled,launch,identity)
    if enabled:
        parameters=read(destination/'round153_parameters.json')
        assert parameters['node_limit']==nodes
        meta=value.get('root')
        if meta:
            assert meta['node_limit']==nodes
            if nodes==16384:
                assert meta['producer_rule']==parameters['producer_rule']=='RN16384_original_gap'
                if meta['qualified']:
                    helper=destination/'external/round153_floor'
                    assert read(helper/'source.json')['producer_rule']==read(helper/'result.json')['producer_rule']=='RN16384_original_gap'
                    fields=(helper/'response.txt').read_text(encoding='ascii').split()
                    assert fields[0]=='R156-FLOOR-v1' and len(fields)==7 and int(fields[-1])==16384
    return value

def verify(launch,identity):
    fn=types.FunctionType(reader.verify.__code__,dict(vars(reader),ROOT=ROOT,OUT=OUT,configure=configure,floor_contract=floor_contract))
    value=fn(launch,identity)
    value['arm'].update(R156_method=launch['R156_method'])
    write(Path(launch['destination'])/'round156_endpoint.json',value['arm'])
    return value
