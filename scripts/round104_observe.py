"""Finite, charged original-ENS observations. No cut selection or submission."""
from round104_common import *
import round103_campaign as inherited

def prepare(name,cap):
    from round100_idle import ensure_idle
    ensure_idle()
    inherited.OUT=OUT; inherited.BUILD=BUILD
    original=inherited.r90.command_for
    def observed(prereg,p,arm,dest):
        command=original(prereg,p,arm,dest)
        return command+['--round104-observe-native','true']
    inherited.r90.command_for=observed
    roles={r['id']:r for r in read(PRIOR/'development_inputs.json')['roles']}
    items=[]
    for id in ['F2','R98-C2','F5']:
        p=dict(roles[id]);p.update(cap_seconds=cap,method_order=['ENS-C'],
            question='read-only first/last observable native root and positive-node vectors on original ENS')
        items.append(p)
    path=OUT/(name+'_protocol.json')
    write(path,dict(roles=items,phase='hull qualification',reference_billing='one_finite_batch',
        observer=True,observer_helper_sha256=sha(__file__),native_sampling_no_cuts=True,
        root_status_interpretation='last observable root only; inherited completion label not all-native-cuts claim'))
    inherited.prepare(name,path)

if __name__=='__main__':
    name=sys.argv[2]
    inherited.OUT=OUT; inherited.BUILD=BUILD
    if sys.argv[1]=='prepare':prepare(name,float(sys.argv[3]))
    elif sys.argv[1]=='run':inherited.run(name,int(sys.argv[3]))
    else:raise ValueError(sys.argv[1])
