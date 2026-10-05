"""Read-only actual-callback failure receipt checks via unchanged R86 reader."""
from round102_common import *
from pathlib import Path
import round86_native_evidence as nej
import sys
if __name__=='__main__':
    root=Path(sys.argv[1]);records=[]
    for name in ['status','cut','certificate','unknown','summary','service_status','service_cut','service_certificate','service_unknown','service_summary']:
        directory=root/name
        r=[nej.receipt(directory/f'event_{i}.commit',1,2) for i in range(1,5)];identity=r[0]['payload']
        panel=dict(input_sha256=identity['input_sha256'],T_seconds=identity['T'],pickup_seconds=identity['pickup_seconds'],drop_seconds=identity['drop_seconds'])
        panel['lambda']=identity['lambda'];before=nej.audit(ROOT,panel,r[:3],'synthetic-no-engine');assert before['LB']==.1
        try:nej.audit(ROOT,panel,r,'synthetic-no-engine')
        except AssertionError as e:assert e.args[0][0]=='journal_failure'
        else:raise AssertionError('failed stream accepted')
        assert not (directory/'event_5.commit').exists()
        records.append(dict(case=name,prior_LB=.1,rejected='journal_failure',failure=r[-1]['payload']['reason']))
    label=sys.argv[2] if len(sys.argv)>2 else 'fault_reader01'
    write(OUT/'engineering'/(label+'.json'),dict(records=records,Optimize_calls=0,limitations='fake API callback-control test, no native B&B or complete storage-loss qualification'))
    print('all ten complete failed streams rejected; zero Optimize')
