"""Rebuild the published candidate/evidence and stopped-family scope tables.

Historical statements are explicitly pinned to R100/R107 in the public
manifest. Current rows use the raw-reconstructed arms and stage decision.
This module has no solver or original-worktree dependency.
"""

def scope_tables(arms,pairs,selection,gate):
    stage=selection['stage'];cancelled=selection['cancelled_arms']
    gaps=[dict(candidate='Frozen R100 M-B',evidence='Inherited mathematics / factor attribution',current_status='QUALIFIED_INHERITANCE',
        scope='Implicit quantity integrality and exact existing A/B; no new mechanism or causal reidentification',remaining_gap='Does not establish current full-method speed or broad generalization'),
        dict(candidate='Frozen R100 M-B',evidence='Current production / real CLI',current_status='INDEPENDENT_ACCEPT',
        scope='Current same PE/DLL, exact diagnostic matrix plus actual H100 P/ENS/M-B, full Starts/cover and legal termination',remaining_gap='H100 functional timing is not formal performance'),
        dict(candidate='Frozen R100 M-B',evidence='Complete F2/C2 contemporary bridge',current_status='PASS' if gate['bridge_pass'] else 'STOP',
        scope='Six own cold-P/full-ENS/frozen-M-B arms; prespecified resource gate',remaining_gap='Known development roles, not prospective generalization'),
        dict(candidate='Frozen R100 M-B',evidence='Exact four prospective roles',current_status=f'{sum(a["id"] in ["S12","B24","L48","N36"] for a in arms)//3}/4 roles completed; WIN={selection["unseen_WIN"]}, LOSS={selection["unseen_LOSS"]}',
        scope='S12/B24/L48/N36 all eligible at first-formal freeze; four-role denominator unchanged',remaining_gap='Only measured roles support outcomes; cancelled roles confer no ENS or M-B qualification'),
        dict(candidate='Frozen R100 M-B',evidence='Known F5 stress role',current_status=next((p['classification'] for p in pairs if p['id']=='F5' and p['control']=='P-GRB'),'NOT_STARTED_CANCELLED'),
        scope='Known input, frozen 5400s per arm if admitted',remaining_gap='Uncertified windows do not identify eventual certification times'),
        dict(candidate='Frozen R100 M-B',evidence='Stage selection',current_status=stage,
        scope='One uniform candidate; default ENS unchanged; no new variant',remaining_gap='Broad paper evidence still required after SELECT; a negative stage does not automatically reopen mechanisms')]
    stopped=[dict(family='R98 alternative state/direction representations and R99 M-BL',retained_status='OUTSIDE_THIS_UNIFORM_CANDIDATE_STUDY',
        evidence_scope='Legal representations, mixed finite factor/search outcomes; M-B priority is not historical dominance',round108_action='No alternate mode, per-input switch or extra linking row'),
        dict(family='R100 ENS-Q',retained_status='NO_OVERALL_ADOPTION',evidence_scope='Legal continuous p/d without A/B; mixed study, protected ENS default',round108_action='Flag absent; no new ENS-Q performance factor grid'),
        dict(family='R102 service-resource cuts',retained_status='RESEARCH_OPT_IN_DEFAULT_OFF',evidence_scope='Finite genuine service projection increment with mixed full-method outcomes and C3 loss',round108_action='No callback/PreCrush/resource strengthening'),
        dict(family='R105 optimal-master-event route decomposition',retained_status='STOP_MEASURED_PROTOTYPE',evidence_scope='F2 lost ENS certificate; C2 optimal events did not improve route UB/strongest LB',round108_action='No new event loop, IIS, route fallback or fixed-Y retry'),
        dict(family='R106 global / R107 frontier existing assignment-STRUCT',retained_status='STOP_TESTED_CONFIGURATION',evidence_scope='Eight same-PE R107 arms; F2 certificate loss and C2 quality deficit; no multiactive-leaf split',round108_action='No forced split, AM tuning, net-return row, new A/B or extension of this combination'),
        dict(family='Frozen R100 M-B reopening',retained_status=stage,evidence_scope=f'{len(arms)} current formal arms, {len(cancelled)} wholly unstarted cancellations',round108_action='Only the prescribed resource/selection decision; no automatic new M-B layer')]
    return {'candidate_evidence_gap':gaps,'stopped_mechanism_families':stopped}
