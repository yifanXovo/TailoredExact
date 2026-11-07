"""Record the finite research stopping decision from actual closed evidence."""
from round157_common import *

def run():
    configure();assert not budget()['unclosed']
    price=read(OUT/'family_floor/rx35_two_families_v1/result.json')
    first=read(OUT/'resource/rx35_family4096_v1/result.json');second=read(OUT/'resource/rx35_second4096_v1/result.json')
    assert first['classification']==second['classification']=='RESOURCE_INFEAS'
    assert price['NodeCount']==16384 and not price['level_excluded']
    prior=read(OUT/'inventory_sources.json')['R-X35-S-T2'];assert price['original_lower']==prior['lower']
    explanation=('Do not freeze a complete E+R candidate. The two preselected RX35 families have meaningful original-T resource impossibility proofs, but they supply no physical route. One finite26-member exclusion/repricing batch returns at16384 nodes with no global lower gain and does not exclude its selected level. The full-inventory resource diagnostic also stalls at the prior floor despite the valid prior lower and known-route start. The checked retained inventory caps this finite batch\'s possible increment at0.0008019063986266512, about1.26% of the inherited physical gap, whereas its two resource proofs plus repricing already cost572.2466407998 outer seconds before qualifications. There is no demonstrated useful and plausibly affordable uniform mechanism for a fresh self-paid complete method. The conditional panel is therefore not started. Further route/global-level questions remain open; the60-hour capacity is a ceiling, not a reason to repeat a stalled mechanism.')
    write(OUT/'final_decision.json',dict(UTC=utc(),study_complete=True,
        disposition='FINITE_FAMILY_RESOURCE_PROOFS_NO_COMPLETE_CANDIDATE',
        complete_candidate_frozen=False,complete_panel_started=False,new_Cpp_build=False,
        new_physical_route=False,new_global_original_J_lower_gain=0.,
        RX35_proved_families=2,RX35_proved_member_vectors=26,NB35_status='UNKNOWN',
        NB35_second_family_queried=False,
        NB35_second_family_disposition='Preselected and retained; the one substantive deepening focused on RX35 proof propagation after its first family exclusion. No posthoc role or stock replacement.',
        fixed_full_fleet_raw_returns='UNKNOWN on both roles; RX35 fixed stock is excluded by the stronger family resource proof',
        target_level=price['target_level'],target_level_excluded=False,
        physical_bounds_unchanged={r:dict(U=s['endpoint']['U'],L=s['endpoint']['L']) for r,s in read(OUT/'inventory_sources.json').items()},
        finite_batch_maximum_increment=price['maximum_increment_over_Eplus_from_this_batch'],
        repeated_stagnation_not_a_structural_impossibility_claim=True,
        stable_default='GI-TBC/B',explanation=explanation))
    print(json.dumps(dict(study_complete=True,complete_panel_started=False)),flush=True)

if __name__=='__main__':run()
