"""One paid finite zero-Optimize batch; explicitly scoped simulated clocks."""
from round115_common import *
import copy,inspect,traceback,types
import round115_campaign as campaign
import read_round115 as reader
import qualify_round114 as previous
import qualify_round113 as fixtures
from round114_claims import reconcile,qualify_endpoint
from round115_sublevel import finite_checks

class Clock:
    def __init__(self):self.now=0.
    def monotonic(self):return self.now
    def perf_counter(self):return self.now
    def time(self):return 1791747924.+self.now
    def sleep(self,n):self.now+=n

def run(label):
    fee,tick=campaign.fee_begin(label,0,30,True);code=1;q=OUT/'qualification'/label;q.mkdir()
    try:
        cases=[];good=previous.frozen_evidence();normal=dict(U=1.,L=.1,gap=.9,certificate=False)
        for name,U,zero,damage in [('normal_open',1.,False,[]),('own_strict_zero',0.,True,[dict(arm='ENS-C',call=1)]),
                ('rejected_claim',1.,False,[dict(arm='P-GRB',call=1)])]:
            e=dict(good,own_U=U,own_exact_zero=zero);ep=qualify_endpoint(e,damage,normal)
            assert ep['formal_protocol_qualified'];cases.append(dict(case=name,endpoint=ep))
        for name,field in [('missing_critical_output','files_verified'),('unknown_return','return_verified'),('true_producer_overcap','clock_valid')]:
            e=dict(good,**{field:False});ep=qualify_endpoint(e,[],normal);assert not ep['formal_protocol_qualified']
            cases.append(dict(case=name,endpoint=ep))
        e=dict(good,necessary_closeout_complete=False);assert not qualify_endpoint(e,[],normal)['formal_protocol_qualified']
        cases.append(dict(case='producer_pending_not_qualified',passed=True))
        # Actual inherited supported mapped-not-started gate, one branch only.
        namespace=dict(vars(fixtures),ROOT=ROOT,OUT=OUT,OLD_ROOT=Path('E:/codes/ExactEBRP-round112'))
        exec(compile(inspect.getsource(fixtures.fixture),__file__+'::supported_fixture','exec'),namespace)
        z=q/'normal_not_started';z.mkdir();l,obs=namespace['fixture'](z,'mapped_not_started');d=Path(l['destination'])
        ps=previous.ps;j=ps.ps_journal(ROOT,l['panel'],d);r=read(d/'result.json');c=read(d/'completion.json')
        own=ps.core.full_fleet(ROOT,l['panel'],read(d/'result.json.round112.startup.json'))
        value=ps.validate_ps_lifecycle(ROOT,l,d,j,r,c,own);assert value['actual_Optimize']==0
        cases.append(dict(case='normal_not_started',lifecycle=value))
        # Known actual same-domain fixture: reuse signed exact proof, no matrix replay.
        source=OUT/'signed_fixture';oldobs=read(source/'04_G50-C1_S0_P-GRB/observations.json')
        call=next(o['payload'] for o in oldobs if o['payload']['kind']=='call');b=next(o['payload'] for o in oldobs if o['payload']['kind']=='bound' and o['payload']['native_bound']>1e-7)
        ownzero=read(source/'02_G50-C1_S0_ENS-C/result.json');p=read(OUT/'inherited_r113/input_manifest.json')['roles'][0]
        w=campaign.audit.core.full_fleet(ROOT,p,ownzero);assert w['F']==0.
        claim=dict(arm='P-GRB',call=call['call'],sequence=b['sequence'],model_SHA=call['model_sha256'],input_SHA=p['input_sha256'],
            scope=call,value=b['native_bound'],source='signed_actual_fixture',available=0.,domain_verified=True,dependencies=[call['call']])
        witness=dict(w,arm='ENS-C',source='signed_existing_own_zero',input_SHA=p['input_sha256'],available=0.,physical_verified=True)
        assert reconcile([claim],[witness])['damaged_calls']==[dict(arm='P-GRB',call=call['call'])]
        cases.append(dict(case='actual_signed_bad_call_reused',model_SHA=call['model_sha256'],full_matrix_replay=False))
        # Original source-extracted supervisor exercised with all OS surfaces mocked.
        clock=Clock();state=dict(kills=0,waits=0)
        class Child:
            pid=123;returncode=None
            def poll(self):
                if clock.now>=2:self.returncode=0
                return self.returncode
            def kill(self):state['kills']+=1;self.returncode=-9
            def wait(self,timeout=None):state['waits']+=1;assert self.poll()==0;return 0
        class Affinity:
            def inherited_core(self,mask):return self
            def __enter__(self):return dict(before=dict(process_mask=4))
            def __exit__(self,*args):return None
            def read_masks(self,pid=None):return dict(process_mask=4)
        directory=q/'clock_source_extracted';directory.mkdir();child=Child()
        local=dict(vars(campaign.supervisor),time=clock,ROOT=ROOT,CAMPAIGN=directory,_arm_tick=0.,
            foreign_heavy_processes=lambda:[],memory_available=lambda:8*1024**3,
            shutil=types.SimpleNamespace(disk_usage=lambda p:types.SimpleNamespace(free=20*1024**3)),
            subprocess=types.SimpleNamespace(Popen=lambda *a,**k:child),affinity=Affinity(),atomic_status=lambda *a:None,
            production_check=lambda *a:dict(state='PRODUCED_PENDING_VERIFICATION',verification_passed=None))
        l=dict(number=1,id='mock',arm='P-GRB',destination=str(directory/'raw'),command=['MOCK_NO_OS_CHILD'],panel={},cap_seconds=120,hard_stop_seconds=118)
        rec=campaign.supervisor_function(local)(l,dict(common=dict(affinity_mask=4)),dict(prereg_sha256='mock',runner_sha256='mock'))
        produced=clock.now;assert rec['audit_passed'] is None and state==dict(kills=0,waits=1)
        clock.sleep(40);assert produced<90 and clock.now-produced==40 and l['hard_stop_seconds']==118
        assert not qualify_endpoint(dict(good,necessary_closeout_complete=False),[],normal)['formal_protocol_qualified']
        assert qualify_endpoint(good,[],normal)['formal_protocol_qualified']
        cases.append(dict(case='simulated_40s_verify_does_not_consume_frozen_native_window',T_produce=produced,T_verify=40.,
            mock_surfaces=['clock','OS child','affinity','memory','disk','physical final check'],actual_source_extracted=True,native_Optimize=0))
        # Post-hoc better U is not an admissible producer update.
        assert reader.namespace['clock_evidence'] is reader.clock_evidence
        bad=q/'posthoc_mutation';bad.mkdir();write(bad/'result.json',dict(mock_own_U=1))
        write(bad/'producer_seal.json',dict(required_SHA={'result.json':sha(bad/'result.json')}))
        write(bad/'producer_receipt.json',dict(producer_seal_SHA=sha(bad/'producer_seal.json'),native_stopped_no_reentry=True))
        (bad/'result.json').write_text('{"mock_own_U":0}\n',encoding='utf-8')
        try:campaign.verify(dict(destination=str(bad)),{})
        except AssertionError:cases.append(dict(case='posthoc_backfill_rejected_by_actual_verifier',passed=True,native_Optimize=0))
        else:raise AssertionError('posthoc producer mutation accepted')
        e=dict(good,clock_valid=3590<=3600)
        assert qualify_endpoint(e,[],normal)['formal_protocol_qualified'] and 3590+40>3600
        cases.append(dict(case='only_verification_slow_total_overcap_qualified_after_valid_audit',T_produce=3590,T_verify=40,T_total=3630,synthetic=True))
        diag=reader.diagnostics_r114('E:/codes/ExactEBRP-round114');assert len(diag)==2 and all(v['state']=='PROTOCOL_DIAGNOSTIC_ONLY' for v in diag)
        write(q/'R114_diagnostic_only.json',diag)
        finite_checks()
        write(q/'summary.json',dict(passed=True,cases=cases,driver_processes=1,OS_children=0,Optimize=0,
            final_helpers=campaign.helpers(),test_SHA=sha(__file__),old_statuses_unchanged=True))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:campaign.fee_pending(fee,tick,True,code,0)

if __name__=='__main__':run(sys.argv[1])
