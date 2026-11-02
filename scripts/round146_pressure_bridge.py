"""Result-dependent RB35 stable-BASE bridge registration, without a solver call."""
from round146_common import *
from round146_campaign import freeze

def main():
    configure();assert not budget()['unclosed']
    full=read(OUT/'reports/full.json');assert not full['pending']
    pair=next(p for p in full['pairs'] if p['role']=='R-B35-S-T2')
    assert pair['same_PE'] and pair['own_H_equal']
    assert pair['GD_U']<pair['STOCK_U'] and pair['GD_L']>pair['STOCK_L']
    reason=('RB35 STOCK+GD improves both endpoints versus same-PE STOCK after the full registered windows, '
        'but historical stable BASE has a materially lower incumbent. One same-PE BASE arm is needed to '
        'resolve that known pressure-role regression before considering the combination for recommendation. '
        'This is one stable comparison, not a second candidate or a repeated STOCK arm; no K35/RN-P/Seed grid is admitted.')
    write(OUT/'stage_rb35.json',dict(UTC=utc(),decision='ENTER_ONE_STABLE_BASE_PRESSURE_BRIDGE',pair=pair,
        U_improvement_percent=100*(pair['STOCK_U']-pair['GD_U'])/pair['STOCK_U'],
        gap_improvement_percentage_points=100*(pair['STOCK_relative_gap']-pair['GD_relative_gap']),
        historical_BASE=dict(round=145,source='results/unified_exact_round145/reports/full.json',
            U=.34464262559194814,L=.2189859496034747,cross_PE_not_new_same_PE_evidence=True),
        reason=reason,next_role='R-B35-S-T2',next_method='BASE',cap_seconds=2400,
        candidate='STOCK+GD-state',primary_reference='STOCK',candidate_unchanged=True,
        total_spent=budget()['G1_seconds'],additional_nominal_caps=2400,
        no_duplicate_entered_position=True,Optimize=0,Native_load=0))
    freeze('base_bridge',[dict(role='R-B35-S-T2',method='BASE')],reason)
    print(json.dumps(dict(stage='RB35 pressure bridge registration',matrix_SHA=sha(OUT/'base_bridge_matrix.json'),budget=budget())))

if __name__=='__main__':main()
