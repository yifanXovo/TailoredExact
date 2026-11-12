"""One finite post-panel semantic readback; never starts Native."""
from round164_common import *

def run():
    import round164_analyze,round164_structure,round164_identity,round164_sources,round164_evidence_tables
    if '--after-analysis' in sys.argv:
        assert read(OUT/'reports/summary.json')['complete_new_arms']==24
        assert read(OUT/'Seed0_reuse_qualification.json')['PASS']
    else:round164_analyze.run()
    round164_structure.run();round164_identity.run();round164_sources.run()
    round164_evidence_tables.run()

if __name__=='__main__':run()
