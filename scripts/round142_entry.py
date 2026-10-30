"""Freeze a separate research profile and check argv without Optimize."""
from round142_common import *
import copy

def profile():
    manifest=read(OUT/'candidate_manifest.json')
    p=copy.deepcopy(read(ROOT/'config/gi_tbc_count_disjunction_round141.json'))
    p.update(algorithm='GI-TBC + R141 D1 + selected count-source shared-factor consistency (research only)',
        source_commit=manifest['source_commit'],research_head=manifest['source_commit'],
        default_executable=manifest['production_PE'],verified_PE_SHA256=manifest['production_PE_SHA'],round=142,
        source_manifest='results/unified_exact_round142/candidate_manifest.json',
        count_products='selected',CP_placement='count_sources_only')
    p['argv']+=['--round142-count-products','selected']
    p['authority']=dict(schema='round142-research-entry-v1',candidate_manifest=p['source_manifest'],candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'))
    write(ROOT/'config/gi_tbc_count_products_round142.json',p)

def check():
    import paper_s2 as stable
    p=read(ROOT/'config/gi_tbc_count_products_round142.json');facts=[]
    parent=read(ROOT/'config/gi_tbc_count_disjunction_round141.json')
    for products in ['off','selected','all']:
        for mode in ['d0','d1']:
            command=[PYTHON,'-B',ROOT/'scripts/paper_s2_count_products.py','--input',ROOT/'results/unified_exact_round132/inputs/K-20-S.txt',
                '--out-dir',WORK/f'temp/round142/dry-{products}-{mode}','--T','5400','--lambda','0.15','--cap','1200','--seed','0','--products',products,'--mode',mode,'--json']
            launch=json.loads(subprocess.check_output(list(map(str,command)),cwd=ROOT,env=environment()))
            assert not Path(launch['output_directory']).exists() and launch['dry_run']
            vector=launch['command']
            assert vector[vector.index('--round142-count-products')+1]==products
            assert vector[vector.index('--round141-count-proof')+1]==mode
            # Apart from the new switch, the original frozen research argv
            # remains complete. This check starts no producer or Native model.
            normalized=stable.normalize(vector,p);del normalized[-2:]
            expected=list(parent['argv']);expected[-1]=mode
            assert normalized==expected
            facts.append(dict(products=products,mode=mode,command=vector))
    preserved={}
    for name in ['scripts/paper_s2.py','scripts/paper_s2_stock_rlt.py','scripts/paper_s2_threshold_count.py',
                 'scripts/paper_s2_count_disjunction.py','config/gi_tbc_round137.json',
                 'config/gi_tbc_stock_rlt_round138.json','config/gi_tbc_count_disjunction_round141.json']:
        if not (ROOT/name).exists():continue
        old=git('show',BASE+':'+name)
        now=(ROOT/name).read_bytes()
        assert now==old or now.replace(b'\r\n',b'\n')==old
        preserved[name]=dict(local_SHA=sha(ROOT/name),Git_SHA=hashlib.sha256(old).hexdigest(),semantics_unchanged=True)
    write(OUT/'entry_check.json',dict(PASS=True,Optimize=0,Native_load=0,profile_SHA=sha(ROOT/'config/gi_tbc_count_products_round142.json'),cases=facts,preserved=preserved))

if __name__=='__main__':globals()[sys.argv[1]]()
