"""Read-only Optimize views bound by serial call, immutable model and ledger.

Whole raw logs are never edited. A view is a byte interval, not a replacement
call or a reason to relax lifecycle/coverage/claim checks. Ambiguity rejects.
"""
from __future__ import annotations
import collections, contextlib, contextvars, hashlib, json, math, re
from pathlib import Path

ACTIVE=contextvars.ContextVar('round118_call_log_views',default=None)

def digest(data):return hashlib.sha256(data).hexdigest()
def segments(data):
    heads=list(re.finditer(rb'(?m)^Optimize a model with ',data))
    if not heads: return []
    starts=[0]
    for previous,current in zip(heads,heads[1:]):
        region=data[previous.end():current.start()]
        versions=list(re.finditer(rb'(?m)^Gurobi Optimizer version ',region))
        assert len(versions)==1,'UNRESOLVED: missing/duplicate per-call version preamble'
        boundary=previous.end()+versions[0].start()
        prefix=data[previous.end():boundary]
        banners=list(re.finditer(rb'(?m)^Gurobi [^\r\n]+ logging started ',prefix))
        logfile=list(re.finditer(rb'(?m)^Set parameter LogFile to value ',prefix))
        if banners:boundary=previous.end()+banners[-1].start()
        elif logfile:boundary=previous.end()+logfile[-1].start()
        starts.append(boundary)
    spans=list(zip(starts,starts[1:]+[len(data)]))
    for lo,hi in spans:
        part=data[lo:hi]
        assert part.count(b'Optimize a model with ')==part.count(b'Gurobi Optimizer version ')==1
        assert re.search(rb'(Solved in |Explored \d+ nodes|Infeasible model|Model is infeasible)',part),'UNRESOLVED: no terminal evidence'
        assert re.search(rb'(Optimal objective|Best objective|Infeasible model|Model is infeasible)',part),'UNRESOLVED: no terminal status/value'
    return spans

def build(root,l,d,j,r,model_parser=None):
    import round108_reader as core
    root=Path(root).resolve();d=Path(d);model_parser=model_parser or core.lp_model
    actual=[cid for cid in j['calls'] if cid not in j['not_started_ids']]
    assert set(actual)==j['actual_started_ids'],'UNRESOLVED: declared call has no actual start/disposition'
    ledger=core.rows(d/'external/paper_optimize_ledger.csv') if l['arm'] in ['ENS-C','M-B'] and actual else []
    assert not ledger or len(ledger)==len(actual),'UNRESOLVED: ledger count'
    groups=collections.defaultdict(list);models=collections.OrderedDict();facts={};views={};bindings=[]
    for cid in j['not_started_ids']:
        c=j['calls'][cid];path=core.portable(root,c['native_log_path'])
        if path.is_file() and not any(core.portable(root,j['calls'][a]['native_log_path'])==path for a in actual):
            assert not segments(path.read_bytes()),'UNRESOLVED: not_started has actual Optimize bytes'
    for ordinal,cid in enumerate(actual):
        c=j['calls'][cid];path=core.portable(root,c['model_path'])
        assert path.is_file() and core.sha(path)==c['model_sha256'],'UNRESOLVED: immutable complete model absent'
        model=models.pop(c['model_sha256'],None)
        if model is None:model=model_parser(path)
        models[c['model_sha256']]=model
        if len(models)>2:models.popitem(last=False)
        core.model_scope_contract(c,model,l['panel'])
        facts[cid]=(len(model['rows']),len(model['order']),collections.Counter(model['types'].values()))
        if c['full_original']:assert c['model_sha256']==l['panel']['reference']['canonical_sha256']
        row=ledger[ordinal] if ledger else None
        if row:
            assert row['leaf_id']==c['leaf'] and row['model_sha256']==c['model_sha256'] and int(row['optimize_return_code'])==0
            assert core.portable(root,row['native_log'])==core.portable(root,c['native_log_path'])
        groups[core.portable(root,c['native_log_path'])].append((ordinal,cid,c,row))
    for path,items in groups.items():
        data=path.read_bytes();spans=segments(data)
        assert len(spans)==len(items),'UNRESOLVED: duplicate/missing/unbound Optimize segment'
        for (ordinal,cid,c,row),(lo,hi) in zip(items,spans):
            part=data[lo:hi];text=part.decode('utf-8');row_count,column_count,counts=facts[cid]
            size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',text)
            assert size and (int(size[1]),int(size[2]))==(row_count,column_count),'UNRESOLVED: wrong per-call model size'
            lp=bool(row and row['solve_kind']=='LP')
            types=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',text)
            if lp:
                assert not c['native_preconditions'] and int(row['integer_domain_restored'])==1
                if types:assert (int(types[1]),int(types[2]),int(types[3]))==(column_count,0,0)
            else:
                assert types and (int(types[1]),int(types[2])-int(types[3]),int(types[3]))==(counts['C'],counts['I'],counts['B'])
            params={name:float(value) for name,value in re.findall(r'(?m)^(TimeLimit|Threads|MIPGap|MIPGapAbs|Seed|Presolve|FeasibilityTol|IntFeasTol|OptimalityTol)\s+([-+0-9.eE]+)\s*$',text)}
            settings=c['settings']
            for name,value in params.items():
                if name=='TimeLimit':
                    assert value>0
                    # MIP TimeLimit is set after paid Start/model work; the ledger
                    # records the earlier request boundary, not the later set call.
                    if row:assert value<=float(row['global_deadline_remaining_at_launch'])+1e-5
                    else:assert value<=l['cap_seconds']
                else:assert name in settings and value==settings[name],'UNRESOLVED: per-call parameter mismatch'
            fp=re.search(r'Model fingerprint: (0x[0-9a-fA-F]+)',text)
            fingerprint_contract=None
            if c['full_original'] and fp:
                before=int(r['gurobi_model_fingerprint'])&0xffffffff
                assert before==(int(l['panel']['reference']['fingerprint'])&0xffffffff)
                if l['arm']=='P-S':
                    # Fingerprint includes optimization attributes such as Start.
                    # The PE's reference API read occurs before Start submission;
                    # the Optimize log observes the later attributed model.
                    # Bind the complete actual matrix and all-column Start instead
                    # of equating fingerprints from two different states.
                    import round112_audit as start
                    checked=start.start_audit(root,l['panel'],d)
                    assert checked
                    fingerprint_contract=dict(pre_Start_reference=hex(before),Optimize_log=fp[1],
                        compared_across_different_attribute_states=False,
                        complete_matrix_types_bounds_objective_and_Start_verified=True,
                        evidence_source='native before/after matrix and complete Start API readback',
                        post_Start_API_Fingerprint='not persisted by frozen PE; no fabricated equality')
                else:
                    assert int(fp[1],16)==before
                    fingerprint_contract=dict(cold_reference=hex(before),Optimize_log=fp[1],same_state_equal=True)
            returned=cid in j['returned_ids']
            assert returned or cid in j['unreturned_ids'] and j.get('failure') is not None,'UNRESOLVED: actual return absent'
            binding=dict(call=cid,serial_ordinal=ordinal+1,model_SHA=c['model_sha256'],leaf=c['leaf'],
                true_G_interval=[c['lower_g'],c['upper_g']],cutoff=c['cutoff'],
                epoch=c.get('epoch'),epoch_source='journal field' if 'epoch' in c else 'scope/cutoff bound; no invented epoch',
                solve_kind=row['solve_kind'] if row else 'MIP',ledger=row,
                raw_log=path.relative_to(root).as_posix(),raw_log_SHA=digest(data),byte_begin=lo,byte_end=hi,
                segment_SHA=digest(part),fingerprint=fp[1] if fp else None,fingerprint_contract=fingerprint_contract,parameters=params,
                native_types=dict(counts) if not lp else {'C':column_count,'I':0,'B':0},
                journal_returned=returned,return_sequence=j['return_sequences'].get(cid),
                return_available=j.get('return_available',{}).get(cid),return_code=0 if returned else None,
                missing_return_requires_unchanged_narrow_gate=not returned)
            views[cid]=dict(binding=binding,text=text);bindings.append(binding)
    return dict(views=views,actual=actual,bindings=sorted(bindings,key=lambda x:x['call']),ledger=ledger)

@contextlib.contextmanager
def activate(view):
    token=ACTIVE.set(view)
    try:yield
    finally:ACTIVE.reset(token)

def call_text(root,call,cid):
    import round108_reader as core
    active=ACTIVE.get(); path=core.portable(root,call['native_log_path'])
    if active is None:
        data=path.read_bytes();spans=segments(data)
        assert len(spans)==1,'UNRESOLVED: reused log needs explicit call/model/ledger context'
        return data.decode('utf-8')
    v=active['views'][cid];b=v['binding']
    assert b['model_SHA']==call['model_sha256'] and b['leaf']==call['leaf']
    assert b['true_G_interval']==[call['lower_g'],call['upper_g']] and b['cutoff']==call['cutoff']
    assert core.sha(path)==b['raw_log_SHA'],'sealed log changed'
    return v['text']

def ledger_text(root,row,ordinal,j):
    actual=[cid for cid in j['calls'] if cid not in j['not_started_ids']]
    cid=actual[ordinal];c=j['calls'][cid]
    assert row['model_sha256']==c['model_sha256']
    if 'leaf_id' in row:assert row['leaf_id']==c['leaf']
    import round108_reader as core
    assert core.portable(root,row['native_log'])==core.portable(root,c['native_log_path'])
    return call_text(root,c,cid)
