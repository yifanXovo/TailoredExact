"""Reconcile closed scientific evidence before the manual final judgment.

No Optimize, producer, compiler, publication or cleanup. This pass does not
declare the study complete and does not replace the independent arithmetic
readers. Run once under an outer fee after all serial experiments close.
"""
from round155_common import *
from round155_price_certificate import qualified_phase
from fractions import Fraction as F


def run(label='final_evidence_readback_v1'):
    from round100_idle import ensure_idle
    configure();ensure_idle()
    account=budget();own=os.environ['ROUND140_METERED_PARENT_LABEL']
    assert [r['label'] for r in account['unclosed']]==[own]
    assert account['G1_seconds']+account['unclosed'][0]['reservation']<=172800
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    references={}

    def ref(path):
        path=Path(path);references[path.relative_to(ROOT).as_posix()]=sha(path)
        return read(path)

    def fee(name,success=True):
        path=OUT/'fees'/name/'receipt.json';receipt=ref(path)
        assert receipt['exit_observed'] and receipt['G1_seconds']>=0
        if success:
            assert receipt['exit_code']==0 and not receipt['timeout'] and not receipt['supervisor_failure']
        return receipt

    def qualification(name):
        result=ref(OUT/'qualification'/name/'result.json');fee(name)
        assert result['PASS'] and result['Optimize']==0
        return result

    for name,terminal in [('remaining_capacity_queue_v3','REMAINING_RESEARCH_AND_RAW_READBACK_COMPLETE_FINAL_JUDGMENT_REQUIRED'),
                          ('nc_stalled_continuation_v1','CONTINUATION_AND_READBACK_COMPLETE_FINAL_JUDGMENT_REQUIRED')]:
        queue=ref(OUT/'infra'/name/'status.json')
        assert queue['decision']==terminal
        owner=ref(OUT/'infra'/name/'started.json')
        birth=meter.process_birth(owner['pid'])
        assert not birth or birth['creation_filetime']!=owner['creation_filetime']
        for row in queue['completed']:
            receipt=fee(row['label'])
            assert receipt['G1_seconds']==row['G1_seconds']
            assert sha(OUT/'fees'/row['label']/'receipt.json')==row['receipt_SHA']
    binding=ref(OUT/'review/remaining_readback_bindings.json')
    assert binding['decision']=='ACCEPT_ACTUAL_LEVEL_PRICES_SELECTORS_AND_SUPPORTS'
    assert binding['price_corrections_SHA']==sha(OUT/'review/native_price_corrections.json')
    phases={};minimum_coverage={}
    for name in ['matched_readback_v1','K35_basic_checkpoint_readback_v1',
                 'K35_level_v2_readback_v2','NC20_level_v2_readback_v1',
                 'K35_remaining_deep_readback_v1','NC20_remaining_deep_readback_v1',
                 'NC20_stalled_continuation_readback_v1']:
        result=qualification(name)
        for row in result['phases']:
            path=Path(row['result']);assert sha(path)==row['SHA256']
            qualified,current=qualified_phase(path)
            # Earlier unchanged audits predate the explicit qualified pointer.
            assert row.get('qualified_result_SHA',row['SHA256'])==sha(qualified)
            assert row['lower']==current['lower'] and row['upper']==current['upper']
            assert path.parent.name not in phases
            phases[path.parent.name]=dict(result=str(path),SHA256=sha(path),qualified_result_SHA=sha(qualified),audit=name)
            minimum_coverage[path.parent.name]=dict(directions=len(row['steps']),
                independently_recomputed_full_current_minima=sum(v['all_current_column_minimum'] for v in row['steps']),
                scope=result['minimum_scope'])
    initial=qualification('K35_level_initial_readback_v3')
    path=OUT/'coupled/K-35-U_feasible_level_deep_v1/result.json'
    assert initial['result_SHA']==sha(path) and initial['warm']['qualified'] and initial['candidate'] is None
    assert not read(path)['records']
    phases[path.parent.name]=dict(result=str(path),SHA256=sha(path),audit='K35_level_initial_readback_v3')
    actual={p.parent.name for p in (OUT/'coupled').glob('*/result.json')}
    assert set(phases)==actual and len(actual)==11
    for item in phases.values():
        result=read(item['result'])
        short={'K-35-U':'K35','N-C20-U':'NC20'}[result['role']]
        fee(short+'_'+result['label'])
    for short in ['K35','NC20']:
        selected=qualification(short+'_level_v2_selector_readback_v1')
        assert selected['all_accepted_candidate_CQ_and_current_column_minima_replayed']
        assert not selected['resolved_levels']
    replays={}
    for name in ['support_readback_v1','K35_basic_support_readback_v1',
                 'K35_level_support_readback_v1','NC20_level_support_readback_v1',
                 'K35_remaining_support_readback_v1','NC20_remaining_support_readback_v1',
                 'NC20_stalled_continuation_support_readback_v1']:
        result=qualification(name)
        for row in result['replays']:
            path=Path(row['result']);assert sha(path)==row['SHA256']
            assert row['all_original_variables_free'] and row['exactly_original_Q_plus_declared_supports']
            assert row['LP_primal_not_used_as_full_hull_upper']
            replays[path.parent.name]=dict(result=str(path),SHA256=sha(path),audit=name)
    assert set(replays)=={p.parent.name for p in (OUT/'support_LP').glob('*/result.json')}
    usage=qualification('column_usage_readback_v1')
    assert {v['phase'] for v in usage['phases']}==actual
    for row in usage['phases']:
        assert row['result_SHA']==phases[row['phase']]['SHA256']
        assert row['all_usage_marginals_and_cumulative_metadata_reconciled']
    assert usage['no_reconstruction_of_unrecorded_intermediate_primal_points']
    # The first continuation revisited the same price function after the
    # refreshed master changed C_Q/tau. Preserve the earlier undecided record;
    # a later true stock can now refute that older target, without treating
    # these sequential calls as a same-effort performance comparison.
    old_dir=ref(OUT/'coupled/N-C20-U_bounded_remaining_v1/iter000044/direction.json')
    new_dir=ref(OUT/'coupled/N-C20-U_first_stalled_continuation_v1/iter000000/direction.json')
    assert old_dir['scope']==new_dir['scope'] and old_dir['d_exact']==new_dir['d_exact']
    assert old_dir['beta']==new_dir['beta'] and old_dir['a_K_exact']==new_dir['a_K_exact']
    old_phase=ref(OUT/'coupled/N-C20-U_bounded_remaining_v1/result.json')
    new_price=ref(OUT/'coupled/N-C20-U_first_stalled_continuation_v1/iter000000/pricing/result.json')
    old_pool={tuple(Y) for Y in old_phase['columns']}
    later_stocks=[dict(Y=v['Y'],price_exact=v['price_exact']) for v in new_price['stocks']
                  if tuple(v['Y']) not in old_pool and F(v['price_exact'])<F(old_dir['tau_exact'])]
    assert later_stocks and old_phase['decision']=='undecided_price_no_new_column'
    revisit=dict(same_exact_beta_potentials_and_aK=True,old_target_exact=old_dir['tau_exact'],
        new_target_exact=new_dir['tau_exact'],same_exact_Q_correction=old_dir['C_Q_exact']==new_dir['C_Q_exact'],
        older_target_refuted_by_later_audited_new_stocks=later_stocks,
        old_raw_undecided_endpoint_preserved=True,sequential_calls_not_a_matched_performance_contrast=True)
    panel=ref(OUT/'panel_completion.json');matrix=ref(OUT/'confirmation_matrix.json')
    assert panel['decision']=='ALL_SIX_FROZEN_ARMS_VERIFIED'
    assert panel['matrix_SHA']==sha(OUT/'confirmation_matrix.json')
    assert {v['position'] for v in panel['accepted_arms']}==set(range(1,7))
    for arm in panel['accepted_arms']:
        fee(arm['fee_label']);assert sha(OUT/'fees'/arm['fee_label']/'receipt.json')==arm['receipt_SHA']
        group=next(v for v in matrix['groups'] if v['position']==arm['position'])
        destination=Path(group['launch']['destination'])
        assert sha(destination/'round154_endpoint.json')==arm['endpoint_SHA']
        assert sha(destination/'verification_closeout.json')==arm['closeout_SHA']
    complete=ref(OUT/'reports/complete_arms.json');pairs=ref(OUT/'reports/complete_pairs.json')
    assert not complete['missing_positions'] and len(complete['arms'])==6
    assert not pairs['missing_positions'] and len(pairs['pairs'])==3
    checkpoints=ref(OUT/'reports/common_checkpoints.json')
    assert len(checkpoints['rows'])==18 and len(checkpoints['mechanisms'])==6
    assert all(v['no_future_return_or_termination_bound_backfilled'] for v in checkpoints['rows'])
    ref(OUT/'reports/research_phases.json')
    identity=ref(OUT/'production_identity.json')
    assert sha(identity['PE'])==identity['PE_SHA'] and sha(identity['DLL'])==identity['DLL_SHA']==DLL_SHA
    manifest=ref(OUT/'source_manifest.json')
    assert manifest['no_Cpp_or_config_changes'] and manifest['no_rebuild']
    fee(manifest['outer_meter_label'])
    for name,digest in manifest['current_new_sources'].items():assert sha(ROOT/name)==digest
    for name,entry in manifest['fixed_python_dependencies'].items():
        raw=subprocess.check_output(['git','show',f'{entry["commit"]}:{name}'],cwd=ROOT)
        assert len(raw)==entry['reference_bytes'] and hashlib.sha256(raw).hexdigest()==entry['reference_SHA256']
        transform=entry['checkout_transform'];assert transform in ('identity','LF_to_CRLF','CRLF_to_LF')
        actual=raw if transform=='identity' else (raw.replace(b'\n',b'\r\n') if transform=='LF_to_CRLF' else raw.replace(b'\r\n',b'\n'))
        assert actual==(ROOT/name).read_bytes() and hashlib.sha256(actual).hexdigest()==entry['SHA256']
    ref(OUT/'reuse_index.json')
    # Initial status paths remain excluded from editing/staging. This is a
    # LATER byte record, not a reconstruction of the empty initial hash table.
    protection=[]
    for root,status_name in [(ROOT,'initial_paper_status.txt'),(Path('E:/codes/ExactEBRP'),'initial_original_status.txt')]:
        saved=OUT/'infra'/status_name
        paths=[line[3:] for line in saved.read_text(encoding='utf-8-sig').splitlines()
               if len(line)>3 and line[:2] not in ('??','!!')]
        if root==ROOT:assert len(paths)==44
        for name in paths:
            path=root/name;digest=sha(path)
            raw=subprocess.check_output(['git','show',f'{BASE}:{name}'],cwd=root) if root==ROOT else None
            protection.append(dict(root=str(root),path=name,SHA256=digest,bytes=path.stat().st_size,
                fixed_base_SHA256=hashlib.sha256(raw).hexdigest() if raw is not None else None,
                equals_fixed_base_bytes=digest==hashlib.sha256(raw).hexdigest() if raw is not None else None))
        staged=subprocess.check_output(['git','diff','--cached','--name-only','--',*paths],cwd=root,text=True).splitlines()
        assert not staged,('preexisting path unexpectedly staged',str(root),staged)
    assert read(OUT/'infra/protected_tracked_bytes.json')=={}
    protection_path=OUT/'review/later_protected_bytes.json';assert not protection_path.exists()
    write(protection_path,dict(UTC=utc(),files=protection,pre_task_byte_snapshot_available=False,
        initial_status_paths_checked=True,not_a_claim_of_pre_task_byte_equality=True,
        exclude_all_listed_paths_from_staging_and_cleanup=True))
    references[protection_path.relative_to(ROOT).as_posix()]=sha(protection_path)
    failures=[]
    for receipt_path in sorted((OUT/'fees').glob('*/receipt.json')):
        record=fee(receipt_path.parent.name,success=False)
        if record['exit_code']!=0 or record['timeout'] or record['supervisor_failure']:
            failures.append(dict(label=receipt_path.parent.name,receipt_SHA=sha(receipt_path),
                G1_seconds=record['G1_seconds'],exit_code=record['exit_code'],timeout=record['timeout']))
    endpoints=[]
    for role,phase,support in [('K-35-U','bounded_remaining_v1','remaining_deep_support_v1'),
                               ('N-C20-U','first_stalled_continuation_v1','stalled_continuation_support_v1')]:
        loop=ref(OUT/'coupled'/f'{role}_{phase}'/'result.json')
        replay=ref(OUT/'support_LP'/f'{role}_{support}'/'result.json')
        endpoints.append(dict(role=role,decision=loop['decision'],iterations=len(loop['records']),
            columns=len(loop['columns']),supports=len(loop['supports']),lower=replay['lower'],upper=replay['upper'],
            width=replay['upper']-replay['lower'],requested_precision=1e-4,
            final_finite_research_judgment_still_required=True))
    write(target/'result.json',dict(PASS=True,disposition='FACTUAL_RECONCILIATION_ONLY_FINAL_JUDGMENT_REQUIRED',
        phases=phases,support_replays=replays,minimum_recomputation_coverage=minimum_coverage,
        endpoints=endpoints,failures=failures,references=references,source_SHA=sha(__file__),
        NC20_stalled_direction_revisit=revisit,
        Optimize=0,Native_model_reads=0,nonimplementer_agent_review=False,
        own_outer_fee_still_open_and_final_closed_cost_report_required=True,
        final_scientific_writing_publication_restore_and_cleanup_not_certified_here=True))
    print(json.dumps(dict(PASS=True,phases=len(phases),support_replays=len(replays),
        endpoints=endpoints,failed_receipts_retained=len(failures),Optimize=0)),flush=True)


if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
