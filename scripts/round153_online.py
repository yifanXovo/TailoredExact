"""Own-root scalar floor helper; current model only, no historical evidence I/O."""
from time import perf_counter
_PROCESS_START=perf_counter()
import argparse,contextlib,traceback
from fractions import Fraction as F
from round108_reader import lp_model
from round151_math import scope_from_model
from round152_math import h_exact
from round153_pricing import Oracle
from round153_common import ROOT,DLL_SHA,sha,read,write,utc,Path,sys,time,math

NODE_LIMIT=4096
ABSOLUTE_PRICE_GAP=1e-4

def verify_loaded_sources(deps):
    actual={}
    for module in list(sys.modules.values()):
        value=getattr(module,'__file__',None)
        if not value:continue
        path=Path(value).resolve()
        try:name=path.relative_to(ROOT).as_posix()
        except ValueError:continue
        if not name.startswith('scripts/') or path.suffix!='.py':continue
        assert name in deps,('unbound_project_import',name)
        digest=sha(path);assert digest==deps[name],('changed_loaded_project_import',name)
        actual[name]=digest
    return actual

def run(args):
    start=_PROCESS_START;source=args.source.resolve();target=args.out.resolve()
    deadline=start+args.remaining_global_seconds
    manifest_sha=sha(args.manifest);manifest=read(args.manifest);deps=manifest['helper_dependencies']
    assert sha(sys.executable)==manifest['python_SHA']
    for name,digest in deps.items():assert sha(ROOT/name)==digest,('helper_source_changed',name)
    source_sha=sha(source);parsed=lp_model(source);scope=scope_from_model(parsed,args.Bminus,args.B)
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();native=binding();assert native['sha256']==DLL_SHA==manifest['DLL_SHA']
    write(target/'source.json',dict(UTC=utc(),source=str(source),source_SHA=source_sha,scope=scope,
          helper_manifest=str(args.manifest.resolve()),helper_manifest_SHA=sha(args.manifest),dependencies=deps,
          python=str(Path(sys.executable).resolve()),python_SHA=sha(sys.executable),Native=native,
          no_historical_inventory_or_price_loaded=True,own_current_canonical_source=True,
          Seed=0,Threads=1,node_limit=NODE_LIMIT,absolute_price_gap=ABSOLUTE_PRICE_GAP,
          stop_rule='exact_DP_attainment_or_Native_gap_or_4096_nodes',wall_time_step_limit=None,
          whole_method_remaining_seconds=args.remaining_global_seconds,global_deadline_ends_whole_method=True))
    costs={(s['i'],y):h_exact(s,y) for s in scope['stations'] for y in s['support']}
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        oracle=Oracle(scope,env,old_joint=True)
        loaded_sources=verify_loaded_sources(deps)
        try:r=oracle.price(1.,costs,target/'pricing',node_limit=NODE_LIMIT,absolute_gap=ABSOLUTE_PRICE_GAP,global_deadline=deadline)
        finally:oracle.close()
    global_stop=time.perf_counter()>=deadline or any(c['Status']==gp.GRB.TIME_LIMIT for c in r['calls'])
    loaded_sources=verify_loaded_sources(deps)
    assert sha(args.manifest)==manifest_sha and sha(source)==source_sha
    qualified=r['complete_domain'] and r['lower'] is not None and math.isfinite(r['lower']) and 0<=r['lower']<=scope['cutoff']+1e-8
    # Preserve lower transport as a decimal that round-trips to the exact
    # qualified binary64 floor. The parent checks its own source SHA again.
    lower=r['lower'] if qualified else 0.
    result=dict(qualified=qualified,lower=lower,upper=r['upper'],source_SHA=source_sha,scope=scope,
                source_helper_manifest_SHA=sha(args.manifest),seconds=time.perf_counter()-start,
                new_Native_calls=len(r['calls']),node_limit=NODE_LIMIT,absolute_price_gap=ABSOLUTE_PRICE_GAP,
                global_deadline_stop=global_stop,whole_method_remaining_seconds=args.remaining_global_seconds,
                no_historical_inventory_or_price_loaded=True,physical_upper_claim=False,
                source_rejection_retains_no_new_native_floor=not qualified)
    result['loaded_project_sources']=loaded_sources
    write(target/'result.json',result)
    helper_sha=sha(__file__)
    (target/'response.txt').write_text(f'R153-FLOOR-v2 {source_sha} {manifest_sha} {helper_sha} {int(qualified)} {lower:.17g}\n',encoding='ascii')
    return 124 if global_stop else 0

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--Bminus',type=int,required=True);p.add_argument('--B',type=int,required=True);p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--remaining-global-seconds',type=float,required=True)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    with (args.out/'helper.stdout.log').open('w') as stdout,(args.out/'helper.stderr.log').open('w') as stderr:
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            try:return run(args)
            except Exception as e:
                traceback.print_exc();write(args.out/'failure.json',dict(UTC=utc(),type=type(e).__name__,message=str(e),no_new_floor=True))
                return 1
    return 0

if __name__=='__main__':sys.exit(main())
