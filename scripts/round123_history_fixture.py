"""Portable finite final/history-U regression; no old campaign restoration."""
from pathlib import Path
import argparse,copy,json,time
import round123_common as c
import round123_evidence as ev

FIXTURE='results/unified_exact_round123/mathematics/history_regression'

def prepare(root):
    root=Path(root).resolve();dest=root/FIXTURE;dest.mkdir(parents=True,exist_ok=False)
    old=c.WORK/'worktrees/round122';ident=c.read(old/'results/unified_exact_round122/campaign/group08/identity.json')
    launch=next(l for l in ident['launches'] if l['arm']=='P-GRB');source=Path(launch['destination'])
    originals={}
    for name in ['observations.json','result.json']:
        raw=(source/name).read_bytes();(dest/name).write_bytes(raw)
        originals[name]=dict(SHA=c.sha(source/name),bytes=len(raw),source_path=str(source/name))
    records=c.read(dest/'observations.json');model_map={}
    current='results/unified_exact_round123/campaign/group01/raw/01_PB-C50-S_S0_P-GRB/compact.lp'
    for r in records:
        e=r['payload']
        if e['kind']=='call':
            assert e['full_original'] and c.sha(root/current)==e['model_sha256']
            model_map[e['model_path']]=dict(current_relative_path=current,SHA=e['model_sha256'])
    c.write(dest/'fixture_manifest.json',dict(originals=originals,panel=launch['panel'],arm=launch['arm'],
        model_path_bindings=model_map,source_commit=c.BASE,
        scope='Only two original JSON files and a profile; reuse identical current canonical model by SHA, no prior campaign/carrier',
        original_bytes_unchanged=True,path_substitution_only_in_memory=True))

def check(root,write_receipt=True):
    tick=time.perf_counter();root=Path(root).resolve();dest=root/FIXTURE;m=c.read(dest/'fixture_manifest.json')
    for name,binding in m['originals'].items():assert c.sha(dest/name)==binding['SHA']
    records=c.read(dest/'observations.json');original=copy.deepcopy(records)
    for r in records:
        e=r['payload']
        if e['kind']=='call':
            binding=m['model_path_bindings'][e['model_path']];p=root/binding['current_relative_path']
            assert c.sha(p)==binding['SHA']==e['model_sha256'];e['model_path']=str(p)
    # Assert every historical field except the explicitly rebound model path is unchanged.
    restored=copy.deepcopy(records)
    for r,o in zip(restored,original):
        if r['payload']['kind']=='call':r['payload']['model_path']=o['payload']['model_path']
    assert restored==original
    panel=m['panel'];result=c.read(dest/'result.json');before=ev.native.audit(root,panel,records,c.PE_SHA)
    failed=False
    try:ev.native.finalize_endpoint(root,panel,m['arm'],copy.deepcopy(before),records,result,'normal_return',panel['reference'])
    except AssertionError:failed=True
    assert failed
    after=copy.deepcopy(before);ev.adapted_finalizer()(root,panel,m['arm'],after,records,result,'normal_return',panel['reference'])
    assert after['endpoint']['U']==result['upper_bound'] and after['endpoint']['L']==result['lower_bound']
    rejected=[]
    for kind in ['bad_final_L','bad_observed_L']:
        audit=copy.deepcopy(before);bad=copy.deepcopy(result)
        if kind=='bad_final_L':bad['lower_bound']=result['upper_bound']+1
        else:audit['LB']=result['upper_bound']+1
        try:ev.adapted_finalizer()(root,panel,m['arm'],audit,records,bad,'normal_return',panel['reference'])
        except AssertionError:rejected.append(kind)
    assert len(rejected)==2
    value=dict(passed=True,original_order_assertion_reproduced=failed,
        history_U=before['UB'],final_endpoint=after['endpoint'],witnesses=len(before['witnesses']),
        bound_events=sum(r['payload']['kind']=='bound' for r in records),negative_bound_fixtures_rejected=rejected,
        original_blobs_and_all_fields_other_than_bound_model_path_retained=True,
        no_old_root_reads_in_check=True,Optimize=0,native_starts=0,seconds=time.perf_counter()-tick,
        fixture_manifest_SHA=c.sha(dest/'fixture_manifest.json'),script_SHA=c.sha(__file__))
    if write_receipt:c.write(dest/'portable_check.json',value)
    print(json.dumps({k:value[k] for k in ['passed','witnesses','bound_events','seconds']}))
    return value

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','check']);parser.add_argument('--root',default=str(c.ROOT));args=parser.parse_args()
    if args.mode=='prepare':prepare(args.root)
    else:check(args.root)
