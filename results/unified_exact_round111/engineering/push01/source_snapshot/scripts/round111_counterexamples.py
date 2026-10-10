"""Finite counterexamples for the changed index/cache, no optimizer."""
from round111_common import *
import copy, re
import round108_reader as old
import round111_seed_audit as new
import round109_seed_scope as computed

def run():
    dest=OUT/'qualification/counterexamples01';dest.mkdir(parents=True,exist_ok=False)
    instance=ROOT/'reference/round111_audit_counterexample.txt'
    instance.write_text('''2 1 [3]
initial = [0,1,1]
target = [1,1,1]
capacities = [0,3,3]
weights = [0,1,1]
points = [(0,0),(1,0),(2,0)]
''',encoding='utf-8')
    p=dict(V=2,M=1,input_path=instance.relative_to(ROOT).as_posix(),Q_vector=[3])
    def model(extra_state=False,quantity_name='p_0_1',lo=0.,hi=.5,cutoff=2.):
        quantities=[quantity_name,'d_0_1','p_0_2','d_0_2']
        states=['state_1_0','state_1_1','state_2_0','state_2_1']+(['state_01_0'] if extra_state else [])
        names=quantities+states+['mode_0_1','mode_0_2','z_0_1','z_0_2','Y_1','Y_2','G','r_1','r_2','h_1_2']
        rows=[]
        for i in [1,2]:
            terms={n:1. for n in quantities if n.endswith('_'+str(i))}
            for n in states:
                if re.fullmatch(r'state_'+str(i)+r'_\d+',n):
                    amount=abs(1-int(n.rsplit('_',1)[1]))
                    if amount:terms[n]=-float(amount)
            rows.append((tuple(sorted(terms.items())),'=',0.))
            rows.append((tuple(sorted({f'z_0_{i}':1.,f'state_{i}_1':1.}.items())),'=',1.))
        objective=(tuple(sorted([('G',1.),('r_1',1.),('r_2',1.)])),0.)
        rows.append((objective[0],'<=',cutoff))
        for gamma,sense in [(hi,'<='),(lo,'>=')]:
            terms={'h_1_2':1.}
            if gamma:terms.update(r_1=-2*gamma,r_2=-2*gamma)
            rows.append((tuple(sorted(terms.items())),sense,0.))
        types={n:('B' if n in states or n.startswith(('mode_','z_')) else 'I' if n.startswith('Y_') else 'C') for n in names}
        return dict(order=names,bounds={n:((lo,hi) if n=='G' else (0.,3.)) for n in names},types=types,rows=rows,objective=objective)
    def save(m,path):
        def expr(terms):return ' '.join(('+' if v>=0 else '-')+' '+str(abs(v))+' '+n for n,v in terms) if terms else '0'
        lines=['Minimize','obj: '+expr(m['objective'][0]),'Subject To']
        lines += [f'c{j}: {expr(terms)} {sense} {rhs}' for j,(terms,sense,rhs) in enumerate(m['rows'])]
        lines += ['Bounds']+[f'{lo} <= {n} <= {hi}' for n,(lo,hi) in m['bounds'].items()]
        for kind,title in [('I','Generals'),('B','Binaries')]:
            names=[n for n in m['order'] if m['types'][n]==kind]
            if names:lines += [title,' '.join(names)]
        lines += ['End'];path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    cases=[]
    def check(name,m,accepted=True,call=None):
        path=dest/(name+'.lp');save(m,path);out=[]
        for contract,scope in [(old.model_contract,old.model_scope_contract)]:
            try:
                facts,parsed=contract(ROOT,p,path,'M-B');out.append((True,facts,scope(call,parsed,p) if call else None))
            except AssertionError:out.append((False,None,None))
        context=new.ArmModels()
        try:
            facts,parsed=context.model_contract(ROOT,p,path,'M-B');out.append((True,facts,context.model_scope_contract(call,parsed,p) if call else None))
        except AssertionError:out.append((False,None,None))
        finally:context.clear()
        assert out[0]==out[1] and out[0][0]==accepted,name
        cases.append(dict(name=name,accepted=accepted,old_new_exact_equal=True))
    call=dict(full_original=False,lower_g=0.,upper_g=.5,cutoff=2.,epoch=1,call=1)
    base=model();check('base',base,call=call)
    check('state_leading_zero_not_station_one',model(True),call=call)
    check('quantity_suffix_leading_zero_preserved',model(quantity_name='p_0_01'),call=call)
    duplicate=copy.deepcopy(base);duplicate['rows']+=duplicate['rows'][:4];check('duplicate_A_B_legal_Counter_ge_one',duplicate,call=call)
    for index,label in [(0,'missing_A'),(1,'missing_B')]:
        bad=copy.deepcopy(base);bad['rows'].pop(index);check(label,bad,False)
    for name,kind in [('Y_1','C'),('state_1_0','I'),('mode_0_1','I'),('p_0_1','I')]:
        bad=copy.deepcopy(base);bad['types'][name]=kind;check('type_'+name,bad,False)
    for field,value in [('lower_g',.1),('upper_g',.6),('cutoff',1.5)]:check('wrong_'+field,base,False,dict(call,**{field:value}))
    changed=model(lo=.1,hi=.6,cutoff=1.5)
    check('legal_positive_G_changed_cutoff',changed,call=dict(call,lower_g=.1,upper_g=.6,cutoff=1.5,epoch=2,call=7))
    check('same_model_legal_changed_call_epoch',base,call=dict(call,call=8,epoch=5))
    path=dest/'same_path.lp';save(base,path);context=new.ArmModels();a,m=context.model_contract(ROOT,p,path,'M-B')
    context.model_contract(ROOT,p,path,'M-B');assert context.metrics['pure_model_cache_hits']==1
    save(changed,path)
    try:context.model_scope_contract(call,m,p)
    except AssertionError:pass
    else:raise AssertionError('stale Counter accepted after same-path bytes replacement')
    b,m2=context.model_contract(ROOT,p,path,'M-B');assert a['SHA']!=b['SHA'] and m is not m2
    assert context.model_scope_contract(dict(call,lower_g=.1,upper_g=.6,cutoff=1.5),m2,p)==old.model_scope_contract(dict(call,lower_g=.1,upper_g=.6,cutoff=1.5),m2,p)
    context.clear();assert not context.models and not context.by_id and not context.paths
    cases.append(dict(name='same_path_changed_bytes_reparse_and_stale_scope_reject',passed=True))
    sample=read(OUT/'replay_plan.json')['samples'][0];launch=sample['launch'];records=read(Path(launch['destination'])/'observations.json')
    completion=read(Path(launch['destination'])/'completion.json');identity=read(OLD_ROOT/sample['identity_path'])
    for field,value in [('Seed',0),('Threads',2),('Presolve',0),('MIPGap',.1),('MIPGapAbs',.1),('FeasibilityTol',1e-5),('OptimalityTol',1e-5),('IntFeasTol',1e-4),('read_return_code',1)]:
        bad=copy.deepcopy(records);next(r['payload'] for r in bad if r['payload']['kind']=='call')['settings'][field]=value
        try:computed.qualify(OLD_ROOT,launch,bad,completion,identity)
        except AssertionError:pass
        else:raise AssertionError(('bad actual per-call setting accepted',field))
        cases.append(dict(name='actual_call_'+field,rejected=True))
    assert records==read(Path(launch['destination'])/'observations.json')
    write(dest/'audit.json',dict(passed=True,cases=cases,Optimize=0,native_processes=0,
        helper_SHA=sha(new.__file__),old_reader_SHA=sha(old.__file__),raw_flags_unchanged=True,
        scope_changes_not_blanket_rejected=True,call_legality_never_cached=True))
    print('finite index/cache/settings counterexamples PASS',len(cases))

if __name__=='__main__':run()
