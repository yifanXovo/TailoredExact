"""One zero-Optimize six-input export, then five bounded known-fixture CLI."""
from round122_common import *
from round122_prepare import EXPORTER,resolve
from round122_campaign import execute
from round122_evidence import extension
from qualify_round120 import child_creation
from read_round122 import complete_H
from round100_idle import ensure_idle
import traceback, collections

def reference(label):
    fee,tick=fee_begin(label,1,300,True,dict(starts=46,seconds=80160+1500));actual=0;code=1
    try:
        ensure_idle();identity();f=read(OUT/'prospective_helper_freeze.json');assert f['helpers']==helpers() and f['source_bindings']==bindings()
        assert sha(EXPORTER)==read(OUT/'engineering/reference_compile/receipt.json')['exporter_SHA']
        cmd=[str(EXPORTER),str(OUT/'qualification/reference_batch.tsv')]
        with (fee/'reference_stdout.log').open('xb') as out:
            child=subprocess.Popen(cmd,cwd=ROOT,env=environment(),stdout=out,stderr=subprocess.STDOUT)
            actual+=1
            try:
                write(fee/'reference_PID.json',dict(pid=child.pid,parent_pid=os.getpid(),actual_creation_unix=child_creation(child),command=cmd,Optimize=0))
                rc=child.wait(timeout=300)
            except BaseException:child.kill();child.wait();raise
        assert rc==0,rc
        for p in read(OUT/'input_manifest.json')['new_roles']:
            d=OUT/'qualification/reference'/p['id'];b=read(d/'build.json');native=read(d/'native_metadata.json')
            assert b['optimizer_calls']==native['Optimize']==0 and sha(d/'original.lp')==b['canonical_sha256']
            assert b['columns']==native['columns'] and b['rows']==native['rows'] and native['objective_constant']==0
        resolve();code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,True,code,actual)

def cli(label):
    fee,tick=fee_begin(label,5,1500,True,dict(starts=40,seconds=80160));actual=0;code=1
    try:
        ensure_idle();identity();gate=read(OUT/'review/pre_contract.json')
        assert gate['decision']=='ACCEPT' and gate['helpers']==helpers() and gate['source_bindings']==bindings()
        assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json')
        from read_round118 import item,finalize
        from read_round116 import reconcile
        result=[]
        for plan in ['qualification/h100_seed1','qualification/h100_seed0']:
            h=read(OUT/plan/'identity.json')
            for l in h['launches']:
                actual+=1;execute(l,h)
            recs=collections.defaultdict(list)
            with extension():
                items=[item(ROOT,l,h,recs) for l in h['launches']];assert all(v['complete'] for v in items)
                final=reconcile([q for v in items for q in v['claims']],[q for v in items for q in v['ind']['witnesses']])
                assert not final['rejections'],'PROOF_RELIABILITY_PRIORITY: qualification contradiction'
                arms=[finalize(ROOT,v,final,recs) for v in items]
            assert all(a['formal_protocol_qualified'] and a['numbers_qualified'] for a in arms)
            result.append(dict(plan=plan,arms=arms,adjudication=final))
            if plan.endswith('seed1'):
                H=complete_H(h['launches'][0]['panel'],{l['arm']:Path(l['destination']) for l in h['launches'] if l['arm']!='P-GRB'})
                assert all(x['qualified'] for x in H['comparisons']);write(OUT/'qualification/full_H_comparison.json',H)
        write(OUT/'qualification/current_core.json',dict(groups=result,actual_CLI=5,Seed1=METHODS,Seed0=['MB-D1'],not_formal_performance=True))
        write(OUT/'review/performance_admission.json',dict(decision='ACCEPT',candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
            final_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,helpers=helpers(),source_bindings=bindings(),pre_contract_SHA=sha(OUT/'review/pre_contract.json'),
            five_known_fixture_actual_CLI=True,Seed1=METHODS,Seed0=['MB-D1'],full_H_equal=True,qualification_core_SHA=sha(OUT/'qualification/current_core.json'),
            no_formal_input_H_LP_MIP_screening=True,all_failed_fees_retained=True,not_performance_superiority=True));code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        launches=[l for plan in ['qualification/h100_seed1','qualification/h100_seed0'] for l in read(OUT/plan/'identity.json')['launches']]
        fee_pending(fee,tick,True,code,actual,child_states(launches))

if __name__=='__main__':{'reference':reference,'cli':cli}[sys.argv[1]](sys.argv[2])
