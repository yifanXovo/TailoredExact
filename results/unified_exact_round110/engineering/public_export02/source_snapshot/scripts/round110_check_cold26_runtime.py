"""Measure a fresh current cache gate without launching the solver."""
from round110_common import *
import round110_cold26_resumed_campaign as resumed

if __name__=='__main__':
    from round100_idle import ensure_idle
    ensure_idle();label=sys.argv[1];tick=time.perf_counter();cache,meta=resumed.qualified_cache();elapsed=time.perf_counter()-tick
    assert set(cache)=={15,17,25,26} and cache[26]['U']>0. and cache[26]['L']==0. and not cache[26]['certificate']
    assert elapsed<15.,'actual cache admission does not fit conservative within-cap reserve'
    out=OUT/'campaign/reader_recovery'/label;out.mkdir(parents=True,exist_ok=False)
    write(out/'runtime_gate.json',dict(cache=cache,projection_bindings=meta,actual_cache_admission_seconds=elapsed,
        large_matrix_gate='all signed current raw/model/vector bytes rehashed; no matrix arithmetic',
        full_matrix_arithmetic_remains_offline=True,wrapper_SHA=sha(ROOT/'scripts/round110_cold26_resumed_campaign.py'),
        scoped_evidence_SHA=sha(ROOT/'scripts/round110_scoped_evidence.py'),cold_runtime_SHA=sha(ROOT/'scripts/round110_cold_runtime.py'),
        Optimize=0,native_environment=0))
    print(json.dumps(dict(actual_cache_admission_seconds=elapsed,Optimize=0,native_environment=0)),flush=True)
