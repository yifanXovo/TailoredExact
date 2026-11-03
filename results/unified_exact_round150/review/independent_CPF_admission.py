"""Independent exact CPF and actual MPS admission; never loads Gurobi."""
from independent_math import F,down,up,components,conditional_oracle
from independent_mps import compare,read_mps
from pathlib import Path
import datetime,gzip,hashlib,json,time
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round150'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run():
    tick=time.perf_counter();frozen=read(OUT/'CPF_frozen.json');facts=[]
    assert frozen['Seed']==0 and frozen['Threads']==1 and frozen['LP_cap_seconds']==120
    assert frozen['baseline_Optimize_new']==0 and len(frozen['domains'])==3
    assert frozen['math_SHA']==sha(ROOT/'scripts/round150_math.py')
    assert frozen['lp_SHA']==sha(ROOT/'scripts/round150_lp.py')
    for item in frozen['domains']:
        role=item['role'];source=ROOT/'results/unified_exact_round149/LP'/f'{role}_PF'
        target=OUT/'LP'/f'{role}_CPF';ar=read(source/'arithmetic.json');scope=ar['scope']
        block=read(target/'arithmetic.json');construction=read(target/'construction.json')
        for name,key in [('model.mps','model_SHA'),('arithmetic.json','arithmetic_SHA'),('construction.json','construction_SHA')]:
            assert sha(target/name)==item[key]
        assert sha(source/'model.mps')==construction['source_model_SHA']
        assert not (target/'call.json').exists(), 'Admission must precede CPF Optimize'
        assert block['scope']==scope and block['mu']==ar['mu'] and block['nu']==ar['nu']
        a,mi,const,sites=components(scope,ar['mu'],ar['nu']);d=const+sum(mi.values())
        assert block['d_exact']==str(d)
        points=json.loads(gzip.decompress((source/'solution.json.gz').read_bytes()))
        compare_result=compare(source/'model.mps',target/'model.mps')
        actual=compare_result['actual_rows'];expected={};violations=[];betas=[];samples=[]
        assert len(block['states'])==sum(len(s['support']) for s in scope['stations'])
        old_mps=read_mps(source/'model.mps')
        objectives=[k for k,v in old_mps['rows'].items() if v=='N'];assert len(objectives)==1
        obj=objectives[0]
        for s in scope['stations']:
            i=s['i'];assert old_mps['columns'][f'e_{i}'][obj]==s['omega']
        for state in block['states']:
            i,y=state['i'],state['y'];s=sites[i];assert y in s['support']
            h=F(s['omega'])*abs(F(s['c'])*y-1)
            leave=const+sum(v for j,v in mi.items() if j!=i)+h+a*y
            delta=h+a*y-mi[i];assert delta>=0
            assert leave==d+delta
            pd=max(F(ar['penalty_lower']),F(0),F(down(leave)))
            desired=min(F(ar['beta']),F(scope['cutoff'])-pd)
            beta=min(ar['beta'],up(desired))
            assert state['conditional_dual_exact']==str(leave)
            assert state['conditional_dual_down']==down(leave)
            assert state['h_exact']==str(h) and state['delta_exact']==str(delta)
            assert F(state['penalty_lower'])==pd and state['beta']==beta
            assert F(beta)>=desired and state['beta_exact_target']==str(desired)
            emitted=beta<ar['beta'] and not 0<abs(beta)<1e-12
            assert state['emitted']==emitted
            if emitted:
                terms={f'state_g_{i}_{y}':1.}
                if beta:terms[f'state_{i}_{y}']=-beta
                expected[f'r150_CPF_{i}_{y}']=dict(sense='L',rhs=0.,terms=terms)
            violation=points[f'state_g_{i}_{y}']-beta*points[f'state_{i}_{y}']
            violations.append(violation);betas.append(beta)
            if not samples or violation>samples[-1]['violation']:
                samples.append(dict(i=i,y=y,conditional_dual_exact=str(leave),violation=violation))
        assert actual==expected
        by_name={r['name']:dict(sense='L',rhs=r['rhs'],terms=r['terms']) for r in block['rows']}
        assert by_name==expected
        for sample in [samples[0],samples[-1]]:
            oracle=conditional_oracle(scope,sample['i'],sample['y'])
            assert F(sample['conditional_dual_exact'])<=oracle
            sample['conditional_oracle_exact']=str(oracle)
        facts.append(dict(role=role,source_model_SHA=sha(source/'model.mps'),model_SHA=sha(target/'model.mps'),
            states=len(block['states']),actual_rows=len(actual),actual_NZ=sum(len(v['terms']) for v in actual.values()),
            beta_min=min(betas),all_state_exact_leave_one_out=True,all_state_upward_transport=True,
            actual_matrix_matches_all_and_only_emitted_rows=True,
            old_objective_constant_bounds_types_support_cutoff_rows_identical_after_deleting_CPF=True,
            old_point_violations_above_1e_8=sum(v>1e-8 for v in violations),max_old_point_violation=max(violations),
            samples=[samples[0],samples[-1]],independent_MPS_seconds=compare_result['elapsed_seconds']))
    receipt=dict(decision='ACCEPT',CPF_frozen_SHA=sha(OUT/'CPF_frozen.json'),
        independent_nonimplementer_review=True,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        Native_load=0,Optimize=0,actual_check_seconds=time.perf_counter()-tick,
        independent_script_SHA=sha(__file__),independent_MPS_script_SHA=sha(Path(__file__).with_name('independent_mps.py')),
        facts=facts,code_review=['Actual binary64 omega already weighted; no extra lambda',
        'Exact Fraction prefix/suffix avoids subtracting two independent lower bounds',
        'Conditional beta remains state indexed; signed and empty-branch behavior safe',
        'Tiny coefficient handling omits entire row and retains all old PF rows',
        'No new variables, old-point fixing, repeated baseline or fourth domain',
        'New solve stores primal, dual, reduced costs, residuals and quality separately'],
        numerical_policy='OPTIMAL and local residual tolerances do not certify exact objective error; K35 old PF primal-dual difference must remain explicit')
    (OUT/'review/CPF_admission.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='facts'}))
if __name__=='__main__':run()
