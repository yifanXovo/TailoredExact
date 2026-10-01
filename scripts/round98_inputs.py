"""Pin development inputs and inherited fixed root states, no Optimize."""
from round98_common import *
import generate_citibike443_regional_v1 as parser
def prepare():
    prior=read(ROOT/'results/unified_exact_round97/development02/identity.json')
    confirmation=read(ROOT/'results/unified_exact_round97/confirmation01/identity.json')
    d6=read(ROOT/'results/unified_exact_round90/preregistration_d6_tail.json')['role']
    if isinstance(d6,list):d6=d6[0]
    records=[]
    for role,old,original_id,cap in [
        ('F2',prior,'F2',900),('F5',prior,'F5',3600),
        ('R97-C2',confirmation,'C2',900),('R97-C3',confirmation,'C3',1200)]:
        launch=next(x for x in old['launches'] if x['id']==original_id and x['arm']=='OFF')
        p=dict(launch['panel'],id=role,cap_seconds=cap)
        witness=Path(launch['destination'])/'external/initial_witness.json'
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        physical=parser.parse_instance_mirror(ROOT/p['input_path'])
        p.update(V=physical['V'],M=physical['M'],Q_vector=physical['Q'])
        p['instance_path']=p['input_path'];p['historical_initial_witness']=witness.relative_to(ROOT).as_posix()
        p['historical_initial_witness_sha256']=sha(witness)
        p['diagnostic_cutoff']=read(witness)['objective']
        p['diagnostic_gamma_L']=0;p['diagnostic_gamma_U']=min(p['diagnostic_cutoff'],(p['V']-1)/p['V'])
        records.append(p)
    physical=parser.parse_instance_mirror(ROOT/d6['input_path'])
    d6=dict(d6,id='D6',cap_seconds=1800,instance_path=d6['input_path'],
        V=physical['V'],M=physical['M'],Q_vector=physical['Q'])
    # Use a already-verified historical seed only as fixed model diagnostics,
    # never as a formal timed Start. Pin a current saved ENS root state.
    for path in (ROOT/'results/unified_exact_round90/runner_lp_g_d6_tail').rglob('initial_witness.json'):
        if 'D6' in path.as_posix():
            d6.update(historical_initial_witness=path.relative_to(ROOT).as_posix(),
                historical_initial_witness_sha256=sha(path),diagnostic_cutoff=read(path)['objective'])
            break
    assert 'diagnostic_cutoff' in d6,'missing exact D6 root seed for diagnosis'
    d6.update(diagnostic_gamma_L=0,diagnostic_gamma_U=min(d6['diagnostic_cutoff'],(d6['V']-1)/d6['V']))
    records.append(d6)
    write(OUT/'development_inputs.json',dict(roles=records,optimizer_calls=0,
        distinction='R97-C2 surplus weak proof and R97-C3 feedback regression are development, not independent confirmation',
        diagnostic_witness_policy='Historical root cutoff only; formal witnesses freshly self-paid each arm'))
    print([{k:p[k] for k in ['id','input_path','input_sha256','V','M','Q_vector','T_seconds']} for p in records])
if __name__=='__main__':prepare()
