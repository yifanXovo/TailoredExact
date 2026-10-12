"""Six-role exact inventory/scale analysis of sealed own outputs, zero Optimize.

Authored as offline analysis after the prospective producer was frozen. It is
not a producer dependency, route generator, strengthened LB, or certificate.
"""
import argparse,collections,json,time
from fractions import Fraction as R
from pathlib import Path
import round115_sublevel as inherited
import round108_reader as core
from read_round116 import ROUND

def ceiling(v):return -(-v.numerator//v.denominator)
def run(root):
    tick=time.perf_counter();root=Path(root).resolve();out=root/ROUND
    manifest=core.read(out/'input_manifest.json');fixed=core.read(out/'fixed_manifest.json');current=core.read(out/'reports_final/current_core.json')
    arms={(a['id'],a['arm']):a for a in current['arms']};roles=[];structure=[];ownrows=[]
    for p in manifest['roles']:
        path=root/p['input_path'];assert core.sha(path)==p['input_sha256'];interpretations={}
        reference=core.read(out/'qualification/reference'/p['id']/'reference_contract.json')
        assert reference['Optimize']==0 and reference['input_parameters']==p
        for interpretation in ['input_decimal','parsed_binary64']:
            a=inherited.instance(path,interpretation);b=inherited.bound(a);D=a['target'][1:];w=a['w'][1:];W=sum(w);delta=R(b['delta']);beta=R(b['beta']);own=[]
            for l in (l for l in fixed['launches'] if l['id']==p['id']):
                arm=arms[p['id'],l['arm']];d=core.portable(root,l['destination'])
                if not (d/'producer_receipt.json').exists():
                    own.append(dict(arm=l['arm'],actual_inventory='unknown',reason='no sealed producer output'));continue
                receipt=core.read(d/'producer_receipt.json');seal=core.read(d/'producer_seal.json')
                assert receipt['producer_seal_SHA']==core.sha(d/'producer_seal.json')
                assert core.sha(d/'result.json')==seal['required_SHA']['result.json']
                physical=core.full_fleet(root,p,core.read(d/'result.json'));Y=physical['Y'][1:]
                assert all(float(y).is_integer() for y in Y),'cannot use noninteger inventory in discrete arithmetic'
                Y=list(map(int,Y));U=inherited.objective(a,Y);K=sum(abs(y-d0) for y,d0 in zip(Y,D))
                ratios=[R(y,d0) for y,d0 in zip(Y,D)];den=a['n']*sum(ratios)
                G=sum(abs(x-y) for i,x in enumerate(ratios) for y in ratios[i+1:])/den if den else R(0)
                P=sum(w0*abs(r-1) for w0,r in zip(w,ratios))
                assert U==G+a['lam']*P and U>=delta*K
                assert b['necessary_total_interval'][0]<=sum(Y)<=b['B']
                assert abs(float(U)-physical['F'])<=1e-7
                if K:assert U>=beta
                sufficient=0<U<=beta
                q=dict(arm=l['arm'],Y=Y,K=K,sumY=sum(Y),exact_U=str(U),U_float=float(U),G=str(G),G_float=float(G),
                    P=str(P),P_float=float(P),lambda_P=str(a['lam']*P),lambda_P_float=float(a['lam']*P),
                    W=str(W),lambda_W=str(a['lam']*W),normalized_weighted_deviation=str(P/W),
                    strict_improvement_inventory_K_max=ceiling(U/delta)-1 if U>0 else None,
                    strict_improvement_only_Y_equals_D=sufficient,own_strict_Y_equals_D=Y==D,
                    beta_positive_minimum_attained_by_this_existing_fleet=K>0 and U==beta,
                    parsed_coefficients_interpretation=interpretation,producer_receipt_SHA=core.sha(d/'producer_receipt.json'),
                    result_SHA=core.sha(d/'result.json'),physical_feasibility_recomputed=True,new_route_constructed=False,
                    stronger_production_bound_or_certificate_added=False,formal_endpoint_fields_changed=False,
                    proof_evidence=arm['proof_evidence'],formal_protocol_qualified=arm['formal_protocol_qualified'])
                own.append(q);ownrows.append(dict(id=p['id'],interpretation=interpretation,**q))
            interpretations[interpretation]=dict(**b,W=str(W),W_float=float(W),lambda_W=str(a['lam']*W),lambda_W_float=float(a['lam']*W),
                inventory_total_minimum_K=max(0,b['sumD']-b['B'],b['necessary_total_interval'][0]-b['sumD']),
                target_inventory_mathematically_excluded=not b['target_total_admissible'],own_fleets=own,
                no_routability_conclusion_from_inventory_necessary_conditions=True,
                own_zero_exists=any(q.get('own_strict_Y_equals_D') and q.get('formal_protocol_qualified') for q in own))
        roles.append(dict(id=p['id'],input_SHA=p['input_sha256'],V=p['V'],M=p['M'],Q=p['Q_vector'],T=p['T_seconds'],interpretations=interpretations))
        v=interpretations['input_decimal'];structure.append(dict(id=p['id'],V=p['V'],M=p['M'],Q=p['Q_vector'],T_seconds=p['T_seconds'],
            B=v['B'],sumD=v['sumD'],sumQ=v['sumQ'],B_lo=v['necessary_total_interval'][0],B_hi=v['B'],
            target_stock_necessary_admissible=v['target_total_admissible'],minimum_necessary_K=v['inventory_total_minimum_K'],
            W=v['W'],W_float=v['W_float'],lambda_W=v['lambda_W'],lambda_W_float=v['lambda_W_float'],
            delta=v['delta'],beta=v['beta'],beta_float=v['beta_float'],own_zero_exists=v['own_zero_exists'],
            cold_reference_columns=reference['native_metadata']['columns'],cold_reference_rows=reference['native_metadata']['rows'],
            cold_reference_actual_types=reference['actual_types'],matrix_coefficient_min_abs=reference['coefficient_min'],
            matrix_coefficient_max_abs=reference['coefficient_max'],native_reference_Optimize=0,
            necessary_conditions_only=True,production_LB_enhanced=False))
    result=dict(Optimize=0,native_starts=0,new_routes=0,production_search_uses_analysis=False,necessary_conditions_only=True,
        formal_UB_LB_certificate_fields_updated=False,coefficient_interpretations=['literal decimal coefficients','parsed binary64 coefficients as exact rationals'],
        formula_authority='Round116 request and unchanged R115 pure arithmetic; no new mathematical mechanism',
        goal_SHA=core.sha(out/'goal.md'),arithmetic_implementation_SHA=core.sha(inherited.__file__),roles=roles,
        seconds=time.perf_counter()-tick,authored_offline_after_producer_freeze=True,
        limitation='beta and K bound are necessary inventory restrictions; neither routing sufficiency nor a full-fleet infeasibility proof; never fed to production')
    core.write(out/'objective_structure_analysis.json',result);core.table(out/'objective_structure.csv',structure);core.table(out/'own_objective_components.csv',ownrows)
    return dict(roles=6,own_component_rows=len(ownrows),seconds=result['seconds'],Optimize=0)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);a=parser.parse_args();print(json.dumps(run(a.root)),flush=True)
