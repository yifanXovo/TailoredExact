"""Independent computed scope qualification for the inherited Seed0 NEJ guard.

Preserves every raw native_preconditions/global_available/global_bound value.
The sidecar establishes native mathematics from the actual model, nine native
readbacks, native type/log/return, and original backend/source restrictions.
It never rewrites journals, reruns performance, or supplies new global samples.
"""
from pathlib import Path
from collections import Counter
import argparse, ast, copy, csv, hashlib, json, math, re, runpy, sys, time, traceback

SETTINGS=dict(read_return_code=0,Threads=1,Seed=1,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
PE_SHA='4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0'
TOL=1e-7
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def obj(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def txt(path):return Path(path).read_text(encoding='utf-8-sig')
def rows(path):return list(csv.DictReader(txt(path).splitlines()))
def require(condition,message):
    if not condition:raise AssertionError(message)
def save(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')

def validate_facts(f):
    require(f['actual_settings']==SETTINGS,'actual per-call Seed1 and all nine readbacks')
    require(f['actual_model_SHA']==f['call_model_SHA'],'actual saved model byte SHA')
    require(f['native_rows_columns']==f['saved_rows_columns'],'actual native pre-presolve model size')
    require(f['native_types']==f['saved_types'],'actual native restored types including all quantities')
    require(f['return_code']==0 and f['committed_return'],'successful exact-call committed native return')
    require(f['source_identity_bound'] and f['unchanged_metadata_seed0_guard'],'exact compiled-source Seed0 guard origin')
    require(f['original_domain_contract'] and f['original_scope_contract'],'complete original domain and numerical true-G/cutoff scope')
    require(f['no_extra_overrides_fixed_inventory_rows_or_modes'],'all forbidden original request/path conjuncts excluded')
    require(f['zero_gap_actual_readback'] and f['backend_finalization_gate'],'actual zero gaps and full backend engineering gate')
    require(f['raw_native_preconditions']==0,'inherited Seed1 raw flag remains false')
    return True

def audit(root,launch):
    root=Path(root).resolve();out=root/'results/unified_exact_round109';review=out/'review';arm=launch['arm'];p=launch['panel']
    def local(saved):
        s=str(saved).replace('\\','/')
        for marker in ('results/','reference/','src/','include/','build/'):
            if marker in s:
                path=(root/s[s.index(marker):]).resolve();require(path.is_relative_to(root),'all source/raw reads remain in explicit root');return path
        raise AssertionError('unsupported evidence path')
    d=local(launch['destination']);raw=obj(d/'result.json');completion=obj(d/'completion.json');actual=obj(d/'launch.json')
    require(p['gurobi_seed']==1 and actual['command']==launch['command'] and actual['panel']==p,'actual frozen Seed1 argv/input panel')
    require(completion['returncode']==0 and completion['stop_reason']=='normal_return' and completion['within_cap'],'actual native child normal complete return')
    source=obj(out/'candidate_contract_freeze.json')['source_bindings'];guard=root/'src/GurobiBaseline.cpp';controller=root/'src/PaperExternalGiniTree.cpp';interface=root/'include/FixedIntervalMipBackend.hpp'
    for path in (guard,controller,interface):require(sha(path)==source[path.relative_to(root).as_posix()],'unchanged production source '+str(path.name))
    code=txt(guard);body=code[code.index('bool evidenceParameterReadback('):code.index('struct ProgressCallbackState')]
    require('return rc==0 && threads==1 && seed==0 && presolve==-1 && gap==0 && absgap==0' in body and 'setintparam' not in body and 'setdblparam' not in body,'legacy fixed-zero Seed predicate changes metadata only')
    require('!out.exact_zero_gap_roundtrip ||' in code and '!out.model_fingerprint_matches_request ||' in code and '!out.feasibility_consistency_gate || !domain_restore_ok ||' in code and 'out.failure_reason = "none";' in code,'original backend all-conjunct post-return engineering gate')
    am={};i=1
    while i<len(launch['command']):
        key=launch['command'][i]
        if key=='--plain-baseline':am[key]=True;i+=1
        else:am[key]=launch['command'][i+1];i+=2
    require(am['--gurobi-seed']=='1' and '--round100-continuous-quantities' not in am,'same frozen Seed1 actual algorithm entrance')
    require(not any(re.match(r'--round(?:60|63|9[567]|10[1-7])-',k) for k in am),'no forbidden inventory/resource/projection/additional research options')
    parser=runpy.run_path(str(review/'round109_independent_parser.py'));parser['input_file'].__globals__.update(txt=txt,require=require);parser['lp'].__globals__.update(txt=txt,require=require)
    kernel=runpy.run_path(str(review/'round109_independent_kernel.py'))
    for fn in ('domain_contract','scope_contract'):kernel[fn].__globals__.update(require=require,Counter=Counter,re=re,TOL=TOL)
    q=parser['input_file'](root/p['input_path']);require(sha(root/p['input_path'])==p['input_sha256'],'exact known/frozen original input bytes')
    fleet=[dict(r) for r in raw['routes']]
    for k in range(q['M']):
        if k not in [r['vehicle'] for r in fleet]:fleet.append(dict(vehicle=k,nodes=[0,0],operations=[]))
    parser['physical'].__globals__.update(require=require)
    ph=parser['physical'](q,fleet,p['T_seconds'],p['lambda'],p['pickup_seconds'],p['drop_seconds'])
    require(abs(ph['U']-raw['objective'])<=TOL and ph['final_inventories']==raw['final_inventories'],'complete own physical final U independently recomputed')
    observations=obj(d/'observations.json');calls={};returned={};bound_events=[]
    for expected,o in enumerate(observations,1):
        e=o['payload'];path=d/'journal'/f'event_{expected}.json';rawbytes=path.read_bytes();commit=txt(path.with_suffix('.commit')).split()
        require(e['sequence']==o['sequence']==expected and json.loads(rawbytes)==e and hashlib.sha256(rawbytes).hexdigest()==o['sha256']==commit[4] and int(commit[3])==len(rawbytes),'exact raw event/commit bytes and contiguous sequence')
        if e['kind']=='call':require(e['settings']==SETTINGS,'all actual native calls use frozen Seed1');calls[e['call']]=e
        elif e['kind']=='returned':require(e['call'] in calls and e['return_code']==0,'exact native call successful return');returned[e['call']]=e
        elif e['kind']=='bound':bound_events.append(e)
    require(set(calls)==set(returned),'all declared actual native calls committed returned')
    ledger=rows(d/'external/paper_optimize_ledger.csv') if arm=='M-B' else []
    if ledger:require(len(ledger)==len(calls),'one same-position native ledger per actual backend call')
    proofs=[]
    for position,(identifier,c) in enumerate(calls.items()):
        mp=local(c['model_path']);m=parser['lp'](mp);domain=kernel['domain_contract'](m,q,arm);nt=txt(local(c['native_log_path']))
        size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',nt);require(size is not None,'actual native call pre-presolve rows and columns')
        kind=ledger[position]['solve_kind'] if ledger else 'MIP'
        if ledger:
            lr=ledger[position];require(lr['leaf_id']==c['leaf'] and lr['model_sha256']==c['model_sha256'] and local(lr['native_log'])==local(c['native_log_path']) and int(lr['optimize_return_code'])==0,'actual same-position native call/model/leaf/log/return ledger')
            kernel['scope_contract'](c,m,q)
        if kind=='LP':
            require(not c['native_preconditions'],'LP retains false integer native precondition');continue
        native=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',nt);require(native is not None,'actual native integer call type header')
        actualtypes=dict(C=int(native[1]),I=int(native[2])-int(native[3]),B=int(native[3]));savedtypes={k:Counter(m['types'].values()).get(k,0) for k in ('C','I','B')}
        if arm=='P-GRB':
            require(len(calls)==1 and c['full_original']==1 and c['model_scope']=='complete_original_compact_milp' and c['cover']==[],'one complete original cold compact P call')
            build=obj(out/'qualification/reference'/p['id']/'build.json')
            require(c['model_sha256']==build['canonical_sha256']==raw['gurobi_canonical_model_sha256'] and raw['gurobi_model_fingerprint']==build['fingerprint'],'exact original cold reference matrix and native fingerprint')
            gates=all(raw[k] is True for k in ('gurobi_native_domain_audit_passed','gurobi_native_variable_names_match','gurobi_native_variable_types_match','gurobi_native_variable_bounds_match','gurobi_native_objective_sense_match','gurobi_solver_finalization_reached','gurobi_lifecycle_valid'))
            require(raw['gurobi_optimize_return_code']==0 and raw['gurobi_optimize_count']==1 and not raw['gurobi_hga_start_requested'] and not raw['gurobi_hga_start_submitted'],'one cold P Optimize and no supplied Start')
        else:
            require(not c['full_original'] and lr['integer_domain_restored']=='1','original scoped MIP restored actual integer domain')
            gates=raw['external_gini_tree_backend_parameter_roundtrip_valid'] and raw['external_gini_tree_lifecycle_complete'] and raw['external_gini_tree_feasibility_consistency_gate'] and raw['external_gini_tree_failure_reason'] in ('none','overall_global_deadline')
            require('variable_bound_overrides' not in txt(controller) and 'round60_fixed_inventory' not in txt(controller) and 'additional_linear_rows' not in txt(controller),'original controller never sets prohibited request collections')
        facts=dict(actual_settings=c['settings'],actual_model_SHA=sha(mp),call_model_SHA=c['model_sha256'],native_rows_columns=[int(size[1]),int(size[2])],saved_rows_columns=[len(m['rows']),len(m['bounds'])],
            native_types=actualtypes,saved_types=savedtypes,return_code=returned[identifier]['return_code'],committed_return=True,source_identity_bound=True,unchanged_metadata_seed0_guard=True,
            original_domain_contract=True,original_scope_contract=True,no_extra_overrides_fixed_inventory_rows_or_modes=True,zero_gap_actual_readback=c['settings']['MIPGap']==c['settings']['MIPGapAbs']==0,
            backend_finalization_gate=bool(gates),raw_native_preconditions=c['native_preconditions'])
        validate_facts(facts)
        printed=re.findall(r'Best objective ([^,]+), best bound ([^,]+), gap ([^\n]+)',nt);require(printed,'actual returned native final log bound')
        L=float(printed[-1][1]);require(math.isfinite(L) and abs(L)<1e90,'actual returned finite native bound')
        if arm=='P-GRB':require(raw['gurobi_obj_bound_c_available'] and abs(L-raw['gurobi_obj_bound_c'])<=TOL and raw['gurobi_obj_bound_c']<=ph['U']+TOL,'P final full-domain native bound actual attribute/log/own physical corroboration')
        proofs.append(dict(call=identifier,solve_kind=kind,facts=facts,computed_native_scope_qualified=True,raw_native_preconditions=c['native_preconditions'],actual_native_final_log_L=L,
            model_path=str(mp.relative_to(root)),model_SHA=sha(mp),native_log_SHA=sha(local(c['native_log_path'])),source_SHA=sha(guard),domain=domain))
    return dict(decision='ACCEPT',id=p['id'],arm=arm,seed=1,proofs=proofs,own_physical=ph,raw_native_preconditions_preserved=True,
        raw_unavailable_global_callback_count=sum(not e['global_available'] and e['global_bound'] is None for e in bound_events),raw_global_flags_and_values_unchanged=True,
        computed_scoped_callback_provenance_is_offline_mathematics=True,new_early_global_checkpoint_values_generated=False,
        source_bindings={x.relative_to(root).as_posix():sha(x) for x in (guard,controller,interface)},actual_full_argv=launch['command'],
        final_bound_available_only_at_return=True,Optimize=0,native_environment=0)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True);p.add_argument('--existing-only',action='store_true');args=p.parse_args()
    root=Path(args.root).resolve();dest=Path(args.out).resolve();require(dest.is_relative_to(root/'results/unified_exact_round109/review'),'exclusive reviewer output root');dest.mkdir(exist_ok=False)
    start=time.perf_counter();error=None;checks=[];results=[]
    save(dest/'launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=sha(__file__),Optimize=0,native_environment=0))
    try:
        identity=obj(root/'results/unified_exact_round109/qualification/cli01/identity.json');pending=[]
        for launch in identity['launches']:
            if launch['panel']['gurobi_seed']!=1:continue
            actualpath=Path(launch['destination'])/'result.json'
            if not actualpath.exists():pending.append(launch['arm']);continue
            results.append(audit(root,launch))
        require(args.existing_only or not pending,'all actual Seed1 P and MB raw results present')
        require(results,'at least one real existing Seed1 arm independently audited')
        facts=results[0]['proofs'][0]['facts'];validate_facts(facts);checks.append('real Seed1P facts accepted from original false flag with full mathematical scope')
        mutations=[('actual_settings',dict(SETTINGS,Seed=0)),('actual_settings',dict(SETTINGS,Threads=2)),('call_model_SHA','wrong'),('native_rows_columns',[0,0]),('native_types',dict(C=0,I=0,B=0)),('return_code',1),('backend_finalization_gate',False),('original_scope_contract',False),('no_extra_overrides_fixed_inventory_rows_or_modes',False)]
        for key,value in mutations:
            changed=copy.deepcopy(facts);changed[key]=value
            try:validate_facts(changed)
            except AssertionError:checks.append('damaged '+key+' correctly rejected')
            else:raise AssertionError('damaged '+key+' accepted')
        value=dict(decision='ACCEPT',arms=results,pending_Seed1_arms=pending,full_Seed1_qualification_complete=not pending,finite_checks=checks,source_SHA=sha(__file__),elapsed_engineering_seconds=time.perf_counter()-start,
            scope='computed native scope qualification only; full own Start/coverage/final stage needs independent raw audit',Optimize=0,native_environment=0,production_edits=0)
    except Exception:
        error=traceback.format_exc();value=dict(decision='HOLD',error=error,arms=results,finite_checks=checks,source_SHA=sha(__file__),Optimize=0,native_environment=0)
    save(dest/'audit.json',value);save(dest/'receipt.json',dict(exit_code=int(error is not None),audit_SHA=sha(dest/'audit.json'),source_SHA=sha(__file__),elapsed_engineering_seconds=time.perf_counter()-start,cwd=str(Path.cwd())))
    (dest/'source_at_execution.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(decision=value['decision'],error=error,finite_checks=len(checks),arms=len(results)),ensure_ascii=False),flush=True)
    if error:sys.exit(1)
if __name__=='__main__':main()
