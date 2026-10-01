"""Zero-Optimize exact-byte recovery for immutable paid R1 C3 journal calls.

Never overwrite a run, journal, matrix or failed audit. Every recovered matrix
must hash to the original committed call before any replay can be accepted.
"""
import subprocess,sys,shutil
import round98_campaign as campaign
from round98_common import *

def run():
    q=read(OUT/'development02/identity.json');launch=q['launches'][13];d=Path(launch['destination'])
    assert q['source_hashes']==bindings() and q['helpers']==campaign.helpers()
    assert sha(BUILD/'ExactEBRP.exe')==q['candidate_binary_sha256']
    original=read(d/'observations.json');p=launch['panel'];root=OUT/'recovered_models/C3_R1'
    root.mkdir(parents=True,exist_ok=False);mapping={}
    known=OUT/'exports/R97-C3/aggregate.lp'
    for row in original:
        e=row['payload']
        if e['kind']!='call':continue
        expected=e['model_sha256']
        if expected in mapping:continue
        old=Path(e['model_path'])
        if old.is_file() and sha(old)==expected:
            mapping[expected]=str(old);continue
        if sha(known)==expected:
            mapping[expected]=str(known);continue
        dest=root/('call'+str(e['call']));dest.mkdir()
        cmd=list(map(str,[BUILD/'Round98ModelExport.exe',ROOT/p['input_path'],p['T_seconds'],
            p['pickup_seconds'],p['drop_seconds'],p['lambda'],e['lower_g'],e['upper_g'],e['cutoff'],dest]))
        write(dest/'launch.json',dict(command=cmd,optimizer_calls=0,
            exporter_sha256=sha(BUILD/'Round98ModelExport.exe'),input_sha256=p['input_sha256']))
        ret=subprocess.run(cmd,cwd=ROOT,env=env(),capture_output=True,text=True,timeout=60)
        (dest/'stdout.log').write_text(ret.stdout);(dest/'stderr.log').write_text(ret.stderr)
        assert ret.returncode==0
        recovered=dest/'aggregate.lp';assert sha(recovered)==expected,('exact journal matrix not recovered',e)
        mapping[expected]=str(recovered)
    # The replay alters only the physical path used to locate identical bytes.
    replay=[]
    for row in original:
        cloned={**row,'payload':dict(row['payload'])}
        if cloned['payload']['kind']=='call':
            e=cloned['payload'];e['model_path']=mapping[e['model_sha256']]
        replay.append(cloned)
    write(root/'path_resolution.json',dict(original_observations_sha256=sha(d/'observations.json'),
        original_failed_audit_sha256=sha(d/'audit.json'),original_completion_sha256=sha(d/'completion.json'),
        mapping=mapping,optimizer_calls=0,native_export_processes=2,
        rule='Original committed sha must match exact restored bytes; original events remain immutable'))
    audited=campaign.adapter(launch,replay,read(d/'completion.json'),q)
    write(root/'replay_observations.json',replay)
    write(root/'qualified_recovery.json',dict(audit=audited,
        original_observations_sha256=sha(d/'observations.json'),original_failed_audit_sha256=sha(d/'audit.json'),
        original_completion_sha256=sha(d/'completion.json'),original_result_sha256=sha(d/'result.json'),
        original_identity_sha256=sha(OUT/'development02/identity.json'),
        path_resolution_sha256=sha(root/'path_resolution.json'),optimizer_calls=0,
        source_sha256=sha(__file__),no_performance_replay=True))
    print(audited['endpoint'])

if __name__=='__main__':run()
