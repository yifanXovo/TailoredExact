"""Scope-verified R100 clocks, plus one common covered precap checkpoint.
No Optimize or native engine timestamp inference. Performance must be idle.
"""
import sys
import round100_measure as inherited
from round100_idle import ensure_idle
from round101_common import *

if __name__=='__main__':
    ensure_idle();label=sys.argv[1];campaigns=sys.argv[2:]
    caps={a['cap_seconds'] for name in campaigns for a in read(OUT/name/'identity.json')['launches']}
    inherited.OUT=OUT
    inherited.CHECKPOINTS=sorted(set(inherited.CHECKPOINTS)|{cap-10 for cap in caps if cap>10})
    inherited.main(label,campaigns)
    write(OUT/label/'round101_clock_identity.json',dict(optimizer_calls=0,
        inherited_sha256=sha(ROOT/'scripts/round100_measure.py'),wrapper_sha256=sha(__file__),
        common_precap_rule='Each preregistered outer cap minus10s; committed/scope-verified prefix only. Certified same-run endpoints may carry forward; unproved normal exit is censored without interpolation.',
        added_checkpoint_status='Supplemental descriptive checkpoints defined before final-source protection and long/confirmation launches; earlier completed development endpoints are not redesign evidence from these checkpoints.'))
