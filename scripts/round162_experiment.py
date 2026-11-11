"""Each real source/completion call owns one outer clock and one closed fee."""
from round162_common import *

def launch(label,args,cap=300):
    cap=float(cap)
    executable=pe();m=read(OUT/'candidate_manifest.json')
    assert sha(executable)==m['research_PE_SHA'] and sha(DLL)==DLL_SHA
    command=[executable,*args]
    write(OUT/'launches'/f'{label}.json',dict(UTC=utc(),command=list(map(str,command)),PE_SHA256=sha(executable),DLL_SHA256=sha(DLL),
        source_commit=git('rev-parse','HEAD').decode().strip(),source_hashes=m['source_hashes'],
        Seed=0,Threads=1,MIPFocus=0,outer_cap=cap,supervisor_margin=30,nested_cost_not_added=True))
    rc=metered(label,'native',command,cap+30)
    if rc:raise RuntimeError((label,rc))

def call(role,form,mode,label,cap=300,lower=0,upper=-1,saved='-',nodes=-1):
    folder=OUT/'inputs'/role;s=read(folder/'source.json');p=s['panel']
    args=[folder/'instance.txt',p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],folder/'parent.txt',
          OUT/'runs'/label,form,mode,cap,nodes,lower,upper,saved]
    launch(label,args,cap)

def capability(role):
    name=role+'_S_LP_v1'
    if not (OUT/'runs'/name/'outcome.json').exists():call(role,'S','LP',name)
    s=read(OUT/'runs'/name/'outcome.json')
    assert s['status']=='OPTIMAL' and s['bound_available'] and s['LP_primal_dual_available'],s
    completion=role+'_F_completion_v2'
    call(role,'F','completion',completion,saved=OUT/'runs'/name/'lp_values.tsv')
    c=read(OUT/'runs'/completion/'outcome.json')
    if c['status']=='OPTIMAL' and c['LP_point_residual']<=1e-6 and abs(c['LP_objective']-s['qualified_restricted_lower'])<=1e-7:
        write(OUT/'reports'/f'{role}_capability.json',dict(S=name,completion=completion,F=None,
            decision='saved S optimum attained in full Q within inherited numerical contract; independent audit pending'))
    else:
        full=role+'_F_LP_v1';call(role,'F','LP',full)
        write(OUT/'reports'/f'{role}_capability.json',dict(S=name,completion=completion,F=full,
            decision='fixed-point diagnostic does not settle free objective; free F solved'))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
