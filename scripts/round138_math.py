"""Exact limited replay of J2/J3 and the heterogeneous pure-product witness."""
from round138_common import *
from fractions import Fraction as F
import io, zipfile
from round133_joint_check import row_check, CARRIER_SHA, PREFIX
from round134_count_bound import old_extensions, integer_extension

def main():
    tick=time.perf_counter()
    oldpath=WORK/'worktrees/round134/results/unified_exact_round134/artifacts/math_failures_and_costs.zip'
    tiny_path=WORK/'worktrees/round132/results/unified_exact_round132/artifacts/complete_tiny_joint_study.zip'
    assert sha(oldpath)=='9ef0dfada8b3ed06f5a0c7011e0c20b439a494823186c38bfbb28946ebe2a1a4'
    assert sha(tiny_path)==CARRIER_SHA
    deps=[]
    def member(z,n):
        data=z.read(n);deps.append(dict(member=n,SHA256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
        return json.loads(data)
    cases={}
    with zipfile.ZipFile(oldpath) as oldzip, zipfile.ZipFile(tiny_path) as tinyzip:
        prior=member(oldzip,'results/unified_exact_round134/math/tiny_exact.json')
        for name in ['J2','J3']:
            original=prior['cases'][name]
            matrix=member(tinyzip,PREFIX+name+'/B_joint_exact_matrix.json')
            enumeration=member(tinyzip,PREFIX+name+'/enumeration.json')
            objective=member(tinyzip,PREFIX+name+'/original_objective_joint.json')
            lam=F(objective['objective_coefficients']['e_1']);assert lam>F(1,12)
            zero={n:F(v) for n,v in original['old_point'].items()}
            tc={n:F(v) for n,v in original['new_point'].items()}
            joint=dict(tc,G=F(1,4))
            for i in range(1,5):joint[f'state_g_{i}_0']=F(1,16)
            points={};full={}
            for label,point in [('base',zero),('stock',zero),('tc',tc),('tc_stock',joint)]:
                check=row_check(matrix,point);assert check['status']=='EXACT_FEASIBLE',check
                cdf=old_extensions(point,F(3,4))
                tau=sum(point.get(f'Y_{i}',F(0)) for i in range(1,5))
                J=sum(point.get(f'zprod_{i}',F(0)) for i in range(1,5));g=point.get('G',F(0))
                stock_slacks=[J,J-F(3,4)*tau-3*g+F(9,4),F(3,4)*tau-J,3*g-J]
                if 'stock' in label:assert min(stock_slacks)>=0
                H=sum(point.get(f'h_{i}_{j}',F(0)) for i in range(1,5) for j in range(i+1,5))
                tc_rhs=sum((1 if y==1 else 4)*point.get(f'state_{i}_{y}',F(0)) for i in range(1,5) for y in (1,2))
                if label.startswith('tc'):assert H>=tc_rhs
                P=sum(point.get(f'e_{i}',F(0)) for i in range(1,5))
                assert all(point.get(f'e_{i}',F(0))>=sum(abs(y-1)*point.get(f'state_{i}_{y}',F(0)) for y in (0,1,2)) for i in range(1,5))
                points[label]=dict(G=str(g),J=str(J),tau=str(tau),P=str(P),F=str(g+lam*P),
                    stock_slacks=list(map(str,stock_slacks)),TC_slack=str(H-tc_rhs),matrix_check=check,CDF=cdf)
                full[label]={n:str(v) for n,v in point.items()}
            assert F(points['tc']['stock_slacks'][-1])==-F(3,16)
            assert F(points['base']['F'])==F(points['stock']['F'])==lam
            assert F(points['tc']['F'])==lam+F(3,16)
            assert F(points['tc_stock']['F'])==lam+F(1,4)
            # Existing matching physical fleet, without regenerating the historical enumeration.
            index=original['balanced_joint_columns'][0]['index']
            pairs=enumeration['joint_pair_indices'];case=enumeration['case'];cars=enumeration['cars']
            integer,Y=integer_extension(case,cars,pairs[index],index)
            integer['G']=F(1,4);integer['r_max']=1;integer['r_min']=0
            for i,y in enumerate(Y,1):
                integer[f'e_{i}']=abs(y-1);integer[f'zprod_{i}']=F(y,4)
                integer[f'state_g_{i}_{y}']=F(1,4)
            for i in range(1,5):
                for j in range(i+1,5):integer[f'h_{i}_{j}']=abs(Y[i-1]-Y[j-1])
            ip_check=row_check(matrix,integer);assert ip_check['status']=='EXACT_FEASIBLE',ip_check
            cases[name]=dict(lambda_hat=str(lam),points=points,full_extensions=full,
                matching_integer_Y=Y,matching_integer_full_check=ip_check,
                matching_integer_point={n:str(v) for n,v in integer.items() if v},
                integer_objective=str(lam+F(1,4)),
                proof='TC implies H>=tau; epigraph and stock RLT imply H<=4J<=12g; P>=4-tau, 0<=tau<=3. Thus F>=min(4lambda,1/4+lambda). lambda_hat>1/12 selects the second endpoint.',
                third_cell_scope='Original lambda_hat and original reference only; inherited R134 lower proof retained',
                GS_equal_target='Valid independent McCormick with 0<=S<=3 also imposes H<=12g and closes this same tiny gap',
                convex_hull_scope='Continuous selected-resource product block only, not integer BRP or objective epigraph')
    s=[[F(3,4),F(1,4),F(0)],[F(5,8),F(0),F(3,8)]]
    q=[[F(1,4),F(0),F(0)],[F(1,16),F(0),F(3,16)]];g=F(1,4)
    assert all(sum(a)==1 and sum(b)==g and all(0<=v<=u/2 for u,v in zip(a,b)) for a,b in zip(s,q))
    Y=[sum(y*v for y,v in enumerate(a)) for a in s];Z=[sum(y*v for y,v in enumerate(a)) for a in q]
    S=Y[0]+Y[1]/2;W=Z[0]+Z[1]/2
    assert sum(Y)==1 and max(F(0),S/2+g-F(1,2))<=W<=min(S/2,g)
    assert sum(Z)-g==F(1,8)
    assert 'gurobipy' not in sys.modules
    write(OUT/'math/exact.json',dict(PASS=True,UTC=utc(),cases=cases,dependencies=deps,
        prior_carriers=dict(R132_SHA=CARRIER_SHA,R134_SHA=sha(oldpath)),
        heterogeneous_product_witness=dict(s=[[str(v) for v in a] for a in s],q=[[str(v) for v in a] for a in q],
            Y=list(map(str,Y)),Z=list(map(str,Z)),S=str(S),W=str(W),stock_violation='1/8',full_BRP_extension_claimed=False),
        Optimize=0,solver_imports=0,seconds=time.perf_counter()-tick))
    print(json.dumps({n:{k:p['F'] for k,p in c['points'].items()} for n,c in cases.items()}))

if __name__=='__main__':main()
