"""Lightweight final-reader delta review; no solver, native process or LP parser."""
import collections,csv,datetime,hashlib,json,math,pathlib
ROOT=pathlib.Path('E:/codes/ExactEBRP-round112');OUT=ROOT/'results/unified_exact_round112';REPORT=OUT/'reports_final';BIND={}
csv.field_size_limit(100000000)
def sha(p):
 p=pathlib.Path(p);h=hashlib.sha256(p.read_bytes()).hexdigest();BIND[str(p)]=h;return h
def read(p):sha(p);return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
def rows(p):
 sha(p)
 with pathlib.Path(p).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def close(a,b,tol=1e-12):assert math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a)-float(b))<=tol,(a,b)
def label(a):return a['campaign'],int(a['number'])
def run():
 prior=read(OUT/'review/postformal03/postformal_review.json');signed=read(OUT/'review/postformal03/signature.json')
 assert sha(OUT/'review/postformal03/postformal_review.json')==signed['bindings'][str(OUT/'review/postformal03/postformal_review.json')]
 summary=read(REPORT/'summary.json');reader_SHA=sha(ROOT/'scripts/read_round112.py');assert reader_SHA==summary['reader_SHA']=='63e388e63901bdebe53e19ff2d937d2cee858d990e60cd5557e05fcd62833b21'
 receipt=read(OUT/'engineering/final_reader02/receipt.json');assert receipt['exit_code']==0 and receipt['Optimize']==0;assert (OUT/'engineering/final_reader02/stderr.txt').stat().st_size==0;sha(OUT/'engineering/final_reader02/stderr.txt');sha(OUT/'engineering/final_reader02/stdout.txt')
 expected={'formal_arm_positions':20,'formal_arms':12,'started_formal_arms':13,'qualified_formal_arms':12,'interrupted_formal_arms':1,'unstarted_formal_arms':7,'pair_positions':30,'evaluable_pairs':18,'unevaluable_pairs':12,'qualified_qualification_arms':7,'conservative_starts':39,'native_Optimize_completed_arm_journals':60,'formal_native_Optimize_qualified_arms':46,'native_Optimize_interrupted_arm':4,'returned_Optimize_interrupted_arm':3,'failed_qualification_native_Optimize':2,'all_actual_started_Optimize':66}
 assert summary['stage']=='BLOCKED'
 for k,v in expected.items():assert summary[k]==v,(k,summary[k],v)
 close(summary['outer_fee_seconds_upper'],prior['outer_seconds_upper'],1e-8)
 campaign=read(OUT/'campaign/identity.json');assert sha(OUT/'candidate_identity.json')==prior['candidate_identity_SHA'];assert sha(OUT/'campaign/identity.json')==prior['campaign_identity_SHA']
 arms=rows(REPORT/'arms.csv');qual=rows(REPORT/'qualification_arms.csv');assert len(arms)==20 and len(qual)==7
 old={(a['id'],a['arm']):a for a in prior['qualified_arms']};rawpreserved=[]
 for x,l in zip(arms,campaign['launches']):
  assert int(x['number'])==l['number'] and x['id']==l['id'] and x['arm']==l['arm'] and int(x['seed'])==0
  assert x['PE_SHA']==prior['production_PE_SHA']
  if l['number']<=12:
   a=old[(x['id'],x['arm'])]
   for k in ('U','L','gap'):close(x[k],a[k])
   close(x['complete_seconds'],a['t'],1e-10);assert (x['certificate']=='True')==a['certificate']
   assert all(x[k]=='True' for k in ('formal_protocol_qualified','certificate_qualified','numbers_qualified','launched'))
   d=pathlib.Path(l['destination']);res=read(d/'result.json')
   for column,key in [('raw_claimed_U','objective'),('raw_claimed_L','lower_bound')]:
    if x.get(column):
     # Raw U/L exports use source-specific fields; exact old export preservation is checked below.
     rawpreserved.append((x['id'],x['arm'],column,x[column]))
  else:
   assert all(x[k]=='' for k in ('U','L','gap','certificate','complete_seconds','relative_gap','native_Optimize'))
   assert all(x[k]=='False' for k in ('formal_protocol_qualified','certificate_qualified','numbers_qualified'))
   assert x['relative_gap_null_reason']=='NO_QUALIFIED_FORMAL_ENDPOINT'
   assert x['status']==('INTERRUPTED_EXECUTION' if l['number']==13 else 'UNSTARTED')
   assert x['launched']==('True' if l['number']==13 else 'False')
 initial=OUT/'review/postformal01/reconstruction';initial_arms=rows(initial/'arms.csv');by={(a['id'],a['arm']):a for a in arms}
 preserved=['raw_claimed_U','raw_claimed_L','raw_claimed_strict_certificate','raw_claimed_relative_gap','raw_tree_termination_reason','legacy_metadata_native_best_bound_return_code','legacy_metadata_serialized_bound_matches_native','tiny_negative_gap_within_original_tolerance']
 for a in initial_arms:
  b=by[(a['id'],a['arm'])]
  for k in preserved:assert a.get(k,'')==b.get(k,''),(a['id'],a['arm'],k)
 assert float(by['R108-L48','P-S']['gap'])<0 and float(by['R108-L48','P-S']['relative_gap'])<0
 pairs=rows(REPORT/'pairs.csv');assert len(pairs)==30
 own={(a['id'],a['candidate'],a['control']):a for a in prior['independent_pairs']}
 for p in pairs:
  key=(p['id'],p['candidate'],p['control'])
  if key in own:
   assert p['evaluable']=='True' and p['classification']==own[key]['classification'] and (p['severe_regression']=='True')==own[key]['severe_regression']
  else:
   assert p['evaluable']=='False' and p['classification']=='UNEVALUABLE'
   fault=p['id']=='G50-C1' and 'M-B' in (p['candidate'],p['control'])
   assert p['reason']==('EXECUTION_STATUS_RENAME_PERMISSION_ERROR' if fault else 'FIXED_ARM_NOT_STARTED')
   for k in ('candidate_U','candidate_L','candidate_gap','candidate_certificate','candidate_complete_seconds','control_U','control_L','control_gap','control_certificate','control_complete_seconds'):assert p[k]==''
 conclusions=read(REPORT/'backend_conclusions.json');assert conclusions==summary['backend_conclusions']
 for method,c in conclusions.items():
  assert c['status']=='INCOMPLETE_ATTRIBUTION' and c['denominator']==5 and c['eligible_count']==3 and c['counts']=={'WIN':2,'LOSS':1}
  assert [a['classification'] for a in c['five_role_vector']]==prior['backend_vector_for_each_ENS_C_and_M_B']
  for a in c['five_role_vector'][3:]:
   assert not a['eligible'];fault=method=='M-B' and a['id']=='G50-C1'
   assert a['reason']==('EXECUTION_STATUS_RENAME_PERMISSION_ERROR' if fault else 'FIXED_ARM_NOT_STARTED')
   assert a['reason_codes'][0]==a['reason']
 same=rows(REPORT/'same_H.csv');assert len(same)==6 and all(a['qualified']=='True' for a in same)
 assert sha(REPORT/'same_H.csv')==sha(initial/'same_H.csv')
 samefleets=rows(REPORT/'same_H_fleets.csv');assert len(samefleets)==9
 for a in samefleets:assert a['complete_H']=='True' and json.loads(a['seed_ids'])==list(range(1,26))
 partial={}
 for name,count in [('partial_journal',12),('partial_fleets',3),('partial_model_contracts',3),('partial_scope_contracts',4),('partial_native_calls',4),('partial_bounds',1)]:
  rr=rows(REPORT/(name+'.csv'));partial[name]=len(rr);assert len(rr)==count and all(a['number']=='13' and a['formal_endpoint']=='False' for a in rr)
 failure=rows(REPORT/'execution_failures.csv');assert len(failure)==1;f=failure[0]
 assert f['number']=='13' and f['formal_endpoint']=='False' and f['qualified_final_L']==f['whole_seconds']==''
 assert int(f['committed_events'])==12 and int(f['started_calls'])==4 and int(f['returned_calls'])==3 and json.loads(f['unreturned_calls'])==[4]
 close(f['partial_own_U'],prior['partial']['own_original_valid_UB'])
 # The partial bound is a recorded/recomputed floor fact, never an arm lower endpoint.
 nativepartial=rows(REPORT/'partial_native_calls.csv');assert [a['returned'] for a in nativepartial]==['True','True','True','False']
 covers=rows(REPORT/'covers.csv');chronological=rows(REPORT/'chronological_covers.csv');proofs=rows(REPORT/'returned_native_proofs.csv');flow=rows(REPORT/'own_UB_flow.csv')
 for name,rr in [('covers',covers),('chronological_covers',chronological),('returned_native_proofs',proofs),('own_UB_flow',flow)]:
  assert not any(a['campaign']=='campaign' and int(a['number'])>=13 for a in rr),name
 formalcovers=[a for a in covers if a['campaign']=='campaign'];assert len(formalcovers)==6
 for a in formalcovers:
  x=by[(a['id'],a['arm'])];assert a['complete_coverage']=='True';close(a['L'],x['L'],1e-7)
  assert (a['all_relevant_closed']=='True')==(x['certificate']=='True')
  assert json.loads(a['scoped_proofs']) and json.loads(a['leaves']) and json.loads(a['timeline'])
 splits=rows(REPORT/'split_exposure.csv');assert len(splits)==12
 for a in splits:
  events=rows(pathlib.Path(campaign['launches'][int(a['number'])-1]['destination'])/'external/paper_tree_events.csv') if a['arm'] not in ('P-GRB','P-S') else []
  actual=collections.Counter(v['event'] for v in events)
  assert int(a['actual_atomic_split_events'])==actual['atomic_split'] and json.loads(a['event_kinds'])==dict(actual)
  assert a['AM_single_factor_cause_identified']=='False'
 assert [int(a['actual_atomic_split_events']) for a in splits if a['id']=='R108-L48' and a['arm'] in ('ENS-C','M-B')]==[2,2]
 target=rows(REPORT/'target_discovery.csv');assert len(target)==12;byflow=collections.defaultdict(list)
 for a in flow:byflow[label(a)].append(a)
 for a in target:
  assert a['unknown_native_true_first_discovery']=='True' and a['external_target_not_imported_as_UB_or_Start']=='True'
  l=campaign['launches'][int(a['number'])-1];x=by[(a['id'],a['arm'])];certs=[float(v['U']) for v in arms if v['id']==a['id'] and v['certificate']=='True'];chosen=min(certs) if certs else None
  assert (a['reliable_positive_certified_target']!='')==(chosen is not None and chosen>1e-7)
  if chosen is None:assert a['reason']=='NO_RELIABLE_TARGET' and not a['first_verified_own_record_available_upper_seconds'];continue
  close(a['reliable_positive_certified_target'],chosen)
  hits=[w for w in byflow[('campaign',int(a['number']))] if float(w['F'])<=chosen+1e-7]
  if not hits:assert a['reason']=='OWN_TARGET_WITNESS_NOT_OBSERVED' and not a['first_verified_own_record_available_upper_seconds'];continue
  first=min(hits,key=lambda w:float(w['available']));c=read(pathlib.Path(l['destination'])/'completion.json');offset=float(x['complete_seconds'])-c['fully_observed_end_to_end_seconds']
  assert offset>=0;close(a['first_verified_own_record_available_upper_seconds'],float(first['available'])+offset,1e-10)
  assert a['first_sequence']==first['sequence'] and a['first_source']==first['source'] and a['reason']=='OWN_COMMITTED_WITNESS'
  assert float(a['first_verified_own_record_available_upper_seconds'])<=float(x['complete_seconds'])+1e-7
 for name in ['model_contracts.csv','scope_contracts.csv','compact_Starts.csv','tailored_Starts.csv','controller_LP_status.csv','controller_native.csv','controller_AM.csv','controller_events.csv','controller_child_bounds.csv','controller_targets.csv','time_partitions.csv','fleets.csv','startup_fleets.csv','journal_trace.csv','native_bounds.csv','checkpoints.csv','fees.csv']:
  assert sha(REPORT/name)==sha(initial/name),name
 for name in ['contribution_evidence_map.md','next_research_decision.md','blocking_incident.json','blocking_incident.md','numerical_policy.md']:sha(OUT/name)
 for path in sorted(REPORT.iterdir()):
  if path.is_file():sha(path)
 sha(__file__)
 delta=dict(schema='round112_independent_final_reader_delta_v1',decision='BLOCKED',reviewer='/root/independent_review',signed_at_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),reader_SHA=reader_SHA,candidate_identity_SHA=prior['candidate_identity_SHA'],production_PE_SHA=prior['production_PE_SHA'],campaign_identity_SHA=prior['campaign_identity_SHA'],native_starts=0,Optimize=0,compiler_starts=0,LP_models_reparsed=0,qualified_formal_arms=12,started_formal_arms=13,interrupted_formal_arms=1,unstarted_formal_arms=7,qualified_qualification_arms=7,formal_fixed_positions=20,pair_positions=30,evaluable_pairs=18,UNEVALUABLE_pairs=12,conservative_starts=39,outer_fee_seconds_upper=summary['outer_fee_seconds_upper'],all_actual_started_Optimize=66,completed_classifications_match_independent_signed_postformal=True,signed_negative_gap_preserved=True,source_raw_claims_legacy_errors_and_null_preserved=True,missing_reason_priority='G50 ENS-C/P-S both unstarted -> FIXED_ARM_NOT_STARTED; comparisons involving G50 M-B -> EXECUTION_STATUS_RENAME_PERMISSION_ERROR; all G100 fixed arms unstarted.',partial_tables=partial,partial_formal_endpoint_lower_certificate_clock_all_absent=True,same_H_comparisons=6,same_H_fleet_records=9,formal_complete_cover_records=6,partial_excluded_from_complete_cover_and_returned_proofs=True,split_exposure='Only actual atomic_split controller event counted; L48 ENS-C and M-B each 2. F2/C2 speculative child LPs are not actual splits; no AM causal identification.',target_discovery='Own first committed witness availability plus all wrapper residual is a conservative upper, independently checked. Native true first discovery is unknown; target not imported as UB or Start.',backend_conclusions=conclusions,contribution_map_and_next_priority_review='Local F2 proof and M-B C2 gains plus real L48 timing losses retained. Both five-role conclusions incomplete; single next priority is a separately authorized, independently frozen complete matched-start attribution experiment after finite reproduction/validation of Windows share/atomic-status contract; no Round112 helper repair/retry/new benchmark.',engineering_failures='Root final_reader01 export duplicate candidate_U TypeError retained; final_reader02 exit 0. Reviewer postformal02 UTF-8 scaffolding failure separately retained; no native or research fee charged.',limitations=['This is a delta review of final offline outputs and missing-data handling, relying on previously signed full raw/matrix review for completed twelve arms.','No new numerical rejection path or injured call proof was exercised. Existing conditional numerical policy and unresolved-damage HOLD remain.','Public restore/export and remote bindings have not yet been reviewed.'],bindings=BIND)
 (OUT/'review/final_reader_delta01.json').write_text(json.dumps(delta,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 print(json.dumps({k:delta[k] for k in ['decision','qualified_formal_arms','started_formal_arms','interrupted_formal_arms','unstarted_formal_arms','qualified_qualification_arms','pair_positions','evaluable_pairs','UNEVALUABLE_pairs','native_starts','LP_models_reparsed']},indent=2))
if __name__=='__main__':run()
