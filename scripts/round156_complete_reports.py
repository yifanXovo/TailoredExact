"""Nine sealed complete arms: paid bounds, certificates and gap decomposition."""
import math
from round156_reports import table
from round156_common import *

def run():
    matrix=read(OUT/'confirmation_matrix.json');arms=[]
    for group in matrix['groups']:
        launch=group['launch'];dest=Path(launch['destination']);arm=read(dest/'round156_endpoint.json')
        close=read(dest/'verification_closeout.json')
        assert close['implementation_qualified'] and close['evidence_complete'] and close['performance_eligible']
        assert sha(dest/'audit.json')==arm['audit_SHA']
        root=read(dest/'round153_control_audit.json')['root'];method=launch['R156_method']
        helper=read(dest/'external/round153_floor/result.json') if root and root['qualified'] else None
        fee=read(OUT/'fees'/f'confirmation_{group["position"]:03}'/'receipt.json')
        assert fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout']
        raw=arm.get('raw_search_L',arm['L']);gap=arm['U']-arm['L']
        row=dict(role=launch['id'],method=method,window=launch['cap_seconds'],U=arm['U'],raw_L=raw,proof_L=arm['L'],
            absolute_gap=gap,relative_gap=gap/abs(arm['U']) if arm['U'] else None,
            T_produce=arm['T_produce'],T_verify=arm['T_verify'],T_total=arm['T_total'],T_cert=arm['T_cert'],
            certificate=arm['certificate'],outer_G1_seconds=fee['G1_seconds'],
            helper_seconds=root['helper_process_seconds'] if root else 0.,
            inventory_lower=root['lower'] if helper else None,inventory_upper=helper['upper'] if helper else None,
            inventory_node_capacity=root['node_limit'] if root else None,
            posthoc_remaining_scalar_floor_opportunity=max(0.,helper['upper']-max(raw,root['lower'])) if helper else None,
            PE_SHA=arm['PE_SHA'],DLL_SHA=arm['DLL_SHA'],input_SHA=arm['input_SHA'],H_semantic_SHA=arm['H_semantic_SHA'],
            endpoint_SHA=sha(dest/'round156_endpoint.json'),destination=str(dest),source_commit=arm['source_commit'])
        if not row['certificate']:assert row['T_cert'] is None
        if method=='B':assert root is None
        else:
            assert root['qualified'] and not root['global_deadline_stop']
            assert root['node_limit']==(16384 if method=='Eplus' else 4096)
            ledger=read(dest/'round154_control_audit.json')['proof_ledger']
            assert ledger['native_floor_rows']==0 and ledger['AM_uses_search_bounds']
        assert row['absolute_gap']>=-1e-7
        arms.append(row)
    assert len(arms)==9 and len({r['PE_SHA'] for r in arms})==1
    pairs=[]
    for role in dict.fromkeys(r['role'] for r in arms):
        by={r['method']:r for r in arms if r['role']==role}
        comparisons=[('E','Eplus')]+([('B','E'),('B','Eplus')] if 'B' in by else [])
        for first,second in comparisons:
            a,b=by[first],by[second]
            assert a['input_SHA']==b['input_SHA'] and a['window']==b['window']
            assert a['H_semantic_SHA']==b['H_semantic_SHA']
            dU=b['U']-a['U'];dL=b['proof_L']-a['proof_L'];dgap=b['absolute_gap']-a['absolute_gap']
            assert math.isclose(dgap,dU-dL,abs_tol=1e-15,rel_tol=0.)
            pairs.append(dict(role=role,first=first,second=second,window=a['window'],
                first_U=a['U'],second_U=b['U'],first_raw_L=a['raw_L'],second_raw_L=b['raw_L'],
                first_proof_L=a['proof_L'],second_proof_L=b['proof_L'],first_gap=a['absolute_gap'],second_gap=b['absolute_gap'],
                delta_U=dU,delta_proof_L=dL,delta_gap=dgap,delta_T_produce=b['T_produce']-a['T_produce'],
                delta_T_verify=b['T_verify']-a['T_verify'],delta_T_total=b['T_total']-a['T_total'],
                delta_T_cert=b['T_cert']-a['T_cert'] if a['certificate'] and b['certificate'] else None,
                first_certificate=a['certificate'],second_certificate=b['certificate'],
                first_helper_seconds=a['helper_seconds'],second_helper_seconds=b['helper_seconds'],
                independently_paid_own_H_and_floor=True,same_PE=True,posthoc_instance_switch=False))
    write(OUT/'reports/complete_arms.json',dict(arms=arms,missing_positions=[]))
    write(OUT/'reports/complete_pairs.json',dict(pairs=pairs))
    table(OUT/'reports/complete_arms.csv',arms);table(OUT/'reports/complete_pairs.csv',pairs)
    print(json.dumps(dict(arms=arms,pairs=pairs)),flush=True)

if __name__=='__main__':run()
