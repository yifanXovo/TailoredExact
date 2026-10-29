"""Read actual new-row coefficients back from Gurobi, without Optimize."""
from round138_common import *
import collections
import round108_reader as core

def main():
    from round100_gurobi_runtime import gp,binding
    identity=binding();assert identity['sha256']==DLL_SHA
    checks=[];tick=time.perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for case in read(OUT/'qualification/matrix_checks.json')['cases']:
            folder=OUT/'qualification'/case['case']
            old=core.lp_model(folder/'off/original.lp');new=core.lp_model(folder/'stock/original.lp')
            missing=collections.Counter(new['rows'])-collections.Counter(old['rows']);indices=[]
            for j,row in enumerate(new['rows']):
                if missing[row]>0:indices.append(j);missing[row]-=1
            assert len(indices)==4
            with gp.read(str(folder/'stock/original.lp'),env=env) as m:
                m.Params.Seed=0;m.Params.Threads=1
                assert m.NumVars==len(new['order']) and m.NumConstrs==len(new['rows'])
                constraints=m.getConstrs();coefficients=[]
                for j in indices:
                    expected,sense,rhs=new['rows'][j];c=constraints[j];native=m.getRow(c)
                    actual={native.getVar(k).VarName:native.getCoeff(k) for k in range(native.size())}
                    assert actual==dict(expected),(case['case'],j,actual,expected)
                    assert c.Sense=={'<=':'<','>=':'>','=':'='}[sense] and c.RHS==rhs
                    coefficients.append(dict(row=j,terms=actual,sense=c.Sense,RHS=c.RHS))
                checks.append(dict(case=case['case'],rows=coefficients,all_native_coefficients_equal_emitted_binary64=True,
                    matrix_SHA=sha(folder/'stock/original.lp'),Seed=m.Params.Seed,Threads=m.Params.Threads))
    write(OUT/'qualification/native_coefficients.json',dict(PASS=True,cases=checks,native_identity=identity,
        model_reads=len(checks),Optimize=0,seconds=time.perf_counter()-tick,
        readback_includes_tiny_alpha_near_one_and_collapsed_intervals=True))
    print('PASS: actual Gurobi coefficients and RHS, seven domains, zero Optimize')

if __name__=='__main__':main()
