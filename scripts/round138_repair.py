"""Bounded new-row transport repair after actual native coefficient readback."""
from round138_common import *
from round138_setup import stock_rows
from round138_delivery import make_zip
import collections,shutil,zipfile
import round108_reader as core

FIX_BUILD=WORK/'build-cache/round138-coefficient-fix'

def scaled_rows(n,alpha,beta,Bminus,B):
    out=[]
    for row in stock_rows(n,alpha,beta,Bminus,B):
        terms,sense,rhs=row;slope=abs(dict(terms).get('Y_1',0.));exponent=0
        if 0<slope<=1e-13:
            while math.ldexp(slope,exponent)<1e-12:
                assert exponent<1023;exponent+=1
        out.append((tuple((name,math.ldexp(value,exponent)) for name,value in terms),sense,math.ldexp(rhs,exponent)))
    return out

def preserve():
    assert not budget()['unclosed']
    old=read(OUT/'candidate_manifest.json');matrix=read(OUT/'matrix_frozen.json')
    helpers=dict(matrix['helpers'])
    for name,r in read(OUT/'review/reader_amendment.json')['helper_replacements'].items():helpers[name]=r['new_SHA']
    sources=dict(old['source_hashes']);sources.update(helpers)
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    carrier=make_zip('source_v1_and_frozen_helpers',[ROOT/name for name in sources])
    write(OUT/'repair/source_v1_archive.json',dict(UTC=utc(),carrier=carrier,source_commit=old['source_commit'],
        files=sources,manifest_SHA=sha(OUT/'candidate_manifest.json'),primary_science_unchanged=True,Optimize=0))
    target=(OUT/'repair/seed1_pre_coefficient_fix').resolve();target.mkdir(parents=True,exist_ok=False)
    names=['seed1_matrix_frozen.json','review/seed1_admission.json','review/seed1_admission.md']
    records={}
    for name in names:
        source=OUT/name;dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,dest);records[name]=sha(source)
    shutil.copyfile(ROOT/'scripts/round138_seed1.py',target/'round138_seed1.py')
    origin=(OUT/'campaign_seed1').resolve();dest=(target/'campaign_seed1').resolve()
    assert origin.is_relative_to(OUT.resolve()) and dest.is_relative_to(OUT.resolve()) and OUT.resolve().is_relative_to(WORK.resolve())
    assert all(p.name=='identity.json' for p in origin.rglob('*') if p.is_file()),'No Seed1 native work may exist'
    shutil.move(str(origin),str(dest))
    for name in names:(OUT/name).unlink()
    write(OUT/'repair/seed1_supersession.json',dict(UTC=utc(),preserved_metadata=records,Seed1_Optimize=0,
        reason='Actual Gurobi LP reader drops 1e-13 new-row coefficients; repair only their exact power-of-two transport before starting Seed1',
        original_Seed0_not_replaced=True,old_matrix_location=target.relative_to(ROOT).as_posix()))
    print('V1 source/helpers and unused pre-repair Seed1 identities preserved; no solving repeated')

def build():
    assert not budget()['unclosed']
    old=read(OUT/'candidate_build.json');FIX_BUILD.mkdir(parents=True,exist_ok=False)
    assert sha(COMPILER)==old['compiler_SHA'] and sha(DLL)==DLL_SHA
    assert sha(old['archive']['path'])==old['archive']['SHA256']
    for path,digest in old['linked_objects'].items():assert sha(path)==digest,path
    flags=old['flags'];obj=FIX_BUILD/'CplexBaseline.o'
    assert metered('repair_compile_CplexBaseline','build',[COMPILER,*flags,'-c',ROOT/'src/CplexBaseline.cpp','-o',obj],timeout=600)==0
    objects=[obj if Path(path).stem=='CplexBaseline' else Path(path) for path in old['linked_objects']]
    system=['-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']
    pe=FIX_BUILD/'ExactEBRP.exe';exporter=FIX_BUILD/'Round138Export.exe'
    assert metered('repair_link_production','build',[COMPILER,BUILD/'main.o',*objects,old['archive']['path'],*system,'-o',pe],timeout=120)==0
    assert metered('repair_compile_exporter','build',[COMPILER,*flags,ROOT/'scripts/round138_export.cpp',*objects,old['archive']['path'],*system,'-o',exporter],timeout=180)==0
    sources={p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','include'] for p in (ROOT/folder).rglob('*') if p.suffix in ('.cpp','.hpp','.h','.inc')}
    prior=read(OUT/'candidate_manifest.json');changed=[name for name,digest in sources.items() if prior['source_hashes'][name]!=digest]
    assert changed==['src/CplexBaseline.cpp'],changed
    manifest=dict(prior,source_commit=git('rev-parse','HEAD').decode().strip(),source_hashes=sources,
        production_PE=str(pe),production_PE_SHA=sha(pe),research_PE=str(pe),research_PE_SHA=sha(pe),
        version='v2-exact-power-of-two-new-row-transport',primary_v1_manifest_SHA=sha(OUT/'candidate_manifest.json'),
        repair='Only new stock rows with nonzero slope <=1e-13 are scaled by an exact positive power of two until slope >=1e-12; all other canonical bytes remain unchanged')
    write(OUT/'candidate_repair_manifest.json',manifest)
    write(OUT/'candidate_repair_build.json',dict(UTC=utc(),manifest_SHA=sha(OUT/'candidate_repair_manifest.json'),
        compiled_units=['CplexBaseline'],unchanged_main_object=dict(path=str(BUILD/'main.o'),SHA256=sha(BUILD/'main.o')),
        linked_objects={str(p):sha(p) for p in objects},archive=old['archive'],compiler_SHA=old['compiler_SHA'],flags=flags,
        exporter_PE=str(exporter),exporter_SHA=sha(exporter),old_production_PE_untouched=True,source_ABI_unchanged=True))
    print('Separately named V2 production/export PE built; V1 PE and manifest retained')

def qualify():
    assert not budget()['unclosed']
    build=read(OUT/'candidate_repair_build.json');root=read(OUT/'roots/K-35-U/scope.json');p=root['panel'];reports=[]
    for case in read(OUT/'qualification/matrix_checks.json')['cases']:
        name=case['case'];alpha,beta,cutoff=case['alpha'],case['beta'],case['cutoff'];folder=OUT/'qualification/repair'/name;models={}
        for variant in ['off','stock']:
            d=folder/variant;args=[build['exporter_PE'],ROOT/p['input_path'],p['T_seconds'],alpha,beta,cutoff,'ms2',d,p['lambda'],variant]
            assert metered('repair_export_'+name+'_'+variant,'diagnostic',args,timeout=60)==0
            models[variant]=core.lp_model(d/'original.lp')
        base=models['off'];old=core.lp_model(OUT/'qualification'/name/'off/original.lp');assert base==old,name
        new=models['stock']
        for key in ['order','bounds','types','objective']:assert new[key]==base[key],(name,key)
        delta=collections.Counter(new['rows'])-collections.Counter(base['rows']);assert not collections.Counter(base['rows'])-collections.Counter(new['rows'])
        a,b=base['bounds']['G'];expected=scaled_rows(p['V'],a,b,root['Bminus'],root['B'])
        assert delta==collections.Counter(expected) and sum(delta.values())==4
        # Scaling is exact in binary64, including the already outward RHS.
        from fractions import Fraction as F
        for before,after in zip(stock_rows(p['V'],a,b,root['Bminus'],root['B']),expected):
            scale=dict(after[0])['zprod_1'];assert scale>=1 and F(scale).denominator==1
            assert {n:F(c)*F(scale) for n,c in before[0]}=={n:F(c) for n,c in after[0]}
            assert F(before[2])*F(scale)==F(after[2]) and before[1]==after[1]
        reports.append(dict(case=name,alpha=a,beta=b,cutoff=cutoff,new_rows=4,new_columns=0,
            historical_and_v1_and_v2_off_equal=True,exact_positive_row_scaling=True,
            row_scales=[dict(r[0])['zprod_1'] for r in expected],
            stock_model=(folder/'stock/original.lp').relative_to(ROOT).as_posix(),stock_SHA=sha(folder/'stock/original.lp')))
    write(OUT/'qualification/repair_matrix_checks.json',dict(PASS=True,cases=reports,Optimize=0,
        repaired_manifest_SHA=sha(OUT/'candidate_repair_manifest.json'),no_tolerance_or_proof_policy_change=True))
    print('V2 seven-domain matrix qualification passes; off unchanged and only four exactly scaled rows')

def native():
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA
    reports=[];used=[];seen=set()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        def inspect(path,expected):
            model=core.lp_model(path);counts=collections.Counter(expected);indices=[]
            for j,row in enumerate(model['rows']):
                if counts[row]>0:indices.append(j);counts[row]-=1
            assert not +counts and len(indices)==4
            with gp.read(str(path),env=env) as m:
                m.Params.Seed=0;m.Params.Threads=1;constraints=m.getConstrs()
                for j in indices:
                    terms,sense,rhs=model['rows'][j];c=constraints[j];r=m.getRow(c)
                    actual={r.getVar(k).VarName:r.getCoeff(k) for k in range(r.size())}
                    assert actual==dict(terms) and c.RHS==rhs and c.Sense=={'<=':'<','>=':'>','=':'='}[sense],(path,j)
            return dict(model=Path(path).relative_to(ROOT).as_posix(),SHA256=sha(path),rows=4,all_native_coefficients_and_RHS_exact=True)
        p=read(OUT/'roots/K-35-U/scope.json')['panel'];scope=read(OUT/'roots/K-35-U/scope.json')
        for c in read(OUT/'qualification/repair_matrix_checks.json')['cases']:
            fact=inspect(ROOT/c['stock_model'],scaled_rows(p['V'],c['alpha'],c['beta'],scope['Bminus'],scope['B']))
            reports.append(dict(case=c['case'],Seed=0,Threads=1,**fact))
        for group in read(OUT/'matrix_frozen.json')['groups']:
            l=group['launch'];p=l['panel']
            if l['method']!='STOCK':continue
            observations=read(Path(l['destination'])/'observations.json')
            data=core.evidence.instance(ROOT,p);B=sum(data['b'][1:]);Bm=max(0,B-sum(p['Q_vector']))
            for row in observations:
                call=row['payload']
                if call['kind']!='call':continue
                path=core.portable(ROOT,call['model_path']);digest=sha(path);assert digest==call['model_sha256']
                if digest in seen:continue
                seen.add(digest);model=core.lp_model(path);alpha,beta=model['bounds']['G']
                assert all(v==0 or abs(v)>1e-13 for v in (alpha,beta)),('A used V1 model entered the repaired branch',path,alpha,beta)
                expected=stock_rows(p['V'],alpha,beta,Bm,B);assert expected==scaled_rows(p['V'],alpha,beta,Bm,B)
                fact=inspect(path,expected);used.append(dict(arm_id=l['arm_id'],alpha=alpha,beta=beta,
                    v2_scaling_branch_not_entered=True,canonical_new_rows_unchanged_by_v2=True,**fact))
    write(OUT/'qualification/native_coefficients.json',dict(PASS=True,cases=reports,Optimize=0,model_reads=len(reports)+len(used),
        Seed=0,Threads=1,native_identity=binding(),repaired_manifest_SHA=sha(OUT/'candidate_repair_manifest.json'),
        prior_failure_preserved='fees/native_coeff_readback',no_tolerance_change=True))
    write(OUT/'repair/primary_native_bridge.json',dict(PASS=True,UTC=utc(),models=used,Optimize=0,
        primary_v1_manifest_SHA=sha(OUT/'candidate_manifest.json'),v2_manifest_SHA=sha(OUT/'candidate_repair_manifest.json'),
        conclusion='Every actually used primary STOCK model preserves all four intended native coefficient maps/RHS. None enters the changed scale branch; V2 emits identical four rows on these scopes and all other source/rows are unchanged. The primary runs remain measured V1 evidence, not retagged V2 repeats.',
        no_primary_native_rerun=True,no_solution_bound_or_certificate_backfill=True))
    print(f'PASS actual native rows: 7 repaired domains and {len(used)} unique used V1 models; zero Optimize')

if __name__=='__main__':globals()[sys.argv[1]]()
