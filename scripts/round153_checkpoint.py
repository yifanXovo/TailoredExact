"""End an explicitly diagnosed owned offline outer, preserving every receipt."""
from round153_common import *

def run(label,target):
    folder=OUT/'fees'/label;identity=read(folder/'PID.json')
    assert 'round153_coupled.py' in ' '.join(identity['command'])
    assert not (folder/'receipt.json').exists()
    snapshot=meter.process_snapshot(identity);assert snapshot['same_process_alive']
    previous=read(Path(target)/'result.json')
    decision=dict(UTC=utc(),kind='adaptive_offline_research_checkpoint',owned_identity=identity,live_snapshot=snapshot,
                  reason='Stable single-stock complete RMP upper with very loose full-domain pricing and no lower progress; pursue the matching zero-potential global floor with old-joint pricing.',
                  completed_iterations=len(previous['records']),lower=previous['lower'],upper=previous['upper'],
                  no_new_bound_from_interrupted_call=True,not_a_research_endpoint=True,
                  next='strengthen exact global zero-potential price; if unresolved deepen coupling/stabilization')
    write(Path(target)/'checkpoint_decision.json',decision)
    result=subprocess.run(['taskkill','/PID',str(identity['pid']),'/T','/F'],capture_output=True)
    write(Path(target)/'checkpoint_termination.json',dict(exit_code=result.returncode,stdout=result.stdout.decode(errors='replace'),stderr=result.stderr.decode(errors='replace')))
    assert result.returncode==0

if __name__=='__main__':run(*sys.argv[1:])
