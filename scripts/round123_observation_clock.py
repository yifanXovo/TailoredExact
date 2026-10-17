"""Post-seal source-clock alignment only; never a production/stop mechanism."""
from pathlib import Path
import hashlib,json

GUARD_SECONDS=1.0
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def alignment(d):
    d=Path(d);native=read(d/'native_end_receipt.json');completion=read(d/'completion.json')
    producer=read(d/'producer_receipt.json');marker=read(d/'process_start_marker.json')
    # wrapper_wall excludes prelaunch, and is relative to the observation
    # marker. Subtracting fully_observed_end_to_end would subtract prelaunch
    # a second time and understate the source origin by that amount.
    mono_origin=native['complete_seconds_until_native_end']-completion['wrapper_wall_seconds']
    origins=[mono_origin,marker['unix_seconds']-producer['t0_unix']]
    sample_path=d/'samples.jsonl'
    samples=[json.loads(s) for s in sample_path.read_text(encoding='utf-8-sig').splitlines() if s] if sample_path.exists() else []
    origins += [s['sampled_unix']-producer['t0_unix']-s['process_seconds'] for s in samples]
    wall_qpc_difference=(producer['t_produce_unix']-producer['t0_unix'])-producer['T_produce']
    spread=max(origins)-min(origins)
    valid=spread<=GUARD_SECONDS and abs(wall_qpc_difference)<=GUARD_SECONDS
    return dict(valid=valid,offset_upper_seconds=max([0.]+origins)+GUARD_SECONDS if valid else None,
        fixed_presentation_guard_seconds=GUARD_SECONDS,observed_origin_range_seconds=[min(origins),max(origins)],
        observed_origin_spread_seconds=spread,wall_vs_producer_QPC_difference_seconds=wall_qpc_difference,
        process_marker_SHA_source='process_start_marker.json',source_clock='supervisor GetTickCount64 elapsed seconds',
        process_marker_SHA=hashlib.sha256((d/'process_start_marker.json').read_bytes()).hexdigest(),
        destination_clock='arm producer QPC elapsed seconds',calibration_samples=len(samples),
        conversion='max(native-end minus wrapper-wall, source wall-origin pairs)+fixed1s; cap only time upper by actual producer seal',
        numerical_solver_tolerances_and_T_produce_T_verify_unchanged=True,
        no_claim_of_exact_internal_discovery_time_or_unobserved_clock_drift=True)

def upper(raw_seconds,align,producer_seconds):
    if not align['valid']:return producer_seconds # only the sealed availability is then known
    return min(producer_seconds,raw_seconds+align['offset_upper_seconds'])
