"""Read sealed complete-arm evidence and rebuild each paid inventory price.

Run only after the serial panel has stopped, under one verification outer.
No Optimize call, legacy evidence overwrite, or retrospective witness is used.
"""
from fractions import Fraction as F
from round108_reader import lp_model
from round151_math import scope_from_model
from round152_math import unary_dp
from round143_math import outward
from round143_lp import semantics
from round156_review import exact_value
from round156_common import *

def run(label):
    from round100_gurobi_runtime import gp,binding
    from round100_idle import ensure_idle
    from round150_lp import affinity
    from round153_pricing import Oracle
    configure();ensure_idle();affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'review'/label;target.mkdir(parents=True,exist_ok=False)
    matrix=read(OUT/'confirmation_matrix.json');admit=read(OUT/'review/confirmation_admission.json')
    assert admit['decision']=='ACCEPT' and admit['matrix_SHA']==sha(OUT/'confirmation_matrix.json')
    candidate=read(OUT/'candidate_manifest.json');facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for group in matrix['groups']:
            launch=group['launch'];dest=Path(launch['destination']);method=launch['R156_method']
            endpoint=read(dest/'round156_endpoint.json');close=read(dest/'verification_closeout.json')
            assert all(close[k] for k in ['necessary_verification_complete','implementation_qualified','evidence_complete','native_proof_qualified','performance_eligible'])
            for field,name in [('audit_SHA','audit.json'),('verification_closeout_SHA','verification_closeout.json'),('arm_total_receipt_SHA','arm_total_receipt.json')]:
                assert endpoint[field]==sha(dest/name),(dest,field)
            for field,name in [('own_evidence_SHA','own_evidence.json'),('claims_SHA','claims.json'),('rejection_SHA','source_rejections.json'),('producer_receipt_SHA','producer_receipt.json')]:
                # The inherited closeout is the authoritative filename map.
                # Not all historical writers use the same optional filenames.
                if (dest/name).exists():assert close[field]==sha(dest/name)
            audit=read(dest/'audit.json');assert audit['passed'] and not audit['source_rejections']
            assert endpoint['source_commit']==candidate['source_commit']
            assert endpoint['PE_SHA']==candidate['production_PE_SHA'] and endpoint['DLL_SHA']==DLL_SHA
            assert endpoint['input_SHA']==launch['panel']['input_sha256']==sha(ROOT/launch['panel']['input_path'])
            assert endpoint['T_seconds']==launch['panel']['T_seconds'] and endpoint['Q_vector']==launch['panel']['Q_vector']
            assert endpoint['cap_seconds']==launch['cap_seconds'] and endpoint['H_complete']
            assert endpoint['R156_method']==method and endpoint['seed']==0
            assert endpoint['T_cert'] is None or endpoint['certificate']
            fee=read(OUT/'fees'/f'confirmation_{group["position"]:03}'/'receipt.json')
            assert fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout']
            assert fee['G1_seconds']>=endpoint['T_total']>=endpoint['T_produce']
            control='round153_control_audit.json' if method=='B' else 'round154_control_audit.json'
            proof=read(dest/control);root=proof['root']
            fact=dict(position=group['position'],role=launch['id'],method=method,
                endpoint_SHA=sha(dest/'round156_endpoint.json'),closeout_SHA=sha(dest/'verification_closeout.json'),
                original_physical_identity=True,own_H=True,sealed_physical_audit_reused=True,
                price_reconstructed=False,Optimize=0)
            if method=='B':
                assert root is None and not proof['enabled']
                facts.append(fact);continue
            assert proof['PASS'] and proof['proof_only'] and proof['all_original_columns_bounds_objective_preserved']
            assert proof['helper_paid_inside_process'] and proof['complete_root_checked'] and proof['cutoff_complement_checked']
            ledger=proof['proof_ledger']
            assert ledger['root_complete'] and ledger['sources_live'] and ledger['native_floor_rows']==0 and ledger['AM_uses_search_bounds']
            assert ledger['proof_L']==endpoint['L'] and ledger['raw_search_L']==endpoint['raw_search_L']
            assert all(m['floor_rows']==0 for m in proof['models'])
            assert root['qualified'] and not root['global_deadline_stop'] and not root['offline_data_used']
            folder=dest/'external/round153_floor';s=read(folder/'source.json');r=read(folder/'result.json')
            p=read(folder/'pricing/result.json');c=read(folder/'pricing/call.json')
            scope=scope_from_model(lp_model(Path(s['source'])),root['Bminus'],root['B'])
            assert scope==s['scope']==r['scope']==p['scope']==c['scope']
            assert sha(s['source'])==root['source_SHA']==s['source_SHA']==r['source_SHA']
            assert Path(s['source']).is_relative_to(dest)
            nodes=16384 if method=='Eplus' else 4096
            assert root['node_limit']==r['node_limit']==c['node_limit']==nodes
            manifest=OUT/('helper_manifest_Eplus.json' if method=='Eplus' else 'helper_manifest_E.json')
            assert sha(manifest)==root['helper_manifest_SHA']==s['helper_manifest_SHA']==r['source_helper_manifest_SHA']
            deps=read(manifest)['helper_dependencies'];assert s['dependencies']==deps
            for name,digest in r['loaded_project_sources'].items():assert sha(ROOT/name)==deps[name]==digest
            if method=='Eplus':
                assert s['producer_rule']==r['producer_rule']==root['producer_rule']=='RN16384_original_gap'
                assert r['no_historical_inventory_or_price_loaded'] and s['no_historical_inventory_or_price_loaded']
                assert (folder/'response.txt').read_text().split()[0]=='R156-FLOOR-v1'
            d={(site['i'],y):F(site['omega'])*abs(F(site['c'])*y-1) for site in scope['stations'] for y in site['support']}
            assert p['beta']==1 and p['d_exact']=={f'{i}:{y}':str(v) for (i,y),v in d.items()}
            fallback=F(scope['gamma_L'])+F(unary_dp(scope,d)['exact'])
            anchors={int(k):F(v) for k,v in c['anchors_exact'].items()};scale=F(c['scale'])
            with gp.read(str(folder/'pricing/model.mps'),env=env) as saved:
                assert sha(folder/'pricing/model.mps')==c['model_SHA']
                oracle=Oracle(scope,env,old_joint=True);m=oracle.model
                m.setObjective(float(1/scale)*oracle.q+gp.quicksum(outward((value-anchors[k[0]])/scale,False)*oracle.x[k] for k,value in d.items()))
                m.update();assert semantics(m)==semantics(saved)
                correction=sum((max([F(0)]+[F(oracle.x[site['i'],y].Obj)-(d[site['i'],y]-anchors[site['i']])/scale for y in site['support']]) for site in scope['stations']),F(0))
                correction+=max(F(0),(F(oracle.q.Obj)-1/scale)*F(scope['gamma_U']))
                assert correction==F(c['objective_correction_scaled_exact']);oracle.close()
            q=p['calls'][0];assert q['Status'] in (2,8) and q['bound_status_qualified']
            lower=max(fallback,scale*(F(q['native_bound'])-F(c['numerical_guard_scaled'])-correction)+sum(anchors.values(),F(0)))
            if p['zero_lower'] is not None:lower=min(lower,F(p['zero_lower']))
            assert F(r['lower'])<=lower and r['lower']==p['lower']==root['lower']
            values=[]
            for v in p['stocks']:
                checked=exact_value(scope,v['Y']);assert checked['feasible'] and checked['phi']==F(v['price_exact'])
                values.append(checked['phi'])
            assert F(r['upper'])>=min(values) and r['upper']==p['upper']
            fact.update(price_reconstructed=True,lower=r['lower'],inventory_upper=r['upper'],
                capacity=nodes,nodes=q['nodes'],price_Status=q['Status'],true_stocks_checked=len(values),
                full_RN_matrix_match=True,exact_original_beta_and_penalty=True,signed_transport_recomputed=True,
                helper_seconds=root['helper_process_seconds'],no_formal_floor_rows=True)
            facts.append(fact)
    assert len(facts)==9 and sum(f['price_reconstructed'] for f in facts)==8
    write(target/'result.json',dict(PASS=True,facts=facts,Optimize=0,source_SHA=sha(__file__),
        same_agent_independent_reconstruction=True,nonimplementer_agent_review=False,
        no_sealed_evidence_overwritten=True,old_qualified_physical_verifiers_reused=True))
    print(json.dumps(facts),flush=True)

if __name__=='__main__':run(sys.argv[1])
