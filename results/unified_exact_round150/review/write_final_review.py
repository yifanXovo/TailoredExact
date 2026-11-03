"""Persist the independent science verdict without changing implementation/evidence."""
from pathlib import Path
import datetime,hashlib,json,time
OUT=Path(__file__).resolve().parents[1]
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
tick=time.perf_counter();check=read(OUT/'review/independent_final_check.json')
assert check['PASS'] and check['independent_nonimplementer_review']
decision=read(OUT/'candidate_decision.json');cpf=read(OUT/'CPF_decision.json')
assert decision['D']['decision']=='RETAIN_LIMITED_UNIFORM_PAPER_CANDIDATE_RESTRICT_CLAIMS'
assert decision['D']['stable_B_primary'] and not decision['D']['recommend_broad_replacement']
assert not decision['D']['role_based_dispatch'] and not decision['D']['strengthen_claim_beyond_R147_selection']
assert cpf['qualification_layer']=='three complete matched numerical LP increments beyond PF'
value=dict(PASS=True,decision='ACCEPT_SCIENTIFIC_CLOSEOUT_AND_PROCEED_TO_BOUNDED_DELIVERY',
    independent_nonimplementer_review=True,reviewer='/root/independent_review',
    UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope='Finite Round150 science, frozen controls, actual complete calls/physical evidence, CPF matrix and numerical qualification, decision and paper scope',
    Native_load=0,Optimize=0,compile=0,baseline_reoptimization=0,
    bindings=check['bindings'],independent_raw_check='review/independent_final_check.json',
    independent_raw_check_SHA=sha(OUT/'review/independent_final_check.json'),
    document_SHA_at_scientific_review={name:sha(OUT/name) for name in ['mathematical_analysis.md','LP_report.md','manuscript.tex','final_report.md','RESUME.md']},
    document_hash_boundary='Only subsequent mechanical fee totals, commit pins and actual publication status may change these delivery documents without changing the reviewed scientific content.',
    findings=[
      'Both additional roles are correctly known/exposed R137 configurations outside GD selection; N-B35-S is not the different R-B35-S-T2 physical input/objective.',
      'All four frozen complete argv vectors preserve the original lambda=.15, physical input/T/cap, H seed20260626, AM geometry, M-B/VD-P and pair-only semantics; paired PE/DLL/source and Seed0/Threads1 are real identities.',
      'All 19 actual complete Native calls return exactly once (4/5/5/5), with actual model SHA/Seed/Threads binding, first-call-SHA GD context and actual 0/2-row groups; no fixed-count assumption or missing-model heuristic-completion requirement was imposed.',
      'Producer seals, required file hashes and immutable verification closeout component hashes match. The accepted physical/R134 chain, complete H and Start checks are retained, and all controls have PF/Shared-S/STOCK/AP disabled.',
      'An independent standard-library reconstruction verifies final physical U and all112 committed improving trajectory points from fleet routes, loads, station inventory, Euclidean travel/1.5, station handling and depot return unloading. All fleets satisfy the original horizons.',
      'N-C20-U B/D have the same positive U and both accepted certificates; D takes43.73383 percent more T_cert and the small supported-L difference is disclosed. Both N-B35-S arms remain open: D loses2.24371 percent U, gains.16464 percent L and has about15.46345 percent larger signed gap.',
      'The two new roles show no complete U or certificate-speed superiority outside the selection roles. Retaining only a limited uniform discussion candidate while restricting the claim is proportionate to these ordinary losses and the genuine R147 K35/RB35 selected-role gains; it does not justify broad replacement, default change or role dispatch.',
      'The severe double-open reference is independently recomputed as false and is not treated as a sufficient adoption rule. Open caps, verification-cost differences and different-quality final-incumbent arrival times are not called convergence speedups.',
      'CPF signs, already weighted omega, exact Fraction leave-one-out, outward beta transport, tiny-row omission, conditional rather than global beta use, integer/nonminimal completion validity and the one-station hull scope are correct. The AP example retains t and explicitly does not prove a full BRP ordering.',
      'The three actual CPF matrices retain all PF semantics and all variables free, as independently checked before Optimize and bound by unchanged model hashes now. There are exactly3 new LPs, no repeated baseline, fourth domain, extra quality Optimize or full CPF arm.',
      'Independent offline primal, row/bound residual, dual sign, stationarity, finite-bound reduced-cost contribution and dual objective recomputation confirms all three positive numerical CPF-minus-PF increments. New numerical primal-dual gaps are tiny; this is not an exact rational optimum certificate.',
      'K35 old PF primal-dual difference about.000619046 and DualVio about8.92e-7 remain explicit. The new CPF numerical dual exceeds the old saved PF primal; the positive finite numerical screen does not require another Optimize. The old scalar-only difference -3.225086737e-7 is retained as consistent with scalar redundancy/old quality, not a CPF increment.',
      'R149 K35/K20 early-incumbent positives, RB35 adverse U and all-open/no-new-certificate boundary, stronger STOCK/TC+STOCK/RN endpoints with version/scope caveats, non-pure R140 Seed1 identity and corrected R52 false/correct-retain anchors are preserved.',
      'The independent current ledger sum is5543.6389105000735s before this final-review charge, below14400s, with no unclosed receipts or new build. Nested Runtime/Work and old costs are not added, and no unused clarification capacity is charged.',
      'Original stable/research entry/config, production source, PE/DLL and protected user-dirty file bytes match the recorded start identities. All new work stays under ExactEBRP-work.',
      'The two tasks close independently. CPF earns future unified complete-cost evaluation only; the concrete future D+PF versus D+PF+CPF original-RB35 own-H comparison is not entered in this round.'
    ],
    material_scientific_issues=[],
    earlier_prose_followup='Resolved: concrete R149 timing/positive/adverse evidence and stronger historical endpoints/negative anchors now appear in final_report.md and manuscript.tex.',
    review_helper_correction=dict(description='The independent physical helper initially omitted returned-load depot drop handling. It was corrected and the same immutable evidence rechecked; no production data or solver run changed.',
        initial_helper_SHA='c781ff05e8431ab31f9f5cd8d1ca41df09b49bbb74d6f94477fab0d19bbb11ae',
        corrected_helper_SHA='8b5cee3bfba1611806bbf055dda378b635d84cb6caf8be7c1f49cc12e1d5ac82',
        initial_process_outer_seconds=1.3961074,corrected_process_outer_seconds=1.3362286,both_charged_once=True),
    timing=dict(known_final_review_process_outer_seconds_before_receipt_write=5.4732802,
        missing_initial_parallel_document_read_process='One companion lightweight read from the first parallel batch has no separately retained exact process timer; disclose rather than invent precision.',
        conservative_extra_seconds_for_that_read=1.,manual_qualification_reading_independently_timed=False,
        no_nested_script_time_added=True,final_fee_reconciliation_pending=True),
    public_delivery_verified=False,PR_creation_or_Draft_readback_verified=False,public_recovery_verified=False,cleanup_verified=False,
    remaining_delivery=[
      'Add this actual necessary review cost once, disclose unmetered qualification allowance and mechanically refresh final fee totals.',
      'Build only the finite incremental carriers and fixed member/hash index; preserve all entered raw evidence.',
      'Normal scientific/delivery commit and push; create/read back English Draft PR against the verified actual base. No merge, force push or old branch deletion.',
      'One bounded public byte/member recovery and current-round-only retention/cleanup record. Zero deletion is acceptable.'
    ],
    no_more_Optimize_or_compile_justified=True)
value['receipt_write_script_seconds']=time.perf_counter()-tick
(OUT/'review/final_scientific_review.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(PASS=True,science_accepted=True,public_delivery_verified=False,seconds=time.perf_counter()-tick)))
