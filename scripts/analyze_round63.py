"""Reuse established physical/LP verification, add independent resource-row checks."""
import csv
import json
import math
import re
from pathlib import Path
import round63_research as run
import analyze_round62 as old
from verify_round62 import check_lp_point, proof_check
from analyze_round61 import physical
from report_round62 import compare
run.bind_runner()

ROOT,OUT,RAW=run.ROOT,run.OUT,run.RAW
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def csvrows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def table(name,rows):old.table(OUT/name,rows)

def resource_row(d,k,support):
    s=set(support);assert len(s)==len(support) and all(1<=i<=d['V'] for i in s)
    c={}
    for i in s:
        if d['handling']:c[f'p_{k}_{i}']=d['handling']
        for h in range(d['V']+1):
            if h!=i and d['travel'][h][i]:c[f'x_{k}_{h}_{i}']=d['travel'][h][i]
        for j in range(d['V']+1):
            if j not in s and d['upper'][i][j]:c[f'x_{k}_{i}_{j}']=-d['upper'][i][j]
    return c

def audit_strength():
    audits=[];lp=[];cut_audits=[]
    for folder in sorted(RAW.glob('strength*/*')):
        identity=folder.name
        if not (folder/'probe_result.json').exists():continue
        result=read(folder/'probe_result.json');d=read(folder/'resource.json')
        # Original input and original LP file identities are fixed in launch.json.
        launch=read(folder/'launch.json');cmd=launch['command'];source=Path(cmd[cmd.index('--model')+1])
        assert run.sha(source)==cmd[cmd.index('--expected-sha')+1]
        for name,model in [('F0',source),('simple',folder/'simple.lp'),('explicit',folder/'explicit.lp'),('closed',source)]:
            point_file=folder/(name+'_point.csv')
            if not point_file.exists():continue
            point={r['variable']:float(r['value']) for r in csvrows(point_file)}
            residual=check_lp_point(model,point);audits.append(dict(id=identity,stage=folder.parent.name,point=name,**residual))
        # The first closure inspection reuses F0 after the simple LP query.
        # Consume the ordered term stream per cut occurrence: a query number
        # alone is not a unique point identity in this diagnostic trace.
        point_terms=iter(csvrows(folder/'cut_points.csv'))
        cuts=[json.loads(s) for s in (folder/'cuts.jsonl').read_text().splitlines()]
        for cut in cuts:
            assert cut['scope']=='original_physical_global' and cut['identity']==d['identity']
            c=resource_row(d,cut['vehicle'],cut['support']);assert c==cut['coefficients']
            p={}
            for name in sorted(c):
                term=next(point_terms)
                assert int(term['query'])==cut['query'] and int(term['vehicle'])==cut['vehicle'] and term['variable']==name
                p[name]=float(term['value'])
            v=math.fsum(c[n]*p[n] for n in c)
            assert abs(v-cut['violation'])<1e-9 and v>1e-7
        assert next(point_terms,None) is None
        cut_audits.append(dict(id=identity,stage=folder.parent.name,rows=len(cuts),all_passed=True))
        q=csvrows(folder/'lp_queries.csv');assert len(q)==result['optimizer_calls']
        for row in q:
            # The inherited backend counter precedes optional row insertion.
            # Read actual post-insertion sizes from the native optimizer log.
            match=re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',
                (folder/('lp_'+row['query']+'.log')).read_text(errors='replace'))
            assert match
            row=dict(row,initial_backend_nonzeros=row['nonzeros'],**dict(zip(['rows','columns','nonzeros'],map(int,match.groups()))))
            lp.append(dict(id=identity,stage=folder.parent.name,**row))
    table('lp_comparison.csv',lp);run.write(OUT/'strength_verification.json',dict(points=audits,cuts=cut_audits))
    return audits

def summarize():
    old.ROOT=ROOT;old.OUT=OUT;old.RAW=RAW
    rows=old.performance();resource=[];calls=[]
    by_number={r['number']:r for r in rows if r['charged']}
    for e in run.runner.entries():
        dest=ROOT/e['destination']
        if not (dest/'completion.json').exists():continue
        count=0
        if (dest/'round63_optimizer_calls.csv').exists():count=len(csvrows(dest/'round63_optimizer_calls.csv'))
        elif (dest/'native_calls.csv').exists():count=len(csvrows(dest/'native_calls.csv'))
        elif (dest/'external/paper_optimize_ledger.csv').exists():count=len(csvrows(dest/'external/paper_optimize_ledger.csv'))
        elif e['charged'] and (dest/'result.json').exists():count=1
        calls.append(dict(number=e['charged_number'],id=e['id'],stage=e['stage'],arm=e['arm'],optimizer_calls=count))
        if e['charged_number'] in by_number and (dest/'round63_root_lp_result.json').exists():
            r=by_number[e['charged_number']];prep=read(dest/'round63_root_lp_result.json')
            r['mip_work']=r['work'];r['preparation_lp_work']=prep['work'];r['work']+=prep['work'];r['optimizer_calls']=count
        for p in sorted(dest.glob('**/*.round63*.json')):
            obj=read(p)
            if 'queries' in obj:resource.append(dict(number=e['charged_number'],id=e['id'],stage=e['stage'],arm=e['arm'],path=str(p.relative_to(ROOT)),**obj))
    table('resource_lifecycle.csv',resource);table('optimizer_calls.csv',calls)
    table('runs.csv',rows)
    run.write(OUT/'budget.json',dict(charged=sum(e['charged'] for e in run.runner.entries()),maximum=72,
        native_micro=sum(e['kind']=='native-micro' for e in run.runner.entries()),optimizer_calls=sum(c['optimizer_calls'] for c in calls),
        maxflow_calls=sum(r['maxflow_calls'] for r in resource)+sum(read(p)['maxflow_calls'] for p in RAW.glob('**/probe_result.json')),
        completed_charged=sum(r['charged'] for r in rows)))
    for r in rows:
        if r.get('objective') is not None:print(r['number'],r['id'],r['arm'],round(r['wall'],3),r.get('fixed_interval_certificate',r.get('strict_certified_original_problem')),r.get('absolute_gap'))
    groups={}
    for row in rows:
        if row.get('scope') and row['performance_eligible']:
            groups.setdefault((row['id'],row['stage'],row['cap'],row['scope'],row['exe_sha256']),{})[row['arm']]=row
    pairs=[]
    for group in groups.values():
        for baseline in ['off','Single-off-off','K1-off-off']:
            if baseline in group:
                for arm in group:
                    if arm!=baseline:pairs.append(compare(group[baseline],group[arm]))
        for baseline,candidate in [('precrush','dry'),('dry','cuts'),('root-dry','root'),('simple','explicit')]:
            if baseline in group and candidate in group:pairs.append(compare(group[baseline],group[candidate]))
    # Exact same-build repeat or a predeclared shared lifecycle may live in a
    # different storage stage. Explicit links preserve both charged identities.
    links=OUT/'comparison_links.json'
    indexed={r['number']:r for r in rows if r['charged']}
    if links.exists():
        for link in read(links):
            if not all(n in indexed for n in [link['baseline'],link['candidate']]):continue
            a,b=indexed[link['baseline']],indexed[link['candidate']]
            assert a['id']==b['id'] and a['performance_eligible'] and b['performance_eligible']
            pair=compare(a,b);pair['link_reason']=link['reason'];pairs.append(pair)
    # Stable K1-H / official P-GRB are complete original-problem comparisons,
    # explicitly separate from the cold research control.
    for group in groups.values():
        for base in ['K1-H','P-GRB']:
            if base in group:
                for candidate in [n for n in group if n.startswith('K1-off-')]:
                    pairs.append(compare(group[base],group[candidate]))
    table('pairs.csv',pairs)
    return rows

if __name__=='__main__':summarize();audit_strength()
