"""Count-disjunction diagnostics. Exact dyadic membership; no solver import."""
from round141_common import *
from fractions import Fraction as F
from round134_count_bound import downward
from round140_math import model_counts, serializable
import collections, gzip, itertools, re, zipfile
import round108_reader as core

ROLES = ['K-35-U', 'R-B35-S-T2', 'K-20-S']
PARENT_POS = {'K-35-U':8, 'R-B35-S-T2':5, 'K-20-S':1,
              'R-X35-S-T2':7, 'R-X20-S-T1':9}

def membership(add, threshold):
    t = F(threshold)
    return [f'state_{i}_{y}' for i, ys in add['supports'].items()
            for y in ys if F(add['ratios'][str(i)])*y >= t]

def child_rows(add, threshold, pivot, side):
    """Propagate by physical threshold, so a frozen threshold need not be a grid member."""
    assert side in ('low', 'high')
    t = F(threshold); n = len(add['supports'])
    coef = collections.defaultdict(F); constant = F(0); ranges = []
    for row in add['thresholds']:
        h = F(row['t']); ell, upper = row['ell'], row['u']
        if side == 'low' and h >= t: upper = min(upper, pivot)
        if side == 'high' and h <= t: ell = max(ell, pivot+1)
        if ell > upper:
            return dict(incompatible=True, threshold=str(h), ell=ell, u=upper)
        delta = F(row['delta'])
        for key in membership(add, h): coef[key] += delta*(n-ell-upper)
        constant += delta*ell*upper
        ranges.append(dict(t=str(h), ell=ell, u=upper))
    return dict(incompatible=False, coefficients={k:downward(v) for k,v in coef.items() if v},
                exact={k:str(v) for k,v in coef.items() if v},
                constant=downward(constant), constant_exact=str(constant), ranges=ranges)

def score(add, point):
    rows = []
    for index, row in enumerate(add['thresholds']):
        lo, hi = row['ell'], row['u']
        if lo == hi: continue
        K = sum((F(point[k]) for k in membership(add, row['t'])), F(0))
        violation = max(F(lo)-K, K-F(hi), F(0))
        item = dict(index=index, threshold=row['t'], ell=lo, u=hi,
                    K_star=float(K), K_star_exact=str(K),
                    count_range_violation=float(violation))
        if violation > F(1e-7):
            # Never score a clipped K or a negative chord remainder.
            item.update(score=None, score_exact=None)
        else:
            value = F(row['delta'])*(K-lo)*(hi-K)
            item.update(score=float(value), score_exact=str(value))
        rows.append(item)
    violations = [r for r in rows if r['count_range_violation'] > 1e-7]
    if violations:
        chosen = max(violations, key=lambda r:(r['count_range_violation'], -r['index']))
        rule = 'largest explicit count-range violation; lower physical threshold breaks ties'
    else:
        chosen = max(rows, key=lambda r:(F(r['score_exact']), -r['index'])) if rows else None
        rule = 'largest exact Delta*(K-ell)*(u-K); lower physical threshold breaks exact ties'
    return chosen, rows, rule

def prepare():
    tick = time.perf_counter(); old = ROOT/'results/unified_exact_round140'
    archive = old/'artifacts/diagnostics_and_failures.zip'
    assert sha(archive) == '2cb1ab936753ce9ac26ae1f970b070b2751190af79f6a80a8b0f5d254902bf5f'
    source_manifest = read(old/'carrier_manifest.json')
    assert next(r for r in source_manifest['carriers'] if r['path'].endswith('/diagnostics_and_failures.zip'))['SHA256'] == sha(archive)
    records = []; positions = []; dependencies = []
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        def verify_member(path):
            rel = path.relative_to(ROOT).as_posix()
            assert rel in names, rel
            data = z.read(rel); assert path.read_bytes() == data, rel
            dependencies.append(dict(member=rel, SHA256=sha(path), bytes=len(data)))
        for role, position in PARENT_POS.items():
            folder = old/'roots'/role
            parent = old/'LP'/f'{position:02}_{role}_tc2_stock'
            scope = read(folder/'scope.json'); add = read(folder/'additions.json')
            record = read(parent/'result.json')
            for p in [folder/'scope.json', folder/'additions.json', parent/'result.json', parent/'solution.json.gz']:
                verify_member(p)
            stock = Path(scope['stock_model']); verify_member(stock)
            assert sha(stock) == scope['stock_SHA'] == record['source_SHA']
            assert sha(parent/'solution.json.gz') == record['solution_SHA']
            assert sha(ROOT/scope['panel']['input_path']) == scope['panel']['input_sha256']
            parsed = core.lp_model(stock)
            fresh = serializable(model_counts(parsed,scope['Bminus'],scope['B']))
            for key in ['supports','ratios','TC','TC2','constant','thresholds']:
                # JSON station keys have become strings in the saved file.
                assert json.loads(json.dumps(fresh[key])) == add[key], (role,key)
            with gzip.open(parent/'solution.json.gz','rt') as stream: point = json.load(stream)
            assert set(point) == set(parsed['order'])
            chosen, ranking, rule = score(add, point)
            assert chosen is not None
            lo, hi = chosen['ell'], chosen['u']
            pivots = [('balanced',lo+(hi-lo)//2),
                      ('lp_floor',max(lo,min(hi-1,math.floor(chosen['K_star']))))]
            seen = set(); cases = []
            for kind, pivot in pivots:
                if pivot in seen: continue
                seen.add(pivot)
                sides = {}
                for side in ['low','high']:
                    child = child_rows(add,chosen['threshold'],pivot,side)
                    rhs = child['constant']+math.fsum(v*point[k] for k,v in child['coefficients'].items())
                    H = math.fsum(v for k,v in point.items() if re.fullmatch(r'h_\d+_\d+',k))
                    sides[side] = dict(conditional_violation_at_saved_point=rhs-H,
                        saved_K_satisfies=(chosen['K_star']<=pivot if side=='low' else chosen['K_star']>=pivot+1))
                    if role in ROLES:
                        for variant in ['plain','conditional']:
                            positions.append(dict(position=len(positions)+1,role=role,pivot=pivot,
                                pivot_kind=kind,side=side,variant=variant,threshold=chosen['threshold'],
                                ell=lo,u=hi,Seed=0,Threads=1,cap_seconds=90))
                cases.append(dict(kind=kind,m=pivot,sides=sides))
            records.append(dict(role=role,scope=scope,parent=record,chosen=chosen,ranking=ranking,
                                selection_rule=rule,pivots=cases))
            write(OUT/'domains'/role/'scope.json',scope)
            write(OUT/'domains'/role/'additions.json',add)
    write(OUT/'inherited_dependencies.json',dict(commit=SCIENCE140,carrier=str(archive.relative_to(ROOT)),
        carrier_SHA=sha(archive),members=dependencies,new_Optimize=0))
    write(OUT/'LP_plan.json',dict(UTC=utc(),roles=ROLES,positions=positions,Seed=0,Threads=1,
        affinity_mask=4,serial=True,parent_TC_and_TC2_retained=True,cap_seconds=90,
        same_domain_except_declared_count_rows=True,source='frozen R140 continuous domains',
        separate_Gini_controls='rebuilt canonical child stock+TC+TC2 at the identical U/cutoff and g midpoint'))
    write(OUT/'offline_screen.json',dict(UTC=utc(),roles=records,new_Optimize=0,
        prepare_seconds=time.perf_counter()-tick))
    write(OUT/'start_receipt.json',dict(UTC=utc(),base=BASE,science140=SCIENCE140,
        branch=git('branch','--show-current').decode().strip(),
        actual_main=git('rev-parse','origin/main').decode().strip(),R140_in_main=False,
        PR_base='codex/round140-two-sided-threshold-count',goal_SHA=sha(OUT/'goal.md'),
        compute_cap_seconds=36000,diagnostic_planned_cap_seconds=3600,
        protected_original='E:/codes/ExactEBRP',no_active_solver_at_start=True,
        stable_entry='scripts/paper_s2.py -> config/gi_tbc_round137.json',
        Gurobi_Seed=0,H_seed=20260626,old_raw_not_deleted=True))
    print(json.dumps([dict(role=r['role'],chosen=r['chosen'],pivots=r['pivots']) for r in records],indent=2))

def tiny():
    tick=time.perf_counter();checked=0
    from round140_math import count_rows
    cases=[({i:[0,1,2] for i in range(1,5)},{i:F(1) for i in range(1,5)},3,5),
           ({1:[0,2],2:[1,3],3:[0,1,4]},{1:F(.1),2:F(.2),3:F(.3)},4,6)]
    for supports,ratios,bm,b in cases:
        raw=count_rows(supports,ratios,bm,b);raw.update(supports=supports,ratios=ratios)
        add=json.loads(json.dumps(serializable(raw)))
        for row in add['thresholds']:
            for pivot in range(row['ell'],row['u']):
                for side in ['low','high']:
                    child=child_rows(add,row['t'],pivot,side)
                    for ys in itertools.product(*supports.values()):
                        if not bm<=sum(ys)<=b:continue
                        ratios_y=[ratios[i]*y for i,y in zip(supports,ys)]
                        K=sum(r>=F(row['t']) for r in ratios_y)
                        inside=K<=pivot if side=='low' else K>=pivot+1
                        if not inside:continue
                        assert not child['incompatible']
                        A=sum(abs(x-y) for i,x in enumerate(ratios_y) for y in ratios_y[i+1:])
                        rhs=F(child['constant_exact'])+sum(F(child['exact'].get(f'state_{i}_{y}',0)) for i,y in zip(supports,ys))
                        assert rhs<=A
                        for interval in child['ranges']:
                            Kh=sum(r>=F(interval['t']) for r in ratios_y)
                            assert interval['ell']<=Kh<=interval['u']
                        checked+=1
    # Exact scalar witnesses; these are not complete BRP points.
    ell,u,m,b0,b1=map(F,[0,4,1,0,2])
    def links(K,b): return K<=m+(u-m)*b and K>=ell+(m+1-ell)*b
    assert links(F(2),F(1,3)) and F(0)>=min(b0,b1) and F(0)<b0+(b1-b0)*F(1,3)
    assert links(F(2),F(1,2)) and F(1)==b0+(b1-b0)*F(1,2)
    assert not any(links(F(2),b) and F(1)>=b0+(b1-b0)*b for b in [F(0),F(1)])
    write(OUT/'math/tiny.json',dict(PASS=True,integer_side_extensions_checked=checked,
        scalar_witnesses_exact=True,scope='count/TC2 algebra and scalar epigraph only',
        seconds=time.perf_counter()-tick,Optimize=0))

if __name__=='__main__': globals()[sys.argv[1]]()
