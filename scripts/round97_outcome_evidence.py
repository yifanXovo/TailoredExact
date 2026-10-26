"""Read normal results or explicitly reviewed interruptions without rewriting raw data."""
from pathlib import Path
from round97_campaign_v2 import ROOT, OUT, read, sha
import round97_interrupted_evidence as interrupted
import round97_recover_v1_interruption as recovery


def load(launch, completed):
    raw=Path(launch['destination'])
    original=read(raw/'audit.json');receipt=read(raw/'completion.json')
    assert receipt==completed['completion']
    assert completed['audit_passed']==original['passed']
    assert completed['endpoint']==original['endpoint']
    if original['passed']:
        result,paths=interrupted.validate_outcome(launch,original,receipt)
        return original,receipt,result,paths,None
    assert raw.resolve()==(OUT/'development02/raw/09_V1_FEEDBACK').resolve()
    assert (launch['number'],launch['id'],launch['arm'])==(9,'V1','FEEDBACK')
    restored=recovery.validate()
    assert completed==restored['original_summary_prefix'][8]
    assert receipt==restored['completion']
    registered=read(OUT/'development02/identity.json')['launches'][8]
    assert launch==registered or launch=={k:v for k,v in registered.items() if k!='command'}
    execution=OUT/'engineering/development02_hard_stop09_recovery02/receipt.json'
    assert read(execution)['exit_code']==0 and read(execution)['optimizer_calls']==0
    paths=[recovery.RECOVERY,Path(recovery.__file__).resolve(),execution]
    bounds={b['sequence']:b for b in restored['independent_root_bounds']}
    assert len(bounds)==89
    return restored['audited'],receipt,None,paths,bounds


certificate_status=interrupted.certificate_status
