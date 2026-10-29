"""Compact exact-scope LP tables and final entered-run comparisons, no solver."""
from round140_common import *
import csv

ROLE_ORDER=['K-15-S','K-20-S','K-35-U','R-B35-S-T2','R-X35-S-T2',
            'R-X20-S-T1','R-B35-S-T1','R-X35-S-T1']

def table(headers,rows):
    def fmt(v):
        if v is None:return 'open'
        if isinstance(v,float):return format(v,'.10g')
        return str(v)
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),
        *['| '+' | '.join(fmt(v) for v in row)+' |' for row in rows]])+'\n\n'

def lp():
    new=[read(p) for p in sorted((OUT/'LP').glob('*/result.json'))];by={(a['role'],a['variant']):a for a in new}
    rows=[];details=[]
    for h in read(OUT/'historical_points.json')['roles']:
        role=h['role'];scope=read(OUT/'roots'/role/'scope.json');add=read(OUT/'roots'/role/'additions.json')
        old={x['variant']:x for x in h['points']}
        stock=by.get((role,'stock'),old.get('stock'));tc=by.get((role,'tc_stock'),old.get('tc_stock'))
        tc2=by[role,'tc2_stock'];n=scope['panel']['V']
        rows.append([role,stock['L'],tc['L'],tc2['L'],tc2['L']-tc['L'],h['thresholds'],h['lower_positive']])
        details.append(dict(role=role,stock=stock,tc_stock=tc,tc2_stock=tc2,validated_U=scope['validated_U'],
            inventory_B=scope['B'],inventory_Bminus=scope['Bminus'],physical_T=scope['panel']['T_seconds'],
            effective_inventory_Bplus=int(add['B']),effective_inventory_Bminus=int(add['Bminus']),
            effective_budget_source='Intersect physical [max(0,B-sumQ), B] with sums of actual supported minima/maxima; never substitute saved LP tau',
            support_construction_seconds=add['construction_seconds'],TC2_constant=add['constant'],
            TC2_negative_coefficients=add['negative_coefficients'],thresholds=h['thresholds'],
            positive_lower_counts=h['lower_positive'],interval_distribution=dict(__import__('collections').Counter(f"{r['ell']}:{r['u']}" for r in add['thresholds'])),
            lower_budget_adds_count=sum(r['lower_activations']>0 for r in add['thresholds']),
            forced_only_positive_lower=sum(r['ell']>0 and r['lower_activations']==0 for r in add['thresholds']),
            maximum_lower_budget_activations=max(r['lower_activations'] for r in add['thresholds']),
            maximum_forced_high=max(len(r['forced']) for r in add['thresholds']),
            extra_rows_over_stock=dict(TC=1,TC_TC2=2),extra_columns=0))
    write(OUT/'reports/LP.json',dict(UTC=utc(),roles=details,new_optimal_LP=len(new),failed_pre_Optimize_attempts=1,
        baseline_reuse='Four exact R138 stock/TC+stock continuous LP domains; RB35-T2 is newly optimized and never labelled old TC ineffective',
        scope='Explicit continuous LP numerical optima on identical supported domain, loaded objective, cutoff and g endpoints; not native MIP roots or complete methods',
        all_new_Seed=0,Threads=1,auxiliaries_free_except_declared_rows=True))
    text='# Round140 finite same-domain LP evidence\n\n'
    text+='Nine new continuous LPs, plus four matching R138 reference pairs. All new solves explicitly use Seed0, one thread and serial execution. The failed Path-type attempt occurred before Optimize, is preserved, and is charged. The same validated U, exact g endpoints, cutoff and source model SHA are retained within each role.\n\n'
    text+=table(['Role','STK L','STK+TC L','STK+TC+TC2 L','TC2 increment','thresholds','ell>0'],rows)
    text+='Saved-point violation, an optimized bound increment and a complete-method outcome are different claims. All five new optimized bounds rise over old TC+stock; RX20 is a small increment of about 0.0000064. The new rows add two aggregates and no columns over stock. Full-precision H_sum, G, J, tau, U, quality, row counts, construction/Optimize cost and frozen identities are in reports/LP.json and the original per-position result records.\n\n'
    text+=table(['Role','budget adds q>0','forced-only ell>0','maximum q'],[[d['role'],d['lower_budget_adds_count'],d['forced_only_positive_lower'],d['maximum_lower_budget_activations']] for d in details])
    assert all(d['maximum_forced_high']==0 for d in details if d['role'] in ['R-B35-S-T2','R-X35-S-T2'])
    text+='RB35-T2 and RX35-T2 have no forced-high stations at any threshold: the positive lower counts and resulting bound increments require the inventory lower budget. RX20 has q=0 at every threshold; its small TC2 improvement instead comes from using forced-high support information that the old zero-lower chord did not use. K20 and K35 combine both sources, without an unsupported additive allocation of their objective gains.\n\n'
    text+=table(['Role','G','H_sum','J','tau','validated U'],[[a['role'],a['G'],a['H_sum'],a['J'],a['tau'],a['validated_U']] for a in new if a['variant']=='tc2_stock'])
    text+='The K20 no-stock complement is fully matched: BASE .19514915244120534; old TC .20262525298673523; TC+TC2 '+format(by['K-20-S','tc2']['L'],'.14g')+'. Stock+TC+TC2 reaches '+format(by['K-20-S','tc2_stock']['L'],'.14g')+'. The RB35-T2 no-stock TC+TC2 auxiliary reaches '+format(by['R-B35-S-T2','tc2']['L'],'.14g')+'; it is not represented as a complete no-stock BASE/TC ablation panel.\n\n'
    text+='The related return-product alternative is screened offline only. All four old stock points admit an extension within numerical residuals. K35 old TC+stock violates one linear R_k<=Q_k upper bound before any product claim; B=326, tau=295. No third complete-method benchmark line is introduced.\n'
    (OUT/'LP_report.md').write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps(rows))

if __name__=='__main__':globals()[sys.argv[1]]()
