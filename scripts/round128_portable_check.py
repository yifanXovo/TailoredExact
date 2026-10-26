"""Finite solver-free recovery checks using the established physical/Start reader."""
from pathlib import Path
import argparse,collections,csv,hashlib,json,math,time
import round108_reader as core
from round127_qualify import compare

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round128'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def portable(p):
    s=str(p).replace('\\','/')
    for prefix in ['results/','reference/','scripts/','src/','include/']:
        where=s.find('/'+prefix)
        if where>=0:return ROOT/s[where+1:]
        if s.startswith(prefix):return ROOT/s
    raise AssertionError(('nonportable evidence path',s))
def same(a,b,tol=1e-8):assert abs(a-b)<=tol,(a,b)
def qualified(a):return all(a.get(k) for k in ['formal_protocol_qualified','numbers_qualified','certificate_qualified']) and not a.get('source_reduced')
def direction(a,b):
    assert a['PE_SHA']==b['PE_SHA'] and a['DLL_SHA']==b['DLL_SHA'] and a['input_SHA']==b['input_SHA'] and a['seed']==b['seed']
    if not qualified(a) or not qualified(b):return 'UNEVALUABLE','UNEVALUABLE',None,None
    if a['certificate'] and b['certificate']:
        same(a['U'],b['U'],1e-7);dt=a['T_cert']-b['T_cert']
        return 'BOTH_CERTIFIED','Win' if dt<0 else 'Lose' if dt>0 else 'Tie',dt,b['T_cert']/a['T_cert']
    if a['certificate']:return 'LEFT_ONLY_CERTIFIED','Win',None,None
    if b['certificate']:return 'RIGHT_ONLY_CERTIFIED','Lose',None,None
    return 'BOTH_OPEN','UNDETERMINED',None,None

def check(receipt):
    tick=time.perf_counter();manifest=read(OUT/'experiment_manifest.json');frozen=read(OUT/'E2_frozen.json')
    for name,h in frozen['source_bindings'].items():assert sha(ROOT/name)==h,('final source byte identity',name)
    for p in read(OUT/'input_manifest.json')['roles']:assert sha(ROOT/p['input_path'])==p['input_sha256']
    for row in read(OUT/'source_E1_manifest.json')['files']:assert sha(ROOT/row['path'])==row['SHA']
    with (OUT/'pairs.csv').open(newline='',encoding='utf-8-sig') as f:table=list(csv.DictReader(f))
    seals=0;models=0;arms=[];comparisons=[];representatives=[]
    for g in manifest['groups']:
        camp=OUT/g['name'];i=read(camp/'identity.json');aa=read(camp/'reconstructed.json')['arms']
        assert [a['method'] for a in aa]==g['methods'] and len(aa)==len(i['launches'])
        assert i['candidate_binary_sha256']==frozen['PE_SHA']
        for l,a in zip(i['launches'],aa):
            d=portable(l['destination']);assert d==portable(a['destination'])
            producer=read(d/'producer_receipt.json');total=read(d/'arm_total_receipt.json');seal=read(d/'producer_seal.json')
            assert producer['producer_seal_SHA']==sha(d/'producer_seal.json')
            assert seal['native_stopped_no_reentry'] and seal['required_outputs_closed']
            for name,h in seal['required_SHA'].items():assert sha(d/name)==h
            same(a['T_produce'],producer['t_produce_perf']-producer['t0_perf'])
            same(a['T_verify'],total['t_verified_perf']-producer['t_produce_perf'])
            same(a['T_total'],a['T_produce']+a['T_verify'])
            assert a['T_produce']<=l['cap_seconds'] and a['T_cert']==(a['T_produce'] if qualified(a) and a['certificate'] else None)
            assert a['PE_SHA']==frozen['PE_SHA'] and a['DLL_SHA']==frozen['DLL_SHA'] and a['binary_layer']=='E2'
            endpoint=read(d/'audit.json')['endpoint'];assert endpoint['certificate']==a['certificate']
            same(endpoint['U'],a['U'],1e-7);same(endpoint['L'],a['L'],1e-7);same(a['gap'],a['U']-a['L'],1e-15)
            physical=core.full_fleet(ROOT,l['panel'],read(d/'result.json'));same(physical['F'],a['U'],1e-7)
            calls=[r['payload'] for r in read(d/'observations.json') if r['payload']['kind']=='call']
            for c in calls:assert sha(portable(c['model_path']))==c['model_sha256'];models+=1
            if l['method']=='P':
                p=read(d/'round127_parameters.json');assert (p['MIPFocus'],p['Cuts'],p['NumStart_before_optimize'])==(0,-1,0)
                assert len(calls)==1 and calls[0]['full_original']
            if l['method']=='MD-R' and calls:
                ledger=core.rows(d/'external/paper_optimize_ledger.csv')
                assert [r['solve_kind'] for r in ledger]==['LP','MIP'] and {r['leaf_id'] for r in ledger}=={'L0'}
                assert ledger[0]['model_sha256']==ledger[1]['model_sha256'] and int(ledger[0]['integer_domain_restored'])==1
                if ledger[-1]['native_status']!='OPTIMAL':assert not a['certificate'] and a['T_cert'] is None
                starts=[(p,read(p)) for p in (d/'external/native_logs').glob('*.round68.start.json')]
                assert sum(bool(v['submitted']) for _,v in starts)==1
                assert sum(v['status']=='round128_pre_lp_validated_without_Start_submission' for _,v in starts)==1
                if g['number']==1:
                    core.start_reader.ROOT=ROOT;submitted=[(p,v) for p,v in starts if v['submitted']]
                    path=portable(calls[-1]['model_path']);checks=core.start_reader.audit_model(path,submitted,'m-binary')
                    own=core.full_fleet(ROOT,l['panel'],read(d/'hga.csv.exchange/final.json'))
                    representatives.append(dict(method='MD-R',group=1,complete_actual_Start_audit=checks,own_H_physical=own,Optimize=0))
            seals+=1;arms.append(a)
        by={a['method']:a for a in aa}
        for left,right in g['pairs']:
            expected=direction(by[left],by[right]);actual=next(r for r in table if int(r['group'])==g['number'] and r['left']==left and r['right']==right)
            assert (actual['classification'],actual['direction'])==expected[:2]
            for key,value in zip(['left_minus_right_seconds','right_over_left_certification_ratio'],expected[2:]):
                if value is None:assert actual[key]==''
                else:same(float(actual[key]),value,1e-10)
            comparisons.append(dict(group=g['number'],left=left,right=right,classification=expected[0],direction=expected[1]))
    first=read(OUT/manifest['groups'][0]['name']/'identity.json');l={l['method']:l for l in first['launches']}
    def root_path(l):
        return portable(next(x['payload']['model_path'] for x in read(portable(l['destination'])/'observations.json') if x['payload']['kind']=='call'))
    deleted=compare(root_path(l['MB']),root_path(l['MS2']),'ms2',15,2)
    assert deleted['removed_rows']==910
    assert seals==16 and len(comparisons)==17 and len({a['input_SHA'] for a in arms})==3
    result=dict(status='PASS',actual_producer_seals=seals,actual_call_model_hashes=models,comparisons=17,distinct_inputs=3,
        all_17_directions_independently_recomputed=True,all_actual_final_fleets_physically_replayed=True,
        representative_MD_R_Start_and_own_fleet=representatives,representative_MS2_actual_deletion=deleted,
        E2_PE_SHA=frozen['PE_SHA'],R127_MD_unstarted_unchanged=3,Optimize=0,native_starts=0,compilation=0,
        finite_scope_not_full_rational_matrix_proof=True,seconds=time.perf_counter()-tick)
    Path(receipt).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if not k.startswith('representative')}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--receipt',required=True);args=parser.parse_args();check(args.receipt)
