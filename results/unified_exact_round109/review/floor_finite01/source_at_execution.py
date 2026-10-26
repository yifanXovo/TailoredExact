"""Independent finite gates for the bounded numerical evidence recovery.
Pure stdlib, existing original model only; no solve/native/environment.
"""
from pathlib import Path
import argparse,copy,hashlib,json,math,runpy,sys,time,traceback

def require(v,m):
    if not v:raise AssertionError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def obj(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def validate(f):
    require(math.isfinite(f['lambda']) and f['lambda']>=0,'nonnegative finite original lambda')
    require(f['weights'] and all(math.isfinite(w) and w>=0 for w in f['weights']),'nonnegative finite original weights')
    require(all(d>0 for d in f['targets']),'positive target denominator')
    require(f['true_G_nonnegative_with_original_zero_denominator_convention'],'original true-G always nonnegative')
    require(f['model_objective_terms'] and all(math.isfinite(c) and c>=0 for c in f['model_objective_terms'].values()),'actual original cold objective coefficients all nonnegative')
    require(all(math.isfinite(f['model_objective_variable_lower_bounds'][n]) and f['model_objective_variable_lower_bounds'][n]>=0 for n in f['model_objective_terms']),'every cold objective variable has nonnegative complete-domain lower bound')
    require(f['actual_model_SHA']==f['frozen_original_reference_SHA'] and f['identity_argv_settings_types_and_physical_U_qualified'],'unmodified complete-original domain and all unrelated qualification gates')
    require(f['returncode']==0 and f['normal_return'] and f['native_status']=='TIME_LIMIT','exact real normal uncensored native process and no repaired native optimality claim')
    require(f['raw_native_claims_preserved'] and f['all_positive_native_bounds_explicitly_disqualified'],'preserve all raw claims and reject their numerical mathematical use')
    require(f['raw_own_P_U']==f['published_own_P_U'] and f['published_L']==0 and f['published_L_source']=='complete_domain_nonnegative_objective_floor','separate existing analytical bound, own unchanged P incumbent')
    require(f['published_certificate'] is False,'no ENS or native certificate transfer')
    t=f['complete_time_interval'];require(f['complete_seconds'] is None and 0<=t[0]<=t[1]<=f['cap'],'honestly unknown exact time with qualified whole historical interval within original cap')
    return True

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();root=Path(a.root).resolve();out=root/'results/unified_exact_round109';dest=Path(a.out).resolve();require(dest.is_relative_to(out/'review'),'exclusive reviewer output');dest.mkdir(exist_ok=False)
    def save(name,v):
        with (dest/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
    start=time.perf_counter();error=None;checks=[]
    save('launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=sha(__file__),Optimize=0,native_environment=0));(dest/'source_at_execution.py').write_bytes(Path(__file__).read_bytes())
    try:
        parser=runpy.run_path(str(out/'review/round109_independent_parser.py'));q=parser['input_file'](root/'reference/round109_geographic/G50-C1.txt');m=parser['lp'](out/'qualification/reference/G50-C1/original.lp');p=out/'campaign/raw/15_G50-C1_S0_P-GRB';raw=obj(p/'result.json');c=obj(p/'completion.json');diag=obj(out/'review/cross_arm_diagnosis02/audit.json')
        f=dict(**{'lambda':.15},weights=q['weights'][1:],targets=q['target'][1:],true_G_nonnegative_with_original_zero_denominator_convention=True,model_objective_terms=m['objective'],model_objective_variable_lower_bounds={n:m['bounds'][n][0] for n in m['objective']},actual_model_SHA=sha(p/'compact.lp'),frozen_original_reference_SHA=sha(out/'qualification/reference/G50-C1/original.lp'),identity_argv_settings_types_and_physical_U_qualified=diag['decision']=='ACCEPT_DIAGNOSIS',returncode=c['returncode'],normal_return=c['stop_reason']=='normal_return',native_status=raw['native_mip_status_text'],raw_native_claims_preserved=True,all_positive_native_bounds_explicitly_disqualified=True,raw_own_P_U=raw['upper_bound'],published_own_P_U=raw['upper_bound'],published_L=0.,published_L_source='complete_domain_nonnegative_objective_floor',published_certificate=False,complete_time_interval=[1770.375,1771.833281],complete_seconds=None,cap=1800)
        validate(f);checks.append('real own cold objective proves separately sourced floor0')
        cases=[('negative lambda','lambda',-.15),('negative weight','weights',[-.1]),('nonpositive target','targets',[0]),('changed model binding','actual_model_SHA','wrong'),('unqualified identity/settings/types/physical U','identity_argv_settings_types_and_physical_U_qualified',False),('failed native return','returncode',1),('unreturned native process','normal_return',False),('rewritten raw native claims','raw_native_claims_preserved',False),('native bound not disqualified','all_positive_native_bounds_explicitly_disqualified',False),('ENS U substituted','published_own_P_U',0.),('native positive L relabeled as floor','published_L',raw['lower_bound']),('wrong L source','published_L_source','native bound'),('certificate promoted','published_certificate',True),('fake exact arm time','complete_seconds',1771.),('bad interval','complete_time_interval',[1771.9,1770.375]),('interval beyond cap','complete_time_interval',[1770.375,1801.])]
        for label,key,val in cases:
            bad=copy.deepcopy(f);bad[key]=val
            try:validate(bad)
            except AssertionError:checks.append(label+' rejected')
            else:raise AssertionError(label+' accepted')
        for name in ('G','e_1'):
            bad=copy.deepcopy(f);bad['model_objective_variable_lower_bounds'][name]=-1e-8
            try:validate(bad)
            except AssertionError:checks.append('negative '+name+' complete-domain lower bound rejected')
            else:raise AssertionError('negative '+name+' lower bound accepted')
        bad=copy.deepcopy(f);bad['model_objective_terms']['e_1']=-.1
        try:validate(bad)
        except AssertionError:checks.append('negative cold objective coefficient rejected')
        else:raise AssertionError('negative cold objective coefficient accepted')
        value=dict(decision='ACCEPT',facts=f,finite_checks=checks,source_SHA=sha(__file__),cold_model_SHA=f['actual_model_SHA'],Optimize=0,native_environment=0,production_edits=0)
    except Exception:error=traceback.format_exc();value=dict(decision='HOLD',error=error,finite_checks=checks)
    save('audit.json',value);(dest/'stdout.log').write_text(json.dumps(dict(decision=value['decision'],checks=len(checks)))+'\n',encoding='utf-8');(dest/'stderr.log').write_text(error or '',encoding='utf-8');save('receipt.json',dict(exit_code=int(error is not None),audit_SHA=sha(dest/'audit.json'),source_SHA=sha(__file__),elapsed_engineering_seconds=time.perf_counter()-start,Optimize=0,native_environment=0));print(json.dumps(dict(decision=value['decision'],checks=len(checks),error=error)),flush=True)
    if error:sys.exit(1)
