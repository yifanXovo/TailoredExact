"""Read-only independent check of both complete pre-result matrices.

Only pinned Git JSON metadata, small identity files and argument strings are
read. No old/native solution, model, Start or result is supplied to a run.
"""
from pathlib import Path, PureWindowsPath
import collections, datetime, hashlib, json, subprocess, time

ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round133'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git_blob(commit,path):return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
def arguments(command):
    result={};index=1
    while index<len(command):
        key=command[index];assert key.startswith('--') and key not in result,(key,'not a unique flag')
        index+=1;values=[]
        while index<len(command) and not command[index].startswith('--'):
            values.append(command[index]);index+=1
        result[key]=values
    return result

def main():
    tick=time.perf_counter();candidate=read(OUT/'candidate_manifest.json')
    assert sha(OUT/'candidate_manifest.json')=='101e8f75d2675d1f728ddd8aa4010d0b57821218e730a7b06207239af6a997b2'
    source_cache={};transports={};records=[];destinations=set();matrices={};helper_sets=[]
    for stage,count,cap in [('D1',14,15600),('D3',8,7200)]:
        path=OUT/'plans'/f'{stage}_matrix_frozen.json';matrix=read(path);matrices[stage]=sha(path)
        assert matrix['stage']==stage and matrix['full_arm_count']==count
        assert matrix['full_arm_cap_sum_seconds']==cap
        assert matrix['serial'] and matrix['own_H_and_Start'] and not matrix['cross_arm_information']
        assert sha(matrix['candidate_manifest_path'])==matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
        draft=read(matrix['source_draft_path']);assert sha(matrix['source_draft_path'])==matrix['source_draft_SHA']
        assert len(draft['arms'])==len(matrix['groups'])==count
        helper_sets.append(matrix['helpers'])
        for name,digest in matrix['helpers'].items():assert sha(ROOT/name)==digest,name
        for pos,(row,group) in enumerate(zip(draft['arms'],matrix['groups']),1):
            assert row['position']==group['position']==pos
            launch=group['launch'];identity_path=OUT/group['group']/'identity.json';identity=read(identity_path)
            assert sha(identity_path)==group['identity_SHA'] and identity['launches']==[launch]
            assert identity['stage']==stage and identity['no_cross_arm_information']
            assert identity['candidate_manifest_SHA']==matrix['candidate_manifest_SHA']
            binding=row['source_binding'];key=(binding['commit'],binding['freeze_path'])
            if key not in source_cache:source_cache[key]=git_blob(*key)
            raw=source_cache[key];raw_sha=hashlib.sha256(raw).hexdigest()
            if raw_sha==binding['freeze_SHA256']:transform='identity';transported=raw
            else:
                assert b'\r' not in raw
                transported=raw.replace(b'\n',b'\r\n')
                assert hashlib.sha256(transported).hexdigest()==binding['freeze_SHA256']
                assert json.loads(raw)==json.loads(transported)
                transform='pinned_Git_LF_to_registered_local_CRLF'
            original=json.loads(raw)[binding['plans_key']][binding['plan_index_zero_based']]
            old_launch=original['launches'][binding['launch_index_zero_based']]
            assert old_launch['command']==row['source_argv']==identity['source_frozen_argv']
            assert old_launch['destination']==row['source_destination']
            assert original['prereg']['common']==binding['source_prereg_common']
            common=dict(original['prereg']['common']);common['gurobi_seed']=row['seed']
            assert identity['prereg']['common']==common
            record=identity['source_manifest_transport_identity']
            assert record['Git_SHA256']==raw_sha and record['registered_manifest_SHA256']==binding['freeze_SHA256']
            assert record['transform']==transform
            transports[key]=dict(commit=key[0],path=key[1],Git_SHA256=raw_sha,Git_bytes=len(raw),
                registered_SHA256=binding['freeze_SHA256'],registered_bytes=len(transported),
                transform=transform,complete_JSON_semantics_equal=True)
            assert launch['id']==row['role'] and launch['method']==row['method'] and launch['seed']==row['seed']
            assert launch['cap_seconds']==row['cap_seconds'] and launch['hard_stop_seconds']==row['hard_stop_seconds']
            assert old_launch['cap_seconds']==launch['cap_seconds'],'original full cap changed'
            destination=launch['destination'];assert destination not in destinations
            destinations.add(destination)
            assert not Path(destination).exists(),'qualification/native result visible before both matrices were independently checked'
            assert Path(destination).is_relative_to(OUT/'campaign')
            expected=[arg.replace(row['destination'],destination) for arg in row['argv']]
            candidate_arm=row['version']=='candidate'
            pe=candidate['research_PE' if row['method'] in ('S2R','GEOM') else 'production_PE'] if candidate_arm else 'E:\\codes\\ExactEBRP-work\\build-cache\\round130\\ExactEBRP.exe'
            digest=candidate['research_PE_SHA' if row['method'] in ('S2R','GEOM') else 'production_PE_SHA'] if candidate_arm else '2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c'
            expected[0]=pe
            for flag in ('--round24-executable-sha256','--round24-manifest-executable-sha256'):
                if flag in expected:expected[expected.index(flag)+1]=digest
            assert launch['command']==expected,'actual frozen argv differs from exact registered adaptation'
            assert identity['candidate_binary_sha256']==digest
            old_flags,new_flags=arguments(old_launch['command']),arguments(launch['command'])
            assert set(old_flags)==set(new_flags),'registered flag set changed'
            changes=[]
            for flag,old_value in old_flags.items():
                current=new_flags[flag]
                if current==old_value:continue
                if flag=='--input':assert current==[launch['panel']['input_path']]
                elif flag in ('--round24-executable-sha256','--round24-manifest-executable-sha256'):
                    assert current==[digest]
                else:
                    adapted=[v.replace(old_launch['destination'],destination) for v in old_value]
                    # The exact frozen argv is checked above. Original/new
                    # output paths may spell the same Windows separator as
                    # slash or backslash; no nonpath value is normalized.
                    assert len(current)==len(adapted) and all(
                        len(a)>2 and a[1]==':' and len(b)>2 and b[1]==':' and
                        PureWindowsPath(a)==PureWindowsPath(b)
                        for a,b in zip(current,adapted)),(stage,pos,flag,old_value,current,'unapproved argv change')
                changes.append(dict(flag=flag,original=old_value,current=current))
            assert new_flags['--gurobi-seed']==[str(row['seed'])]
            assert new_flags['--threads']==new_flags['--mip-threads']==['1']
            assert float(new_flags['--process-wall-time-limit'][0])==launch['cap_seconds']
            assert sha(launch['panel']['input_path'])==launch['panel']['input_sha256']
            assert launch['expected_configuration']==row['expected_configuration']
            if row['method'] in ('S2R','GEOM'):
                assert new_flags['--round127-mode']==['s2-root']
                assert new_flags['--round132-expression']==['geom' if row['method']=='GEOM' else 'off']
            elif row['method']=='S2':assert new_flags['--round127-mode']==['ms2']
            elif row['method']=='PS':assert '--round112-ens-start-compact' in new_flags and '--round127-mode' not in new_flags
            records.append(dict(stage=stage,position=pos,role=row['role'],method=row['method'],seed=row['seed'],
                version=row['version'],cap=launch['cap_seconds'],actual_argv_exact=True,source_argv_exact=True,
                source_common_exact=True,allowed_changes=changes,transport=transform,group_identity_SHA=group['identity_SHA']))
        assert sum(g['launch']['cap_seconds'] for g in matrix['groups'])==cap
    assert helper_sets[0]==helper_sets[1],'D1/D3 helpers differ'
    role_counts=collections.Counter((r['stage'],r['role'],r['method'],r['seed'],r['version']) for r in records)
    assert len(role_counts)==22 and set(role_counts.values())=={1}
    bridge=[r for r in records if r['stage']=='D3']
    for offset in range(0,8,2):
        left,right=bridge[offset:offset+2]
        assert (left['role'],left['seed'])==(right['role'],right['seed'])
        versions=['candidate' if r['version']=='candidate' else 'old' for r in (left,right)]
        role_index=('SC-C15-B','SC-B20-S').index(left['role'])
        expected=['old','candidate'] if (role_index+left['seed'])%2==0 else ['candidate','old']
        assert versions==expected,'D3 original/candidate pair order differs from prospective role/Seed counterbalance'
    output=dict(schema='round133-independent-pre-result-matrix-check-v1',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        matrices=matrices,candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),helper_hashes=helper_sets[0],
        full_positions=22,D1_positions=14,D1_cap_sum=15600,D2_limit_within_D=2400,D3_positions=8,D3_cap_sum=7200,
        all_source_launches_and_common_configuration_match_pinned_Git=True,
        all_actual_argv_are_exact_registered_identity_path_adaptations=True,
        no_physical_parameter_or_native_resource_policy_changed=True,
        D3_complete_pair_order='prospective role-index plus Seed parity; two original-first and two candidate-first pairs',
        no_formal_raw_destination_or_result_visible=True,transports=list(transports.values()),positions=records,
        Optimize=0,native_module_imports=0,compilation=0,outer_seconds=time.perf_counter()-tick)
    target=OUT/'review/frozen_matrix_identity_checks.json';assert not target.exists()
    target.write_text(json.dumps(output,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PASS_PRE_RESULT_MATRIX_IDENTITIES',positions=22,transports=len(transports),
        Optimize=0,seconds=time.perf_counter()-tick)))

if __name__=='__main__':main()
