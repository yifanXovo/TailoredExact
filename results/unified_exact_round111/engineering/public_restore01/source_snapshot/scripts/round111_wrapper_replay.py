"""Zero-native retained-raw branch coverage of final billed wrapper boundaries.

This is engineering only. The supervisor boundary is replaced by copying the
two completed qualification records; it does not establish a new CLI run.
"""
from round111_common import *
import round111_campaign as wrapper
import ast, copy, difflib, shutil, traceback

def main(mode,label):
    assert mode in ('normal','trailer_failure')
    destination=OUT/'qualification'/('wrapper_replay_'+mode+'_'+label)
    destination.mkdir(parents=True,exist_ok=False)
    real_out=OUT
    old=real_out/'fees/qualification_cli02/source_snapshot/scripts'
    paths=['round111_campaign.py','round111_common.py']
    comparisons={}
    for name in paths:
        before=(old/name).read_text(encoding='utf-8');after=(ROOT/'scripts'/name).read_text(encoding='utf-8')
        diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='actual_cli/'+name,tofile='final/'+name))
        (destination/(name+'.diff')).write_text(diff,encoding='utf-8')
        comparisons[name]=dict(actual_SHA=sha(old/name),final_SHA=sha(ROOT/'scripts'/name),diff_SHA=sha(destination/(name+'.diff')))
    btree=ast.parse((old/'round111_campaign.py').read_text(encoding='utf-8'))
    atree=ast.parse((ROOT/'scripts/round111_campaign.py').read_text(encoding='utf-8'))
    for name in ('helpers','records','prepare','supervised_run','remaining_reserve'):
        b=next(n for n in btree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        a=next(n for n in atree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        assert ast.dump(a)==ast.dump(b),name
    actual_budget=wrapper.budget()
    assert actual_budget['qualification_starts']==6 and actual_budget['qualification_seconds']==583.7201481292723
    wrapper.OUT=destination
    shutil.copyfile(real_out/'protocol.json',destination/'protocol.json')
    (destination/'qualification').mkdir()
    shutil.copyfile(real_out/'qualification/envelope.json',destination/'qualification/envelope.json')
    write(destination/'campaign/identity.json',read(real_out/'campaign/identity.json'))
    ident=read(real_out/'qualification/cli01/identity.json')
    ident=copy.deepcopy(ident)
    ident['helpers']=wrapper.helpers();ident['runner_sha256']=sha(wrapper.__file__)
    for launch in ident['launches']:
        original=launch['destination'];launch['retained_fixture_destination']=original
        launch['destination']=str(destination/'qualification/cli01/raw'/Path(original).name)
        launch['command']=[s.replace(original,launch['destination']) for s in launch['command']]
    write(destination/'qualification/cli01/identity.json',ident)
    wrapper.budget=lambda:dict(paid_starts=0,paid_outer_seconds=0,remaining_starts=24,remaining_outer_seconds=18000,
        qualification_starts=0,qualification_seconds=0,unclosed=[])
    events=[];metadata_costs=[];actual_write=wrapper.write
    def measured_write(path,value):
        tick=time.perf_counter();result=actual_write(path,value);duration=time.perf_counter()-tick
        events.append(dict(path=Path(path).relative_to(destination).as_posix(),end_tick=time.perf_counter(),seconds=duration))
        if Path(path).name=='audit_execution_metrics.json':metadata_costs.append(duration)
        return result
    wrapper.write=measured_write
    calls=[]
    retained_records=wrapper.records(real_out/'qualification/cli01')
    def retained_supervision(launch,identity,arm_tick):
        src=Path(launch['retained_fixture_destination']);dest=Path(launch['destination']);dest.mkdir(parents=True)
        for name in ('completion.json','audit.json'):
            shutil.copyfile(src/name,dest/name)
        if launch['arm']=='M-B':
            (dest/'external/native_logs').mkdir(parents=True)
            shutil.copyfile(src/'external/paper_optimize_ledger.csv',dest/'external/paper_optimize_ledger.csv')
            for p in (src/'external/native_logs').glob('*.round68.start.json'):
                value=read(p)
                if mode=='trailer_failure':value['submitted']=False
                write(dest/'external/native_logs'/p.name,value)
        record=copy.deepcopy(retained_records[launch['number']-1]);record['destination']=str(dest)
        with (destination/'qualification/cli01/summary.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
        wrapper.audit.last_metrics=read(src/'audit_execution_metrics.json')
        calls.append(dict(number=launch['number'],source=str(src),audit_SHA=sha(src/'audit.json'),actual_native_children=0))
        return record
    wrapper.supervised_run=retained_supervision
    code=0;error=None
    tick=time.perf_counter()
    try:wrapper.billed('qualification/cli01',1,2,'retained_wrapper',qualification=True)
    except AssertionError:
        code=1;error=traceback.format_exc()
        if mode!='trailer_failure':raise
    assert code==(1 if mode=='trailer_failure' else 0)
    receipt=read(destination/'fees/retained_wrapper/receipt.json')
    assert receipt['exit_code']==code and receipt['actual_native_children_with_launch']==0
    assert (destination/'qualification/identity.json').exists()==(mode=='normal')
    for launch in ident['launches']:
        base='qualification/cli01/raw/'+Path(launch['destination']).name+'/'
        metric=next(e for e in events if e['path']==base+'audit_execution_metrics.json')
        whole=next(e for e in events if e['path']==base+'whole_arm_receipt.json')
        assert metric['end_tick']<whole['end_tick']
    if mode=='normal':
        identity=next(e for e in events if e['path']=='qualification/identity.json')
        fee=next(e for e in events if e['path']=='fees/retained_wrapper/receipt.json')
        assert identity['end_tick']<fee['end_tick']
    else:assert (destination/'fees/retained_wrapper/failure.txt').exists()
    write(destination/'audit.json',dict(passed=True,mode=mode,actual_native_processes=0,Optimize=0,
        retained_supervisor_boundary=True,not_a_new_CLI_qualification=True,final_sources=wrapper.helpers(),source_comparisons=comparisons,
        unchanged_functions=['helpers','records','prepare','supervised_run','remaining_reserve'],
        actual_corrected_budget=actual_budget,events=events,retained_calls=calls,
        maximum_required_metadata_write_seconds=max(metadata_costs),metric_writes_before_whole_clock=True,
        qualification_trailer_before_fee_or_failure_receipt=True,actual_expected_exception=error,
        fee_receipt_SHA=sha(destination/'fees/retained_wrapper/receipt.json'),engineering_seconds=time.perf_counter()-tick))
    print(mode+' final wrapper engineering PASS',flush=True)

if __name__=='__main__':main(sys.argv[1],sys.argv[2])
