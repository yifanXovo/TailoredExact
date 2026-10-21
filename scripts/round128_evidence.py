"""Use the established full physical/model/Start/source/return/cover reader."""
from round128_common import *
import round127_evidence as inherited
import types,contextlib,inspect
import round108_reader as core

def is_mdr(d):
    identity=read(d.parents[1]/'identity.json')
    return next(l for l in identity['launches'] if core.portable(ROOT,l['destination'])==d)['method']=='MD-R'

@contextlib.contextmanager
def extension():
    # Only preformal E1 bridge arms can read the unchanged parent source tree.
    # Every E2 formal arm binds the actual current source bytes as usual.
    namespace=inherited.qualify_seed.__globals__;old=namespace['source_path']
    def source_path(root,l,identity,name):
        p=Path(root)/name
        if sha(p)==identity['source_hashes'][name]:return p
        assert l['binary_layer']=='E1' and 'qualification' in str(l['destination'])
        p=PREVIOUS/name;assert sha(p)==identity['source_hashes'][name];return p
    namespace['source_path']=source_path
    try:
        with inherited.extension():
            old_cover,old_endpoint=core.complete_cover,core.endpoint
            def complete_cover(d,U,j,controller,gmax):
                result=old_cover(d,U,j,controller,gmax)
                if is_mdr(d):
                    leaves=result['leaves'];assert len(leaves)==1 and leaves[0]['leaf_id']=='L0'
                    full=leaves[0]['status']=='closed' and leaves[0]['closure_source']=='native_terminal_mip_optimal'
                    result['all_relevant_closed']=result['all_relevant_closed'] and full
                    result['MD_R_requires_complete_native_optimal_root_return']=True
                return result
            source=inspect.getsource(old_endpoint).replace(
                "if U-L<=decision.CLOSURE_TOL and not certificate:raise AssertionError",
                "if U-L<=decision.CLOSURE_TOL and not certificate and launch.get('method')!='MD-R':raise AssertionError")
            ns=dict(old_endpoint.__globals__,complete_cover=complete_cover)
            exec(compile(source,__file__+'::MD_R_complete_native_root_return','exec'),ns)
            core.complete_cover=complete_cover;core.endpoint=ns['endpoint']
            try:yield
            finally:core.complete_cover,core.endpoint=old_cover,old_endpoint
    finally:namespace['source_path']=old

def verify(l,i):
    if l['arm']=='P-GRB':
        p=read(Path(l['destination'])/'round127_parameters.json')
        assert p['MIPFocus']==0 and p['Cuts']==-1 and p['NumStart_before_optimize']==0
        assert p['loaded_after_presets'] and p['authoritative_model_environment']
    fn=types.FunctionType(inherited.inherited.verify.__code__,dict(vars(inherited.inherited),extension=extension),'round128_full_verify')
    return fn(l,i)
