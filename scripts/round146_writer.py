"""Directed arithmetic, canonical transport, complete Start and zero-domain QA."""
import collections
import round108_reader as parser
from round143_qualify import actual_spec,point_residual
from round146_math import compiled
from round146_build import BUILD,COMPILER,SYSTEM
from round146_common import *
configure()
def build():
    configure();m=read(OUT/'candidate_manifest.json');pe=BUILD/'Round146Writer.exe'
    assert metered('compile_writer','build',[COMPILER,*m['flags'],ROOT/'scripts/round146_writer.cpp',*m['objects'],m['archive']['path'],*SYSTEM,'-o',pe],timeout=180)==0
    write(OUT/'writer_driver.json',dict(PE=str(pe),PE_SHA=sha(pe),source_SHA=sha(ROOT/'scripts/round146_writer.cpp')))
    assert metered('writer_cpp','diagnostic',[pe,OUT/'qualification/writer',ROOT/'results/unified_exact_round132/inputs/K-35-U.txt'],30,60)==0
def native():
    configure()
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA;root=OUT/'qualification/writer';facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for tag,bm,b in [('positive',2,3),('fixed',3,3),('zero_lower',0,3),('K35',251,326)]:
            folder=root/tag;off=parser.lp_model(folder/'off.lp');on=parser.lp_model(folder/'on.lp')
            block=compiled(actual_spec(off,bm,b),OUT/'qualification/actual_rows'/f'{tag}.json');rows=block['rows']
            for key in ('order','bounds','types','objective'):assert off[key]==on[key],(tag,key)
            wanted=collections.Counter((tuple(sorted(r['terms'].items())),'>=',0.) for r in rows)
            assert collections.Counter(on['rows'])==collections.Counter(off['rows'])+wanted
            if tag=='K35':assert off==parser.lp_model(ROOT/'results/unified_exact_round143/inherited/roots/K-35-U/inherited/original.lp')
            else:
                for name in ['physical_start','nonminimal_epigraph']:
                    point=read(folder/(name+'.json'));assert set(point)==set(on['order']);res=point_residual(on,point);assert max(res.values())<=1e-6,(tag,name,res)
                    facts.append(dict(tag=tag,point=name,residual=res,complete=True))
            pairs=[('off','on',rows)]
            if tag=='positive':
                child=parser.lp_model(folder/'child_off.lp');inherited=[dict(r,terms={k:v for k,v in r['terms'].items() if k in child['order']}) for r in rows]
                assert set(child['order'])<set(off['order']);pairs.append(('child_off','child_on',inherited))
            for before,after,expected in pairs:
                old=parser.lp_model(folder/(before+'.lp'));new=parser.lp_model(folder/(after+'.lp'))
                assert collections.Counter(new['rows'])==collections.Counter(old['rows'])+collections.Counter((tuple(sorted(r['terms'].items())),'>=',0.) for r in expected)
                with gp.read(str(folder/(after+'.lp')),env=env) as model:
                    assert model.NumVars==len(old['order']) and {v.VarName:v.VType for v in model.getVars()}==old['types']
                    for v in model.getVars():assert (v.LB,v.UB)==old['bounds'][v.VarName]
                    for r in expected:
                        c=model.getConstrByName(r['name']);e=model.getRow(c)
                        assert c.Sense=='>' and c.RHS==0 and {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==r['terms']
                    facts.append(dict(tag=tag,model=after,GD_rows=len(expected),GD_nonzeros=sum(len(r['terms']) for r in expected),Native_readback=True,columns_unchanged=True))
    write(OUT/'qualification_native_writer.json',dict(PASS=True,Optimize=0,Native=binding(),facts=facts,actual_off_K35_equals_historical_BASE=True))
    print('PASS actual writer, full/nonminimal Start, subset inheritance, unchanged OFF and Native readback')
def run():
    configure();assert metered('writer_native','diagnostic',[LP_PYTHON,'-B',__file__,'native'],30,60)==0
if __name__=='__main__':globals()[sys.argv[1]]()
