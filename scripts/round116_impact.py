"""Finite old G100 global-claim impact, no model reproof or performance replay."""
from round116_common import *
import copy,csv,io,shutil,subprocess
import round108_reader as core
import round111_decisions as decisions

SHA_INPUT='b3f3a1270f062e9f3af64d5b00392f51821bb775818edc6cd383fcd62550618f'
def run():
    tick=time.perf_counter();d=OUT/'historical_impact';d.mkdir(exist_ok=False);authorities=[]
    def signed(rel):
        data=subprocess.check_output(['git','show',BASE+':'+rel],cwd=ROOT)
        p=d/'signed'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        authorities.append(dict(path=p.relative_to(ROOT).as_posix(),original_path=rel,SHA=sha(p),Git_base=BASE,
            Git_blob=subprocess.check_output(['git','rev-parse',BASE+':'+rel],cwd=ROOT,text=True).strip()))
        return data
    original_input=signed('reference/round109_geographic/G100-R2.txt');import hashlib
    assert hashlib.sha256(original_input).hexdigest()==SHA_INPUT
    target=ROOT/'reference/round109_geographic/G100-R2.txt';target.parent.mkdir(parents=True,exist_ok=True)
    assert not target.exists();target.write_bytes(original_input)
    r115=Path('E:/codes/ExactEBRP-round115/results/unified_exact_round115')
    manifest=json.loads(signed('results/unified_exact_round115/input_manifest.json'));p=manifest['roles'][0]
    assert p['input_sha256']==SHA_INPUT and p['T_seconds']==18000 and p['Q_vector']==[30]*8 and p['lambda']==.15
    old=r115/'campaign/raw/03_G100-R2_S0_P-S';seal=read(old/'producer_seal.json');assert sha(old/'result.json')==seal['required_SHA']['result.json']
    producer=read(old/'producer_receipt.json');assert producer['producer_seal_SHA']==sha(old/'producer_seal.json')
    close=read(old/'verification_closeout.json');assert close['necessary_verification_complete'] and close['no_new_solution_or_certificate_backfilled']
    physical=core.full_fleet(ROOT,p,read(old/'result.json'));a=core.evidence.instance(ROOT,p)
    assert physical['Y'][1:]==a['D'][1:] and physical['F']==physical['G']==physical['P']==0.
    for name in ['result.json','producer_seal.json','producer_receipt.json','verification_closeout.json','arm_total_receipt.json']:
        shutil.copyfile(old/name,d/('R115_P-S_'+name))
    write(d/'zero_witness_verification.json',dict(physical=physical,input_SHA=SHA_INPUT,T=18000,Q=[30]*8,
        literal_coefficients_identical=True,old_global_optimum_now_known=0,independent_floor0=True,
        sealed_R115_own_fleet_SHA=sha(old/'result.json'),produced_T_seconds=producer['T_produce'],R115_head=BASE,
        no_new_fleet_constructed=True,Optimize=0))
    impacted=[];changed_pairs=[];by_round={}
    for rnd in [110,111,114]:
        m=json.loads(signed(f'results/unified_exact_round{rnd}/input_manifest.json'))
        pp=next(q for q in m['roles'] if q['id']=='G100-R2')
        for key in ['input_sha256','T_seconds','Q_vector','lambda','pickup_seconds','drop_seconds','V','M']:assert pp[key]==p[key],('wrong original problem',rnd,key)
        rel=f'results/unified_exact_round{rnd}/reports_final/'+('new_arms.csv' if rnd==114 else 'arms.csv')
        raw=list(csv.DictReader(io.StringIO(signed(rel).decode('utf-8'))));rows=[]
        for row in raw:
            if row['id']!='G100-R2':continue
            if row.get('input_SHA'):assert row['input_SHA']==SHA_INPUT
            if row.get('T_seconds'):assert float(row['T_seconds'])==18000 and json.loads(row['Q_vector'])==[30]*8
            U=float(row['U']) if row.get('U') else None;L=float(row['L']) if row.get('L') else None
            if L is not None and L>0:
                impacted.append(dict(round=rnd,id='G100-R2',seed=row.get('seed','0'),arm=row['arm'],old_global_L=L,current_trusted_L=0.,
                    old_own_U=U,current_own_U=U,exact_optimum=0,input_SHA=SHA_INPUT,T_seconds=18000,Q_vector=[30]*8,
                    lambda_value=.15,objective_coefficients_same_input_bytes=True,claim_scope='published full original problem global LB',
                    current_global_claim_trust='REVOKED_BY_R115_OWN_ZERO',cognition_unix=time.time(),basis_SHA=sha(d/'zero_witness_verification.json'),
                    internal_local_positive_G_claims_not_adjudicated=True,old_clock_and_phase_unchanged=True,
                    formal_observation_eligibility_unchanged=row.get('formal_protocol_qualified',row.get('formal_performance')),
                    new_formal_R116_observation=False))
            rows.append(row)
        by_round[rnd]=rows
        if rnd==114:continue
        pairs_rel=f'results/unified_exact_round{rnd}/reports_final/'+('seed_pairs.csv' if rnd==111 else 'pairs.csv')
        published=list(csv.DictReader(io.StringIO(signed(pairs_rel).decode('utf-8'))))
        def arm(row):
            return dict(arm=row['arm'],U=float(row['U']),L=float(row['L']),gap=float(row['gap']),certificate=row['certificate']=='True',
                certificate_qualified=row['certificate_qualified']=='True',numbers_qualified=row['numbers_qualified']=='True',
                complete_seconds=float(row['complete_seconds']) if row.get('complete_seconds') else None,
                formal_protocol_qualified=row.get('formal_protocol_qualified',row.get('formal_performance'))=='True')
        for pair in published:
            if pair['id']!='G100-R2':continue
            seed=str(pair.get('seed','0'))
            hits={r['arm']:r for r in rows if str(r.get('seed','0'))==seed}
            if pair['candidate'] not in hits or pair['control'] not in hits:continue
            aa,cc=arm(hits[pair['candidate']]),arm(hits[pair['control']])
            if not aa['formal_protocol_qualified'] or not cc['formal_protocol_qualified']:
                changed_pairs.append(dict(round=rnd,seed=seed,id='G100-R2',candidate=aa['arm'],control=cc['arm'],old_classification=pair['classification'],
                    current_description=pair['classification'],old_eligibility_unchanged=True,reason='original incomplete/overcap cannot be requalified',new_R116_observation=False));continue
            before=decisions.pair(aa,cc);assert before['classification']==pair['classification']
            an=copy.deepcopy(aa);cn=copy.deepcopy(cc)
            for value in [an,cn]:value['L']=0.;value['gap']=value['U']
            after=decisions.pair(an,cn)
            changed_pairs.append(dict(round=rnd,seed=seed,id='G100-R2',candidate=aa['arm'],control=cc['arm'],
                old_U_candidate=aa['U'],old_U_control=cc['U'],old_L_candidate=aa['L'],old_L_control=cc['L'],
                current_L_candidate=an['L'],current_L_control=cn['L'],old_gap_candidate=aa['gap'],old_gap_control=cc['gap'],
                current_gap_candidate=an['gap'],current_gap_control=cn['gap'],old_classification=before['classification'],current_description=after['classification'],
                classification_changed=before['classification']!=after['classification'],old_severe=before['severe_regression'],current_severe=after['severe_regression'],
                old_clock_and_phase_unchanged=True,new_R116_observation=False))
    core.table(OUT/'known_G100_claim_impact.csv',impacted);core.table(OUT/'known_G100_pair_primitive_impact.csv',changed_pairs)
    write(d/'authority_manifest.json',dict(files=authorities,scope='R110/R111 published same G100 global primitives, plus R114 qualified global claim; no full-history or local-leaf reproof',
        Optimize=0,native_starts=0,seconds=time.perf_counter()-tick,old_raw_and_times_modified=False,
        affected_claims=len(impacted),pair_descriptions=changed_pairs,claim_impact_SHA=sha(OUT/'known_G100_claim_impact.csv')))
    print(json.dumps(dict(affected_global_claims=len(impacted),pair_primitives=len(changed_pairs),Optimize=0,seconds=time.perf_counter()-tick)))

if __name__=='__main__':run()
