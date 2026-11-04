"""Finite saved-evidence audit, with no Optimize, compilation or producer."""
from fractions import Fraction as F
from collections import Counter
import csv,zipfile
from round152_math import evaluate
from round152_common import *

def resolve_reuse():
    index=read(OUT/'reuse_index.json');known=[]
    for round_id in [135,138,140,143]:
        p=ROOT/f'results/unified_exact_round{round_id}/carrier_manifest.json'
        if not p.exists():continue
        manifest=read(p)
        for a in manifest.get('archives',[]):
            if isinstance(a.get('members'),list):
                known.extend(dict(commit=BASE,archive=a['path'],archive_SHA=a['SHA256'],member=m['member'],SHA256=m['SHA256'],bytes=m['bytes']) for m in a['members'])
    # R138's internal index is in its already published carrier.
    name='results/unified_exact_round138/artifacts/diagnostics_and_failures.zip'
    path=WORK/'restore/round152-inherited/R138_diagnostics_and_failures.zip'
    if not path.exists():path.write_bytes(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT))
    digest=sha(path);assert digest=='98176d441008d0263644702b73574f782377b78c5d0541fe092e4086940739c0'
    with zipfile.ZipFile(path) as z:
        for member in z.namelist():
            if '/roots/K-35-U/' not in member:continue
            if not member.endswith(('original.lp','result.json','solution.json.gz','scope.json')):continue
            data=z.read(member);known.append(dict(commit=BASE,archive=name,archive_SHA=digest,member=member,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
    resolved=[]
    for r in index['dependencies']:
        assert sha(r['restored'])==r['SHA256']
        if 'archive' in r:resolved.append(r);continue
        match=next((x for x in known if x['SHA256']==r['SHA256']),None)
        if match:resolved.append(dict(match,restored=r['restored']))
        else:
            # Thin inherited interpretation metadata is explicitly retained;
            # authoritative model/point bytes must always have carrier members.
            assert r['path'].endswith('scope.json'),r
            target=OUT/'engineering/inherited_K35_scope.json';target.write_bytes(Path(r['restored']).read_bytes())
            resolved.append(dict(r,thin_metadata_snapshot=target.relative_to(ROOT).as_posix(),
                                 interpretation_only=True,actual_scope_independently_read_from_model=True))
    index['dependencies']=resolved;index['fixed_reference_commit']=BASE
    index['public_old_producer_needed']=False;write(OUT/'reuse_index.json',index)
    return len(resolved)

def audit():
    configure();start=time.perf_counter();result={};calls=[];returns=[]
    for call in sorted(OUT.rglob('*call.json')):
        if call.name not in ('call.json','joint_call.json'):continue
        record=read(call);ret=call.with_name(call.name.replace('call','return'));assert ret.exists(),call
        returned=read(ret);entry=dict(path=call.relative_to(OUT).as_posix(),return_path=ret.relative_to(OUT).as_posix(),kind=record.get('kind','LP'),Status=returned.get('Status'),Runtime=returned.get('Runtime'),Work=returned.get('Work'))
        if record.get('model_SHA'):
            options=[call.parent/'model.mps',call.parent/'reference.mps']
            model=next((p for p in options if p.exists() and sha(p)==record['model_SHA']),None);assert model is not None,(call,record['model_SHA'])
            entry['model_SHA']=record['model_SHA']
        calls.append(entry);returns.append(ret)
    assert len(returns)==len(set(returns))
    lp=[]
    for p in sorted((OUT/'LP').glob('*/result.json')):
        r=read(p);assert r['qualified'],p
        assert r['all_variables_free']
        assert max(r['quality'].values())<=1e-6
        assert max(r['residual']['constraints'],r['residual']['bounds'])<=1e-6
        assert sha(p.parent/'model.mps')==r['model_SHA']
        lp.append(dict(path=p.relative_to(OUT).as_posix(),role=r['role'],variant=r['variant'],L=r['L'],new_Optimize=r.get('Optimize_new',0),gain=r.get('gain'),
                       rows=r.get('after',{}).get('rows'),columns=r.get('after',{}).get('columns'),quality_max=max(r['quality'].values())))
    prices=[];stock_count=0
    for p in sorted(OUT.rglob('result.json')):
        r=read(p)
        if not all(k in r for k in ['decision','pi','scope','lower','upper','stocks']):continue
        if p.parts[len(OUT.parts)].startswith('qualification_aggregate'):continue
        pi={tuple(map(int,k.split(':'))):v for k,v in r['pi'].items()};true=[]
        for st in r['stocks']:
            ev=evaluate(r['scope'],st['Y'],pi,True);assert ev['feasible'],(p,st)
            true.append(ev['price']);stock_count+=1
        if r['upper'] is not None:
            assert true and F(r['upper'])>=min(true),(p,r['upper'],str(min(true)))
        if r['lower'] is not None and r['upper'] is not None:assert r['lower']<=r['upper']+1e-7,p
        if 'active_bins' in r:
            nodes=r['active_bins'];parts=[v['lower'] for v in nodes if not v['empty']]+([r['zero_lower']] if r['zero_lower'] is not None else [])
            assert r['lower']==(min(parts) if parts else None),p
            bounds=r['denominator_scope']
            intervals=sorted(v['interval'] for v in nodes)
            if bounds['upper']>0:
                assert intervals[0][0]<=bounds['lower'] and intervals[-1][1]>=bounds['upper']
                for a,b in zip(intervals,intervals[1:]):assert a[1]>=b[0]
            assert r['complete_cover']
        if r['decision']=='SEPARATION':assert r['lower']>r['threshold']+1e-7
        if r['decision']=='DIRECTION_NONSEPARATING':assert r['upper']<=r['threshold']+1e-9
        prices.append(dict(path=p.relative_to(OUT).as_posix(),decision=r['decision'],lower=r['lower'],upper=r['upper'],threshold=r['threshold'],
                           seconds=r['seconds'],calls=len(r['calls']),negative_lower=r['lower'] is not None and r['lower']<0))
    protection=subprocess.check_output(['git','diff',BASE,'--name-only','--','src','include','config','scripts/paper_s2.py','scripts/paper_s2_round137.py'],cwd=ROOT).decode().strip()
    assert not protection
    pe=WORK/'build-cache/round151/ExactEBRP.exe';assert sha(pe)=='fbdd7c2ece5c748e086761f2490fd901ccdaeffa29df357d2d98fd8743e1dc39';assert sha(DLL)==DLL_SHA
    reused=resolve_reuse();failed=[]
    for p in (OUT/'fees').glob('*/receipt.json'):
        r=read(p)
        if r.get('exit_code',r.get('returncode',0)) not in (0,None):failed.append(dict(label=p.parent.name,receipt=r))
    write(OUT/'reports/native_calls.json',calls);write(OUT/'reports/LP_results.json',lp);write(OUT/'reports/pricing_results.json',prices)
    result=dict(PASS=True,UTC=utc(),new_native_calls=len(calls),returned=len(returns),call_kinds=dict(Counter(c['kind'] for c in calls)),
                qualified_LP_records=len(lp),LP_Optimize_new=sum(r['new_Optimize'] for r in lp),pricing_records=len(prices),
                pricing_decisions=dict(Counter(p['decision'] for p in prices)),true_inventory_UBs_rechecked=stock_count,
                inherited_members_or_thin_metadata=reused,all_saved_native_call_returns_present=True,
                production_source_entries_profiles_byte_unchanged=True,production_PE_SHA=sha(pe),Native_DLL_SHA=sha(DLL),
                complete_algorithm_arms=0,physical_U_or_Tcert_for_new_method=None,Optimize_in_this_audit=0,
                seconds=time.perf_counter()-start)
    write(OUT/'reports/audit.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':audit()
