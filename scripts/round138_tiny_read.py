"""Selected historical members and pure exact replay, including an empty public root."""
from round138_common import *
from fractions import Fraction as F
import zipfile,argparse
from round133_joint_check import row_check
from round134_count_bound import old_extensions,integer_extension

def prepare():
    assert not budget()['unclosed']
    exact=read(OUT/'math/exact.json')
    paths=[WORK/'worktrees/round132/results/unified_exact_round132/artifacts/complete_tiny_joint_study.zip',
           WORK/'worktrees/round134/results/unified_exact_round134/artifacts/math_failures_and_costs.zip']
    target=OUT/'math/dependencies.zip';assert not target.exists()
    members=[]
    with zipfile.ZipFile(paths[0]) as a,zipfile.ZipFile(paths[1]) as b,zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        for record in exact['dependencies']:
            name=record['member'];source=b if '/unified_exact_round134/' in name else a
            raw=source.read(name);assert hashlib.sha256(raw).hexdigest()==record['SHA256'] and len(raw)==record['bytes']
            out.writestr(name,raw);members.append(record)
    write(OUT/'math/dependencies_manifest.json',dict(zip_SHA=sha(target),members=members,
        R132_pin='52b02252ba47e8228b73e071d6ed692385a4f816',
        R134_pin='d3353749e6933e6685c7f0d92d153d0641816bcb',
        complete_old_archives_not_copied=True,Optimize=0))
    print(f'{len(members)} necessary historical members preserved, no full archive recovery')

def check(root=ROOT):
    root=Path(root);out=root/'results/unified_exact_round138';tick=time.perf_counter()
    exact=read(out/'math/exact.json');manifest=read(out/'math/dependencies_manifest.json')
    carrier=out/'math/dependencies.zip';assert sha(carrier)==manifest['zip_SHA']
    result={}
    with zipfile.ZipFile(carrier) as z:
        assert set(z.namelist())=={r['member'] for r in manifest['members']}
        for r in manifest['members']:
            raw=z.read(r['member']);assert hashlib.sha256(raw).hexdigest()==r['SHA256'] and len(raw)==r['bytes']
        for name,c in exact['cases'].items():
            prefix=f'results/unified_exact_round132/joint/{name}/'
            matrix=json.loads(z.read(prefix+'B_joint_exact_matrix.json'));checks={}
            objective=json.loads(z.read(prefix+'original_objective_joint.json'))['objective_coefficients']
            coefficients={n:F(v) for n,v in objective.items()};lam=coefficients['e_1']
            assert lam==F(c['lambda_hat']) and lam>F(1,12)
            targets={'base':lam,'stock':lam,'tc':lam+F(3,16),'tc_stock':lam+F(1,4)}
            for label,values in c['full_extensions'].items():
                point={n:F(v) for n,v in values.items()};fact=row_check(matrix,point)
                assert fact['status']=='EXACT_FEASIBLE';cdf=old_extensions(point,F(3,4))
                assert all(point.get(f'e_{i}',F(0))>=sum(abs(y-1)*point.get(f'state_{i}_{y}',F(0)) for y in (0,1,2)) for i in range(1,5))
                tau=sum(point.get(f'Y_{i}',F(0)) for i in range(1,5));J=sum(point.get(f'zprod_{i}',F(0)) for i in range(1,5));g=point.get('G',F(0))
                slacks=[J,J-F(3,4)*tau-3*g+F(9,4),F(3,4)*tau-J,3*g-J]
                if 'stock' in label:assert min(slacks)>=0
                H=sum(point.get(f'h_{i}_{j}',F(0)) for i in range(1,5) for j in range(i+1,5))
                TC=sum((1 if y==1 else 4)*point.get(f'state_{i}_{y}',F(0)) for i in range(1,5) for y in (1,2))
                if label.startswith('tc'):assert H>=TC
                value=sum(coef*point.get(n,F(0)) for n,coef in coefficients.items())
                assert value==targets[label]==F(c['points'][label]['F'])
                checks[label]=dict(full_matrix=fact,CDF=cdf,stock_slacks=list(map(str,slacks)),original_objective=str(value))
            ip={n:F(v) for n,v in c['matching_integer_point'].items()}
            assert row_check(matrix,ip)['status']=='EXACT_FEASIBLE'
            assert sum(coef*ip.get(n,F(0)) for n,coef in coefficients.items())==lam+F(1,4)==F(c['integer_objective'])
            enumeration=json.loads(z.read(prefix+'enumeration.json'));index={'J2':27,'J3':34}[name]
            zero,Y=integer_extension(enumeration['case'],enumeration['cars'],enumeration['joint_pair_indices'][index],index)
            assert Y==[0,0,0,0];zero['G']=zero['r_min']=zero['r_max']=F(0)
            for i in range(1,5):zero[f'e_{i}']=F(1)
            zero_check=row_check(matrix,zero);assert zero_check['status']=='EXACT_FEASIBLE'
            assert sum(coef*zero.get(n,F(0)) for n,coef in coefficients.items())==4*lam
            old_extensions(zero,F(3,4))
            result[name]=dict(cells=checks,matching_IP=True,zero_inventory_loaded_return_full_matrix=zero_check,
                zero_stock_slacks=['0','9/4','0','0'],lambda_hat=c['lambda_hat'])
    assert 'gurobipy' not in sys.modules
    receipt=dict(PASS=True,cases=result,Optimize=0,vendor_DLL_loads=0,seconds=time.perf_counter()-tick)
    print(json.dumps(dict(PASS=True,cases=list(result),Optimize=0,vendor_DLL_loads=0,seconds=receipt['seconds'])))
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','check']);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--receipt',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare()
    else:
        result=check(a.root)
        if a.receipt:write(a.receipt,result)
