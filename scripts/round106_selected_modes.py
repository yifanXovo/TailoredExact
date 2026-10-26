"""Deterministic informative-mode selection from complete formal raw evidence.

This is a selection/index, not another solver or a mathematical audit. Every
selected mode retains its full source candidate and proof/witness references.
"""
import argparse, csv, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified_exact_round106'

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    identity = read(OUT / 'development01/identity.json')
    selected, seen, coverage = [], set(), []
    sources = {}
    for arm in identity['launches']:
        if not arm['arm'].startswith('EVENT-'):
            continue
        d = OUT / 'development01/raw' / Path(arm['destination'].replace('\\', '/')).name / 'external/round106'
        ev = [json.loads(x) for x in (d / 'events.jsonl').read_text().splitlines()]
        cuts = list(csv.DictReader((d / 'lazy.csv').open(encoding='utf-8', newline='')))
        s = read(d / 'summary.json')
        by_event = {e['event']: e for e in ev}
        proof = {}
        for p in d.glob('certificate_*.json'):
            c = read(p)
            e = int(p.stem.split('_')[1])
            proof.setdefault((e, c['vehicle'], c['family']), []).append(p)
        tagged = {(k, tuple(q)) for e in ev for k, q in enumerate(e['operations'])}
        p=arm['panel']
        physical={(p['input_sha256'],p['Q_vector'][k],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],tuple(q))
                  for e in ev for k,q in enumerate(e['operations'])}
        assert len(tagged)==s['distinct_car_modes']
        coverage.append(dict(id=arm['id'], arm=arm['arm'], events=s['events'],
            complete_fleet_candidates=s['distinct_fleet_candidates'], distinct_Y=s['distinct_Y'],
            physical_parameter_keyed_car_modes=len(physical),
            vehicle_tagged_car_modes=len(tagged), repeat_events=s['repeat_events']))
        sources[(arm['id'], arm['arm'])] = (arm, d, ev, cuts, by_event, proof)

    def add(id, strategy, e, k, reason, family=None):
        arm, d, ev, cuts, by_event, proof = sources[(id, strategy)]
        point = by_event[e]
        q = point['operations'][k]
        p=arm['panel']
        key=(p['input_sha256'],p['Q_vector'][k],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],tuple(q))
        if key in seen:
            return False
        seen.add(key)
        paths = proof.get((e, k, family), []) if family else []
        submissions = [c for c in cuts if int(c['event']) == e and int(c['vehicle']) == k and (not family or c['family'] == family)]
        candidate = d / f'candidate_{e}.sol'
        selected.append(dict(id=id, arm=strategy, event=e, vehicle=k,
            source='current_formal_native_MIPSOL_noninitial' if not point['matches_start_fleet'] else 'current_formal_native_start_fleet',
            reason=reason, matches_start_fleet=point['matches_start_fleet'], repeat=point['repeat'],
            fleet_id=point['fleet_id'], inventory_id=point['inventory_id'], Y=point['Y'],
            operations=q, Q=arm['panel']['Q_vector'][k], T=arm['panel']['T_seconds'],
            h=arm['panel']['pickup_seconds']+arm['panel']['drop_seconds'],
            model_objective=point['model_objective'], Ftrue=point['Ftrue'],
            candidate=candidate.relative_to(ROOT).as_posix(), candidate_SHA=sha(candidate),
            proof_files=[dict(path=p.relative_to(ROOT).as_posix(), SHA=sha(p)) for p in sorted(paths)],
            actual_lazy=submissions, event_outcome=point['outcome'],
            next_event=next((x['event'] for x in ev if x['event']>e), None)))
        return True

    for id, family, limit in [('F2', 'B_THRESHOLD', 3), ('R98-C2', 'A_MST', 2)]:
        count = 0
        for c in sources[(id, 'EVENT-STRUCT')][3]:
            if c['family'] == family and add(id, 'EVENT-STRUCT', int(c['event']), int(c['vehicle']), 'naturally exposed strong structural conflict', family):
                count += 1
                if count == limit:
                    break
        assert count == limit
    for id, strategy, reason in [('F2','EVENT-STRUCT','native FULL fallback without A/B rejection'), ('R98-C2','EVENT-CORE','native semantic IIS/released-template core')]:
        for c in sources[(id,strategy)][3]:
            if c['family'] in ['FULL','CORE'] and add(id,strategy,int(c['event']),int(c['vehicle']),reason,c['family']):
                break
        else:
            raise AssertionError('no distinct fallback/core mode')
    arm,d,ev,cuts,by_event,proof = sources[('R98-C2','EVENT-STRUCT')]
    accept = list(csv.DictReader((d/'submission_acceptance.csv').open(encoding='utf-8',newline='')))
    e = int(next(r for r in accept if r['final_native_accepted']=='1')['event'])
    for k,q in enumerate(by_event[e]['operations']):
        if any(q) and add('R98-C2','EVENT-STRUCT',e,k,'new complete feasible fleet; exact-vector native acceptance'):
            selected[-1]['physical_witness'] = (d/'physical_ub_4.json').relative_to(ROOT).as_posix()
            selected[-1]['acceptance'] = accept
            break
    assert len(selected) == 8 and all(not r['matches_start_fleet'] for r in selected)
    record = dict(selection_recipe='First three distinct F2 threshold modes, first two distinct C2 A modes, first distinct F2 fallback, first distinct C2 CORE, first nonzero car of accepted new C2 fleet; physical keys deduplicated across strategies.',
        selected_modes=selected, coverage=coverage, independent_formal_inputs=2,
        historical_scope='R105 nine INF car modes came from three complete candidate sources, not nine independent instances; historical/replay records are not counted as formal new inputs.',
        terminology='Physical-parameter keys independently omit vehicle label when all parameters coincide; source summary distinct_car_modes and vehicle-tagged CSV retain it. Candidate counts are fleets, never independent instances.',
        selection_source_SHA=sha(__file__),
        Optimize_calls=0, IIS_calls=0)
    with args.output.open('x',encoding='utf-8') as f:
        json.dump(record,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(selected=len(selected),Optimize_calls=0,IIS_calls=0)))

if __name__=='__main__':
    main()
