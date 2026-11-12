"""Check the complete frozen Seed matrix before the first formal arm."""
from round164_common import *

def run():
    from round164_campaign import Arm,tokens,command
    m=read(OUT/'matrix_frozen.json');facts=[];keys=set()
    for group in m['groups']:
        arm=Arm(**group['arm']);launch=group['launch'];p=launch['panel'];values=tokens(launch['command'])
        assert launch['command']==command(p,arm,Path(launch['destination']))
        assert arm.gurobi_seed==launch['seed']==launch['gurobi_seed']==p['gurobi_seed']
        identity=read(OUT/group['group']/'identity.json')
        assert identity['prereg']['common']['gurobi_seed']==arm.gurobi_seed
        assert sha(OUT/group['group']/'identity.json')==group['identity_SHA256']
        assert values['--gurobi-seed']==str(arm.gurobi_seed)
        assert float(values['--lambda'])==p['lambda'] and float(values['--T'])==p['T_seconds']
        assert p['exposed'] and not Path(launch['destination']).exists()
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        key=(arm.input_id,arm.gurobi_seed,arm.method,arm.repeat,launch['cap_seconds'],PE_SHA,DLL_SHA)
        assert key not in keys;keys.add(key)
        facts.append(dict(position=group['position'],id=arm.input_id,seed=arm.gurobi_seed,method=arm.method,
            H_seed=20260626,cap=launch['cap_seconds'],scientific_reservation=launch['cap_seconds']+300,
            fault_timeout=launch['cap_seconds']+900,own_lifecycle=True))
    assert len(facts)==24 and sum(r['cap'] for r in facts)==43200
    assert len({(r['id'],r['seed']) for r in facts})==12 and len({r['id'] for r in facts})==6
    assert read(OUT/'qualification/result.json')['PASS']
    write(OUT/'pre_panel_admission.json',dict(PASS=True,UTC=utc(),facts=facts,
        matrix_SHA256=sha(OUT/'matrix_frozen.json'),primal_targets_SHA256=sha(OUT/'primal_targets_frozen.json'),
        qualification_SHA256=sha(OUT/'qualification/result.json'),protected=check_protected(),
        all_24_positions_frozen=True,methods_B_P_only=True,scientific_total_hard_limit=57600,
        implementing_agent_check_not_independent_person_review=True,Optimize=0))
    print('PASS: 24 distinct positions, 12 pairs, 6 inputs; Seed identity and separate timeout/reservation.')

if __name__=='__main__':run()
