"""Finite matrix deletion/default-off checks; no Optimize or new qualification regime."""
from round137_common import *
import collections
import round108_reader as core

def main():
    p=next(p for p in read(OUT/'input_manifest.json')['roles'] if p['id']=='K-15-S')
    q=OUT/'qualification/matrices_v2';models={}
    old=q/'historical-off'
    if not (old/'build.json').exists():
        assert metered('export_historical_off_v2','engineering',[WORK/'build-cache/round135/Round135Export.exe',
            ROOT/p['input_path'],p['T_seconds'],0,1,1,'ms2',old],timeout=60)==0
    for variant in ['off','no-ab','no-cr','no-cg']:
        dest=q/variant
        if not (dest/'build.json').exists():
            assert metered('export_'+variant+'_v2','engineering',[BUILD/'Round137Export.exe',ROOT/p['input_path'],
                p['T_seconds'],0,1,1,'ms2',dest,.15,variant],timeout=60)==0
        models[variant]=core.lp_model(dest/'original.lp')
    base=models['off'];assert base==core.lp_model(old/'original.lp'),'default-off changed accepted matrix'
    rows={};base_rows=collections.Counter(base['rows'])
    for name,m in models.items():
        if name=='off':continue
        removed=base_rows-collections.Counter(m['rows']);added=collections.Counter(m['rows'])-base_rows
        assert not added and removed
        assert m['objective']==base['objective']
        for n in m['order']:
            assert m['bounds'][n]==base['bounds'][n] and m['types'][n]==base['types'][n]
        missing=set(base['order'])-set(m['order'])
        if name=='no-ab':assert not missing and sum(removed.values())==2*p['V']
        if name=='no-cr':assert not missing
        if name=='no-cg':assert missing<= {'W_SP','r_min','r_max'},missing
        rows[name]=dict(removed_rows=sum(removed.values()),added_rows=0,removed_columns=sorted(missing),
            original_types_bounds_and_objective_unchanged=True,
            removed_row_counter=[dict(terms=list(t),sense=s,rhs=r,count=c) for (t,s,r),c in removed.items()])
    source=(ROOT/'include/Round127Research.hpp').read_text()
    assert 'return round127().mode!="ms2" && round127().mode!="s2-root";' in source
    write(OUT/'qualification/matrix_checks.json',dict(PASS=True,Optimize=0,fixture=p,
        default_off_equals_accepted_R135=True,pair_only_preserved_by_ms2=True,groups=rows,
        matrices={n:dict(SHA256=sha(q/n/'original.lp'),rows=len(m['rows']),columns=len(m['order'])) for n,m in models.items()}))
    print(json.dumps({n:dict(rows=r['removed_rows'],columns=r['removed_columns']) for n,r in rows.items()}))

if __name__=='__main__':main()
