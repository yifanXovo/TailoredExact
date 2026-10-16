"""Independent bounded actual claims/display review of the complete prose.

No producer, optimization, report generator or production decision is invoked.
All writes are this reviewer's receipts under review/.
"""
from pathlib import Path
from decimal import Decimal
import collections,csv,datetime,json,math,re,sys,time
from independent_review_round122 import ROOT,OUT,REVIEW,read,sha,save_receipt
from post_formal_independent import typed_equal

USED={}
def rd(path):USED[str(path)]=sha(path);return read(path)
def text(path):USED[str(path)]=sha(path);return Path(path).read_text(encoding='utf-8-sig')
def rows(path):
    USED[str(path)]=sha(path)
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def displayed(cell,value):
    number=Decimal(cell);tolerance=Decimal(5).scaleb(number.as_tuple().exponent-1)
    assert abs(Decimal.from_float(float(value))-number)<=tolerance+Decimal.from_float(2*math.ulp(float(value))),(cell,value)
def tables(prose):
    result=[];active=[]
    for line in prose.splitlines()+['']:
        if line.startswith('|'):active.append([x.strip() for x in line.strip().strip('|').split('|')])
        elif active:
            assert len(active)>2 and all(re.fullmatch(r':?-+:?',x) for x in active[1])
            result.append((active[0],active[2:]));active=[]
    return result
def block(prose,start,end):return prose[prose.index(start):prose.index(end,prose.index(start))]

def run(expected_SHA):
    tick=time.perf_counter();path=OUT/'paper_result_interpretation.md'
    assert len(expected_SHA)==64 and sha(path)==expected_SHA
    prose=text(path);receipt=rd(OUT/'engineering/sealed_interpretation_receipt.json')
    ind=rd(REVIEW/'post_formal_independent.json');assert ind['decision']=='ACCEPT'
    assert receipt['document_SHA']==sha(path) and receipt['full_actual_independent_review_SHA']==sha(REVIEW/'post_formal_independent.json')
    for n,digest in receipt['core_SHAs'].items():assert sha(OUT/f'reconstruction/group{int(n):02d}/current_core.json')==digest
    for k,n in [('all32_arms_SHA','all32_arms.json'),('all48_pairs_SHA','all48_pairs.json'),('stage_decision_SHA','stage_decision.json')]:assert receipt[k]==ind[k]==sha(OUT/n)
    assert receipt['script_SHA']==sha(OUT/'engineering/finalize_interpretation.py')
    before=OUT/'engineering/paper_interpretation_before_final.md';old_receipt=OUT/'engineering/sealed_interpretation_receipt_before_final.json'
    assert receipt['previous_document_SHA']==sha(before)=='4c31221192f06c449c5ee460acce6fd6241a1cf67b4f16e4331520c8ffcacf9e'
    assert receipt['previous_receipt_SHA']==sha(old_receipt)
    prior=text(before);prior=block(prior,'## V20 certification','## Evidence and claim limits')
    prior=prior.replace('This is a finite candidate-selection condition, not a significance\ntest. The complete stage rule still requires the remaining fixed Seed1\ngroup, including its possible higher-priority proof or severe-regression\noutcomes. No final stage or replacement paper reference is selected in\nthis partial-panel draft.',
        'This is a finite candidate-selection condition, not a significance\ntest. Both mandatory Seed1 groups are now complete. Neither the proof-risk\npriority nor either primary performance veto fires; the final stage and\none fixed existing paper reference are stated below.')
    prior=prior.replace('The final PB-C50-S\nSeed1 group remains necessary before any full-panel stage decision.',
        'The final PB-C50-S\nSeed1 group is retained separately below; neither repeat adds a new role.')
    kept=block(prose,'## V20 certification','## Fixed PB-C50-S Seed1 repeat')
    assert re.sub(r'\s','',prior)==re.sub(r'\s','',kept),'earlier sealed case text changed beyond two pending statements'
    arms=rd(OUT/'all32_arms.json');pairs=ind['independent_pairs'];decision=ind['independent_stage']
    by={(x['group_number'],x['arm']):x for x in arms}
    phys={(x['group'],x['arm']):x for x in ind['all_32_physical_objective_and_clocks']}
    pair={(x['group_number'],x['candidate'],x['control']):x for x in pairs}
    tab=tables(prose)
    endpoint=[r for h,r in tab if h==['Method','Own U','Qualified L','Signed gap']]
    decomp=[r for h,r in tab if h==['Pair','dU','dL','dgap','dG','d(lambda*P)']]
    clocks=[r for h,r in tab if h==['Method','T_produce','T_verify','T_total']]
    assert len(endpoint)==len(decomp)==6 and len(clocks)==1
    displayed_endpoints=displayed_decomp=displayed_clocks=0
    aliases={'D1':'MB-D1','P':'P-GRB'}
    for n,table in zip([3,4,5,6,7,8],endpoint):
        assert {r[0] for r in table}=={'P-GRB','ENS-C','M-B','MB-D1'} and len(table)==4
        for method,*values in table:
            for cell,k in zip(values,['U','L','gap']):displayed(cell,by[n,method][k]);displayed_endpoints+=1
    for n,table in zip([3,4,5,6,7,8],decomp):
        for direction,*values in table:
            c,p=[aliases.get(q,q) for q in direction.split('/')];d=pair[n,c,p]
            quantities=[d['dU'],d['dL'],d['dgap'],phys[n,c]['G']-phys[n,p]['G'],phys[n,c]['lambda_P']-phys[n,p]['lambda_P']]
            for cell,v in zip(values,quantities):displayed(cell,v);displayed_decomp+=1
    assert len(clocks[0])==4
    for method,*values in clocks[0]:
        for cell,k in zip(values,['T_produce','T_verify','T_total']):displayed(cell,by[8,method][k]);displayed_clocks+=1
    sections={
        1:block(prose,'On PB-C20-B','On PB-B20-S'),
        2:block(prose,'On PB-B20-S','## V35 open'),
        3:block(prose,'PB-C35-U remains','PB-B35-B also'),
        4:block(prose,'PB-B35-B also','## V50 common'),
        5:block(prose,'## V50 common','## V50 open gains'),
        6:block(prose,'## V50 open gains','## The complete six-role'),
        7:block(prose,'## Fixed PB-B35-B Seed1','## Fixed PB-C50-S Seed1'),
        8:block(prose,'## Fixed PB-C50-S Seed1','## Final candidate decision')}
    paragraph_values=[]
    def shown(n,value,fmt,label):
        token=format(value,fmt);assert token in sections[n],(n,label,token)
        paragraph_values.append(dict(group=n,claim=label,value=value,display=token))
    for n in [1,2]:
        assert len({by[n,m]['U'] for m in ['P-GRB','ENS-C','M-B','MB-D1']})==1
        shown(n,by[n,'MB-D1']['U'],'.10f','common physical U')
        shown(n,phys[n,'MB-D1']['G'],'.10f','common physical G')
        shown(n,phys[n,'MB-D1']['lambda_P'],'.10f','common weighted penalty')
        for m in ['P-GRB','ENS-C','M-B','MB-D1']:
            if n==1 and m=='P-GRB':continue
            assert by[n,m]['nonzero_numerical_certificate'];shown(n,by[n,m]['T_produce'],'.4f',m+' certified producer time')
    assert not by[1,'P-GRB']['certificate'] and by[2,'P-GRB']['nonzero_numerical_certificate']
    shown(1,by[1,'P-GRB']['L'],'.10f','cold open L');shown(1,by[1,'P-GRB']['gap'],'.10f','cold signed gap')
    for n,c,p in [(1,'MB-D1','M-B'),(1,'MB-D1','ENS-C'),(2,'MB-D1','P-GRB')]:shown(n,pair[n,c,p]['certified_time_ratio'],'.6g','actual certified ratio '+c+'/'+p)
    for n in [4,5,6,7,8]:
        for m in ['MB-D1','M-B','ENS-C','P-GRB']:
            shown(n,phys[n,m]['G'],'.10f',m+' physical G');shown(n,phys[n,m]['lambda_P'],'.10f',m+' weighted penalty')
    assert by[4,'P-GRB']['L']==0 and by[7,'P-GRB']['L']>0
    assert 'independent lower floor L=0' in sections[4] and '2.0271896642e-18' in sections[7]
    # Native costs/counts are rederived from original raw ledgers and result.
    costs={};mechanisms={};native_cost_rows=0;identities={}
    for n in range(1,9):
        identities[n]=rd(OUT/f'campaign/group{n:02d}/identity.json')
        l=next(l for l in identities[n]['launches'] if l['arm']=='MB-D1');d=Path(l['destination'])
        events=[json.loads(line) for line in text(d/'external/round120_events.jsonl').splitlines()]
        controller=rows(d/'external/paper_tree_events.csv')
        mechanisms[n]=dict(events=events,controller=controller)
        installed=[e for e in events if e['kind']=='root_formulation_installed'];proofs=[e for e in events if e['kind']=='paid_root_LP_returned']
        assert len([e for e in events if e['kind']=='extended_native_returned'])==(0 if n in [5,8] else 2 if n in [1,2] else 1)
        if n in [5,8]:
            assert not installed and len(proofs)==1
            nonexposed=[e for e in events if e['kind']=='not_exposed'];assert len(nonexposed)==1 and not nonexposed[0]['pair_complete']
            splits=[e for e in controller if e['event']=='atomic_split'];assert len(splits)==3
            assert all(e['detail']=='adaptive_mass_preserve_child_infeasibility_split' for e in splits[:2]) and splits[2]['detail']=='adaptive_mass_score_reaches_tau'
            leaves={e['leaf_id']:e for e in rows(d/'external/paper_leaf_ledger.csv')}
            assert all(leaves[q]['status']=='empty' and leaves[q]['lp_infeasible']=='1' for q in ['L0.1','L0.0.1'])
            if n==8:assert nonexposed[0]['leaf']=='L0.0.0.0';shown(n,nonexposed[0]['process_seconds'],'.7f','not exposed actual time')
        else:
            assert len(installed)==1 and len(proofs)==2
            root=rd(d/'external/round120_root_pair.json')
            assert by[n,'MB-D1']['U']>root['beta1']
            if n in [1,3,4,6,7]:shown(n,root['beta1'],'.10f','own beta1')
            if n in [3,4,6,7]:shown(n,installed[0]['installation_seconds'],'.7f','installation cost')
            if n in [3,6,7]:shown(n,root['m'],'.10f','root midpoint')
            if n in [6,7]:
                shown(n,root['b'],'.10f','root b')
                am=rows(d/'external/adaptive_mass_decision_ledger.csv')
                assert any(q['selected_action']=='exact-close' and q['deterministic_reason']=='adaptive_mass_no_strict_child_improvement' for q in am)
                assert not any(q['event']=='atomic_split' for q in controller)
            if n==6:
                shown(n,root['beta0'],'.10f','own beta0')
                sample=[e for e in events if e['kind']=='native_incumbent_observed'][-1]
                shown(n,sample['native_objective'],'.10f','last native objective');shown(n,sample['physical_F'],'.10f','last sample physical F')
                assert sample['h']==0 and sample['fixing_or_branching']=='unknown'
        if n<3:continue
        costs[n]=[]
        for launch in identities[n]['launches']:
            if launch['arm']=='P-GRB':continue
            dest=Path(launch['destination']);result=rd(dest/'result.json');ledger=rows(dest/'external/paper_optimize_ledger.csv')
            observations=rd(dest/'observations.json');returned={q['payload']['call'] for q in observations if q['payload']['kind']=='returned'}
            expected_LP=7 if n in [5,8] else 3
            assert len(ledger)==len(returned)==expected_LP+1
            assert sum(q['solve_kind']=='LP' for q in ledger)==expected_LP and sum(q['solve_kind']!='LP' for q in ledger)==1
            assert all(int(q['optimize_return_code'])==0 for q in ledger)
            fact=dict(method=launch['arm'],H=result['process_elapsed_at_exact_phase_start_seconds'],
                LP=sum(float(q['solver_runtime']) for q in ledger if q['solve_kind']=='LP'),
                MIP=sum(float(q['solver_runtime']) for q in ledger if q['solve_kind']!='LP'),T_verify=by[n,launch['arm']]['T_verify'])
            costs[n].append(fact);native_cost_rows+=1
        for key in ['H','LP','MIP']:
            for value in [min(q[key] for q in costs[n]),max(q[key] for q in costs[n])]:shown(n,value,'.4f',key+' recorded range')
            if key=='MIP':assert all(q['MIP']>q['H']+q['LP'] for q in costs[n])
        if n in [5,6,7]:
            for value in [min(q['T_verify'] for q in costs[n]),max(q['T_verify'] for q in costs[n])]:shown(n,value,'.4f','postseal verify range')
            shown(n,by[n,'P-GRB']['T_verify'],'.4f','cold postseal verify')
    shown(6,rd(Path(next(l for l in identities[6]['launches'] if l['arm']=='P-GRB')['destination'])/'result.json')['gurobi_runtime'],'.4f','cold actual MIP runtime')
    for n,label in [(7,'formal07'),(8,'continue08d1')]:shown(n,rd(OUT/f'fees/{label}/group_verification_receipt.json')['seconds'],'.7f' if n==8 else '.4f','separate group reconciliation')
    # Registered denominator and reference counts are independently tabulated.
    counts={}
    for layer,selected in [('new',range(1,7)),('all',range(1,9))]:
        counts[layer]={c+'/'+p:dict(collections.Counter(q['classification'] for q in pairs if q['group_number'] in selected and q['candidate']==c and q['control']==p)) for c,p in [('MB-D1','P-GRB'),('M-B','P-GRB'),('ENS-C','P-GRB'),('MB-D1','M-B'),('MB-D1','ENS-C'),('M-B','ENS-C')]}
    assert counts['new']['MB-D1/P-GRB']=={'WIN':5,'MIXED':1} and counts['all']['MB-D1/P-GRB']=={'WIN':7,'MIXED':1}
    assert counts['all']['M-B/P-GRB']=={'WIN':8} and counts['new']['M-B/ENS-C']=={'TIE':4,'LOSS':1,'WIN':1}
    assert counts['all']['M-B/ENS-C']=={'TIE':5,'LOSS':2,'WIN':1}
    assert counts['new']['MB-D1/M-B']==counts['new']['MB-D1/ENS-C']=={'LOSS':2,'TIE':2,'WIN':1,'MIXED':1}
    assert counts['all']['MB-D1/M-B']==counts['all']['MB-D1/ENS-C']=={'LOSS':2,'TIE':3,'WIN':2,'MIXED':1}
    certs={m:sum(a['nonzero_numerical_certificate'] for a in arms if a['seed']==0 and a['arm']==m) for m in ['P-GRB','ENS-C','M-B','MB-D1']}
    assert certs=={'P-GRB':1,'ENS-C':2,'M-B':2,'MB-D1':2}
    assert not any(a['nonzero_numerical_certificate'] and a['V'] in [35,50] for a in arms)
    assert not any(a['source_reduced'] or a['own_exact_zero'] for a in arms)
    assert not any(p['severe_regression'] for p in pairs) and len(ind['major_negative_results_review'])==9
    assert [k for k,v in decision['conditions'].items() if not v]==['at_least_two_exposed_material_M_B_gains_or_new_certificates']
    assert decision['new_D1_exposed']==5 and decision['new_exposed_M_B_gains']==1 and not any(decision['veto'].values())
    assert 'decision does not use ENS dominance as an additional hidden gate' in prose
    assert 'below the registered requirement of two' in prose and 'only PB-B50-U supplies an exposed new material D1/M-B WIN' in prose
    reference=rd(OUT/'paper_reference_recommendation.json')
    assert reference['method']=='M-B' and reference['project_default']=='ENS-C' and reference['default_changed'] is False
    assert not reference['instance_or_Seed_dispatch'] and not reference['automatic_further_batch']
    assert reference['all48_pairs_SHA']==sha(OUT/'all48_pairs.json') and reference['stage_decision_SHA']==sha(OUT/'stage_decision.json')
    # Exact historical direction comes from the finite restored R121 authority.
    history=text(ROOT/'results/unified_exact_round121/final_report.md')
    assert '| R98-C2 | MB-D1/M-B | LOSS | True | WIN | False | False |' in history
    assert '| R98-C2 | M-B/P-GRB | WIN | False | WIN | False | False |' in history
    historical=rd(ROOT/'results/unified_exact_round121/stage_decision.json')
    assert historical['execution_stage']=='COMPLETE' and historical['stage']=='ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK'
    assert 'historical R120 C2 Seed0 has severe D1/M-B LOSS (while M-B/P is WIN)' in prose,'historical comparison direction must identify D1/M-B'
    assert 'historical R120 C2 Seed0 severe M-B regression' not in prose
    limits=['not an instance winner selector','does not claim M-B dominates ENS-C','No method obtains a new V35/V50 nonzero certificate',
        'Both C50 D1-unexposed observations remain valid full-method results','batch ends without automatic extra inputs, Seeds, variants or algorithm changes',
        'No best-of-Seed endpoint, across-instance winner dispatch or cross-round exact speedup','Two Seeds do not estimate population probabilities',
        'finite, non-IID and nonfactorial','not mathematical contributions','not a guarantee against every possible floating-point error']
    assert all(q in prose for q in limits)
    recovery=rd(OUT/'recovery/group08/reaudit_receipt.json');investigation=rd(REVIEW/'group08_cold_investigation.json')
    assert 'F='+repr(investigation['best_committed_witness']['F']) in sections[8]
    assert 'final returned fleet has F='+repr(recovery['final_U']) in sections[8]
    assert 'Every other finalizer statement remains identical' in sections[8]
    assert all(repr(recovery[k]) in sections[8] for k in ['T_produce','T_verify','T_total','final_U','final_L'])
    assert 'stronger historical witness is not substituted' in sections[8]
    resource=rd(OUT/'resource_summary.json')
    assert str(resource['paid_outer_seconds'])+'/100000' in prose and str(resource['qualification_seconds'])+'/6000' in prose
    assert resource['paid_starts']==50 and resource['additional_distinct_controller_starts']==5 and resource['total_observed_or_conservative_starts']==55
    assert resource['qualification_seconds']<3000 and 'no soft-plan extension was needed' in prose
    for filename in USED:assert sha(filename)==USED[filename],'claims evidence changed during review'
    result=dict(decision='ACCEPT',scope='Actual bounded final complete paper interpretation numeric/display/stage/reference/history/limits review; publication and empty-root replay remain separate.',
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='independent executor /root/contract_review',review_script_SHA=sha(__file__),
        document_SHA=sha(path),sealed_prose_receipt_SHA=sha(OUT/'engineering/sealed_interpretation_receipt.json'),
        independent_scientific_review_SHA=sha(REVIEW/'post_formal_independent.json'),prior_case_text_preserved_except_two_pending_statements=True,
        endpoint_table_cells_checked=displayed_endpoints,decomposition_cells_checked=displayed_decomp,clock_table_cells_checked=displayed_clocks,
        additional_numeric_paragraph_checks=paragraph_values,raw_integrated_native_cost_rows=native_cost_rows,cost_ranges=costs,
        independently_tabulated_pair_counts=counts,clean_new_Seed0_certificate_counts=certs,
        all9_major_negatives_explicitly_retained=ind['major_negative_results_review'],
        independent_stage=decision['stage'],sole_unmet_positive_condition='distinct exposed new D1/M-B material gains:1<2',
        hidden_ENS_stage_gate=False,fixed_existing_paper_reference='M-B',project_default_unchanged='ENS-C',
        historical_direction='R120 C2 Seed0 D1/M-B severe LOSS; historical M-B/P remains WIN',
        all_unexposed_Seed_layers_recovery_failures_and_signed_gaps_retained=True,
        claim_limits_preserved=limits,evidence_files=len(USED),all_reviewed_evidence_unchanged=True,
        native_starts=0,Optimize=0,raw_or_production_helper_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('post_formal_prose_claims.json',result)

if __name__=='__main__':assert len(sys.argv)==2;run(sys.argv[1])
