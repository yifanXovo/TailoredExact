"""Final bounded-delivery checks. No optimizers are started."""
import csv
import json
from round61_research import ROOT, OUT, RAW, entries, panel, sha, write

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    log=entries();assert sum(e['charged'] for e in log)<=72
    assert sum(e['kind']=='native-micro' for e in log)<=4
    assert not (OUT/'active_run.lock').exists(),'experiment still running'
    for e in log:
        c=read(ROOT/e['destination']/'completion.json')
        assert c['returncode']==0 and not c['watchdog'] and c['within_budget'],e
    for p in panel().values():assert sha(ROOT/p['instance_path'])==p['input_sha256']
    for i in ['D6','D7']:
        ds=[RAW/'fixed120_corrected'/i/m for m in ['off','archive','submit']]
        assert len({sha(d/'canonical_model.lp') for d in ds})==1
        assert len({read(d/'launch.json')['executable_sha256'] for d in ds})==1
        assert read(ds[-1]/'result.json')['round60_candidates_submitted']>0
    for i in ['D3','D4','D7']:
        ds=[RAW/'long600'/i/m for m in ['off','submit']]
        assert len({sha(d/'canonical_model.lp') for d in ds})==1
        assert len({read(d/'launch.json')['executable_sha256'] for d in ds})==1
        assert all(read(d/'launch.json')['cap_seconds']==600 for d in ds)
    for i,stage in [('C1','confirmation300'),('C2','confirmation600')]:
        launches=[read(RAW/stage/i/m/'launch.json') for m in ['off','submit']]
        assert len({l['executable_sha256'] for l in launches})==1
        assert all(l['scope']=='full_original_problem' for l in launches)
        assert len({sha(RAW/stage/i/m/'external/initial_decomposition_ledger.csv') for m in ['off','submit']})==1
    k1=read(RAW/'k1_corrected/C2/submit/result.json')
    assert len({read(RAW/'k1_corrected/C2'/m/'launch.json')['executable_sha256'] for m in ['off','submit']})==1
    assert k1['round60_candidates_submitted']>0,'K1 has no effective candidate submission'
    assert k1['external_gini_tree_optimize_count']>=3
    assert k1['external_gini_tree_lp_optimize_count']>=1
    assert k1['external_gini_tree_partial_mip_optimize_count']+k1['external_gini_tree_terminal_mip_optimize_count']>=1
    expected={r['instance_id']:r['expected_gurobi_model_fingerprint'] for r in read(ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/pgrb_expected_fingerprints.json')['entries']}
    reference=read(RAW/'references/C2/P-GRB/result.json')
    assert reference['gurobi_model_fingerprint']==expected[panel()['C2']['scenario_id']]
    for i in ['D3','D4','D6']:
        for m in ['lp','mip']:assert (RAW/'oracle_history'/i/m/'oracle_result.json').exists()
    for m in ['lp','mip']:assert (RAW/'oracle_prefix/D3'/m/'oracle_result.json').exists()
    conflict=read(OUT/'conflict_result.json')
    assert 1<=len(conflict['attempts'])<=3
    assert conflict['static_trial_decision']!='requires cost assessment; never submit automatically'
    cheap=read(OUT/'cheap_inventory_time_diagnostics.json')
    charged_cheap=[e for e in log if e['stage']=='cheap_proof_batch']
    assert len(charged_cheap)==1 and charged_cheap[0]['charged'] and charged_cheap[0]['solver_calls_planned']==0
    d4=next(r for r in cheap if r['id']=='D4')
    assert len(d4['clique'])==d4['M']+1
    assert all(p['duration_lower']>d4['T']+1e-5*max(1,d4['T']) for p in d4['pair_proofs'])
    assert d4['point_checks'] and not any(p['violated'] for p in d4['point_checks'])
    assert d4['static_trial']=='not_run_nonviolated_on_recorded_points'
    witnesses=rows('witness_verification.csv')
    for w in witnesses:
        if not w['stage'].startswith('oracle'):assert w['original_T_feasible']=='True'
    for i in ['D3','D4','D6','D7']:
        final=[r for r in rows('candidate_quality.csv') if r['id']==i and r['stage']=='quality_final']
        assert len(final)==5 and all(r.get('first_nonempty_seconds') for r in final)
    text=(OUT/'final_report.md').read_text(encoding='utf-8')
    assert '<!-- FINAL_' not in text,'final narrative still incomplete'
    write(OUT/'completion_audit.json',dict(status='passed',charged_launches=sum(e['charged'] for e in log),
        native_micro=sum(e['kind']=='native-micro' for e in log),
        independently_recomputed_witnesses=len(witnesses),
        required_long_pairs=['D3 fixed 600','D7 fixed 600','C2 full 600'],D4_protection='fixed 600',
        confirmations=['C1','C2'],K1_effective_submissions=k1['round60_candidates_submitted'],
        original_PGRB_fingerprint=reference['gurobi_model_fingerprint'],
        diagnostic_proofs_excluded_from_original_problem_certificates=True))
    print('Round61 completion audit passed')

if __name__=='__main__':main()
