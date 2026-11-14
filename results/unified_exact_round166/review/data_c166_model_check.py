"""Pure strict-LP contract for C166, with duplicate-preserving row checks.

Public API:
    check_c166_model(model, panel, instance, counter=None)
    compare_common_model_rows(b_model, c166_model, panel, instance)

`model` is the already strictly parsed dictionary returned by
round108_reader.lp_model / round111_seed_audit.ArmModels.data()[1][0].
`instance` uses round107_reader.instance's b,D,c,w,xy,Q keys.  No solver,
native library, file fallback or cached legality is used by either API.
"""
from collections import Counter
from pathlib import Path
import json, re, sys, time

VERSION='round166-c166-strict-shared-state-contract-v1'

def _row(terms,sense,rhs):
    return (tuple(sorted((n,float(v)) for n,v in terms.items() if v)),sense,float(rhs))

def _encoding(name):
    return name.startswith(('state_','r166_t_','r166_q_','bit_','prod_'))

def _support(low,high,initial):
    return sorted({low,high,*[a for a in (initial-1,initial,initial+1) if low<=a<=high]})

def check_c166_model(model,panel,instance,counter=None,_return_expected=False):
    """Raise AssertionError on any representation/type/row/objective mismatch.

    All encoding rows are accounted for as a multiset, including duplicated
    standard and tightened product rows at fixed/zero interval endpoints.
    Thus merely finding one correct row cannot hide an extra state-dependent
    row, missing parallel copy or a duplicate with changed coefficients.
    """
    m=model;n=int(panel['V']);vehicles=int(panel['M']);a=instance
    rows=Counter(m['rows']) if counter is None else counter
    assert rows==Counter(m['rows']),'C166 supplied row Counter is stale'
    names=m['order'];types=m['types'];bounds=m['bounds'];name_set=set(names)
    assert len(names)==len(name_set) and name_set==set(types)==set(bounds),'C166 complete unique column identity'
    assert not any(s.startswith('state_') for s in names),'C166 must not retain one-hot/LOG selectors'
    alpha,beta=bounds['G'];assert 0<=alpha<=beta<=1,'C166 legal G interval'
    quantities=[s for s in names if s.startswith(('p_','d_'))]
    assert set(quantities)=={f'{kind}_{k}_{i}' for kind in ('p','d') for k in range(vehicles) for i in range(1,n+1)},'C166 complete quantity columns'
    assert all(types[s]=='C' for s in quantities),'C166 requires continuous frozen-B quantities'
    assert all(types[s] in ('I','B') for s in names if s.startswith(('x_','load_','Y_'))),'C166 route/load/Y integer domains'
    modes=[s for s in names if s.startswith('mode_')]
    assert set(modes)=={f'mode_{k}_{i}' for k in range(vehicles) for i in range(1,n+1)},'C166 complete direction columns'
    assert all(types[s]=='B' for s in names if s.startswith(('mode_','z_')) and not s.startswith('zprod_')),'C166 binary direction/assignment'
    expected_names=set();expected=Counter();epigraph=Counter();supports=[]
    for i in range(1,n+1):
        lo,hi=bounds[f'Y_{i}'];assert lo==int(lo) and hi==int(hi) and lo<=hi,'C166 legal storage inventory domain'
        low,high=int(lo),int(hi);initial=int(a['b'][i]);cap=int(a['c'][i])
        assert 0<=low<=high<=cap,'C166 stock domain within physical capacity'
        support=_support(low,high,initial);assert 1<=len(support)<=5
        ts={x:f'r166_t_{i}_{x}' for x in support};qs={x:f'r166_q_{i}_{x}' for x in support}
        expected_names.update(ts.values());expected_names.update(qs.values())
        for x in support:
            assert types.get(ts[x])=='C' and bounds.get(ts[x])==(0.,1.),('C166 continuous t domain',ts[x])
            assert types.get(qs[x])=='C' and bounds.get(qs[x])==(0.,beta),('C166 continuous q domain',qs[x])
            expected[_row({qs[x]:1.,ts[x]:-alpha},'>=',0.)]+=1
            expected[_row({qs[x]:1.,ts[x]:-beta},'<=',0.)]+=1
        expected[_row({t:1. for t in ts.values()},'=',1.)]+=1
        expected[_row({f'Y_{i}':1.,**{ts[x]:-float(x) for x in support}},'=',0.)]+=1
        expected[_row({**{f'p_{k}_{i}':1. for k in range(vehicles)},**{f'd_{k}_{i}':1. for k in range(vehicles)},**{ts[x]:-float(abs(initial-x)) for x in support}},'=',0.)]+=1
        expected[_row({**{f'z_{k}_{i}':1. for k in range(vehicles)},**{ts[x]:-float(x!=initial) for x in support}},'=',0.)]+=1
        expected[_row({'G':-1.,**{q:1. for q in qs.values()}},'=',0.)]+=1
        expected[_row({f'zprod_{i}':1.,**{qs[x]:-float(x) for x in support}},'=',0.)]+=1
        bits=1
        while (1<<bits)-1<cap: bits+=1
        for h in range(bits):
            bit=f'bit_{i}_{h}';prod=f'prod_{i}_{h}';expected_names.update((bit,prod))
            assert types.get(bit)=='B' and bounds.get(bit)==(0.,1.),('C166 absolute bit domain',bit)
            assert types.get(prod)=='C' and bounds.get(prod)==(0.,beta),('C166 absolute product domain',prod)
            # Original P's three inequalities plus the shared factory's four
            # legal-interval inequalities. Positivity is also a column bound.
            expected[_row({prod:1.,'G':-1.},'<=',0.)]+=1
            expected[_row({prod:1.,bit:-1.},'<=',0.)]+=1
            expected[_row({prod:1.,'G':-1.,bit:-1.},'>=',-1.)]+=1
            expected[_row({prod:1.,bit:-alpha},'>=',0.)]+=1
            expected[_row({prod:1.,bit:-beta},'<=',0.)]+=1
            expected[_row({prod:1.,'G':-1.,bit:-beta},'>=',-beta)]+=1
            expected[_row({prod:1.,'G':-1.,bit:-alpha},'<=',-alpha)]+=1
        expected[_row({f'Y_{i}':1.,**{f'bit_{i}_{h}':-float(1<<h) for h in range(bits)}},'=',0.)]+=1
        expected[_row({f'zprod_{i}':1.,**{f'prod_{i}_{h}':-float(1<<h) for h in range(bits)}},'=',0.)]+=1
        epigraph[_row({f'e_{i}':1.,f'r_{i}':-1.},'>=',-1.)]+=1
        epigraph[_row({f'e_{i}':1.,f'r_{i}':1.},'>=',1.)]+=1
        epigraph[_row({f'r_{i}':1.,f'Y_{i}':-1./a['D'][i]},'=',0.)]+=1
        supports.append(dict(station=i,lower=low,upper=high,initial=initial,support=support,bits=bits))
    actual_names={s for s in names if _encoding(s)}
    assert actual_names==expected_names,('C166 exact encoding-column set',sorted(actual_names-expected_names),sorted(expected_names-actual_names))
    # Rows with an encoding auxiliary form exactly the declared two blocks.
    # Some all-zero support rows can lose every auxiliary after coefficient
    # simplification (e.g. a singleton y=0); account for those separately.
    expected_with=Counter({r:c for r,c in expected.items() if any(_encoding(s) for s,_ in r[0])})
    actual_with=Counter(r for r in m['rows'] if any(_encoding(s) for s,_ in r[0]))
    assert actual_with==expected_with,('C166 exact encoding row multiset',list((expected_with-actual_with).items())[:3],list((actual_with-expected_with).items())[:3])
    assert not (expected-rows),('C166 missing reconstruction rows',list((expected-rows).items())[:3])
    assert not (epigraph-rows),('C166 original ratio/e epigraph absent',list((epigraph-rows).items())[:3])
    obj={n:v for n,v in m['objective'][0]}
    expected_obj={'G':1.,**{f'e_{i}':float(panel['lambda'])*a['w'][i] for i in range(1,n+1) if float(panel['lambda'])*a['w'][i]}}
    assert obj==expected_obj and m['objective'][1]==0.,'C166 original G + lambda weighted-e objective'
    report=dict(contract_version=VERSION,rows=len(m['rows']),columns=len(names),quantity_columns=len(quantities),quantity_type='C',direction_columns=len(modes),frozen_A_B_rows_checked=2*n,breakpoint_joint_rows_checked=sum(6+2*len(s['support']) for s in supports),absolute_bit_rows_checked=sum(2+7*s['bits'] for s in supports),e_epigraph_and_ratio_rows_checked=3*n,encoding_columns=len(expected_names),route_load_Y_integer=True,inventory_bit_assignment_direction_binary=True,breakpoint_weights_continuous=True,supports=supports,alpha=alpha,beta=beta,original_objective_preserved=True,all_encoding_rows_accounted=True)
    if _return_expected: report['_representation_rows']=expected
    return report

def compare_common_model_rows(b_model,c166_model,panel,instance):
    """Compare duplicate-preserving physical/valid rows and common columns.

    Subtract the complete declared representation counters on *each* side.
    This includes degenerate reconstruction rows without an auxiliary column
    (e.g. sum z=0 when the legal domain is the singleton initial state).
    Identical remaining physical rows retain their original multiplicities.
    """
    c_rep=check_c166_model(c166_model,panel,instance,_return_expected=True)['_representation_rows']
    b_rep=Counter();alpha,beta=b_model['bounds']['G'];expected_b_names=set()
    for i in range(1,int(panel['V'])+1):
        lo,hi=b_model['bounds'][f'Y_{i}'];values=range(int(lo),int(hi)+1);initial=instance['b'][i]
        ss={x:f'state_{i}_{x}' for x in values};qq={x:f'state_g_{i}_{x}' for x in values}
        expected_b_names.update(ss.values());expected_b_names.update(qq.values())
        for x in values:
            assert b_model['types'].get(ss[x])=='B' and b_model['types'].get(qq[x])=='C','B requires original VD-P columns'
            b_rep[_row({qq[x]:1.,ss[x]:-alpha},'>=',0.)]+=1
            b_rep[_row({qq[x]:1.,ss[x]:-beta},'<=',0.)]+=1
        b_rep[_row({s:1. for s in ss.values()},'=',1.)]+=1
        b_rep[_row({f'Y_{i}':1.,**{ss[x]:-float(x) for x in values}},'=',0.)]+=1
        b_rep[_row({'G':-1.,**{q:1. for q in qq.values()}},'=',0.)]+=1
        b_rep[_row({f'zprod_{i}':1.,**{qq[x]:-float(x) for x in values}},'=',0.)]+=1
        b_rep[_row({**{f'p_{k}_{i}':1. for k in range(int(panel['M']))},**{f'd_{k}_{i}':1. for k in range(int(panel['M']))},**{ss[x]:-float(abs(initial-x)) for x in values}},'=',0.)]+=1
        b_rep[_row({**{f'z_{k}_{i}':1. for k in range(int(panel['M']))},**({ss[initial]:1.} if initial in ss else {})},'=',1.)]+=1
    assert {s for s in b_model['order'] if _encoding(s)}==expected_b_names,'B comparison requires exact original VD-P representation'
    b_all=Counter(b_model['rows']);c_all=Counter(c166_model['rows'])
    assert not (b_rep-b_all),'B declared representation incomplete'
    assert not (c_rep-c_all),'C166 declared representation incomplete'
    b,c=b_all-b_rep,c_all-c_rep
    assert b==c,('B/C166 common physical/valid row multiset differs',list((b-c).items())[:3],list((c-b).items())[:3])
    bn={s for s in b_model['order'] if not _encoding(s)};cn={s for s in c166_model['order'] if not _encoding(s)}
    assert bn==cn,'B/C166 common column set differs'
    assert {s:b_model['bounds'][s] for s in bn}=={s:c166_model['bounds'][s] for s in cn},'B/C166 common bounds differ'
    assert {s:b_model['types'][s] for s in bn}=={s:c166_model['types'][s] for s in cn},'B/C166 common types differ'
    assert b_model['objective']==c166_model['objective'],'B/C166 original objective differs'
    return dict(common_rows=sum(b.values()),distinct_common_rows=len(b),common_columns=len(bn),same_duplicate_preserving_common_rows=True,same_common_domains=True,same_original_objective=True)

def audit_qualification():
    """Read-only CLI audit of already generated native qualifications."""
    root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'scripts'))
    import round108_reader as core
    q=root/'results/unified_exact_round166/qualification'
    roles=json.loads((root/'results/unified_exact_round163/input_manifest.json').read_text())['roles']
    result=[];start=time.perf_counter()
    for bd in sorted((q/'global').glob('*_B')):
        cd=bd.with_name(bd.name[:-1]+'C166');ident=bd.name.rsplit('_',2)[0]
        p=next(r for r in roles if r['id']==ident);a=core.evidence.instance(root,p)
        bm=core.lp_model(bd/'model.lp');cm=core.lp_model(cd/'model.lp')
        result.append(dict(id=bd.name[:-2],B_SHA=core.sha(bd/'model.lp'),C166_SHA=core.sha(cd/'model.lp'),C166=check_c166_model(cm,p,a),common=compare_common_model_rows(bm,cm,p,a)))
    assert len(result)==8
    target=Path(__file__).resolve().parent/'data_c166_contract_results.json'
    target.write_text(json.dumps(dict(PASS=True,reviewer='independent data_review agent',new_Optimize=0,seconds=time.perf_counter()-start,pairs=result),indent=2)+'\n')
    print('C166 exact representation and B/common-row contracts PASS:',len(result),'pairs; Optimize=0')

if __name__=='__main__':audit_qualification()
