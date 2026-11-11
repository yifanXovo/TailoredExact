"""One evidence-backed uniform RN envelope revision; no controller grid."""
from round161_common import *
from round161_qualify import matrix,rows,cols
from round161_experiment import command,call
from fractions import Fraction as F

def child(cmd,folder,label):
    dest=Path(cmd[7]);mode=str(cmd[9]);terminal='outcome.json' if mode in ('LP','MIP') else 'zero_start.json' if mode=='export-zero' else 'admission.json'
    if (dest/terminal).exists():return
    result=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=meter.environment(),capture_output=True)
    folder.mkdir(parents=True,exist_ok=True);(folder/(label+'.stdout')).write_bytes(result.stdout);(folder/(label+'.stderr')).write_bytes(result.stderr)
    assert result.returncode==0,(cmd,result.stderr.decode())

def qualify():
    current=read(OUT/'candidate_manifest.json');old=read(OUT/'measured_manifest.json');root=OUT/'qualification/revision';version=PE.parent.name
    def object_hash(m,stem):return next(h for p,h in m['added_objects'].items() if Path(p).stem==stem)
    identical={s:object_hash(current,s)==object_hash(old,s) for s in ('GurobiBaseline','MipStartMapping')}
    assert all(identical.values())
    results=[];diag=read(OUT/'reports/envelope_diagnostic.json')['results']
    for role in ('R-X35-S-T2','N-B35-S'):
        checks={}
        for form in ('OLD','RN-P'):
            label=f'{role}_{form}_export_{version}';folder=OUT/'runs'/label
            child(command(role,form,'export',label,120,-1),root,label)
            if form=='OLD':
                base=OUT/'runs'/f'{role}_OLD_LP_v1'
                assert rows(folder,'actual')==rows(base,'actual') and cols(folder,'actual')==cols(base,'actual')
                assert read(folder/'start.json')==read(base/'start.json')
                assert sha(folder/'model.lp')==sha(base/'model.lp')
                checks['OLD_exact_model_Start_SHA_unchanged']=True
            else:
                b=read(folder/'block.json');expected=next(x for x in diag if x['role']==role)
                sl,su=F(expected['exact_sl']),F(expected['exact_su'])
                assert F(b['S_lower'])<=sl and abs(b['S_lower']-float(sl))<1e-11
                assert F(b['S_upper'])>=su and abs(b['S_upper']-float(su))<1e-11
                assert F(b['t_lower'])<=1/su and F(b['t_upper'])>=1/sl
                checks['RN_P']=dict(block=b,matrix=matrix(folder),Start=read(folder/'admission.json'))
        results.append(dict(role=role,checks=checks))
    tiny=[]
    for tag in ('positive','zero_union','zero_only'):
        source=OUT/'qualification/tiny'/tag;dest=root/'tiny'/tag
        child([PE,source/'instance.txt',100,2,3,.1,source/'parent.txt',dest,'RN-P','MIP',30,-1],root,'tiny_'+tag)
        value=read(dest/'outcome.json');exact=read(source/'enumeration.json')['minimum']
        assert abs(value['physical_U']-exact)<1e-7 and value['bound_available'] and abs(value['qualified_lower']-exact)<1e-7
        fresh=root/'tiny_current_exports'/tag
        child([PE,source/'instance.txt',100,2,3,.1,source/'parent.txt',fresh,'RN-P','export',30,-1],root,'tiny_current_'+tag)
        assert rows(fresh,'actual')==rows(dest,'actual') and cols(fresh,'actual')==cols(dest,'actual') and read(fresh/'start.json')==read(dest/'start.json')
        tiny.append(dict(case=tag,outcome=value,matrix=matrix(fresh),current_model_matches_paid_v5_optimum=True,
            paid_optimum_PE_SHA=read(OUT/'build_v5.json')['research_PE_SHA'],current_model_SHA=sha(fresh/'model.lp')))
    probe=root/'scaled_zero'
    if probe.exists():
        rejected=root/'scaled_zero_rejected_integer_target';assert probe.resolve().is_relative_to(OUT.resolve()) and rejected.resolve().is_relative_to(OUT.resolve())
        assert not rejected.exists();probe.rename(rejected)
        for suffix in ('stdout','stderr'):
            p=root/('scaled_RN.'+suffix)
            if p.exists():p.rename(root/('scaled_RN_rejected_integer_target.'+suffix))
    write(root/'reader_probe_correction_final.json',dict(reason='The existing Parser stores integer targets using llround; positive real targets below .5 round to zero. Both failed candidate inputs/logs remain. The earlier >1e-9 diagnosis was incorrect.',
        repair='Use an algebraic objective-block scaling unit, explicitly not a full route input. Ordinary integer-target positive/zero physical optima remain tested. No reader or numerical-tolerance change.'))
    receipt=root/'scaled_zero_kernel.json'
    result=subprocess.run([str(PE),'--qualify-zero-kernel',str(receipt)],cwd=ROOT,env=meter.environment(),capture_output=True)
    (root/'kernel.stdout').write_bytes(result.stdout);(root/'kernel.stderr').write_bytes(result.stderr)
    assert result.returncode==0,result.stderr.decode();probes=[read(receipt)];assert probes[0]['PASS'] and probes[0]['kernel_only']
    write(OUT/'qualification/revision.json',dict(PASS=True,real=results,tiny=tiny,scaled_zero=probes,
        Native_backend_and_mapper_objects_identical=identical,reused_OLD_control='R161 own paid v3 controls; not a new same-PE panel',
        major_revision=1,numerical_tolerances_unchanged=True))
    current['verified_CPP_commit']=current['source_commit'];current['performance_samples']='RN-P affected two-source LP/MIP bridge; old controls paid in core phase'
    write(OUT/'measured_manifest_RNP.json',current)
    print('PASS RN-P exact bound enclosure, unchanged OLD/model/Start/backend, tiny optima and scaled zero completion')

def panel():
    assert read(OUT/'qualification/revision.json')['PASS']
    for role in ('R-X35-S-T2','N-B35-S'):
        for mode in ('LP','MIP'):
            call(role,'RN-P',mode,f'{role}_RNP_{mode}_v2',300 if mode=='LP' else 900,-1 if mode=='LP' else 4096)

if __name__=='__main__':globals()[sys.argv[1]]()
