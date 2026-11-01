"""Finite actual canonical PC writer, complete Start, scope and off checks."""
import collections
import round108_reader as parser
from round143_qualify import point_residual
from round145_build import COMPILER,BUILD,SYSTEM
from round145_common import *
configure()
def build():
    configure();m=read(OUT/'candidate_manifest.json');pe=BUILD/'Round145Writer.exe'
    assert metered('compile_writer','build',[COMPILER,*m['flags'],ROOT/'scripts/round145_writer.cpp',*m['objects'],m['archive']['path'],*SYSTEM,'-o',pe],timeout=180)==0
    write(OUT/'qualification_writer_build.json',dict(PE=str(pe),PE_SHA=sha(pe),source_SHA=sha(ROOT/'scripts/round145_writer.cpp')))
    row=read(OUT/'compact/K-35-U/compiled_projection.json')['row'];p=OUT/'qualification/K35_row.txt';p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w') as f:
        f.write(f'{row["rhs"]:.17g} {len(row["terms"])}\n')
        for k,v in row['terms'].items():f.write(f'{k} {v:.17g}\n')
    assert metered('writer_cpp','diagnostic',[pe,OUT/'qualification/writer',ROOT/'results/unified_exact_round132/inputs/K-35-U.txt',p],30,60)==0

def native():
    configure()
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA;root=OUT/'qualification/writer';facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for a,b in [('tiny_base','tiny_compact'),('tiny_child_base','tiny_child_compact'),('K35_off','K35_compact')]:
            old=parser.lp_model(root/(a+'.lp'));new=parser.lp_model(root/(b+'.lp'))
            assert all(old[k]==new[k] for k in ['order','bounds','types','objective'])
            difference=collections.Counter(new['rows'])-collections.Counter(old['rows'])
            assert sum(difference.values())==1 and collections.Counter(new['rows'])==collections.Counter(old['rows'])+difference
            assert not any(k.startswith('rn_') for k in new['order'])
            if a=='tiny_base':
                p=read(root/'tiny_start.json');check=point_residual(new,p);assert set(p)==set(new['order']) and max(check.values())<=1e-6
            else:check=None
            if a=='K35_off':assert old==parser.lp_model(ROOT/'results/unified_exact_round143/inherited/roots/K-35-U/inherited/original.lp')
            with gp.read(str(root/(b+'.lp')),env=env) as model:
                c=model.getConstrByName('r145_PC');e=model.getRow(c)
                actual=(tuple(sorted((e.getVar(i).VarName,e.getCoeff(i)) for i in range(e.size()))),{'<':'<=','>':'>=','=':'='}[c.Sense],c.RHS)
                assert actual==next(iter(difference))
                assert {v.VarName:v.VType for v in model.getVars()}==new['types']
                for v in model.getVars():assert (v.LB,v.UB)==new['bounds'][v.VarName]
            facts.append(dict(base=a,compact=b,all_terms_RHS_types_bounds_read_back=True,columns=len(new['order']),PC_rows=1,RN_columns=0,complete_Start_residual=check))
    write(OUT/'qualification_native_writer.json',dict(PASS=True,Optimize=0,Native=binding(),facts=facts,actual_off_K35_equals_historical_BASE=True))
    print('PASS actual compact writer / Y / complete physical Start / narrower child / scope rejection / unchanged OFF')

def run():
    configure();assert metered('writer_native','diagnostic',[LP_PYTHON,'-B',__file__,'native'],30,60)==0
if __name__=='__main__':globals()[sys.argv[1]]()
