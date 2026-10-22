"""Finite preformal real paid-H controls on existing training input S12."""
from round130_common import *
from round130_campaign import prepare_group
from round127_data import TRAIN
from compare_round112_startup import reconstruct as H
import round108_reader as core
import copy

def prepare():
    p=copy.deepcopy(TRAIN[0]);p.update(cap_seconds=90,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},source='qualification',inventory='unspecified')
    plans=[('qualification/native_S12_S0',['P','PS','S2','S2R'],0),('qualification/native_S12_S1',['PS','S2R'],1)]
    for name,methods,seed in plans:
        if not (OUT/name/'identity.json').exists():prepare_group(name,'E3',p,methods,seed)
    write(OUT/'qualification/native_plan.json',dict(plans=plans,formal_performance=False,existing_training_only=True,nominal_seconds=540))

def run():
    for name,_,_ in read(OUT/'qualification/native_plan.json')['plans']:
        if (OUT/name/'reconstructed.json').exists():continue
        label=name.replace('/','_');attempt=len(list((OUT/'fees').glob(label+'_*')))+1
        assert metered(label+f'_{attempt:02d}','qualification',[PYTHON,ROOT/'scripts/round130_campaign.py',name],reservation=28800+2400)==0
    records=[]
    for name,methods,seed in read(OUT/'qualification/native_plan.json')['plans']:
        camp=OUT/name;i=read(camp/'identity.json');aa=read(camp/'reconstructed.json')['arms']
        assert all(a['formal_protocol_qualified'] for a in aa)
        own={}
        for a,l in zip(aa,i['launches']):
            d=Path(l['destination']);r=read(d/'result.json')
            if l['method']!='P':own[l['method']]=H(ROOT,l['panel'],d)
            if l['method']=='PS':
                assert a['native_Optimize']==1
                assert core.lp_model(d/'compact.lp')==core.lp_model(camp/'reference'/l['id']/'original.lp')
                assert read(d/'native.log.round112.start.json')['submitted']
                assert read(d/'round130_parameters.json')['NumStart_before_optimize']==1
            if l['method']=='S2R':
                ledger=core.rows(d/'external/paper_optimize_ledger.csv')
                assert [x['solve_kind'] for x in ledger]==['LP','MIP']
                assert all(x['leaf_id']=='L0' for x in ledger)
                assert r['external_gini_tree_split_count']==0
                receipts=[read(x) for x in (d/'external/native_logs').glob('*.round68.start.json')]
                assert sum(bool(x['submitted']) for x in receipts)==1
            records.append(dict(method=l['method'],seed=seed,qualified=a['formal_protocol_qualified'],native_Optimize=a['native_Optimize'],
                certificate=a['certificate'],status=a['status'],T_produce=a['T_produce'],destination=str(d)))
        ref=own['PS']
        for method,h in own.items():
            assert h['complete'] and ref['complete'] and h['fleet']==ref['fleet'] and h['semantic_traces']==ref['semantic_traces']
    write(OUT/'qualification/native_qualification.json',dict(UTC=utc(),passed=True,records=records,
        actual_paid_complete_H_fleet_and_semantic_actions_equal=True,S2R_nonzero_two_call_chain=True,
        PS_original_compact_full_Start_mapping_submission_readback_and_own_MIP=True,
        unequal_vehicle_capacities=TRAIN[0]['Q_vector'],no_formal_role_screened=True))
    print('NATIVE_INCREMENTAL_QUALIFICATION_PASS')
if __name__=='__main__':{'prepare':prepare,'run':run}[sys.argv[1]]()
