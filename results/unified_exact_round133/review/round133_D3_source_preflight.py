"""Before old D3 native execution, check every exact registered source byte.

No source transformation is applied to execution or to a frozen identity.
A possible LF/CRLF match is diagnostic only and cannot grant admission.
"""
from pathlib import Path
import datetime, hashlib, json, subprocess, time
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round133'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def digest(raw):return hashlib.sha256(raw).hexdigest()
def sha(p):return digest(Path(p).read_bytes())
def main():
    tick=time.perf_counter();matrix_path=OUT/'plans/D3_matrix_frozen.json'
    assert sha(matrix_path)=='1f1839df95a8d2d62280aa4e4417177cd6d2829ec7618c2acdf3273893f88182'
    matrix=read(matrix_path);items={};positions=[]
    for group in matrix['groups']:
        launch=group['launch']
        if launch['version']=='candidate':continue
        identity_path=OUT/group['group']/'identity.json';assert sha(identity_path)==group['identity_SHA']
        identity=read(identity_path);assert identity['launches']==[launch]
        assert launch['method']=='S2' and launch['command'][launch['command'].index('--round127-mode')+1]=='ms2'
        assert identity['candidate_binary_sha256']=='2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c'
        assert sha(launch['command'][0])==identity['candidate_binary_sha256']
        assert not Path(launch['destination']).exists(),'Old D3 data visible before source preflight'
        position=dict(position=group['position'],role=launch['id'],seed=launch['seed'],identity_SHA=group['identity_SHA'],source_keys=[])
        for name,registered in identity['source_hashes'].items():
            key=identity['measured_source_commit']+':'+name
            if key not in items:
                raw=subprocess.check_output(['git','show',key],cwd=ROOT)
                transformed=raw.replace(b'\n',b'\r\n') if b'\r' not in raw else None
                items[key]=dict(key=key,source_commit=identity['measured_source_commit'],source_path=name,
                    registered_SHA=registered,Git_SHA=digest(raw),Git_bytes=len(raw),
                    exact_bytes_match=digest(raw)==registered,
                    LF_count=raw.count(b'\n'),CR_count=raw.count(b'\r'),
                    diagnostic_only_LF_to_CRLF_matches=bool(transformed is not None and digest(transformed)==registered),
                    transformed_diagnostic_SHA=digest(transformed) if transformed is not None else None,
                    transformed_diagnostic_bytes=len(transformed) if transformed is not None else None,
                    actual_transform_applied=False)
            assert items[key]['registered_SHA']==registered
            position['source_keys'].append(key)
        positions.append(position)
    assert len(positions)==4
    failures=[value for value in items.values() if not value['exact_bytes_match']]
    receipt=dict(schema='round133-independent-before-old-D3-source-byte-preflight-v1',
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='/root/reliability_review',
        matrix_SHA=sha(matrix_path),old_positions_checked=4,unique_source_keys=len(items),
        all_registered_Git_source_bytes_equal=not failures,source_records=list(items.values()),positions=positions,
        mismatch_count=len(failures),mismatches=failures,admission='NOT_GRANTED_BY_THIS_PREFLIGHT',
        no_implicit_source_transport_or_local_worktree_fallback=True,old_original_PE_identity_checked=True,
        native_Optimize=0,compilation=0,outer_seconds=time.perf_counter()-tick)
    target=OUT/'review/D3_old_source_preflight.json';assert not target.exists()
    target.write_text(json.dumps(receipt,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(exact_source_match=not failures,old_positions=4,unique_keys=len(items),mismatches=len(failures),
        possible_CRLF_only=sum(value['diagnostic_only_LF_to_CRLF_matches'] for value in failures),Optimize=0,seconds=time.perf_counter()-tick)))
if __name__=='__main__':main()
