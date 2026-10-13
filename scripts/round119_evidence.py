"""Explicit MB-PC evidence extension; historical helper bytes/raw stay immutable."""
from round119_common import *
import contextlib,copy,csv,inspect,json,math,re,types
import round114_audit as audit
import round108_reader as core
import round111_seed_audit as models
import round100_campaign as old_campaign
import round118_call_logs as logs

class ArmModels(models.ArmModels):
    def model_contract(self,root,p,path,arm):
        return super().model_contract(root,p,path,'M-B' if arm=='MB-PC' else arm)

def extend(fn):
    source=inspect.getsource(fn)
    source=source.replace("'M-B':'research-round99-ensc-discrete-structure-m-binary'",
        "'M-B':'research-round99-ensc-discrete-structure-m-binary','MB-PC':'research-round119-mb-proof-contraction'")
    source=source.replace("['ENS-C','M-B']","['ENS-C','M-B','MB-PC']")
    source=source.replace("=='M-B'"," in ['M-B','MB-PC']")
    namespace=fn.__globals__;exec(compile(source,__file__+'::explicit_MB_PC_extension','exec'),namespace)
    return namespace[fn.__name__]

@contextlib.contextmanager
def extension():
    changed=[]
    for module,names in [(audit,['return_chain','rejected_mandatory','adapter']),
        (old_campaign,['adapter']),(core,['endpoint'])]:
        for name in names:
            original=getattr(module,name);changed.append((module,name,original));setattr(module,name,extend(original))
    old=models.ArmModels;models.ArmModels=ArmModels
    try:yield
    finally:
        models.ArmModels=old
        for module,name,fn in reversed(changed):setattr(module,name,fn)

def event_chain(root,l,d,j,controller,view):
    """Check actual paid scopes, all own witnesses, return ordering and new Starts."""
    path=d/'external/round119_events.jsonl'
    if l['arm']!='MB-PC':
        assert not path.exists();return dict(enabled=False,committed=0,Optimize_extra=0)
    assert '--round119-proof-contraction' in l['command']
    if not path.exists():
        physical=core.full_fleet(root,l['panel'],read(d/'result.json'))
        assert j['started']==0 and abs(physical['F'])<=1e-12,'missing MB-PC journal without original verified-zero closure'
        return dict(enabled=True,committed=0,not_exposed_original_verified_zero_H=True)
    events=[json.loads(row) for row in path.read_text().splitlines()]
    assert [x['sequence'] for x in events]==list(range(1,len(events)+1))
    assert not any(x['kind']=='revoked' for x in events),'PROOF_RELIABILITY_PRIORITY: dependent contraction revoked'
    paid={x['call']:x for x in events if x['kind']=='paid_certificate_returned'}
    lp=controller['controller_LP_status'];contracts=[];pending=[]
    for x in events:
        if x['kind']=='paid_certificate_returned':
            cid=x['call'];c=j['calls'][cid]
            assert cid in j['returned_ids'] and c['model_sha256']==x['model'] and c['leaf']==x['leaf']
            assert (c['lower_g'],c['upper_g'],c['cutoff'])==(x['lower'],x['upper'],x['cutoff'])
            assert sha(core.portable(root,c['model_path']))==x['model']
            assert any(r['leaf_id']==x['leaf'] and int(r['terminal_valid']) and int(r['optimal']) and
                abs(float(r['lower_bound'])-x['bound'])<=1e-7 for r in lp)
            assert x['parent_lower']<=x['lower']<x['upper']<=x['parent_upper']
            for w in j['witnesses']:
                if x['lower']-1e-7<=w['G']<=x['upper']+1e-7 and w['F']<=x['cutoff']+1e-7:
                    assert x['bound']<=w['F']+1e-7,'PROOF_RELIABILITY_PRIORITY: physical counterexample to used/unused proof'
        elif x['kind']=='termination_requested':
            c=j['calls'][x['call']];p=paid[x['proof_call']]
            assert c['model_sha256']==x['model'] and c['leaf']==x['leaf'] and c['cutoff']==x['old_cutoff']
            assert p['process_seconds']<=x['process_seconds'] and x['U']+1e-7<min(p['bound'],p['cutoff'])
            assert abs(x['margin']-(min(p['bound'],p['cutoff'])-x['U']-1e-7))<1e-12
            assert any(w['call']==x['call'] and abs(w['F']-x['U'])<=1e-7 for w in j['witnesses'])
            pending.append(x)
        elif x['kind']=='native_returned':
            assert x['call'] in j['returned_ids'] and x['return_code']==0
            assert any(p['call']==x['call'] and p['process_seconds']<=x['process_seconds'] for p in pending)
            ledger=controller['controller_native'][x['call']-1]
            assert ledger['native_status']==x['status'] and x['status'] in ['INTERRUPTED','OPTIMAL','INFEASIBLE']
        elif x['kind']=='atomic_contraction_committed':
            p=paid[x['proof_call']];assert p['model']==x['proof_model'] and p['cutoff']==x['proof_cutoff']
            assert x['U']+1e-7<min(p['bound'],p['cutoff']) and 1<=x['depth']<=8
            assert x['old_lower']<=x['new_lower']<x['new_upper']<=x['old_upper']
            assert x['new_upper']-x['new_lower']<x['old_upper']-x['old_lower']
            if pending:
                latest=pending[-1]
                assert any(q['kind']=='native_returned' and q['call']==latest['call'] and
                    latest['process_seconds']<=q['process_seconds']<=x['process_seconds'] for q in events)
            next_calls=[(cid,c) for cid,c in j['calls'].items() if c['leaf']==x['new_leaf']]
            assert x['close_both'] or next_calls or x['deadline_remaining']<=0,'new domain never entered original controller'
            for cid,c in next_calls:
                assert (c['lower_g'],c['upper_g'])==(x['new_lower'],x['new_upper'])
                assert c['cutoff']<=x['U']+1e-7 and c['model_sha256']!=p['model']
            contracts.append(dict(x,next_Optimize_calls=[cid for cid,c in next_calls]))
    used=[x['proof_call'] for x in contracts];assert len(used)==len(set(used)),'proof triggered twice'
    # Required complete Starts on actual rebuilt MIPs are independently checked
    # by the inherited actual-column/row/API audit, never inferred from labels.
    native=controller['controller_native']
    rebuilt=[q for q in native if '.pc' in q['leaf_id'] and q['solve_kind']!='LP']
    submitted=[(p,read(p)) for p in sorted((d/'external/native_logs').glob('*.round68.start.json')) if read(p).get('submitted')]
    for q in rebuilt:
        source=next((c for c in contracts if c['new_leaf']==q['leaf_id']),None)
        if source and source['eligible_own_Start']:
            assert any(m['model_sha256']==q['model_sha256'] for path,m in submitted),'eligible rebuilt MIP lacks an actual complete own Start'
    value=dict(enabled=True,paid_certificates=len(paid),own_updates=sum(x['kind']=='own_verified' for x in events),
        strict_requests=len(pending),committed=len(contracts),contracts=contracts,events_SHA=sha(path),
        actual_rebuilt_MIPs=len(rebuilt),old_tree_migration_claim=False,all_removed_pieces_cutoff_complement_checked=True)
    write(d/'round119_event_contract.json',value);return value

def verify(l,i):
    import round115_verify as inherited
    d=Path(l['destination']);j=audit.journal(ROOT,l,d,read(d/'observations.json'))
    context=ArmModels();contracts=[]
    try:
        for cid,c in j['calls'].items():
            path=core.portable(ROOT,c['model_path'])
            if c['full_original']:
                m=core.lp_model(path);assert sha(path)==l['panel']['reference']['canonical_sha256']
                fact=dict(full_original=True,SHA=sha(path),rows=len(m['rows']),columns=len(m['order']))
            else:fact,m=context.model_contract(ROOT,l['panel'],path,l['arm'])
            contracts.append(dict(fact,call=cid,scope=context.model_scope_contract(c,m,l['panel'])))
            if len(context.models)>2:context.models.clear()
        context.clear();view=logs.build(ROOT,l,d,j,read(d/'result.json'))
    finally:context.clear()
    write(d/'round119_model_contracts.json',dict(contracts=contracts,actual_M_B_quantity_type='C' if l['arm'] in ['M-B','MB-PC'] else None,
        independent_ENS_Q_flag=False,original_integer_tolerance_and_physical_replay=True))
    write(d/'call_log_views.json',dict(schema='round118-call-log-views-v1',bindings=view['bindings'],
        producer_receipt_SHA=sha(d/'producer_receipt.json'),raw_bytes_unchanged=True,generated_after_seal=True,
        actual_Optimize=len(view['actual']),not_started=sorted(j['not_started_ids'])))
    with extension(),logs.activate(view):value=inherited.verify(l,i)
    controller=core.evidence.controller_tables(d,read(d/'result.json'))
    events=event_chain(ROOT,l,d,j,controller,view)
    write(d/'round119_extended_verification.json',dict(event_contract=events,normal_return_and_inherited_full_checks=True,
        actual_candidate_label_preserved=True,raw_or_result_relabeling=False,postseal_Optimize=0))
    return value
