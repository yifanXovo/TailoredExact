"""Replay selected declared roles into new outputs from identical qualified bytes.

This entry point is not invoked as part of the original campaign. It requires
the local R71 executable/reference/test log; rebuilding needs new qualification.
"""
import argparse,shutil,subprocess
from pathlib import Path
import round72_campaign as campaign
run=campaign.run

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    parser.add_argument('--ids',nargs='+',required=True,choices=['D3','C2','D4','D7'])
    args=parser.parse_args();campaign.assert_frozen()
    original=run.OUT;identity,protocol=run.assert_frozen()
    assert not (original/'active_run.lock').exists()
    assert len(args.ids)==len(set(args.ids))
    if 'D7' in args.ids:assert run.read(original/'long_gate.json')['admitted'],'D7 reserve was not admitted'
    destination=(run.ROOT/args.output).resolve()
    assert destination.is_relative_to(run.ROOT) and not destination.exists()
    maximum=3*len(args.ids);assert maximum<=12
    destination.mkdir(parents=True)
    for name in ['plan.md','mathematics.md','affinity_qualification.json','qualification.json']:
        shutil.copyfile(original/name,destination/name)
    new_protocol=dict(protocol)
    new_protocol.update(panel=[p for p in protocol['panel'] if p['id'] in args.ids],
        maximum_performance=maximum,maximum_reference_exports=len(args.ids),
        worst_case_seconds=sum(3*protocol['caps'][i] for i in args.ids),
        validation_scope='Fresh separate same-byte reproduction; not an original campaign observation or independent confirmation')
    run.write(destination/'protocol.json',new_protocol)
    new_identity=dict(identity)
    new_identity.update(reproduction_script_sha256=run.sha(__file__),
        reproduction_source_manifest_sha256=run.sha(original/'build_v1.json'),
        reproduction_checkout_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=run.ROOT).decode().strip())
    run.write(destination/'build_v1.json',new_identity)
    run.write(destination/'reproduction_plan.json',dict(ids=args.ids,maximum_launches=maximum,
        full_process_caps={i:protocol['caps'][i] for i in args.ids},
        inherited_ctests=49,new_ctests=0,new_qualification_calls=0,
        original_campaign=str(original.relative_to(run.ROOT)),
        diagnostic_routes_imported=False,logical_processor=2,affinity_mask=4))
    campaign.OUT=destination;campaign.bind();campaign.assert_frozen()
    import round71_endpoint as endpoint
    for identity in args.ids:
        run.refbuild([identity])
        for arm in protocol['allowed_arms'][identity]:
            run.run([identity],[arm],protocol['caps'][identity],'development')
            endpoint.check(sum(e['charged'] for e in run.runner.entries()))
    campaign.package.main()
    import round71_delivery as delivery
    delivery.main()

if __name__=='__main__':main()
