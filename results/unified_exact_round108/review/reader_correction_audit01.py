"""Finite reader-only correction review; no project imports/native/raw archive reads."""
from pathlib import Path
import ast, copy, difflib, hashlib, json, time, types

ROOT=Path('E:/codes/ExactEBRP-round108');OUT=ROOT/'results/unified_exact_round108';REVIEW=OUT/'review'
OLD=OUT/'engineering/signed_gap_reader_correction01/round108_decisions.py';NEW=ROOT/'scripts/round108_decisions.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def funcs(tree):return {n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
def same(a,b):return ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
def namespace(path):
    tree=ast.parse(path.read_text())
    assert all(isinstance(n,(ast.Expr,ast.Assign,ast.FunctionDef,ast.Import)) for n in tree.body)
    assert all(n.names[0].name=='math' for n in tree.body if isinstance(n,ast.Import))
    q={'__name__':'independent_finite_reader'};exec(compile(tree,str(path),'exec'),q);return q,tree

tick=time.perf_counter();old,ot=namespace(OLD);new,nt=namespace(NEW);of,nf=funcs(ot),funcs(nt)
candidate=read(OUT/'candidate_identity.json');pre=read(OUT/'engineering/signed_gap_reader_correction01/before.json');post=read(OUT/'engineering/signed_gap_reader_correction01/after.json')
assert sha(OLD)==candidate['decision_reader_SHA']==pre['original_SHA']=='c110f7aab57e966c44158208ce1a5cd0d6169186db7f37c57ef1928bd33d421a'
assert sha(NEW)==post['corrected_SHA']=='9a827d2fccd9b37483c2d3a5f8aa5877abb5c2db434554d18abed28d13c63c46'
assert sha(OUT/'candidate_identity.json')==post['unchanged_frozen_candidate_identity_SHA']
unchanged=[]
for k in ['finite','qualified_numbers','relative','selection','early_impossible']:
    assert same(of[k],nf[k]);unchanged.append(k)
pair=copy.deepcopy(nf['pair']);op=next(n for n in of['pair'].body if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='good');np=next(n for n in pair.body if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='good')
np.body[-1]=copy.deepcopy(op.body[-1]);assert same(pair,of['pair'])
bridge=copy.deepcopy(nf['bridge']);ol=next(n for n in of['bridge'].body if isinstance(n,ast.For));nl=next(n for n in bridge.body if isinstance(n,ast.For));oa=next(n for n in ol.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='percentage' for t in n.targets));ni=next(i for i,n in enumerate(nl.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='percentage' for t in n.targets));nl.body[ni]=copy.deepcopy(oa);assert same(bridge,of['bridge'])
# Run the already inspected finite fixture with an injected pure decision namespace;
# remove its project import and never execute its command-line writer.
CP=ROOT/'scripts/round108_reader_counterexamples.py';ct=ast.parse(CP.read_text());ct.body=[n for n in ct.body if not (isinstance(n,ast.Import) and any(a.name=='round108_decisions' for a in n.names))]
env={'__name__':'independent_finite_counterexamples','d':types.SimpleNamespace(**new)};exec(compile(ct,str(CP),'exec'),env)
checks=env['checks']();assert checks['passed'] and len(checks['cases'])==17 and checks['Optimize']==checks['solver_processes']==checks['IIS']==0
saved=read(OUT/'engineering/reader_counterexamples02/checks.json');assert saved==checks
arm=env['arm'];extra=[]
def check(name,condition,detail=None):assert condition,name;extra.append(dict(name=name,passed=True,detail=detail))
c=arm(U=.19,L=.19+1e-15);p=arm(method='P-GRB',U=.2,L=.1)
a,b=old['pair'](c,p),new['pair'](c,p)
strip=lambda q:{k:v for k,v in q.items() if k not in ['gap_ratio','gap_ratio_null_reason','percentage_gap_path_applicable']}
check('negative candidate gap has only percentage metadata difference in pair',strip(a)==strip(b) and a['gap_ratio']<0 and b['gap_ratio'] is None and not b['percentage_gap_path_applicable'],dict(original_gap_ratio=a['gap_ratio'],corrected_gap_ratio=b['gap_ratio'],signed_gap=c['gap'],classification=b['classification']))
check('signed relative U normalization unchanged',old['relative'](c)==new['relative'](c) and new['relative'](c)[0]<0)
for role in ['F2','C2']:
    arms=[arm(role=r,method=m,U=.2,L=.1) for r in ['F2','C2'] for m in ['P-GRB','ENS-C','M-B']]
    for x in arms:
        if x['arm']=='M-B':x.update(U=.19,L=.12,gap=.07)
        if x['id']==role and x['arm']=='M-B':x.update(U=.19,L=.19+1e-15,gap=.19-(.19+1e-15))
    a,b=old['bridge'](arms),new['bridge'](arms)
    check(role+' tiny negative candidate cannot use bridge percentage',a['gates'][role]['passed'] and not b['gates'][role]['passed'] and not b['gates'][role]['percentage_path_applicable'])
for cert in [False,True]:
    c=arm(U=.2,L=.2+1e-15,cert=cert,t=70);p=arm(method='P-GRB',U=.2,L=.2,cert=cert,t=100)
    check('absolute/certificate branch unchanged with signed negative '+str(cert),strip(old['pair'](c,p))==strip(new['pair'](c,p)))
for c,p in [(arm(U=.19,L=.12),arm(method='P-GRB')),(arm(U=.2,L=.1),arm(method='P-GRB',U=.2,L=.2+1e-15)),(arm(U=0,L=0),arm(method='P-GRB',U=0,L=0))]:
    check('ordinary or reference-negative case preserves classification',strip(old['pair'](c,p))==strip(new['pair'](c,p)))
diff=''.join(difflib.unified_diff(OLD.read_text().splitlines(True),NEW.read_text().splitlines(True),fromfile=str(OLD),tofile=str(NEW)))
result=dict(schema='round108-independent-reader-correction-review-v1',decision='ACCEPT',scope='Only pure signed-gap percentage metadata/path qualification correction. Does not alter production/performance admission or select candidate.',reviewed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),original_reader_SHA=sha(OLD),corrected_reader_SHA=sha(NEW),candidate_identity_SHA=sha(OUT/'candidate_identity.json'),performance_admission_SHA=sha(REVIEW/'performance_admission.json'),development_protocol_SHA=sha(OUT/'development_protocol.json'),confirmation_protocol_SHA=sha(OUT/'confirmation_protocol.json'),before_record_SHA=sha(OUT/'engineering/signed_gap_reader_correction01/before.json'),after_record_SHA=sha(OUT/'engineering/signed_gap_reader_correction01/after.json'),finite_counterexample_source_SHA=sha(CP),producer_17_case_record_SHA=sha(OUT/'engineering/reader_counterexamples02/checks.json'),independently_rerun_17_cases=checks,additional_independent_cases=extra,unchanged_functions_ast=unchanged,pair_all_other_ast_unchanged=True,bridge_all_other_ast_unchanged=True,signed_absolute_gap_not_clipped=True,signed_relative_gap_unchanged=True,thresholds_and_absolute_materiality_certificate_time_branches_unchanged=True,user_requirement='Section 8: tolerance-sized negative signed gap is retained separately with no percentage division; qualified finite U/L relative gap remains (U-L)/abs(U). Section 7: only independently qualified complete certificate branches can bypass unavailable percentage path.',diff=diff,reviewer_script_SHA=sha(Path(__file__)),reviewer_calls=dict(Optimize=0,LP_solve=0,IIS=0,native_environment=0,compiler=0,full_reader=0,raw_archive_scan=0),elapsed_seconds=time.perf_counter()-tick)
with (REVIEW/'reader_correction_review01.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
print(json.dumps(dict(decision=result['decision'],producer_cases=17,additional_cases=len(extra),review_SHA=sha(REVIEW/'reader_correction_review01.json'))))
