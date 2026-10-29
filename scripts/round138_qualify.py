"""Default-off bridge and actual four-row deltas, with zero Optimize calls."""
from round138_common import *
from round138_setup import stock_rows
from fractions import Fraction as F
import collections
import round108_reader as core

def main():
    root=read(OUT/'roots/K-35-U/scope.json');p=root['panel'];U=root['validated_U']
    cases=[('root',0.,U,U),('child_low',0.,U/2,U),('child_high',U/2,U,U),
           ('cutoff_refresh',0.,U,U*.9),('degenerate',.2,.2,2.),
           ('tiny_alpha',1e-13,.2,2.),('near_one',1.-5e-13,1.,2.)]
    reports=[]
    for name,alpha,beta,cutoff in cases:
        folder=OUT/'qualification'/name;models={}
        for variant,exe in [('historical',WORK/'build-cache/round137/Round137Export.exe'),
                            ('off',BUILD/'Round138Export.exe'),('stock',BUILD/'Round138Export.exe')]:
            d=folder/variant
            label='export_'+name+'_'+variant
            args=[exe,ROOT/p['input_path'],p['T_seconds'],alpha,beta,cutoff,'ms2',d,p['lambda'],
                  'stock' if variant=='stock' else 'off']
            if (OUT/'fees'/label/'receipt.json').exists():
                assert read(OUT/'fees'/label/'receipt.json')['exit_code']==0
                assert read(OUT/'fees'/label/'launch.json')['command']==list(map(str,args))
            else: assert metered(label,'engineering',args,timeout=60)==0
            models[variant]=core.lp_model(d/'original.lp')
        base=models['off'];assert base==models['historical'],name
        if name=='root': assert base==core.lp_model(OUT/'roots/K-35-U/inherited/original.lp')
        new=models['stock']
        for key in ['order','bounds','types','objective']:assert new[key]==base[key],(name,key)
        oldrows=collections.Counter(base['rows']);newrows=collections.Counter(new['rows'])
        removed=oldrows-newrows;delta=newrows-oldrows;assert not removed and sum(delta.values())==4
        actual_alpha,actual_beta=base['bounds']['G']
        expected=stock_rows(p['V'],actual_alpha,actual_beta,root['Bminus'],root['B'])
        assert collections.Counter(expected)==delta,(name,delta,expected)
        rounding=[]
        for terms,sense,rhs in expected:
            t=dict(terms);slope=-t.get('Y_1',0.);budget=-t.get('G',0.)
            exact=-F(slope)*F(budget)
            assert (F(rhs)>=exact if sense=='<=' else F(rhs)<=exact)
            assert all(t.get(f'Y_{i}',0.)==-slope for i in range(1,p['V']+1))
            rounding.append(dict(sense=sense,exact_rhs=str(exact),loaded_rhs=rhs,
                                 outward_error=str(abs(F(rhs)-exact))))
        physical=[]
        for g in [actual_alpha,actual_beta]:
            Y=root['physical_initial']['Y'];valid=True
            for terms,sense,rhs in expected:
                vector={'G':F(g)}
                for i in range(1,p['V']+1):vector[f'Y_{i}']=F(Y[i]);vector[f'zprod_{i}']=F(g)*Y[i]
                lhs=sum(F(c)*vector[n] for n,c in terms)
                assert (lhs<=F(rhs) if sense=='<=' else lhs>=F(rhs))
            physical.append(dict(g=g,exact_product_rows_feasible=True,
                physical_evidence=root['physical_initial'],physical_Y=Y))
        reports.append(dict(case=name,alpha=actual_alpha,beta=actual_beta,cutoff=cutoff,
            old_PE_and_new_off_canonical_equal=True,new_columns=0,new_rows=4,removed_rows=0,
            full_precision_coefficients=True,RHS_rounding=rounding,physical_product_checks=physical,
            off_SHA=sha(folder/'off/original.lp'),stock_SHA=sha(folder/'stock/original.lp')))
    write(OUT/'qualification/matrix_checks.json',dict(PASS=True,cases=reports,Optimize=0,
        unchanged_default_config_SHA=sha(ROOT/'config/gi_tbc_round137.json'),
        compatibility_config_SHA=sha(ROOT/'config/paper_s2.json'),
        heterogeneous_Q=p['Q_vector'],heterogeneous_D=True,depot_stock_excluded=True,
        zero_G_and_collapsed_intervals_covered=True,loaded_return_covered=True))
    print('PASS: 7 actual domains; historical=off; exactly four full-precision rows; zero Optimize')

if __name__=='__main__':main()
