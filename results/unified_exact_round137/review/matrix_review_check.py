"""Independent saved-file audit only. No solver, native load, compile or mutation."""
from pathlib import Path
import ast, collections, hashlib, json, math, subprocess, sys

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round137'
sys.path.insert(0,str(ROOT/'scripts'))
sys.dont_write_bytecode=True

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parsed(p):
    result={}
    for line in Path(p).read_text().splitlines():
        if '=' in line:
            key,value=line.split('=',1)
            try:result[key.strip()]=ast.literal_eval(value.strip())
            except (SyntaxError,ValueError):pass
    return result

def main():
    frozen_sha=sha(OUT/'matrix_frozen.json')
    m=read(OUT/'matrix_frozen.json');plan=read(OUT/'experiment_plan.json')
    inp=read(OUT/'input_manifest.json');candidate=read(OUT/'candidate_manifest.json')
    assert m['experiment_plan_SHA']==sha(OUT/'experiment_plan.json')
    assert m['input_manifest_SHA']==sha(OUT/'input_manifest.json')
    assert m['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    assert len(m['groups'])==m['full_arm_count']==120
    assert sum(g['launch']['cap_seconds'] for g in m['groups'])==174600
    assert m['serial'] and m['threads']==m['mip_threads']==1 and m['affinity_mask']==4
    assert plan['limit_seconds']==216000 and plan['reserve_seconds']==41400
    assert plan['default_AM']==.08 and not plan['default_AP'] and plan['pair_only']
    assert candidate['production_PE_SHA']==sha(candidate['production_PE'])
    assert candidate['DLL_SHA']==sha(candidate['DLL'])
    for path,digest in candidate['source_hashes'].items():assert sha(ROOT/path)==digest,path
    for path,digest in m['helpers'].items():assert sha(ROOT/path)==digest,path
    stages=collections.defaultdict(lambda:[0,0])
    by={p['id']:p for p in inp['roles']}
    assert len(by)==20 and len({p['base_id'] for p in by.values()})==16
    B1=[p for p in by.values() if p['module']=='B1']
    assert collections.Counter(p['V'] for p in B1)=={15:4,20:4,35:4}
    assert sum(p['known'] for p in B1)==6
    assert {p['source'] for p in B1}=={'CITI','CABI','DIVVY'}
    resources={};floors=[]
    for p in by.values():
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        if p['module']!='B2':continue
        a=parsed(ROOT/p['input_path']);b=a['initial'][1:];D=a['target'][1:];w=a['weights'][1:]
        assert sum(D)-sum(b)==p['shortage']>0 and min(w)>0
        assert any(x>y for x,y in zip(b,D)) and any(x<y for x,y in zip(b,D))
        omega=sum(w);lower=min(x/y for x,y in zip(w,D));floor=p['lambda']*lower*(sum(D)-sum(b))
        assert math.isclose(omega,p['Omega'],rel_tol=1e-12,abs_tol=1e-12)
        assert math.isclose(p['lambda']*omega,1.,abs_tol=1e-14)
        assert math.isclose(floor,p['positive_objective_floor'],rel_tol=1e-12)
        assert floor>0
        resources.setdefault(p['base_id'],[]).append(p)
        floors.append(dict(id=p['id'],shortage=p['shortage'],Omega=omega,a=lower,floor=floor,T=p['T_seconds']))
    for base,pair in resources.items():
        pair=sorted(pair,key=lambda p:p['T_seconds']);assert len(pair)==2
        x,y=pair
        assert x['input_path']==y['input_path'] and x['input_sha256']==y['input_sha256']
        for key in set(x)|set(y):
            if key not in {'id','T_seconds'}:assert x.get(key)==y.get(key),(base,key)
        assert x['T_seconds']<y['T_seconds']
    default=[];comparisons=[]
    for index,g in enumerate(m['groups'],1):
        assert g['position']==index
        identity_path=OUT/g['group']/'identity.json';identity=read(identity_path)
        assert sha(identity_path)==g['identity_SHA']
        launch=g['launch'];assert identity['launches']==[launch]
        assert identity['candidate_binary_sha256']==candidate['production_PE_SHA']
        assert identity['measured_source_commit']==candidate['source_commit']
        p=launch['panel'];cmd=launch['command'];method=launch['method']
        assert cmd[0]==candidate['production_PE']
        def val(flag):
            assert cmd.count(flag)==1,(index,flag)
            return cmd[cmd.index(flag)+1]
        assert val('--input')==p['input_path']
        assert float(val('--lambda'))==p['lambda']
        assert float(val('--T'))==p['T_seconds']
        assert int(val('--gurobi-seed'))==launch['seed']==p['gurobi_seed']
        assert int(val('--time-limit'))==p['cap_seconds']-6
        assert int(val('--process-wall-time-limit'))==p['cap_seconds']
        assert val('--threads')==val('--mip-threads')=='1'
        assert val('--gurobi-presolve')=='-1'
        assert '--round135-aggregate-penalty' not in cmd
        assert not any(flag in cmd for flag in ['--external-incumbent','--frontier-resume-state','--mip-start'])
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        reference=OUT/g['group']/'reference'/p['id']
        assert sha(reference/'original.lp')==p['reference']['canonical_sha256']
        assert read(reference/'build.json')==p['reference']
        if launch['stage']=='B3':
            baseline=by[p['physical_configuration_id']]
            assert p['rho'] in (.5,2.)
            assert (p['input_sha256'],p['T_seconds'],p['cap_seconds'])==(
                baseline['input_sha256'],baseline['T_seconds'],baseline['cap_seconds'])
            assert math.isclose(p['lambda'],p['rho']/p['Omega'],rel_tol=1e-14)
            assert math.isclose(p['positive_objective_floor'],
                baseline['positive_objective_floor']*p['rho'],rel_tol=1e-14)
        if method in ('P','PS'):
            assert val('--method')=='gurobi' and '--plain-baseline' in cmd
            for flag in ['--round24-executable-sha256','--round24-manifest-executable-sha256']:
                assert val(flag)==candidate['production_PE_SHA']
            assert ('--round112-ens-start-compact' in cmd)==(method=='PS')
            assert '--round98-state-service' not in cmd
            if method=='P':assert val('--round127-mode')=='p'
            else:assert '--round127-mode' not in cmd
        else:
            assert val('--round98-state-service')=='m-binary'
            assert val('--round127-mode')==('s2-root' if method=='S2R' else 'ms2')
            assert val('--algorithm-preset')=='research-round83-vds-equal-net-exchange'
            deletions=[flag for flag in cmd if flag.startswith('--round137-delete-')]
            assert deletions==(['--round137-delete-'+method[3:].lower()] if method.startswith('NO_') else [])
            assert p['round137_delete_ab']==(method=='NO_AB')
            if method.startswith('AM'):assert float(val('--round137-am-threshold'))==launch['AM_threshold']
            else:assert '--round137-am-threshold' not in cmd and launch['AM_threshold']==.08
        stages[launch['stage']][0]+=1;stages[launch['stage']][1]+=p['cap_seconds']
        key=(p['input_sha256'],p['T_seconds'],p['lambda'],p['cap_seconds'],launch['seed'])
        if method=='S2':default.append(key)
        if launch['stage'] in ('C1','C2','D2-AM','D2-mechanism'):comparisons.append((index,key))
    assert all(default.count(key)==1 for index,key in comparisons)
    expected={'B1':[36,50400],'B2':[24,43200],'B3':[12,21600],'C1':[8,10800],'C2':[16,21600],
              'D2-main':[12,16200],'D2-AM':[4,3600],'D2-mechanism':[8,7200]}
    assert dict(stages)==expected
    old=read(OUT/'infra/pre_weight_floor_matrix.json')
    assert len(old['groups'])==120
    for previous,current in zip(old['groups'],m['groups']):
        assert previous['launch']['command']==current['launch']['command']
        a,b=previous['launch'].copy(),current['launch'].copy()
        a['panel']=dict(a['panel']);b['panel']=dict(b['panel'])
        if b['stage']=='B3':
            a['panel'].pop('positive_objective_floor');b['panel'].pop('positive_objective_floor')
        assert a==b,('unexpected launch change',current['position'])
    import round108_reader as core
    import round137_read
    q=OUT/'qualification/matrices_v2';base=core.lp_model(q/'off/original.lp')
    assert base==core.lp_model(q/'historical-off/original.lp')
    facts={};p=by['K-15-S'];rowcounter=collections.Counter(base['rows'])
    for name,expected_count in [('no-ab',30),('no-cr',240),('no-cg',531)]:
        model=core.lp_model(q/name/'original.lp');rows=collections.Counter(model['rows'])
        removed=rowcounter-rows;assert not rows-rowcounter
        assert sum(removed.values())==expected_count
        assert model['objective']==base['objective']
        for n in model['order']:assert (model['bounds'][n],model['types'][n])==(base['bounds'][n],base['types'][n])
        missing=set(base['order'])-set(model['order'])
        assert missing==({'W_SP','r_min','r_max'} if name=='no-cg' else set())
        facts[name]=dict(removed=expected_count,added=0,removed_columns=sorted(missing))
    ctx=round137_read.ArmModels()
    noab=dict(p,round137_delete_ab=True)
    contract,_=ctx.model_contract(ROOT,noab,q/'no-ab/original.lp','M-B')
    assert contract['deleted_A_B_rows_checked']==30
    ctx.clear()
    ctx=round137_read.ArmModels()
    contract,_=ctx.model_contract(ROOT,p,q/'off/original.lp','M-B')
    assert contract['frozen_A_B_rows_checked']==30
    ctx.clear()
    assert sha(OUT/'matrix_frozen.json')==frozen_sha
    answer=dict(PASS=True,matrix_SHA=frozen_sha,source_commit=candidate['source_commit'],
        checked_current_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        PE_SHA=candidate['production_PE_SHA'],source_files=len(candidate['source_hashes']),
        helper_files=len(m['helpers']),positions=120,caps=174600,reserve=41400,limit=216000,
        stages=dict(stages),shortage_floors=floors,deletions=facts,shared_defaults_checked=len(comparisons),
        current_reader_model_contract_checks=['full A/B presence','minus A/B absence; continuous quantities and retained integer/binary types'],
        B3_floor_metadata_correct_for_actual_rho=True,all_120_argv_unchanged_by_floor_correction=True,
        Optimize=0,compilation=0,commercial_native_loads=0)
    target=OUT/'review/matrix_review_evidence.json'
    target.write_text(json.dumps(answer,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(answer,indent=2))

if __name__=='__main__':main()
