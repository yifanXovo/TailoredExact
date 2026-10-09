"""Independent bounded review of one already-paid qualification native slot.

Reads immutable raw/launch/receipt/source bytes. Starts no native work.
An ACCEPT admits only the exact final H100/Seed1/MB qualification recovery,
not the formal performance campaign or final Seed1 proof.
"""
from pathlib import Path
import hashlib,json,math,sys,time

ROOT=Path('E:/codes/ExactEBRP-round109').resolve()
OUT=ROOT/'results/unified_exact_round109'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def obj(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def need(x,m):
    if not x:raise AssertionError(m)
def save(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')

started=time.perf_counter();dest=OUT/'review/seed_recovery_budget_review01';dest.mkdir(exist_ok=False)
candidate=OUT/'candidate_identity.json';identity=obj(candidate)
campaign=obj(OUT/'campaign/identity.json');cli=obj(OUT/'qualification/cli01/identity.json')
before=obj(OUT/'engineering/seed_reader_repair02/campaign_identity_before.json')
need(campaign['launches']==before['launches'] and len(campaign['launches'])==42,'all42 exact pre-recovery formal argv unchanged')
need([x['command'] for x in campaign['launches']]==identity['full_argv'],'candidate full formal argv bind all42 launches')
need([x['command'] for x in cli['launches']]==identity['qualification_argv'],'candidate binds all5 frozen qualification argv')
need(identity['planned_total_starts']==72 and identity['qualification_conservative_starts_with_failures']==15 and identity['starts_reserve']==0,'explicit72 plan and zero spare starts')
for path,digest in identity['helpers'].items():need(sha(ROOT/path)==digest,'current exact frozen helper '+path)
for path,digest in identity['source_bindings'].items():need(sha(ROOT/path)==digest,'unchanged production source '+path)
need(sha(ROOT/'build/research/round109-inherited-mb-v1/ExactEBRP.exe')==identity['production_PE_SHA']=='4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0','same original production PE')
need(sha(Path('D:/gurobi1302/win64/bin/gurobi130.dll'))==identity['DLL_SHA']=='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88','same loaded native DLL identity')
fees={};paid_starts=0;paid_seconds=0
for path in sorted((OUT/'fees').glob('*/launch.json')):
    receipt=path.parent/'receipt.json';need(receipt.is_file(),'no unclosed prior paid wrapper')
    a=obj(path);r=obj(receipt);need(a['conservative_process_starts']==r['conservative_process_starts'],'launch/receipt fee equal')
    need(math.isfinite(r['outer_seconds']) and r['outer_seconds']>=0,'finite actual outer fee')
    paid_starts+=a['conservative_process_starts'];paid_seconds+=r['outer_seconds']
    fees[path.parent.name]=dict(launch_SHA=sha(path),receipt_SHA=sha(receipt),starts=a['conservative_process_starts'],outer_seconds=r['outer_seconds'])
need(set(fees)=={'qualification_prepare01','qualification_cli01','qualification_cli02'} and paid_starts==14,'exact original prior conservative starts no refunded failures')
old=OUT/'fees/qualification_cli02';old_receipt=obj(old/'receipt.json');old_launch=obj(old/'launch.json')
need(old_launch['declared_native_children']==5 and old_receipt['conservative_process_starts']==6 and old_receipt['actual_native_children_with_launch']==4,'one declared previously-paid never-started fifth native slot')
need(old_receipt['exit_code']==1 and old_receipt['stop_reason']=='actual_exception','original second wrapper failure remains visible')
need('Audit failed; retain evidence and stop before next arm' in (old/'failure.txt').read_text(),'failure was after fourth native output audit, not hidden process rerun')
prior=[]
for x in cli['launches'][:4]:
    d=Path(x['destination']);a=obj(d/'launch.json');c=obj(d/'completion.json');marker=obj(d/'process_start_marker.json')
    need(a['command']==x['command'] and a['panel']==x['panel'],'prior child exact frozen argv')
    need(c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap'],'four existing actual native children complete normally')
    prior.append(dict(number=x['number'],argv=x['command'],launch_SHA=sha(d/'launch.json'),completion_SHA=sha(d/'completion.json'),process_start_marker_SHA=sha(d/'process_start_marker.json'),marker=marker))
last=cli['launches'][4];need(last['arm']=='M-B' and last['seed']==1 and last['id']=='H100' and last['number']==5,'only exact original fifth H100 Seed1 MB child')
need(not Path(last['destination']).exists(),'fifth destination never created before this review')
need(not (OUT/'campaign/summary.jsonl').exists(),'zero formal arms before recovery review')
groups={x['group_number'] for x in campaign['launches']};remaining_starts=len(campaign['launches'])+len(groups)
nominal=sum(x['cap_seconds'] for x in campaign['launches']);overhead=120*len(groups)
need(remaining_starts==57 and nominal==88200 and overhead==1800,'all42 nominal caps and all15 wrappers reserved without early-stop credits')
need(paid_starts+1+remaining_starts==72,'one new wrapper, no new child fee or old refund, exactly72 maximum')
need(paid_seconds+240<=1200 and paid_seconds+240+nominal+overhead<=100000,'qualification cap and full remaining fixed outer envelope fit')
recovery=ROOT/'scripts/round109_seed_recovery.py';code=recovery.read_text();scope=ROOT/'scripts/round109_seed_scope.py';scope_code=scope.read_text()
need(code.count("campaign.run('qualification/cli01',5,True)")==1 and 'subprocess.' not in code,'recovery directly invokes one native via inherited run and no extra driver')
need('conservative_process_starts=1' in code and 'native_child_fee_already_in_qualification_cli02=True' in code and 'nested_seconds_added=False' in code,'one new outer wrapper fee and explicit original native coupon')
need('full_fourth_qualification_arm_seconds=\'unknown:' in code and 'reader_only_recovery=True' in code,'old fourth full clock honestly unknown, no new measured native claim')
need("observations==read(d/'observations.json')" in scope_code and "len({c['call'] for c in calls})==len(calls)" in scope_code and "all(e['return_code']==0 for e in return_events)" in scope_code,'scope proof consumes actual unique raw calls and rejects failed native returns')
need("physical['F']<=1e-12" in scope_code and 'core.full_fleet' in scope_code,'zero-call native-free closure relies on independently physical zero floor')
conditions=['Consume only qualification_cli02 ordinal5 exact frozen argv; record real recovery wrapper PID and real native PID/launch.','Keep all three old fee receipts, failure text, raw result/journal bytes and preserved failed audit/summary; no refund and no child fee counted twice.','Recovery fee is one newly created wrapper outer interval; never add nested child intervals.','The fourth full qualification clock remains unknown; native/supervisor clocks cannot substitute for complete arm timing.','All five actual qualification children must pass independent raw physics/model/Start/coverage/scope audit before performance admission.','Total conservative starts will be15 qualification plus57 formal=72, with zero spare starts; another process or failure requires explicit budget re-evaluation.','Raw Seed1 native_preconditions=0 and global_available=false/global_bound=null remain unchanged; computed proof is offline mathematical provenance only.']
value=dict(decision='ACCEPT',scope='exact final prepaid qualification native slot recovery only; formal campaign not admitted',candidate_identity_SHA=sha(candidate),coupon_original_receipt_SHA=sha(old/'receipt.json'),prepaid_native_child=dict(fee='qualification_cli02',ordinal=5,receipt_SHA=sha(old/'receipt.json'),argv=last['command'],destination=last['destination'],previously_started=False),source_at_review_SHA=sha(__file__),frozen_recovery_source_SHA=sha(recovery),frozen_scope_source_SHA=sha(scope),fees=fees,prior_actual_native_children=prior,current_paid_starts=paid_starts,current_paid_outer_seconds=paid_seconds,new_wrapper_starts=1,new_child_fee=0,qualification_total_starts=15,reserved_formal_starts=57,planned_total_starts=72,nominal_formal_seconds=nominal,reserved_formal_wrapper_seconds=overhead,qualification_outer_envelope=paid_seconds+240,total_outer_envelope=paid_seconds+240+nominal+overhead,formal_native_started=0,conditions=conditions,Optimize=0,native_environment=0)
save(dest/'audit.json',value);save(OUT/'review/seed_recovery_budget_review.json',value)
(dest/'source_at_execution.py').write_bytes(Path(__file__).read_bytes())
(dest/'recovery_source_at_review.py').write_bytes(recovery.read_bytes());(dest/'scope_source_at_review.py').write_bytes(scope.read_bytes())
save(dest/'receipt.json',dict(exit_code=0,elapsed_engineering_seconds=time.perf_counter()-started,audit_SHA=sha(dest/'audit.json'),source_SHA=sha(__file__),Optimize=0,native_environment=0))
print(json.dumps(dict(decision='ACCEPT',candidate_identity_SHA=value['candidate_identity_SHA'],total_starts=72,coupon_receipt_SHA=value['coupon_original_receipt_SHA'])))
