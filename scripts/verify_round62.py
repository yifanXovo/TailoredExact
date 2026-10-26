"""Independent physical witness and threshold-proof audit; no optimizer."""
import ast
import argparse
import csv
import json
import math
import re
import shutil
import hashlib
from fractions import Fraction
from round62_research import ROOT,OUT,RAW,panel,sha,write,previous
from analyze_round61 import physical
from analyze_round62 import table

def data(p):
    text=(ROOT/p['instance_path']).read_text(encoding='utf-8')
    def vec(n):return ast.literal_eval(re.search(r'(?m)^'+n+r'\s*=\s*(.*)$',text)[1])
    points=vec('points');d=[[math.dist(a,b)/1.5 for b in points] for a in points]
    for k in range(len(d)):
        for i in range(len(d)):
            for j in range(len(d)):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
    q=ast.literal_eval(text.splitlines()[0][text.splitlines()[0].index('['):])
    return vec('initial'),vec('capacities'),q,d

def proof_check(p,proof):
    b,cap,Q,d=data(p);T=float(p['T_seconds']);c=float(p['pickup_seconds'])+float(p['drop_seconds']);margin=1e-5*max(1,T)
    assert proof['scope']=='original_physical_global'
    assert proof['T']==T and proof['handling']==c and abs(proof['margin']-margin)<1e-12
    domains={i:(max(0,b[i]-max(Q)),min(cap[i],b[i]+max(Q))) for i in range(1,len(b))}
    assert proof['domains']==[[i,*bounds] for i,bounds in domains.items()]
    edge_count=0;regions=[]
    for conflict in proof['conflicts']:
        events=conflict['events'];assert len({e['station'] for e in events})==len(events)
        eligible=[];region=1
        for e in events:
            i,s,q=e['station'],e['direction'],e['q'];assert s in [-1,1] and q>=1
            assert q<= (b[i] if s<0 else cap[i]-b[i])
            ks=[k for k,Qk in enumerate(Q) if q<=Qk and d[0][i]+d[i][0]+c*q<=T+margin]
            assert ks==e['eligible'];eligible.append(set(ks))
            L=max(0,b[i]-max(Q));U=min(cap[i],b[i]+max(Q));theta=b[i]+s*q
            region*=max(0,theta-L+1 if s<0 else U-theta+1)
        union=set().union(*eligible);assert sorted(union)==conflict['vehicle_union'] and len(events)>len(union)
        assert len(conflict['edges'])==len(events)*(len(events)-1)//2
        for edge in conflict['edges']:
            x,y=edge['first'],edge['second'];a,e=events[x],events[y];i,j=a['station'],e['station']
            travel=min(d[0][i]+d[i][j]+d[j][0],d[0][j]+d[j][i]+d[i][0])
            handling=c*(a['q']+e['q'] if a['direction']==e['direction'] else max(a['q'],e['q']))
            common=eligible[x]&eligible[y];assert sorted(common)==edge['common']
            assert abs(travel-edge['travel'])<1e-6 and abs(handling-edge['handling'])<1e-6
            assert abs(travel+handling-edge['duration'])<1e-6 and (not common or travel+handling>T+margin)
            edge_count+=1
        regions.append(region)
    # Recompute final coefficients independently using exact rational box ratios.
    projections={}
    for j,conflict in enumerate(proof['conflicts']):
        coefficients={};rhs=Fraction(1)
        for e in conflict['events']:
            i,s,q=e['station'],e['direction'],e['q'];L,U=domains[i];theta=b[i]+s*q
            assert L<=theta<U if s<0 else L<theta<=U
            denom=theta+1-L if s<0 else U-theta+1
            coefficients[f'Y_{i}']=Fraction(-s,denom)
            rhs+=Fraction(L if s<0 else -U,denom)
        projections[f'r62conflict_{j}']=(coefficients,rhs)
    for row in proof['rows']:
        name=row['name'];coef=None;rhs=None;sense=row['sense']
        if name.startswith('r62conflict_'):
            if '_rlt_' in name:
                base,side=name.split('_rlt_');a,brhs=projections[base]
                l,u=row['gamma_lower'],row['gamma_upper'];assert row['scope']=='canonical_gini_interval' and 0<=l<=u<=1
                factor=l if side=='lower' else u;direction=1 if side=='lower' else -1
                coef={'G':-direction*float(brhs)}
                for n,v in a.items():
                    coef['zprod_'+n[2:]]=direction*float(v)
                    if factor:coef[n]=-direction*factor*float(v)
                rhs=-direction*factor*float(brhs);assert sense=='>'
            elif sense=='>' and any(n.startswith(('p_','d_')) for n in row['coefficients']):
                conflict=proof['conflicts'][int(name.split('_')[1])];coef={};rhs=Fraction(1)
                for e in conflict['events']:
                    i,s,q=e['station'],e['direction'],e['q']
                    service_cap=min(max(Q),b[i] if s<0 else cap[i]-b[i]);denom=service_cap-q+1
                    assert denom>0
                    rhs-=Fraction(service_cap,denom)
                    for k in range(len(Q)):coef[f"{'p' if s<0 else 'd'}_{k}_{i}"]=Fraction(-1,denom)
            elif sense=='>':coef,rhs=projections[name]
            else:
                conflict=proof['conflicts'][int(name.split('_')[1])]
                coef={(f"r62{'lo' if e['direction']<0 else 'hi'}_{e['station']}_{e['q']}"):1 for e in conflict['events']}
                rhs=len(conflict['vehicle_union']);assert sense=='<'
        else:
            m=re.fullmatch(r'(r62(lo|hi)_(\d+)_(\d+))_(.*)',name);assert m,name
            z,direction,i,q,suffix=m.groups();i,q=int(i),int(q);s=-1 if direction=='lo' else 1
            L,U=domains[i];theta=b[i]+s*q;y=f'Y_{i}'
            if suffix.startswith('nested_'):
                weaker=int(suffix[7:]);coef={z:1,f'r62{direction}_{i}_{weaker}':-1};rhs=0;assert sense=='<' and weaker<q
            elif suffix=='constant':
                coef={z:1};rhs=int(U<=theta if s<0 else L>=theta);assert sense=='='
            elif suffix=='upper':
                coef={y:1,z:U-theta if s<0 else -(U-theta+1)};rhs=U if s<0 else theta-1;assert sense=='<'
            elif suffix=='lower':
                coef={y:1,z:theta+1-L if s<0 else -(theta-L)};rhs=theta+1 if s<0 else L;assert sense=='>'
            elif suffix.startswith('service_'):
                service_cap=min(max(Q),b[i] if s<0 else cap[i]-b[i])
                coef={f"{'p' if s<0 else 'd'}_{k}_{i}":1 for k in range(len(Q))}
                if suffix=='service_lower':coef[z]=-q;rhs=0;assert sense=='>'
                else:coef[z]=-(service_cap-q+1);rhs=q-1;assert suffix=='service_upper' and sense=='<'
            elif suffix=='visit':coef={z:1,**{f'z_{k}_{i}':-1 for k in range(len(Q))}};rhs=0;assert sense=='<'
            else:raise AssertionError(name)
        assert set(coef)==set(row['coefficients']),name
        assert max((abs(float(v)-row['coefficients'][n]) for n,v in coef.items()),default=0)<1e-10,name
        assert abs(float(rhs)-row['rhs'])<1e-10,name
    deficiencies=[len(c['events'])-len(c['vehicle_union']) for c in proof['conflicts']]
    return dict(passed=True,conflicts=len(proof['conflicts']),edges=edge_count,rows_recomputed=len(proof['rows']),
        clique_deficiencies=deficiencies,forbidden_box_region_sizes=regions)


def check_lp_point(model,point):
    """Parse the repository's emitted linear LP syntax, independently of Gurobi.

    Integer declarations are relaxed, while their original bounds are retained.
    The original objective-cutoff constraint is still among the checked rows.
    """
    number=r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
    signed=r'[+-]?'+number
    name=r'[A-Za-z_]\w*'
    term=re.compile(r'\s*([+-]?)\s*(?:('+number+r')\s+)?('+name+r')')
    bounds={n:[0.,math.inf] for n in point};state=None;count=0;maximum=0.;worst='';objective=None
    for raw in model.read_text().splitlines():
        line=raw.strip()
        if line in ['Subject To','Bounds','Generals','Binaries','Binary','End']:state=line;continue
        if not line or line.startswith('\\'):continue
        if state is None and line.startswith('obj:'):
            expression=line.split(':',1)[1];position=0;terms=[]
            while expression[position:].strip():
                found=term.match(expression,position);assert found,expression[position:]
                sign,coefficient,variable=found.groups()
                terms.append((-1 if sign=='-' else 1)*float(coefficient or 1)*point[variable]);position=found.end()
            objective=math.fsum(terms)
        if state=='Subject To':
            label,expression=line.split(':',1)
            lhs,sense,rhs=re.split(r'\s*(<=|>=|=)\s*',expression)
            position=0;terms=[]
            if lhs.strip()!='0':
                while lhs[position:].strip():
                    found=term.match(lhs,position);assert found,(label,lhs[position:])
                    sign,coefficient,variable=found.groups();assert variable in point,variable
                    terms.append((-1 if sign=='-' else 1)*float(coefficient or 1)*point[variable]);position=found.end()
            value=math.fsum(terms)-float(rhs)
            violation=value if sense=='<=' else -value if sense=='>=' else abs(value)
            if violation>maximum:maximum=violation;worst=label
            count+=1
        elif state=='Bounds':
            match=re.fullmatch('('+signed+r')\s*<=\s*('+name+r')\s*<=\s*('+signed+')',line)
            if match:
                lo,n,hi=match.groups();bounds[n]=[float(lo),float(hi)];continue
            match=re.fullmatch('('+name+r')\s*=\s*('+signed+')',line)
            if match:n,value=match.groups();bounds[n]=[float(value)]*2;continue
            raise AssertionError(('unsupported emitted LP bound',line))
        elif state in ['Binaries','Binary']:
            for n in line.split():bounds[n][1]=min(bounds[n][1],1.)
    bound_violation=max((max(lo-point[n],point[n]-hi) for n,(lo,hi) in bounds.items()),default=0.)
    assert maximum<=1e-5 and bound_violation<=1e-5,(maximum,worst,bound_violation)
    assert objective is not None,'original objective missing'
    return dict(original_LP_objective_recomputed=objective,original_LP_rows_checked=count,maximum_original_row_violation=maximum,
        worst_original_row=worst,maximum_bound_violation=max(0.,bound_violation))


def containment_checks():
    results=[]
    for e in previous.entries():
        if e['kind']!='LP-audit':continue
        folder=ROOT/e['destination']
        if not (folder/'completion.json').exists():continue
        audit=json.loads((folder/'audit_result.json').read_text());command=e['command']
        model=ROOT/command[command.index('--model')+1];assert sha(model)==audit['source_model_sha256']
        point={p['variable']:float(p['value']) for p in csv.DictReader((folder/'maximum_violation_point.csv').open(newline=''))}
        checked=check_lp_point(model,point)
        proof=json.loads((folder/'projection.round62.json').read_text())
        row=next(r for r in proof['rows'] if r['name']==audit['maximum_violation_row'])
        violation=row['rhs']-math.fsum(c*point[n] for n,c in row['coefficients'].items())
        assert abs(violation-audit['maximum_violation'])<1e-8
        service_check={}
        if audit.get('service_projection_LP_optimal'):
            values={p['variable']:float(p['value']) for p in csv.DictReader((folder/'service_projection_optimum.csv').open(newline=''))}
            service_check=check_lp_point(model,values)
            assert abs(service_check['original_LP_objective_recomputed']-audit['service_projection_LP_objective'])<1e-9
            service=json.loads((folder/'service_projection.round62.json').read_text())
            violation_new=max((r['rhs']-math.fsum(c*values[n] for n,c in r['coefficients'].items()) for r in service['rows']),default=0.)
            assert violation_new<=1e-5
            service_check.update(maximum_new_row_violation=violation_new,passed=True)
        results.append(dict(number=e['charged_number'],id=e['id'],**audit,**checked,service_projection_check=service_check,
            independently_recomputed_violation=violation,passed=True))
        dest=OUT/'projection_audit'/e['id'];dest.mkdir(parents=True,exist_ok=True)
        for name in ['queries.csv','maximum_violation_point.csv','service_projection_optimum.csv','audit_result.json']:
            if (folder/name).exists():shutil.copyfile(folder/name,dest/name)
    write(OUT/'projection_containment_verification.json',results)

def main():
    panels=panel();checks=[];proofs=[]
    for e in previous.entries():
        folder=ROOT/e['destination']
        if not (folder/'completion.json').exists():continue
        p=panels[e['id']];assert sha(ROOT/p['instance_path'])==p['input_sha256']
        candidates=list(folder.glob('**/*witness.json'))
        result=folder/'result.json'
        if result.exists() and 'routes' in json.loads(result.read_text()):candidates.append(result)
        for path in candidates:
            witness=json.loads(path.read_text(encoding='utf-8'));checked=physical(p,witness)
            diagnostic=e['kind']=='oracle'
            assert diagnostic or checked['original_T_feasible'],(path,checked)
            checks.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],stage=e['stage'],
                file=str(path.relative_to(ROOT)),sha256=sha(path),scope='time_diagnostic' if diagnostic else 'original_problem',**checked))
            dest=OUT/'witnesses'/str(e['charged_number'])/path.relative_to(folder)
            dest.parent.mkdir(parents=True,exist_ok=True)
            if path.name=='result.json':
                compact={k:witness[k] for k in ['objective','routes','verification'] if k in witness};write(dest,compact)
            else:shutil.copyfile(path,dest)
    seen={}
    for e in previous.entries():
        folder=ROOT/e['destination']
        if not (folder/'completion.json').exists():continue
        paths=list(folder.glob('**/*.round62.json'))
        if e['kind']=='proof':paths += [p for p in folder.glob('*.json') if p.name in ['generated.json','regression.json']]
        for path in paths:
            p=panels[e['id']];proof=json.loads(path.read_text());signature=dict(proof);signature.pop('seconds',None)
            key=hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest()
            if key not in seen:
                checked=proof_check(p,proof);seen[key]=checked
                dest=OUT/'proofs'/p['id']/(key+'.json');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
            proofs.append(dict(id=p['id'],number=e['charged_number'],file=str(path.relative_to(ROOT)),sha256=sha(path),deduplicated_proof=key,**seen[key]))
    table(OUT/'witness_verification.csv',checks);write(OUT/'proof_verification.json',proofs);containment_checks()
    print('independent route witnesses',len(checks),'proof records',len(proofs),'all passed')
def submitted():
    """Verify the committed witnesses/proofs without requiring local raw logs.

    Does not regenerate or overwrite measured result/verification tables.
    Native LP containment requires the separately hashed raw canonical model.
    """
    panels=panel();entries={e['charged_number']:e for e in previous.entries() if e['charged']}
    count=0
    for path in sorted((OUT/'witnesses').glob('**/*.json')):
        number=int(path.relative_to(OUT/'witnesses').parts[0]);entry=entries[number]
        checked=physical(panels[entry['id']],json.loads(path.read_text(encoding='utf-8')))
        assert entry['kind']=='oracle' or checked['original_T_feasible'],path
        count+=1
    proofs=0
    for path in sorted((OUT/'proofs').glob('*/*.json')):
        proof_check(panels[path.parent.name],json.loads(path.read_text()));proofs+=1
    assert count and proofs,'no submitted evidence found'
    print('submitted evidence passed:',count,'physical witnesses,',proofs,'distinct threshold proofs; no optimizer')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--submitted',action='store_true')
    (submitted if parser.parse_args().submitted else main)()
