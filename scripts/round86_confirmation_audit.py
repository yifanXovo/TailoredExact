"""Verify prospective freeze and all retained input identities, without regeneration."""
import json
import subprocess
import time
from pathlib import Path
import generate_citibike443_regional_v1 as citi
from round83_qualify import ROOT,sha,write
from round86_generate import structural_record

OUT=ROOT/'results/unified_exact_round86'
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    started=time.perf_counter();campaign=OUT/'campaign'
    assert not (campaign/'active_run.lock').exists()
    assert not (campaign/'confirmation_audit.json').exists()
    assert read(campaign/'audit.json')['all_checks_passed']
    assert read(campaign/'mechanism_audit.json')['all_checks_passed']
    prereg=read(OUT/'preregistration.json');generation=read(OUT/'generation.json')
    protocol=read(OUT/'protocol.json');identity=read(campaign/'identity.json')
    assert generation['generated_count']==4 and generation['screened_or_rejected_count']==0
    assert protocol['order']==['F1','F2','F5','F6']
    assert len(prereg['roles'])==4 and prereg['planned_runs']==12
    assert prereg['maximum_process_seconds']==protocol['maximum_process_seconds']==22860
    freeze=generation['freeze_commit'];rows=[]
    binding=dict(generation['generators'])
    binding.update({'results/unified_exact_round86/preregistration.json':generation['preregistration_sha256'],
                    'results/unified_exact_round86/plan.md':generation['plan_sha256']})
    import hashlib
    for name,digest in binding.items():
        data=subprocess.check_output(['git','show',freeze+':'+name.replace(chr(92),'/')],cwd=ROOT)
        assert sha(ROOT/name)==digest,name
        if name.replace(chr(92),'/')=='scripts/generate_citibike443_regional_v1.py':
            assert data.replace(b'\r\n',b'\n')==(ROOT/name).read_bytes().replace(b'\r\n',b'\n'),name
        else:
            assert hashlib.sha256(data).hexdigest()==digest,name
    assert prereg['base']==read(OUT/'base_publication.json')['head_sha']
    assert identity['preregistration_sha256']==sha(OUT/'preregistration.json')
    assert identity['generation_sha256']==sha(OUT/'generation.json')
    assert identity['source_commit']==prereg['candidate_source']
    for role,panel,record in zip(prereg['roles'],protocol['panel'],generation['structures']):
        assert all(panel[k]==v for k,v in role.items())
        assert sha(ROOT/panel['instance_path'])==panel['input_sha256']==generation['input_sha256'][role['id']]
        parsed=citi.parse_instance_mirror(ROOT/panel['instance_path'])
        assert (parsed['V'],parsed['M'],parsed['Q'])==(role['V'],role['M'],[role['Q']]*role['M'])
        assert structural_record(role,parsed,citi)==record
        if role['id'] in ['F2','F5','F6']:
            assert record['shortage']>0 and record['input_only_penalty_bound']['value']>0
        matching=[l for l in identity['launches'] if l['panel']['id']==role['id']]
        assert [l['arm'] for l in matching]==['P-GRB','ENS-C','K1-R']
        assert all(l['panel']==panel and l['cap']==role['cap'] for l in matching)
        rows.append(dict(id=role['id'],input_sha256=panel['input_sha256'],cap=role['cap'],
            zero_analytically_excluded=record['zero_analytically_excluded'],
            input_only_penalty_bound=record['input_only_penalty_bound']))
    for source in generation['old_selection_sources']:
        assert sha(ROOT/source['path'])==source['sha256']
    output=dict(all_checks_passed=True,preregistration_commit=freeze,base=prereg['base'],
        roles=rows,generated_roles_retained=4,unallocated_proposal_roles=['F3','F4'],
        matched_full_runs=12,original_parameters_unchanged=True,optimizer_calls=0,
        script_sha256=sha(__file__),generation_sha256=sha(OUT/'generation.json'),
        wall_seconds=time.perf_counter()-started,
        scope='Prospective identity and structural audit, not a performance acceptance or a proof of statistical independence. Related CitiBike geography and artificial synthetic structures remain explicit; input-only bounds are not algorithm information.')
    write(campaign/'confirmation_audit.json',output);print(json.dumps(output,indent=2))


if __name__=='__main__':main()
