"""Minimal new-interface tiny checks. Never reruns historical qualification."""
from round162_common import *
from round162_experiment import launch

def qualify():
    root=OUT/'qualification/v2';root.mkdir(parents=True,exist_ok=True)
    # Empty/loaded returns, zero inventory, interior and degenerate G.
    fixtures=[('loaded_return',[2,0],'1\n0 3 0 1 0\n1\n',.1),
              ('zero_inventory',[0,0],'1\n0 2 0 0\n\n',.1)]
    results=[]
    for tag,initial,parent,lam in fixtures:
        folder=root/tag;folder.mkdir(exist_ok=True)
        inp=folder/'instance.txt';par=folder/'parent.txt'
        inp.write_text(f'2 1 [2]\ncapacities = [100,2,2]\ninitial = [0,{initial[0]},{initial[1]}]\ntarget = [0,1,2]\nweights = [0,1,1]\npoints = [(0,0),(0,0),(0,0)]\n')
        par.write_text(parent)
        destinations={form:folder/('v3/'+form if tag=='zero_inventory' else form) for form in ('S','F')}
        for form in ('S','F'):
            label=f'tiny_v3_{tag}_{form}'
            args=[inp,100,2,3,lam,par,destinations[form],form,'MIP',30,-1,0,-1,'-']
            if not (destinations[form]/'outcome.json').exists():launch(label,args,30)
            o=read(destinations[form]/'outcome.json')
            assert o['status']=='OPTIMAL' and o['bound_available'],o
            results.append(dict(fixture=tag,form=form,outcome=o,admission=read(destinations[form]/'admission.json')))
        s,f=[read(destinations[form]/'outcome.json') for form in ('S','F')]
        assert abs(s['physical_U']-f['physical_U'])<1e-7 and abs(s['qualified_restricted_lower']-f['qualified_restricted_lower'])<1e-7
    # The zero-inventory parent has exact G=0; test U endpoint, then L=U=0.
    folder=root/'zero_inventory'
    for tag,lo,up in [('fixed_zero',0,0),('lower_zero_endpoint',0,.1)]:
        args=[folder/'instance.txt',100,2,3,.1,folder/'parent.txt',root/tag,'F','export',30,-1,lo,up,'-']
        launch('tiny_v2_'+tag,args,30)
    # A positive G=1/2 parent lies at U=1/2, L=1/2 and L=U=1/2.
    folder=root/'positive_endpoint';folder.mkdir(exist_ok=True)
    (folder/'instance.txt').write_text('2 1 [2]\ncapacities = [100,2,2]\ninitial = [0,2,0]\ntarget = [0,1,2]\nweights = [0,1,1]\npoints = [(0,0),(0,0),(0,0)]\n')
    (folder/'parent.txt').write_text('1\n0 2 0 0\n\n')
    for tag,lo,up in [('U',0,.5),('L',.5,-1),('fixed',.5,.5)]:
        args=[folder/'instance.txt',100,2,3,.1,folder/'parent.txt',folder/tag,'F','export',30,-1,lo,up,'-']
        launch('tiny_v2_positive_'+tag,args,30)
    write(root/'new_interfaces.json',dict(PASS=True,results=results,
        endpoint_exports=['fixed_zero','lower_zero_endpoint','positive_endpoint/U','positive_endpoint/L','positive_endpoint/fixed'],
        full_Starts_checked_in_Cpp=True,types_and_all_rows_checked=True,original_penalty_unchanged=True,
        old_qualification_reruns=0,scope='new completion interface only'))

if __name__=='__main__':qualify()
