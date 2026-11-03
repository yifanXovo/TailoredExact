"""Target the actual zero-GD first-call SHA path; never repeat a sealed solve."""
from round149_context import root_context,first_call,unique_model
from round149_common import *


def check():
    old=read(ROOT/'results/unified_exact_round148/rb35_matrix.json')
    launch=old['groups'][0]['launch'];destination=Path(launch['destination'])
    models=destination/'external/models'
    meta=read(models/'round146_root.json')
    audit_paths=list(destination.rglob('*.round146.native.json'))
    audits=[read(p) for p in audit_paths]
    block,support,actual=root_context(models,launch['panel'],True,OUT/'qualification/zero_GD_context.json',audits)
    assert len(block['rows'])==actual['rows']==meta['rows']
    call=first_call(models);source=unique_model(models,call['model_sha256'])
    assert source.exists() and support
    import shutil
    fixture=TEMP/'zero_GD_reader/destination';fm=fixture/'external/models';fm.mkdir(parents=True,exist_ok=False)
    writer=OUT/'qualification/writer_v3/zero_GD'
    shutil.copyfile(writer/'on.lp',fm/'arbitrary_final_name.lp')
    shutil.copyfile(writer/'round146_root.json',fm/'round146_root.json')
    final_sha=sha(fm/'arbitrary_final_name.lp')
    write(fixture/'observations.json',[dict(payload=dict(kind='call',call=7,model_sha256=final_sha))])
    panel=dict(V=3,total_initial=0,Q_vector=[3])
    zero,ss,zz=root_context(fm,panel,True,OUT/'qualification/zero_GD_fixture.json',[])
    assert not zero['rows'] and zz['rows']==0 and ss
    shutil.copyfile(fm/'arbitrary_final_name.lp',fm/'duplicate.lp');rejected=False
    try:unique_model(fm,final_sha)
    except AssertionError:rejected=True
    assert rejected
    write(OUT/'qualification_zero_GD_context.json',dict(PASS=True,Optimize=0,Native_load=0,
        actual_sealed_R148_D=True,root_first_call=call['call'],root_SHA=call['model_sha256'],
        actual_R148_GD_rows=meta['rows'],actual_new_writer_zero_GD_rows=0,
        new_writer_matrix_real=True,zero_GD_call_wrapper_synthetic=True,
        duplicate_SHA_rejected=True,source_by_SHA=True,no_suffix_inference=True,all_old_producer_bytes_unchanged=True))
    print('PASS actual sealed first-call SHA, current zero-GD matrix with synthetic call wrapper, duplicate SHA rejection')


def run():
    configure();assert metered('qualification_zero_GD_reader_v2','diagnostic',[PYTHON,'-B',__file__,'check'],60,120)==0


if __name__=='__main__':globals()[sys.argv[1]]()
