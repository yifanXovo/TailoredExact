"""Bounded current-safe dependency restoration and zero-new-solve R118 replay."""
from pathlib import Path
import csv,hashlib,io,json,subprocess,tarfile,time
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round119'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def restore():
    import publication_security as security
    tick=time.perf_counter();base=ROOT/'results/unified_exact_round118/compact_evidence';m=read(base/'manifest.json')
    selected={p:v for p,v in m['files'].items() if p.startswith(('results/','reference/'))}
    data=[]
    for part in m['parts']:
        p=ROOT/part['path'];assert sha(p)==part['SHA'] and p.stat().st_size==part['bytes'];data.append(p.read_bytes())
    found=[];preserved=[]
    with tarfile.open(fileobj=io.BytesIO(b''.join(data)),mode='r|gz') as arc:
        for member in arc:
            if member.name not in selected:continue
            security.Scanner.member_name(member.name);assert member.isfile()
            raw=arc.extractfile(member).read();v=selected[member.name]
            assert hashlib.sha256(raw).hexdigest()==v['SHA'] and len(raw)==v['bytes']
            p=ROOT/member.name
            if p.exists():
                if p.read_bytes()!=raw and '/raw/' not in member.name and not member.name.startswith('reference/') and (
                    p.suffix=='.md' or p.read_bytes().replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n')):
                    preserved.append(dict(path=member.name,current_SHA=sha(p),carrier_SHA=v['SHA'],reason='published_document_or_checkout_EOL_preserved'))
                else:assert p.read_bytes()==raw,(member.name,sha(p),v['SHA'])
            else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            found.append(member.name)
    assert set(found)==set(selected)
    write(OUT/'safe_dependency_receipt.json',dict(manifest_SHA=sha(base/'manifest.json'),parts=m['parts'],
        selected_members=selected,preserved_current_documents=preserved,restored_files=len(found),current_R118_core_only=True,old_R116_carrier=False,
        overwritten_candidate_source=False,network=False,Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(restored_files=len(found),Optimize=0)))
def replay():
    import round108_reader as core
    tick=time.perf_counter();old=ROOT/'results/unified_exact_round118';rows=list(csv.DictReader((old/'reconstruction01/own_UB_flow.csv').open(encoding='utf-8')))
    values=[]
    for arm,stem in [('M-B','02_N40-R1-S_S0_M-B'),('ENS-C','04_N40-R1-S_S0_ENS-C')]:
        d=old/'campaign/raw'/stem;receipt=read(d/'producer_receipt.json');launch=read(d/'launch.json')
        observations=read(d/'observations.json');calls=[x for x in observations if x['payload']['kind']=='call']
        returns=[x for x in observations if x['payload']['kind']=='returned']
        proof=calls[2]['payload'];cid=proof['call'];returned=[x for x in returns if x['payload']['call']==cid]
        assert len(returned)==1 and returned[0]['payload']['return_code']==0
        # Bind the original binary64 scoped LP, actual API/ledger return and full model.
        model=core.portable(ROOT,proof['model_path']);assert sha(model)==proof['model_sha256']
        ledger=list(csv.DictReader((d/'external/lp_status_ledger.csv').open(encoding='utf-8')))
        lp=next(x for x in ledger if x['leaf_id']==proof['leaf'])
        bound=float(lp['lower_bound']);cutoff=proof['cutoff'];b=min(bound,cutoff)
        candidates=[x for x in rows if x['arm']==arm and x['physical_verified']=='True' and float(x['F'])+1e-7<b]
        crossing=min(candidates,key=lambda x:float(x['available']))
        seq=int(crossing['sequence']);obs=next(x for x in observations if x['sequence']==seq)
        assert obs['payload']['kind']=='witness' and abs(obs['payload']['objective']-float(crossing['F']))<=1e-7
        # The supervisor's first-observed clock has a different origin from T_produce.
        completion=read(d/'completion.json');end=read(d/'native_end_receipt.json')
        marker=read(d/'process_start_marker.json')
        offset=end['complete_seconds_until_native_end']-completion['fully_observed_end_to_end_seconds']
        assert offset>=0;origin=receipt['t0_perf']+offset
        converted=offset+float(crossing['available'])
        parsed=core.lp_model(model);assert parsed['bounds']['G']==(proof['lower_g'],proof['upper_g'])
        values.append(dict(arm=arm,source_call=cid,source_model_SHA=sha(model),source_scope=proof,
            returned_receipt=returned[0],LP=lp,conservative_interval_bound=b,own_U=float(crossing['F']),
            own_true_G=float(crossing['G']),own_CPP_U=obs['payload']['objective'],own_sequence=seq,own_call=int(crossing['call']),
            original_own_UB_flow_available=float(crossing['available']),supervisor_origin_perf=origin,
            producer_origin_perf=receipt['t0_perf'],origin_offset_seconds=offset,
            conversion_method='inherited_R118_recorded_receipt_end_anchor_not_exact_internal_discovery',
            start_marker_monotonic_minus_producer_perf=marker['monotonic_seconds']-receipt['t0_perf'],
            start_marker_unix_minus_producer_unix=marker['unix_seconds']-receipt['t0_unix'],
            differing_clock_anchor_estimates_disclosed=True,
            converted_T_produce_available=converted,original_R118_report_conversion_offset=end['complete_seconds_until_native_end']-completion['fully_observed_end_to_end_seconds'],
            own_receipt_data_close_seconds=obs['data_close_seconds'],
            observation_upper_bound_not_internal_first_discovery=True,own_witness_SHA=obs['sha256'],
            applicable=proof['lower_g']>0 and float(crossing['G'])<proof['lower_g'] and float(crossing['F'])+1e-7<b,
            old_atomic_splits=0,no_new_native_Optimize=True,old_result_unchanged=True))
    write(OUT/'preflight_replay.json',dict(arms=values,Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick))
    print(json.dumps([dict(arm=x['arm'],applicable=x['applicable'],available=x['converted_T_produce_available']) for x in values]))
if __name__=='__main__':
    import sys
    {'restore':restore,'replay':replay}[sys.argv[1]]()
