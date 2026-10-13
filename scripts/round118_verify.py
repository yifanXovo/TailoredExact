"""R115 measurement-v2 closeout with explicit per-call raw-log views."""
import json,time
from pathlib import Path
import round114_audit as audit
import round115_verify as inherited
import round118_call_logs as logs
import round111_seed_audit as models
from round118_common import ROOT,read,write,sha

def verify(l,i):
    d=Path(l['destination']);j=audit.journal(ROOT,l,d,read(d/'observations.json'))
    context=models.ArmModels();contracts=[]
    try:
        for cid,c in j['calls'].items():
            path=audit.core.portable(ROOT,c['model_path'])
            if c['full_original']:
                m=audit.core.lp_model(path);assert sha(path)==l['panel']['reference']['canonical_sha256']
                fact=dict(full_original=True,SHA=sha(path),rows=len(m['rows']),columns=len(m['order']))
            else:fact,m=context.model_contract(ROOT,l['panel'],path,l['arm'])
            contracts.append(dict(fact,call=cid,scope=context.model_scope_contract(c,m,l['panel'])))
        view=logs.build(ROOT,l,d,j,read(d/'result.json'))
    finally:context.clear()
    write(d/'round118_model_contracts.json',dict(contracts=contracts,actual_M_B_quantity_type='C' if l['arm']=='M-B' else None,
        independent_ENS_Q_flag=False,original_integer_tolerance_and_physical_replay=True))
    write(d/'call_log_views.json',dict(schema='round118-call-log-views-v1',bindings=view['bindings'],
        producer_receipt_SHA=sha(d/'producer_receipt.json'),raw_bytes_unchanged=True,
        generated_after_seal=True,actual_Optimize=len(view['actual']),not_started=sorted(j['not_started_ids'])))
    with logs.activate(view):return inherited.verify(l,i)
