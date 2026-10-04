"""Completed-campaign compact reporting through the established R100 reader.
Performance must be idle before this heavier artifact pass. No Optimize calls.
"""
import sys,json
import round101_reporting_core as inherited
from round101_recover_scope import records_view
from round100_idle import ensure_idle
from round101_common import *

def main(label,campaigns):
    ensure_idle();inherited.OUT=OUT
    original_read=inherited.read
    def receipt_view(path):
        value=original_read(path)
        if Path(path).name=='receipt.json' and 'optimizer_calls' not in value:
            name=Path(path).parent.name
            if name in ['pure01','pure02','pure03','pure04','pure05','cost_replay01','numeric_replay01','matrix_guards01']:
                assert value['maximum_optimizer_calls']==0
                value=dict(value,optimizer_calls=0)
        return value
    inherited.read=receipt_view
    inherited.extract(label,campaigns)
    target=OUT/label;fleet=[];isolation=[]
    for name in campaigns:
        camp=OUT/name
        done=records_view(camp)
        group={r['arm']:r for r in done if r['id']=='F2'}
        if name.startswith('isolation'):
            for reference,candidate in [('ENS-C','FLEET-SHELL'),('FLEET-SHELL','FLEET-SHADOW'),
                    ('FLEET-SHADOW','FLEET-SUBMIT'),('FLEET-SUBMIT','FLEET-ROOT')]:
                if reference not in group or candidate not in group:continue
                a,b=group[reference],group[candidate];both=a['endpoint']['certificate'] and b['endpoint']['certificate']
                isolation.append(dict(campaign=name,role='F2',reference=reference,candidate=candidate,
                    both_certified=both,reference_certificate=a['endpoint']['certificate'],candidate_certificate=b['endpoint']['certificate'],
                    reference_full_seconds=a['completion']['end_to_end_seconds'],candidate_full_seconds=b['completion']['end_to_end_seconds'],
                    certified_time_delta=b['completion']['end_to_end_seconds']-a['completion']['end_to_end_seconds'] if both else None,
                    reference_gap=a['endpoint']['gap'],candidate_gap=b['endpoint']['gap'],
                    inference='Combined parameter/execution effects and changed native paths; no same-point causal decomposition'))
        for r in done:
            d=Path(r['destination']);base=dict(campaign=name,number=r['number'],role=r['id'],arm=r['arm'])
            for p in sorted((d/'external/native_logs').glob('*.round101.summary.json')):
                s=read(p);log=Path(str(p).replace('.round101.summary.json',''))
                native,_,_=inherited.native_log(log)
                cuts=json.loads(native['cuts'])
                certs=Path(str(p).replace('.summary.json','.certificates.jsonl'))
                saved=[json.loads(x) for x in certs.read_text().splitlines()] if certs.exists() else []
                literal={ (tuple(sorted((col,coef) for col,coef,value in row['columns'])),row['proof']['rank']) for row in saved }
                fleet.append(dict(base,path=p.relative_to(ROOT).as_posix(),summary_sha256=sha(p),
                    native_User_cut_count=cuts.get('User'),native_cut_counts=native['cuts'],
                    unique_literal_rows_in_saved_certificates=len(literal),
                    saved_row_nonzeros_min=min((len(row['columns']) for row in saved),default=None),
                    saved_row_nonzeros_max=max((len(row['columns']) for row in saved),default=None),
                    unique_event_rank_proof_keys=s.get('unique_rows'),
                    completed_nontrivial_rank_problems=s['proved']-s['unexcluded'],
                    proof_count_scope='Completed necessary-system ranks including cache hits; unexcluded means rank equals support; small/large counts are proof requests, not independent DP executions',**s))
    inherited.csv_write(target/'fleet_native_calls.csv',fleet)
    inherited.csv_write(target/'isolation_pairs.csv',isolation)
    from round101_budget import account
    budget=account();assert not budget['reserved'] and not budget['incomplete_receipt_batches'] and budget['within_limits']
    write(target/'fee_reconciliation.json',budget)
    write(target/'round101_reporting_identity.json',dict(optimizer_calls=0,
        inherited_reader_sha256=sha(ROOT/'scripts/round100_results.py'),adapted_reader_sha256=sha(inherited.__file__),wrapper_sha256=sha(__file__),
        receipt_adapter='Actual zero-Optimize standalone pure/replay batches; missing native final results stay missing; immutable recovery06 overlay qualifies only original committed arm6 prefix; no forensic receipts modified',
        API_success_is_not_native_retention=True,default_changed=False))
    print(json.dumps(dict(passed=True,fleet_native_calls=len(fleet),billed_starts=budget['completed_charged_starts'],
        conservatively_charged_seconds=budget['completed_charged_seconds'],Optimize=0)))

if __name__=='__main__':main(sys.argv[1],sys.argv[2:])
