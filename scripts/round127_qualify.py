"""Finite zero-Optimize default equivalence, deletion and path checks."""
from round127_common import *
from round127_data import TRAIN
import collections,math,itertools,csv
import round108_reader as core

def row_family(row):
    terms,sense,rhs=row;v=dict(terms);names=set(v)
    p=[n for n in names if n.startswith('p_')];z=[n for n in names if n.startswith('z_')];d=[n for n in names if n.startswith('d_')]
    h=[n for n in names if n.startswith('h_')];r=[n for n in names if n.startswith('r_')];e=[n for n in names if n.startswith('e_')]
    if d and len(d)==1 and set(d+p)==names and sense=='<=' and rhs==0 and v[d[0]]==1 and all(v[n]==-1 for n in p):return 'ordered_supply'
    if z and len(z) in [2,3] and set(z)==names and all(v[n]==1 for n in z) and sense=='<=' and rhs==len(z)-1:return f'cover_{len(z)}'
    if z and len(z) in [2,3] and len(p)==len(z) and set(p+z)==names and all(v[n]==120 for n in p) and len({v[n] for n in z})==1 and sense=='<=':return f'conditional_{len(z)}'
    if 'W_SP' in names:return 'W_SP'
    if h and len(h)==1 and set(h+r)==names and sense=='<=' and rhs==0:return 'H_spread'
    if r and not h and set(r)==names and sense=='<=':return 'explicit_centering'
    if h and e and set(h+e)==names and sense=='<=':return 'linear_objective_estimator'
    return 'UNEXPECTED'
def compare(base,path,mode,V,M):
    a=core.lp_model(base if base.is_file() else base/'original.lp');b=core.lp_model(path if path.is_file() else path/'original.lp')
    assert a['objective']==b['objective']
    ca=collections.Counter(a['rows']);cb=collections.Counter(b['rows'])
    assert not cb-ca,'ablation added rows'
    removed=ca-cb;families=collections.Counter()
    for row,n in removed.items():families[row_family(row)]+=n
    allowed={'mr':{'ordered_supply','cover_2','cover_3','conditional_2','conditional_3'},
        'ms2':{'cover_3','conditional_3'},'mg':{'H_spread','explicit_centering','linear_objective_estimator','W_SP'}}[mode]
    assert set(families)<=allowed,(mode,families)
    aux={'W_SP','r_min','r_max'} if mode=='mg' else set()
    assert set(a['types'])-set(b['types'])==aux and not set(b['types'])-set(a['types'])
    assert {k:v for k,v in a['types'].items() if k not in aux}==b['types']
    assert {k:v for k,v in a['bounds'].items() if k not in aux}==b['bounds']
    if mode=='mr':assert sum(families.values())==M*(math.comb(V,2)+math.comb(V,3)+V),families
    if mode=='ms2':assert sum(families.values())==M*math.comb(V,3),families
    if mode=='mg':assert sum(families.values())==5*math.comb(V,2)+6 and families['W_SP']==5 and families['linear_objective_estimator']==1,families
    return dict(mode=mode,removed_rows=sum(removed.values()),removed_columns=sorted(aux),families=dict(families),
        remaining_objective_types_bounds_and_duplicate_preserving_rows_identical=True)
def exports():
    q=OUT/'qualification/exports';q.mkdir(parents=True,exist_ok=True);records=[]
    def launch(label,args):
        dest=Path(args[-1])
        if (dest/'build.json').exists() and (dest/'native_metadata.json').exists():
            assert sha(dest/'original.lp')==read(dest/'build.json')['canonical_sha256']
            assert read(dest/'native_metadata.json')['Optimize']==0
            return 0
        attempt=len(list((OUT/'fees').glob(label+'*')))+1
        return metered(label+f'_{attempt:02d}','qualification',args)
    for p in [TRAIN[0],TRAIN[2]]:
        # Qualification U is the physical empty fleet objective, never passed
        # to a formal arm. Names/roles are training inputs only.
        a=core.evidence.instance(ROOT,p);ratios=[b/d for b,d in zip(a['b'][1:],a['D'][1:])];S=sum(ratios)
        G=sum(abs(x-y) for j,x in enumerate(ratios) for y in ratios[j+1:])/(p['V']*S) if S else 0
        U=G+.15*sum(w*abs(r-1) for w,r in zip(a['w'][1:],ratios));hi=min(U,(p['V']-1)/p['V'])
        scopes=[('root',0,hi),('left',0,hi/2),('right',hi/2,hi)]
        for scope,lo,upper in scopes:
            modes=['mb','mr','mg','ms2'] if scope=='root' or p==TRAIN[0] else ['mb','mg']
            for mode in modes:
                dst=q/p['id']/scope/mode
                cmd=[BUILD/'Round127ExportE1.exe',ROOT/p['input_path'],p['T_seconds'],lo,upper,U,mode,dst]
                rc=launch(f'zero_{p["id"]}_{scope}_{mode}',cmd)
                assert rc==0
            base=q/p['id']/scope/'mb'
            for mode in modes[1:]:records.append(dict(id=p['id'],scope=scope,**compare(base,q/p['id']/scope/mode,mode,p['V'],p['M'])))
        for mode in ['mb','p']:
            dst=q/p['id']/'E0'/mode
            assert launch(f'zero_E0_{p["id"]}_{mode}',[BUILD/'Round127ExportE0.exe',ROOT/p['input_path'],p['T_seconds'],0,hi,U,mode,dst])==0
            new=q/p['id']/'root'/mode
            if mode=='p':assert launch(f'zero_E1_{p["id"]}_{mode}',[BUILD/'Round127ExportE1.exe',ROOT/p['input_path'],p['T_seconds'],0,hi,U,mode,new])==0
            assert core.lp_model(dst/'original.lp')==core.lp_model(new/'original.lp')
            for name in ['native_columns.csv','native_rows.csv','native_metadata.json']:
                assert (dst/name).read_bytes()==(new/name).read_bytes()
        renamed=TEMP/p['id']/'different-name.txt';renamed.parent.mkdir(parents=True,exist_ok=True);renamed.write_bytes((ROOT/p['input_path']).read_bytes())
        dst=q/p['id']/'renamed'
        assert launch(f'zero_rename_{p["id"]}',[BUILD/'Round127ExportE1.exe',renamed,p['T_seconds'],0,hi,U,'mb',dst])==0
        assert core.lp_model(dst/'original.lp')==core.lp_model(q/p['id']/'root/mb/original.lp')
    write(OUT/'qualification/zero_optimize.json',dict(UTC=utc(),Optimize=0,comparisons=records,
        E0_E1_MB_P_full_native_columns_objective_types_bounds_and_rows_equal=True,path_rename_checks=['S12','R98-C2'],
        V50_M4_support_candidate_count=83300,budget=50000,by_vehicle_before_cap=[20825,20825,8350,0],
        core_candidates=[1120,2660,21420],no_V50_solve=True,no_four_station_generation=True))
if __name__=='__main__':exports()
