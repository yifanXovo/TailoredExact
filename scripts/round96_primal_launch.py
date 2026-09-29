"""Explicit final admission gate around the frozen primal runner."""
import argparse
from round96_prepare import OUT,read,write,sha
import round96_primal as campaign

FILES=['primal/identity.json','production_build_identity.json','primal_numeric_audit.json',
       'primal_auditor_fixture.json','route_order_oracle.json','route_order_cli/passed.json']

def hashes():return {path:sha(OUT/path) for path in FILES}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['admit','run']);parser.add_argument('--number',type=int)
    args=parser.parse_args()
    if args.action=='admit':
        campaign.idle();campaign.build_identity();identity=read(OUT/'primal/identity.json')
        assert identity['bindings']==campaign.bindings()
        for path in ['primal_numeric_audit.json','primal_auditor_fixture.json','route_order_oracle.json','route_order_cli/passed.json']:
            assert read(OUT/path)['passed']
        assert read(OUT/'primal_numeric_audit.json')['identity_sha256']==sha(OUT/'primal/identity.json')
        write(OUT/'primal_admission.json',dict(admitted=True,files=hashes(),launcher_sha256=sha(__file__),
            planned_starts=12,maximum_process_seconds=24300,optimizer_calls=0,
            scope='Research-only complete OFF/ON/P; no default adoption or LP-G combination.'))
    else:
        admission=read(OUT/'primal_admission.json')
        assert admission['admitted'] and admission['files']==hashes() and admission['launcher_sha256']==sha(__file__)
        assert args.number and 1<=args.number<=12
        campaign.run(args.number)

if __name__=='__main__':main()
