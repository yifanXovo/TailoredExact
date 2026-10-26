from round104_common import *
if __name__=='__main__':
    from round100_idle import ensure_idle
    ensure_idle()
    campaign=read(OUT/'control01/identity.json')
    result=dict(source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        record_kind='consolidation of the prior pre-launch control01 freeze; this script is executed later',
        prelaunch_campaign_identity_sha256=sha(OUT/'control01/identity.json'),
        prelaunch_campaign_prepared_unix=campaign['prepared_unix'],
        consolidated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        source_bindings=bindings(),binary=(BUILD/'ExactEBRP.exe').relative_to(ROOT).as_posix(),
        PE_sha256=sha(BUILD/'ExactEBRP.exe'),compression_PE_sha256=sha(BUILD/'Round104Compression.exe'),
        reference_PE_sha256=sha(BUILD/'Round65ReferenceBuild.exe'),DLL_sha256=sha('D:/gurobi1302/win64/bin/gurobi130.dll'),
        helpers={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'scripts').glob('round104*.py') if 'make_' not in p.name},
        control_protocol_sha256=sha(OUT/'control01_protocol.json'),
        rules=dict(candidate='self-paid finite pool, numerical ACTIVE requalification; no historical inputs',
            stopping='all inspected members; finite no-new-direction UNKNOWN; support/precision UNKNOWN; global deadline only',
            native='unchanged original ENS and Gurobi13.0.2 Threads1 Seed0 PresolveAuto original tolerances',
            default='ENS-C, R104 off; M-B/R101/R102-J/R103-H separate',
            shadow='same paid preparation, no formal bound/cutoff/row mutation',
            confirmation='not admitted; first complete four-arm F2 cost control only'))
    assert result['source_bindings']==campaign['source_hashes']
    assert result['PE_sha256']==campaign['candidate_binary_sha256']
    write(OUT/'production_freeze.json',result);print(json.dumps(dict(source=result['source_head'],PE=result['PE_sha256'])))
