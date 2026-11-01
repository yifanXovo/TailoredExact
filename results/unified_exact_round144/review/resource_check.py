"""Independent RB35 stage admission; bounded current bytes only, no solver."""
from pathlib import Path
import json, hashlib, time, datetime, subprocess
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round144'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    start=time.perf_counter();path=OUT/'resource_matrix.json';m=read(path);manifest=read(OUT/'candidate_manifest.json')
    old=read(OUT/'review/pilot_admission.json');report=read(OUT/'reports/full.json');cost=read(OUT/'cost_report.json')
    assert m['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')==old['manifest_SHA']
    assert sha(Path(manifest['production_PE']))==old['PE_SHA']==manifest['production_PE_SHA']
    assert m['batch']=='resource' and len(m['groups'])==2 and m['new_nominal_caps']==4800
    assert m['serial'] and m['threads']==1 and m['Seed_default']==0 and m['H_seed']==20260626 and m['all_own_H']
    commands=[];inputs=[]
    for g,method in zip(m['groups'],['OFF','RNP']):
        l=g['launch'];p=l['panel'];cmd=l['command'];identity_path=OUT/g['group']/'identity.json'
        assert l['id']=='R-B35-S-T2' and l['R144_method']==method and l['cap_seconds']==2400 and l['seed']==0
        assert (p['V'],p['M'],p['T_seconds'],p['Q_vector'],p['lambda'])==(35,3,7200,[20,25,30],.055125275219827186)
        assert sha(identity_path)==g['identity_SHA'];identity=read(identity_path)
        assert identity['candidate_binary_sha256']==old['PE_SHA'] and identity['measured_source_commit']==old['source_commit']
        assert identity['no_cross_arm_information'] and identity['candidate_manifest_SHA']==old['manifest_SHA']
        assert cmd[0]==manifest['production_PE'] and float(cmd[cmd.index('--lambda')+1])==p['lambda']
        for flag,value in [('--round144-projection','on' if method=='RNP' else 'off'),('--gurobi-seed','0'),('--threads','1'),('--mip-threads','1'),
            ('--process-wall-time-limit','2400'),('--time-limit','2394'),('--round127-mode','ms2'),('--T','7200')]:assert cmd[cmd.index(flag)+1]==value
        assert l['AM_threshold']==.08 and not Path(l['destination']).exists()
        assert all(flag not in cmd for flag in ['--round138-stock-rlt','--round140-counts','--round141-count-proof','--round142-count-products','--round143-rn'])
        input_path=Path(cmd[cmd.index('--input')+1]);input_path=input_path if input_path.is_absolute() else ROOT/input_path
        assert sha(input_path)==p['input_sha256'];inputs.append(p['input_sha256'])
        normalized=[x.replace(l['destination'],'DESTINATION') for x in cmd];normalized[normalized.index('--round144-projection')+1]='METHOD'
        commands.append(normalized)
    assert commands[0]==commands[1] and len(set(inputs))==1
    unchanged={}
    for p,digest in old['source_hashes'].items():
        if p.startswith(('src/','include/')):
            assert sha(ROOT/p)==digest==manifest['source_hashes'][p];unchanged[p]=digest
    for p,digest in m['helpers'].items():assert sha(ROOT/p)==digest
    assert subprocess.check_output(['git','diff','--','src','include','scripts/round118_call_logs.py'],cwd=ROOT)==b''
    primary=report['new_arms'];assert len(primary)==4 and report['all_entered_preserved'] and not report['pending']
    assert all(a['native_proof_qualified'] and a['performance_eligible'] and a['declared_calls']==a['returned_calls'] and a['PE_SHA']==old['PE_SHA'] for a in primary)
    assert cost['experiment']['remaining_G1_seconds']>m['new_nominal_caps']+240 and not cost['experiment']['unclosed']
    result=dict(decision='ACCEPT',matrix_SHA=sha(path),independent_nonimplementer_review=True,
        reviewer='/root/round144_independent_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope='Only R-B35-S-T2 OFF/RN-P full-window same-V5-PE Seed0 pair; K20 not entered by this gate',
        PE_SHA=old['PE_SHA'],source_commit=old['source_commit'],manifest_SHA=old['manifest_SHA'],
        same_pair_input_SHA=inputs[0],complete_primary_arms=4,budget_remaining_snapshot=cost['experiment']['remaining_G1_seconds'],
        reader_boundary_review=dict(decision='ACCEPT',reader_SHA=sha(ROOT/'scripts/round144_read.py'),
            source_not_reached='Allowed only with no producer source receipt, no RN/PC audits and no declared Native call; inherited complete reader still qualifies result',
            derived_disposition='Marked postverification, stored only in derived control audit; no invented producer source receipt',
            source_missing_with_any_call='Rejected',positive_source_path='Unchanged'),
        rationale='Qualified K35 primal/gap gain with moderate dual tradeoff and RX20 equal-objective faster proof leave no severe-stop or qualification blocker; important resource role is informative',
        conditions=['Serial Threads1, Seed0, separate own H and complete 2400-second windows for both entered roles',
            'No source-bound/control injection, no algorithm change and aggregate experiment ceiling 28800 seconds',
            'Keep all endpoints, failed qualifiers and complete postverification charges; decide later K20/bridges from these results'],
        unchanged_production_hashes=unchanged,evidence_hashes={p:sha(OUT/p) for p in ['reports/full.json','reports/same_PE_pairs.csv','cost_report.json','review/pilot_admission.json']},
        seconds=time.perf_counter()-start,Optimize=0,Native_load=0,compile=0)
    (OUT/'review/resource_admission.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['decision','matrix_SHA','independent_nonimplementer_review','same_pair_input_SHA','seconds','Optimize','Native_load','compile']}))
if __name__=='__main__':main()
