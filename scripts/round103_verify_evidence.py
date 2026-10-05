"""Execution-team final full-model, support and physical-row replay.

Zero Optimize; support repricing is counted and charged. This repeats the
production oracle, not an independent alternative recurrence or native B&B.
"""
import sys,json,hashlib
from fractions import Fraction as F
from round103_points import typed_matrix
from round103_hull import Oracle,exact
from round103_common import *
from round103_native_audit import audit
from round100_idle import ensure_idle
from round100_gurobi_runtime import gp,binding
from round98_projection_vector_audit import check
from round70_affinity import inherited_core
import analyze_round61 as physical

def main(label,campaigns):
    ensure_idle();physical.ROOT=ROOT;directory=OUT/'diagnostics'/label;directory.mkdir(exist_ok=False)
    tick=time.perf_counter();witnesses={};sources={};rows=[];audits=[]
    for name in campaigns:
        q=read(OUT/name/'identity.json');done=[json.loads(s) for s in (OUT/name/'summary.jsonl').read_text().splitlines()]
        assert len(done)==len(q['launches']) and all(x['audit_passed'] for x in done)
        for launch in q['launches']:
            panel=launch['panel'];folder=Path(launch['destination']);h=panel['input_sha256']
            for o in read(folder/'observations.json'):
                if o['payload']['kind']!='witness':continue
                w=o['payload'];v=physical.physical(panel,w);assert v['original_T_feasible']
                key=json.dumps(w['routes'],sort_keys=True)
                witnesses.setdefault(h,{})[key]=w['routes']
            if not launch['arm'].startswith('H-'):continue
            audits.append(dict(campaign=name,number=launch['number'],**audit(folder)))
            for p in (folder/'external/native_logs').glob('*.round103.summary.json'):
                s=read(p)
                if s['cache_hit']:continue
                prefix=str(p).removesuffix('.summary.json');c=read(prefix+'.contract.json')
                assert c['input_sha256']==h and sha(c['source_path'])==s['source_sha256']
                key=(h,c['source_sha256'],s['canonical_sha256'],s['mode'])
                sources.setdefault(key,dict(panel=panel,contract=c,summary=s,point=prefix+'.point.json'))
                rows.extend((key,row) for row in read(prefix+'.rows.json')['rows'])
    recomputed=set();records=[];matrix_reads=0;successful_reads=0;DP_calls=0;physical_checks=0
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding()
        def read_model(path):
            nonlocal matrix_reads,successful_reads
            matrix_reads+=1
            with (directory/'model_reads.jsonl').open('a') as f:
                f.write(json.dumps(dict(event='begin',call=matrix_reads,path=str(path)))+'\n')
            result=gp.read(str(path),env=engine);successful_reads+=1
            with (directory/'model_reads.jsonl').open('a') as f:
                f.write(json.dumps(dict(event='return',call=matrix_reads,path=str(path),success=True))+'\n')
            return result
        for number,(key,entry) in enumerate(sources.items(),1):
            h,source_sha,canonical_sha,mode=key;c=entry['contract'];s=entry['summary'];d=directory/f'source_{number:03d}';d.mkdir()
            with read_model(c['source_path']) as original:
                original_rows=original.NumConstrs;typed_matrix(original,d/'matrix.txt')
                if s['root_optimal']:
                    point=dict(read(entry['point'])['variables']);residual=check(original,point)
                    assert residual['maximum_absolute_residual']<=1e-6,residual
                else:residual=None
                oracle=Oracle(entry['panel'],d/'matrix.txt',d)
                try:
                    assert oracle.contract==c['column_contract']
                    these=list({json.dumps([row['coefficients'],row['rhs']],sort_keys=True):row
                        for rowkey,row in rows if rowkey==key}.values())
                    for row in these:
                        proof=row['proofs'][0];signature=(h,json.dumps(oracle.contract['resource'],sort_keys=True),proof['vehicle'],json.dumps(proof['weights']))
                        if signature not in recomputed:
                            result=oracle.support(proof['vehicle'],proof['weights']);assert result['upper']==proof['upper']
                            recomputed.add(signature)
                        for routes in witnesses[h].values():
                            operations={r['vehicle']:{(o['station'] if isinstance(o,dict) else o[0]):
                                ((o['pickup'],o['drop']) if isinstance(o,dict) else (o[1],o[2])) for o in r['operations']} for r in routes}
                            values={}
                            for k in range(entry['panel']['M']):
                                for i in range(1,entry['panel']['V']+1):
                                    p,dq=operations.get(k,{}).get(i,(0,0));values.update({f'p_{k}_{i}':p,f'd_{k}_{i}':dq,f'z_{k}_{i}':int(p+dq>0)})
                            activity=sum((exact(a)*values[n] for n,a in row['coefficients']),F(0))
                            assert activity<=exact(row['rhs']);physical_checks+=1
                    if s['mode']=='submit' and these:
                        with read_model(s['canonical_path']) as enriched:
                            oldvars=original.getVars();newvars=enriched.getVars()
                            assert len(oldvars)==len(newvars)
                            assert original.ModelSense==enriched.ModelSense and original.ObjCon==enriched.ObjCon
                            for a,b in zip(oldvars,newvars):assert (a.VarName,a.VType,a.LB,a.UB,a.Obj)==(b.VarName,b.VType,b.LB,b.UB,b.Obj)
                            def coefficients(model,row):
                                expr=model.getRow(row);return {expr.getVar(j).VarName:exact(expr.getCoeff(j)) for j in range(expr.size())}
                            oldrows=original.getConstrs();newrows=enriched.getConstrs()
                            newer={r.ConstrName:r for r in newrows};oldnames={r.ConstrName for r in oldrows}
                            assert len(newer)==len(newrows) and len(oldnames)==len(oldrows)
                            for r in oldrows:
                                z=newer[r.ConstrName];assert (r.Sense,r.RHS)==(z.Sense,z.RHS) and coefficients(original,r)==coefficients(enriched,z)
                            extras=[r for r in newrows if r.ConstrName not in oldnames]
                            assert len(extras)==len(these)
                            for row in these:
                                matches=[r for r in extras if coefficients(enriched,r)=={n:exact(a) for n,a in row['coefficients']}]
                                assert len(matches)==1 and matches[0].Sense=='<' and exact(matches[0].RHS)==exact(row['rhs'])
                finally:DP_calls+=oracle.calls;oracle.close()
            records.append(dict(input_sha256=h,source_sha256=source_sha,source_rows=original_rows,
                source_path=c['source_path'],canonical_sha256=s['canonical_sha256'],rows=len(these),full_point_residual=residual))
    write(directory/'summary.json',dict(passed=True,Optimize_calls=0,DP_calls=DP_calls,model_read_attempts=matrix_reads,
        successful_model_reads=successful_reads,
        distinct_repriced_supports=len(recomputed),saved_rows=len(rows),physical_row_witness_checks=physical_checks,
        unique_physical_witnesses={h:len(w) for h,w in witnesses.items()},native_audits=audits,records=records,
        runtime=runtime,affinity=affinity,outer_seconds=time.perf_counter()-tick,script_sha256=sha(__file__),
        scope='Execution-team repeated production DP and exact binary-rational row/combination checks, numeric full old-matrix point residuals and exact old/new model data preservation. No Optimize, independent alternative pricing or native B&B.'))
    print(json.dumps(dict(passed=True,Optimize_calls=0,DP_calls=DP_calls,model_reads=matrix_reads,rows=len(rows),physical_checks=physical_checks)))

if __name__=='__main__':main(sys.argv[1],sys.argv[2:])
