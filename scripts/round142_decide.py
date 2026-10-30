"""Seal the independently selected finite study after both matched bridges."""
from round142_common import *
from round142_analyze import require_idle
configure()

def main():
    require_idle();full=read(OUT/'reports/full.json');lp=read(OUT/'reports/LP.json')
    selection=read(OUT/'review/selection.json');cost=read(OUT/'cost_report.json')
    assert selection['independently_assessed'] and not selection['promote_stable_default']
    assert len(full['new_arms'])==6 and len(full['same_PE_bridges'])==2
    assert not full['failures'] and not full['unstarted']
    assert lp['LP_Optimize']==12 and lp['C_Optimize']==0
    candidates={r['role']:r for r in full['new_arms'] if r['method']=='CP'}
    controls={r['role']:r for r in full['new_arms'] if r['method']=='D1'}
    assert set(candidates)=={'K-15-S','K-20-S','K-35-U','R-B35-S-T2'}
    assert set(controls)=={'K-20-S','R-B35-S-T2'}
    old={r['role']:r for r in full['reused_arms'] if r['method']=='D1'}
    stock={r['role']:r for r in full['reused_arms'] if r['method']=='both'}
    c15,c20,k35,rb=(candidates[r] for r in ['K-15-S','K-20-S','K-35-U','R-B35-S-T2'])
    b20,brb=(controls[r] for r in ['K-20-S','R-B35-S-T2'])
    matched={r['role']:r for r in full['same_PE_bridges']}
    for r in full['new_arms']:
        assert r['pair_ready'] and r['count_LP_calls']==2 and r['seed']==0
    assert c15['certificate'] and c20['certificate'] and not k35['certificate'] and not rb['certificate']
    bridge20=matched['K-20-S'];bridgeRB=matched['R-B35-S-T2']
    complete=(f'All four selected Seed0 roles complete their original protocols. K15 and K20 keep the same two '
        f'qualified proofs as old D1 and stock, with production {c15["T_produce"]:.6f} / {c20["T_produce"]:.6f} s '
        f'and total {c15["T_total"]:.6f} / {c20["T_total"]:.6f} s. Against historical R141 D1 their production '
        f'gains are {old["K-15-S"]["T_produce"]-c15["T_produce"]:.6f} / '
        f'{old["K-20-S"]["T_produce"]-c20["T_produce"]:.6f} s, below the inherited max(10 s,10% of the smaller '
        f'clock) threshold. K20 versus historical stock improves production by '
        f'{stock["K-20-S"]["T_produce"]-c20["T_produce"]:.6f} s, which is substantive, but total by only '
        f'{stock["K-20-S"]["T_total"]-c20["T_total"]:.6f} s, below 10 s. This is a cross-version whole-method '
        f'comparison, not an isolated CP timing claim. K35 ends at U/L={k35["U"]:.12f}/{k35["L"]:.12f}; '
        f'its old-D1 changes are U +{k35["U"]-old["K-35-U"]["U"]:.12f} and '
        f'L {k35["L"]-old["K-35-U"]["L"]:.12f}. RB35-T2 ends at '
        f'{rb["U"]:.12f}/{rb["L"]:.12f}, a repair over historical old D1 but still a worse U/stronger L '
        f'tradeoff against stable GI-TBC, and worse at both endpoints than old TC+stock and TC2+stock. '
        f'K35 is also dominated by old TC+stock. All open certificate times stay null; no cap is called convergence.')
    outcome=('improves both endpoints' if bridgeRB['delta_U']<-1e-7 and bridgeRB['delta_L']>1e-7 else
             'worsens both endpoints' if bridgeRB['delta_U']>1e-7 and bridgeRB['delta_L']<-1e-7 else
             'trades incumbent and supported bound' if bridgeRB['delta_U']*bridgeRB['delta_L']>0 else
             'has a mixed or numerically equal endpoint result')
    attribution=(f'Two independently paid same-PE old-D1 bridges retain the identical source/PE, input, own H, '
        f'root, selection/pivot, count links and complete window. The first integer matrices match after '
        f'removing only the floor row; source CP is absent from those integer models. K20 old D1 produces '
        f'its proof in {b20["T_produce"]:.6f} s ({b20["T_total"]:.6f} total); selected CP changes production '
        f'by {bridge20["delta_T_produce"]:.6f} s and total by {bridge20["delta_T_total"]:.6f} s, without '
        f'a substantive incremental proof-clock gain. RB old D1 ends at U/L={brb["U"]:.12f}/{brb["L"]:.12f}; '
        f'CP {outcome}, with U delta {bridgeRB["delta_U"]:.12f} and L delta '
        f'{bridgeRB["delta_L"]:.12f}. This is the actual matched complete intervention: stronger source '
        f'models and the returned two floor coefficients. It does not identify Native branching on b or '
        f'attribute the result only to the weak-side raw objective increment. K35 has no new same-PE '
        f'bridge; retain its adverse cross-version comparison without assigning causality solely to CP. '
        f'Native returned bounds and the externally merged supported L remain separate full-table fields.')
    decision=('Retain the uniform selected-CP entry as research-only and close this count-proof continuation. '
        'Conditional count products fill a real shared-factor relaxation freedom and raise all three weaker '
        'sources/min-covers. They do not provide a sufficiently consistent complete-method increment for '
        'promotion: the small-role old-D1 proof benefit is not substantive under same-PE matching, K35 '
        'regresses at both endpoints against historical D1, and the hard roles remain behind old TC+stock '
        'at both endpoints. Stable R137 GI-TBC remains the default. Preserve the actual RB matched result '
        'and every adverse/failed result as finite research evidence; neither stronger LPs nor this panel '
        'proves general Native performance dominance.')
    conditional=('The independently selected K20/RB same-PE bridges are complete. No remaining-four-role '
        'expansion, new D0 grid or Seed1 is entered: these would not change the adoption/stop decision '
        'given the completed hard-role boundary. No missing role is inferred. ALL has no useful extra '
        'source information, reverse inventory bounds are implied and unchanged, and further similar RLT, '
        'AM/Seed grids or H redesign are not opened. A future continuation needs genuinely different joint '
        'information or search evidence, under a new explicit task. Stopping is based on scientific and '
        'marginal decision value with ample unused budget, not the 8-hour ceiling.')
    result=dict(round=142,study_complete=True,delivery_record='RESUME.md and additive PR/public/cleanup receipts',
        recommendation='RESEARCH_ONLY_CLOSE_COUNT_PROOF_CONTINUATION',promote_stable_default=False,
        stable_default='R137 GI-TBC, unchanged',uniform_candidate='selected CP inside both R141 D1 count LP sources',
        actual_production_source=read(OUT/'candidate_manifest.json')['source_commit'],
        PE_SHA=read(OUT/'candidate_manifest.json')['production_PE_SHA'],
        complete_discussion=complete,attribution_discussion=attribution,
        decision_paragraph=decision,conditional_work_discussion=conditional,
        standalone_continuous_LPs=12,zero_Optimize_range_controls=12,formal_selected_Seed0_positions=4,
        same_PE_old_D1_Seed0_bridges=2,healthy_cap90_qualifications=1,new_Seed1_positions=0,
        failed_pure_fixture_constructions=1,failed_Optimize_positions=0,
        matched_cover_gains=lp['covers'],same_PE_bridges=full['same_PE_bridges'],
        charged_new_experiment_seconds=cost['charged_new_experiment_seconds'],
        online_G1_seconds=cost['experiment']['G1_seconds'],budget_ceiling_seconds=28800,
        independent_selection_SHA=sha(OUT/'review/selection.json'),remaining_required_experiments=[],
        delivery_scope='Scientific completion does not certify later PR/public/cleanup steps; their actual status is additive in RESUME.md and the corresponding receipts.')
    write(OUT/'candidate_decision.json',result)
    print(json.dumps(dict(recommendation=result['recommendation'],same_PE_bridges=[{k:r[k] for k in
        ['role','delta_U','delta_L','delta_T_produce','delta_T_total']} for r in full['same_PE_bridges']],
        charged_seconds=result['charged_new_experiment_seconds'])))

if __name__=='__main__':main()
