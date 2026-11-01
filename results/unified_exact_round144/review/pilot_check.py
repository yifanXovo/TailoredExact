"""Bounded independent full-test admission from already-completed evidence.

Only stdlib arithmetic/bytes are read. No solver module, Optimize or compile.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
import json, csv, hashlib, re, time, datetime, subprocess
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round144'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def named_rows(p,prefix):
    result=[]
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if ':' not in line:continue
        name,body=line.strip().split(':',1)
        if not name.startswith(prefix):continue
        match=re.search(r'\s(<=|>=|=)\s+([-+0-9.eE]+)\s*$',body);assert match,line
        ts=body[:match.start()].split();terms={};i=0
        while i<len(ts):
            sign=1
            if ts[i] in ('+','-'):sign=-1 if ts[i]=='-' else 1;i+=1
            value=sign*float(ts[i]);key=ts[i+1];i+=2
            assert key not in terms
            if value:terms[key]=value
        result.append(dict(name=name,sense=match[1],rhs=float(match[2]),terms=terms))
    return result
def main():
    started=time.perf_counter()
    manifest_path=OUT/'candidate_manifest.json';manifest=read(manifest_path);matrix_path=OUT/'pilot_matrix.json';matrix=read(matrix_path)
    expected_pe='180126ae1ecf7db892c3fbb92faa73b517d19029e9824f62cd922e0d9e277d7b'
    assert manifest['source_commit']=='0b5858544a671722142c8450db9b88c09c9b1c72'
    assert manifest['production_PE_SHA']==expected_pe==sha(Path(manifest['production_PE']))
    assert matrix['candidate_manifest_SHA']==sha(manifest_path)
    assert (matrix['Seed_default'],matrix['H_seed'],matrix['threads'],matrix['serial'],matrix['all_own_H'])==(0,20260626,1,True,True)
    assert len(matrix['groups'])==4 and matrix['new_nominal_caps']==7200
    expected=[('K-35-U','OFF',2400),('K-35-U','RNP',2400),('R-X20-S-T1','OFF',1200),('R-X20-S-T1','RNP',1200)]
    for g,(role,method,cap) in zip(matrix['groups'],expected):
        l=g['launch'];cmd=l['command'];identity_path=OUT/g['group']/'identity.json'
        assert (l['id'],l['R144_method'],l['cap_seconds'],l['seed'])==(role,method,cap,0)
        assert g['identity_SHA']==sha(identity_path);identity=read(identity_path)
        assert identity['candidate_binary_sha256']==expected_pe and identity['no_cross_arm_information']
        assert identity['measured_source_commit']==manifest['source_commit']
        assert cmd[0]==manifest['production_PE'] and cmd[cmd.index('--round144-projection')+1]==('on' if method=='RNP' else 'off')
        for flag,val in [('--gurobi-seed','0'),('--threads','1'),('--mip-threads','1'),('--process-wall-time-limit',str(cap)),('--time-limit',str(cap-6)),('--round127-mode','ms2')]:
            assert cmd[cmd.index(flag)+1]==val
        assert l['AM_threshold']==.08
        assert all(flag not in cmd for flag in ['--round138-stock-rlt','--round140-counts','--round141-count-proof','--round142-count-products','--round143-rn'])
        assert not Path(l['destination']).exists(),'full producer already entered before independent admission'
    relevant=['include/Round144Research.hpp','include/ObjectiveResourceCompression.hpp','src/ObjectiveResourceCompression.cpp',
        'src/PaperExternalGiniTree.cpp','src/GurobiBaseline.cpp','src/main.cpp']
    for p in relevant:assert sha(ROOT/p)==manifest['source_hashes'][p],p
    for p,digest in matrix['helpers'].items():assert sha(ROOT/p)==digest,p
    unchanged=subprocess.check_output(['git','diff','--','scripts/round118_call_logs.py'],cwd=ROOT)
    assert unchanged==b''
    d=OUT/'qualification03/runs/001/raw/R144_qualification03_001_R-X20-S-T1_S0_RNP'
    endpoint=read(d/'round135_endpoint.json');audit=read(d/'audit.json');control=read(d/'round144_control_audit.json')
    closeout=read(d/'verification_closeout.json');source=read(d/'external/round144_source.json');projection=read(d/'external/round144_projection.json')
    assert endpoint['PE_SHA']==expected_pe and endpoint['source_commit']==manifest['source_commit']
    assert endpoint['H_complete'] and endpoint['implementation_qualified'] and endpoint['evidence_complete']
    assert endpoint['certificate'] and endpoint['native_proof_qualified'] and endpoint['declared_calls']==endpoint['returned_calls']==5
    assert closeout['necessary_verification_complete'] and closeout['no_new_solution_or_certificate_backfilled']
    assert audit['passed'] and audit['raw_tree_lifecycle_complete'] and not audit['source_rejections']
    assert control['PASS'] and source['qualified'] and source['source_solves']==1 and source['PC_emitted']
    assert not source['formal_control_from_source'] and source['formal_RN_columns']==0
    assert source==control['source'] and projection['source_SHA']==source['source_SHA']
    sourcepath=d/'external/models/round144_RN_source.lp';assert sha(sourcepath)==source['source_SHA']
    rn=named_rows(sourcepath,'rn_');assert len(rn)==708
    pi={r['name']:r['Pi'] for r in projection['constraints']};cols={v['name']:v for v in projection['variables']}
    a=defaultdict(F);b=F(0)
    for r in rn:
        p=F(pi[r['name']])
        if r['sense']=='>=':p=max(p,F(0))
        elif r['sense']=='<=':p=min(p,F(0))
        else:assert r['sense']=='='
        b+=p*F(r['rhs'])
        for k,v in r['terms'].items():a[k]+=p*F(v)
    sigma=F(0)
    for k in list(a):
        if k.startswith('rn_'):
            c=cols[k];assert max(abs(c['LB']),abs(c['UB']))<1e100
            sigma+=max(a[k]*F(c['LB']),a[k]*F(c['UB']));del a[k]
    actual=projection['row'];needed=-b+sigma
    for k in set(a)|set(actual['terms']):
        delta=F(actual['terms'].get(k,0.))+a.get(k,F(0));c=cols[k]
        needed+=max(delta*F(c['LB']),delta*F(c['UB']))
    slack=F(actual['rhs'])-needed;assert slack>=0 and actual['sense']=='<'
    assert all(k=='G' or k.startswith('state_') for k in actual['terms'])
    ledger=rows(d/'external/paper_optimize_ledger.csv');statuses=rows(d/'external/lp_status_ledger.csv')
    source_ledgers=[r for r in ledger if r['model_sha256']==source['source_SHA']]
    assert len(source_ledgers)==1 and source_ledgers[0]['solve_kind']=='LP' and int(source_ledgers[0]['integer_domain_restored'])==1
    assert len(ledger)==5 and len(statuses)==3
    assert all(p['call']!=source['source_call'] for p in audit['qualified_cover']['scoped_proofs'])
    assert {p['call'] for p in audit['qualified_cover']['scoped_proofs']}=={2,3,4,5}
    assert audit['Start_checks'] and all(v['per_column_restored_type_checked'] and v['ordered_native_columns_checked'] for v in audit['Start_checks'])
    for fact in control['native_compact_audits']:assert fact['PASS'] and fact['RN_columns']==fact['RN_rows']==0 and fact['PC_rows']==1
    modelpaths={sha(p):p for p in (d/'external/models').glob('*.lp')}
    for fact in control['models']:
        if fact['kind']!='formal_compact':continue
        text=modelpaths[fact['model_SHA']].read_text();assert not re.search(r'\brn_',text)
        pc=named_rows(modelpaths[fact['model_SHA']],'r144_PC');assert len(pc)==1
        assert pc[0]['terms']==actual['terms'] and pc[0]['rhs']==actual['rhs'] and pc[0]['sense']=='<='
    child=read(OUT/'LP/R-X20-S-T1_actual_high_child/result.json')
    assert child['PASS'] and child['root_PC_descendant_loss']==0 and child['new_LP_Optimize']==1
    # This is admission to measurements, not promotion or a performance claim.
    bindings={p:sha(ROOT/p) for p in relevant+['scripts/round144_read.py','scripts/round118_call_logs.py','scripts/round144_campaign.py']}
    paths=['qualification_native_transport.json','qualification_native_writer.json','math/fixtures.json',
        'qualification03/runs/001/raw/R144_qualification03_001_R-X20-S-T1_S0_RNP/round135_endpoint.json',
        'qualification03/runs/001/raw/R144_qualification03_001_R-X20-S-T1_S0_RNP/round144_control_audit.json',
        'qualification03/runs/001/raw/R144_qualification03_001_R-X20-S-T1_S0_RNP/verification_closeout.json',
        'LP/R-X20-S-T1_actual_high_child/result.json']
    result=dict(decision='ACCEPT',matrix_SHA=sha(matrix_path),independent_nonimplementer_review=True,
        reviewer='/root/round144_independent_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_commit=manifest['source_commit'],PE_SHA=expected_pe,manifest_SHA=sha(manifest_path),
        scope='Four pre-frozen full-window same-PE Seed0 positions only; no promotion or guaranteed speed benefit',
        exact_online_PC_validity_margin=str(slack),source_excluded_only_from_control_proof_reconstruction=True,
        all_five_raw_Native_calls_preserved_qualified_and_charged=True,formal_proof_call_ids=[2,3,4,5],
        complete_Start_and_H=True,formal_RN_columns=0,conditions=[
            'Preserve failed qualifiers and their actual source/PE/reader identities; no retroactive qualification',
            'Serial single-thread timing; full 2400/1200-second producer windows for entered roles; 28800-second aggregate experimental ceiling',
            'Own H per method, once-root current source, no historical point/bound injection, no source bound as formal control',
            'Report all entered endpoints and postverification costs; later expansion remains result-dependent'],
        source_hashes=bindings,evidence_hashes={p:sha(OUT/p) for p in paths},
        seconds=time.perf_counter()-started,Optimize=0,Native_load=0,compile=0)
    (OUT/'review/pilot_admission.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['decision','matrix_SHA','independent_nonimplementer_review','exact_online_PC_validity_margin','seconds','Optimize','Native_load','compile']}))
if __name__=='__main__':main()
