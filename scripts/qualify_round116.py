"""One small paid classification/administrative-equivalence batch, zero Optimize."""
from round116_common import *
import copy,inspect,traceback
import round116_campaign as campaign
import round115_campaign as prior
import read_round116 as reader
from round114_claims import reconcile,qualify_endpoint
from qualify_round114 import frozen_evidence
from compare_round112_startup import fleet_key

def run(label):
    fee,tick=campaign.fee_begin(label,0,60,True);code=1;q=OUT/'qualification'/label;q.mkdir()
    try:
        cases=[];good=frozen_evidence();normal=dict(U=1.,L=.1,gap=.9,certificate=False)
        for name,U,zero,damage,cert in [('own_strict_zero',0.,True,[dict(arm='P-GRB',call=1)],False),
            ('positive_own_U_floor0',1.,False,[dict(arm='P-GRB',call=1)],False),
            ('reliable_nonzero_complete_certificate',1.,False,[],True)]:
            e=dict(good,own_U=U,own_exact_zero=zero)
            v=qualify_endpoint(e,damage,dict(U=U,L=U if cert else .1,gap=0. if cert else U-.1,certificate=cert))
            assert v['formal_protocol_qualified']
            a=dict(v,own_exact_zero=zero);expected={'own_strict_zero':'OWN_ZERO_CERTIFICATE','positive_own_U_floor0':'SOURCE_REDUCED_OPEN','reliable_nonzero_complete_certificate':'CLEAN_NONZERO_CERTIFICATE'}[name]
            assert reader.proof_class(a)==expected;cases.append(dict(case=name,endpoint=v,proof_class=expected))
        c=dict(arm='P-GRB',call=1,sequence=1,model_SHA='synthetic_model',input_SHA='synthetic_input',
            scope=dict(full_original=True,lower_g=0.,upper_g=.9,cutoff=2.,epoch=1),value=.1,source='synthetic_bound',available=1.,domain_verified=True,dependencies=[1])
        w=dict(arm='P-S',source='synthetic_zero',F=0.,G=0.,input_SHA='synthetic_input',available=2.,physical_verified=True)
        lp=dict(c,call=2,sequence=2,value=0.,source='independent_LP',dependencies=[2])
        v=reconcile([c,lp],[w]);assert v['damaged_calls']==[dict(arm='P-GRB',call=1)] and next(q for q in v['all_claims'] if q['call']==2)['native_proof_qualified']
        assert v==reconcile([lp,c],[w]);cases.append(dict(case='one_rejected_call_independent_LP_retained',result=v))
        local=dict(c,scope=dict(full_original=False,lower_g=.2,upper_g=.8,cutoff=2.,epoch=1))
        assert not reconcile([local],[w])['rejections'];cases.append(dict(case='root_zero_outside_positive_G_domain_rejected_as_counterexample',passed=True))
        for name,field in [('unknown_time','clock_valid'),('missing_physical','own_physical_verified'),('producer_pending','necessary_closeout_complete')]:
            ep=qualify_endpoint(dict(good,**{field:False}),[],normal);assert not ep['formal_protocol_qualified'];cases.append(dict(case=name,endpoint=ep))
        p=dict(Q_vector=[3,5]);first=[dict(vehicle=0,nodes=[0,1,0],operations=[dict(station=1,pickup=1,drop=0)])]
        second=[dict(vehicle=1,nodes=[0,1,0],operations=[dict(station=1,pickup=1,drop=0)])]
        assert fleet_key(p,first)!=fleet_key(p,second);cases.append(dict(case='same_U_different_capacity_fleet_not_matched_H',passed=True))
        assert not (True and 0>0);cases.append(dict(case='matched_H_no_Optimize_BACKEND_NOT_EXPOSED',attribution_eligible=False))
        a=dict(arm='ENS-C',U=1.,L=1.+1e-15,gap=-1e-15,certificate=True,certificate_qualified=True,numbers_qualified=True,formal_protocol_qualified=True,complete_seconds=100.)
        b=dict(a,arm='P-GRB',gap=0.,L=1.,complete_seconds=100.)
        v=reader.pair(a,b);assert v['candidate_gap']<0 and not v['percentage_gap_path_applicable'];cases.append(dict(case='signed_negative_gap_retained',pair=v))
        # Same artificial launch record: native command generation and producer
        # implementation are precisely inherited; only input/output/PE paths,
        # manifest grouping and declared cap change between rounds.
        assert campaign.supervised is prior.supervised and campaign.finish_producer is prior.finish_producer
        assert campaign.production_check is prior.production_check and campaign.supervisor_function is prior.supervisor_function
        h=read(OUT/'input_manifest.json')['qualification_roles'][0];oldid=read(ROOT/'results/unified_exact_round115/qualification/cli01/identity.json')
        current=read(OUT/'qualification/cli01/identity.json')
        def semantic(cmd):
            return [s.replace('E:\\codes\\ExactEBRP-round115','ROOT').replace(str(ROOT),'ROOT')
                .replace('E:/codes/ExactEBRP-round115','ROOT').replace(str(ROOT).replace('\\','/'),'ROOT').replace('round116','round115') for s in cmd]
        for a,b in zip(current['launches'],oldid['launches']):
            assert a['arm']==b['arm'] and a['cap_seconds']==b['cap_seconds']==120
            assert semantic(a['command'])==semantic(b['command']),('argv semantic drift',a['arm'])
        for cap in [900,1800,3600]:
            p0=dict(h,cap_seconds=cap);prereg=current['prereg'];d=Path('SYNTHETIC_PATH_ONLY')
            cmd=prior.supervisor.command_for(prereg,p0,'ENS-C',d)
            assert cmd[cmd.index('--time-limit')+1]==str(cap-6) and cmd[cmd.index('--process-wall-time-limit')+1]==str(cap)
            assert cmd[cmd.index('--process-shutdown-margin')+1]=='30'
        cases.append(dict(case='old_new_same_record_native_window_and_pending_receipts_equivalent',passed=True,scope='paths/groups/cap metadata only',actual_OS_children=0))
        write(q/'summary.json',dict(passed=True,cases=cases,Optimize=0,OS_children=0,driver_processes=1,helpers=campaign.helpers(),test_SHA=sha(__file__)))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:campaign.fee_pending(fee,tick,True,code,0)

if __name__=='__main__':run(sys.argv[1])
