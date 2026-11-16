"""Independent read-only table/claim reconciliation. No optimizer or H call."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, io, json, math, re, time

START=time.perf_counter()
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round169'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def text(p):return Path(p).read_text(encoding='utf-8-sig')
def bind(p):
    p=Path(p)
    return dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,SHA256=hashlib.sha256(p.read_bytes()).hexdigest())
def close(a,b):return math.isclose(a,b,rel_tol=2e-13,abs_tol=1e-13)
def fmt(v):return format(v,'.9g')

rows=read(OUT/'complete_arms.json')['rows']
cost=read(OUT/'cost_report.json')
body=text(ROOT/'results/unified_exact_round137/paper_body.md')
supp=text(ROOT/'results/unified_exact_round137/supplement.md')
report=text(OUT/'final_report.md')
note=text(OUT/'research_decision.md')
memo=text(OUT/'author_decision_memo.md')
by={(r['role'],r['arm']):r for r in rows}
assert len(rows)==18 and len(by)==18
checks=[]
for r in rows:
    a=read(ROOT/r['audit_path']);raw=read(ROOT/r['raw_result'])
    assert a['passed'] and a['Optimize_run_by_reviewer']==0
    assert all(close(a[k],r[k]) for k in ['U','L','relative_gap'])
    assert a['certificate']==r['certificate']
    assert close(a['true_final_physical']['F'],r['U'])
    assert close(a['true_final_physical']['G'],r['G']) and close(a['true_final_physical']['P'],r['P'])
    assert close(r['G']+r['lambda_value']*r['P'],r['U'])
    assert close(raw['initial_heuristic_UB'],r['initial_U'])
    assert close(raw['upper_bound'],r['U']) and close(raw['lower_bound'],r['L'])
    assert close(r['signed_absolute_gap'],r['U']-r['L'])
    assert close(r['relative_gap'],(r['U']-r['L'])/abs(r['U']))
    assert r['H_calls']==(1 if r['arm']=='B' else 3)
    assert r['process_outer_seconds']<r['cap_seconds']
    assert r['process_wall_time_comparable'] and r['full_initialization_complete']
    assert not r['end_state_source_rejected']
    assert r['actual_Optimize']==a['actual_Optimize']==len(a['actual_call_log_bindings'])
    assert r['LP']==a['LP'] and r['MIP']==a['MIP']
    assert r['actual_Optimize']==r['LP']+r['MIP']
    assert close(r['Native_seconds'],a['Native_seconds'])
    endpoint='| '+r['role']+'/'+r['arm']+' | '+' | '.join([
        fmt(r['initial_U']),fmt(r['U']),fmt(r['L']),fmt(max(0,r['relative_gap'])),
        'CERT' if r['certificate'] else 'OPEN',fmt(r['process_outer_seconds'])])+' |'
    fee='| '+r['role']+'/'+r['arm']+' | '+' | '.join([
        fmt(r['H_seconds']),fmt(r['all_model_build_seconds']),f"{r['LP']} / {r['MIP']}",
        fmt(r['Native_seconds']),fmt(r['Work']),fmt(r['nodes'])])+' |'
    assert endpoint in report and endpoint in supp,endpoint
    assert fee in report and fee in supp,fee
    checks.append(dict(position=r['position'],role=r['role'],arm=r['arm'],initial_U=r['initial_U'],
        U=r['U'],L=r['L'],relative_gap=r['relative_gap'],certificate=r['certificate'],
        process_seconds=r['process_outer_seconds'],Optimize=r['actual_Optimize'],LP=r['LP'],MIP=r['MIP']))

roles=list(dict.fromkeys(r['role'] for r in rows))
comparisons=[]
for role in roles:
    b,m,c=[by[role,arm] for arm in ['B','M','C']]
    compact='| '+role+' | '+' | '.join(fmt(r['U'])+' / '+fmt(r['L']) for r in [b,m,c])+' |'
    assert compact in body and compact in report
    comparisons.append(dict(role=role,final_B_minus_M=b['U']-m['U'],final_M_minus_C=m['U']-c['U'],
        C_L_minus_B=c['L']-b['L'],C_L_minus_M=c['L']-m['L'],all_certified=all(r['certificate'] for r in [b,m,c])))
assert [int(x) for x in re.findall(r'^\*\*Table (\d+)\.',body,re.M)]==list(range(1,12))
for role in roles[3:]:
    b,m,c=[by[role,arm] for arm in ['B','M','C']]
    assert c['U']<min(b['U'],m['U'])-1e-6
    assert not any(r['certificate'] for r in [b,m,c])
assert sum(r['certificate'] for r in rows)==9
assert by['R163-C20-S','C']['process_outer_seconds']>max(by['R163-C20-S',arm]['process_outer_seconds'] for arm in ['B','M'])
assert by['R163-X35-S','M']['initial_U']==by['R163-X35-S','B']['initial_U']
assert by['R163-X35-S','M']['U']<by['R163-X35-S','B']['U']
assert by['R163-B35-S','C']['L']>by['R163-B35-S','B']['L']
for role in ['R163-C35-U','R163-X35-S']:assert by[role,'C']['L']<by[role,'B']['L']

h=read(OUT/'h_results.json');pools=[]
for r in h['rows']:
    d=OUT/'h_raw'/r['role']/'primal'
    path={k:read(d/k/'path.json') for k in ['base','M_s1','M_s2','C_s1','C_s2']}
    b=path['base']['path_seconds'];m=b+sum(path[k]['path_seconds'] for k in ['M_s1','M_s2']);c=b+sum(path[k]['path_seconds'] for k in ['C_s1','C_s2'])
    line='| '+r['role']+' | '+' | '.join(fmt(v) for v in [b,m,c])+' |'
    assert line in report and line in supp,line
    pools.append(dict(role=r['role'],B_path_seconds=b,M_pool_seconds=m,C_pool_seconds=c))
assert sum(r['actual_Optimize'] for r in rows)==cost['actual_Optimize']==93
assert sum(r['LP'] for r in rows)==cost['LP']==66
assert sum(r['MIP'] for r in rows)==cost['MIP']==27
assert sum(r['H_calls'] for r in rows)==cost['complete_H_calls']==42
for field,cost_field in [('Native_seconds','Native_seconds'),('Work','Native_Work'),
    ('process_outer_seconds','complete_process_outer_seconds')]:
    assert close(sum(r[field] for r in rows),cost[cost_field])

d=read(OUT/'decision.json')
assert d['decision']=='recommend_independent_limited_confirmation'
assert d['default']=='B' and not any(d[k] for k in ['C166','D167','C169'])
assert d['new_P_pairs']==0 and d['no_Round170']
for phrase in ['Matched M also improves the paid X35 primal endpoint despite its unchanged H Start.',
    'not default promotion or a claim of uniform acceleration.', 'small known-role panel supports no statistical or new P-GRB win-rate claim.']:
    assert phrase in body
assert 'does not reject\nmultistart generally' in report
assert 'not complete dominance or robust acceleration' in report and 'not complete dominance or robust acceleration' in note
assert 'does not fill the remaining broader OR mechanism/theory gap' in memo
assert '[@paquete2003two]' in body and '[@paquete2003two]' in supp
assert '@misc{paquete2003two' in text(ROOT/'results/unified_exact_round137/references.bib')

changes=read(OUT/'fleet_changes.json')['rows']
structural=[]
for row in changes:
    if row['arm']!='C':continue
    c=row['changes'];assert not c['R168_parent_certificate_applied'] and not c['sign_flips']
    structural.append(dict(role=row['role'],served_added=c['served_added'],served_removed=c['served_removed'],
        owner_changes=len(c['owner_changes']),stock_changes=len(c['stock_changes']),order_inversions=len(c['relative_order_inversions'])))

csv_recon=read(OUT/'CSV_reconciliation.json')
assert not csv_recon['authoritative_112_available'] and csv_recon['new_master_rows']==0 and csv_recon['new_P_pairs']==0
inc=ROOT/csv_recon['increment']['path'];raw=inc.read_bytes();assert raw.startswith(b'\xef\xbb\xbf')
incrows=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))));assert len(incrows)==7 and all(len(r)==28 for r in incrows)
assert all('N/A-P' in '|'.join(row) and '无配对结果' in row and 'N/A' in row for row in incrows[1:])
assert csv_recon['eligible_B_increment_rows']==6 and not csv_recon['M_C_in_master']

prov=read(OUT/'weight_provenance.json')['final_first_hit']
assert prov['first_verified_witness_producer_publication_marker_seconds']==2311.5796264
assert prov['first_external_observation_process_seconds']==2311.7349999998696
assert prov['precise_internal_solver_discovery_seconds'] is None
assert 'producer publication/close marker' in report and 'unrecorded internal solver discovery' in report
assert '2370.0371459s after return' in report

review=dict(schema='round169-independent-research-review-final-v1',UTC=datetime.now(timezone.utc).isoformat(),
    reviewer='/root/research_review',status='PASS_RESEARCH_AND_TEXT_TARGETED_PDF_PENDING',blocking_findings=[],
    scope='All 18 actual endpoint rows, raw results and qualified audit outputs; tables in body/final report/S169; H path/pool costs; decision and limitations; corrected historic timing and CSV increment. Targeted new PDF review follows separately.',
    Optimize=0,H_calls=0,all_18_endpoint_and_fee_rows_match_raw_and_audit=True,
    main_compact_table_rows_match=True,all_7_H_pool_expense_rows_match=True,
    actual_Optimize=93,LP=66,MIP=27,complete_H_calls=42,H_only_H_calls=35,
    n20_certificates=9,n35_certificates=0,comparisons=comparisons,endpoint_readback=checks,
    H_pool_costs=pools,structural_readback=structural,
    interpretation='C retains a finite paid original-objective primal benefit beyond matched M on all three n35 roles, with no n35 certification and mixed L. C20 is a slower certified counterexample. M improves the paid X35 endpoint despite identical H Start, so no blanket restart-null explanation or causal speed claim is made. Only a future independently preregistered limited confirmation is recommended; B stays default.',
    prior_art_and_history_boundaries_preserved=True,new_OR_theory_claim=False,new_P_pair_claim=False,
    exposed_known_inputs_and_single_Native_Seed_limits_explicit=True,
    weight_provenance_clock_correction='review/provenance_clock_update.json remains authoritative correction to preserved initial review; current report uses validated NEJ1 producer marker versus external availability, unrecorded internal discovery and later outer-store acceptance.',
    CSV_increment=dict(records=6,columns=28,UTF8_BOM=True,no_P_pairs=True,actual_master_available=False,
        actual_master_rows_added=0,no_112_to_118_fabrication=True,increment=bind(inc)),
    pending_delivery_check='At read time final_report mentions CSV_QA.json; root was notified to create it or correct that reference before final delivery. PDF generation/visual review pending root paths.',
    seconds=time.perf_counter()-START,evidence=[bind(p) for p in [OUT/'complete_arms.json',OUT/'complete_arms.csv',
        OUT/'final_report.md',OUT/'research_decision.md',OUT/'decision.json',OUT/'author_decision_memo.md',
        ROOT/'results/unified_exact_round137/paper_body.md',ROOT/'results/unified_exact_round137/supplement.md',
        ROOT/'results/unified_exact_round137/references.bib',OUT/'weight_provenance.json',OUT/'CSV_reconciliation.json']])
(OUT/'review/research_review_final.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('PASS 18 endpoints/fees, 6 compact rows, 7 H cost rows, 93 calls, claims and CSV; PDF pending')
