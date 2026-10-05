"""Identity freeze without launching optimization. Refuses overwrite."""
from round103_common import *
if __name__=='__main__':
    from round100_idle import ensure_idle
    ensure_idle();label=sys.argv[1]
    result=dict(stage=label,source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_bindings=bindings(),PE_sha256=sha(BUILD/'ExactEBRP.exe'),oracle_PE_sha256=sha(BUILD/'Round103HullOracle.exe'),
        reference_PE_sha256=sha(BUILD/'Round65ReferenceBuild.exe'),DLL_sha256=sha('D:/gurobi1302/win64/bin/gurobi130.dll'),
        runners={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'scripts').glob('round103*.py')},
        rules=dict(domain='R102 actual conservative predicate; base domain; all stations',
            model_stage='one self-paid standard LP and hull pass per qualified new canonical terminal/partial-target MIP',
            scale='physical per-coordinate widths; zero widths checked; member tolerance1e-8',
            quantization='nearest dyadic bits=max(30,ceil(log2(4*total_width/tolerance))), at most48',
            emit='at most one row per car, exact power2 rescaling, signed violation>10*unchanged official FeasibilityTol',
            stop='member/verified row/UNKNOWN or structural4096 columns; only whole-algorithm global deadline',
            cache='full original SHA/leaf/scope/row signature/gamma/cutoff/input SHA/mode',
            default='ENS-C unchanged; R103 off; no M-B/R101/R102 stacking'),
        complete_performance_starts_before_freeze=0 if label=='production_freeze' else None)
    write(OUT/(label+'.json'),result);print(json.dumps(dict(stage=label,source_head=result['source_head'],PE=result['PE_sha256'])))
