"""Explicit disposition of the prelaunch-only observer false positive."""
from round164_common import *

def run():
    from round164_campaign import admission,panel
    group=admission()['groups'][0];launch=group['launch'];d=Path(launch['destination'])
    old=read(OUT/'fees/arm_001/receipt.json')
    assert old['exit_code']==1 and not old['timeout']
    error=(OUT/'fees/arm_001/stderr.log').read_text()
    assert 'foreign optimizer/build process active' in error and 'round164_live_watch.py' in error
    write(OUT/'execution_dispositions.json',dict(UTC=utc(),failures=[dict(position=1,fee_label='arm_001',
        reason='read-only watcher interpreter pathname matched inherited old-optimizer regex',
        Native_started=False,producer_destination_created=False,scientific_seconds=old['G1_seconds'],
        original_evidence_preserved=True)],
        healthy_producers_repeated=0,algorithm_or_producer_changed=False,matrix_changed=False,
        resolution='use existing D:/msys64/ucrt64/bin/python.exe for metadata-only observer',
        qualified_fee_by_position={'1':'arm_001_retry01'}))
    if not (d/'round164_endpoint.json').exists():
        assert not d.exists(),'this explicit retry is only for an unstarted producer'
        assert not (OUT/'fees/arm_001_retry01').exists()
        result=metered('arm_001_retry01','panel',[PYTHON,'-B',ROOT/'scripts/round164_campaign.py','arm',1],
            reservation=launch['cap_seconds']+300,fault_timeout=launch['cap_seconds']+900)
        assert result==0,'preserve affected retry; inspect before further production'
    panel()

if __name__=='__main__':run()
