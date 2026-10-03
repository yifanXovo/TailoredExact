"""Exactly one uniform candidate freeze after completed development.
Creates no solver job or confirmation input and cannot overwrite a prior freeze.
"""
import json,subprocess
from round101_common import *
from round101_campaign import helpers
from round101_budget import account

if __name__=='__main__':
    protocol=read(OUT/'development_protocol01.json');fleet=protocol['fleet_arm']
    campaign=OUT/'development01';identity=read(campaign/'identity.json')
    rows=[json.loads(x) for x in (campaign/'summary.jsonl').read_text().splitlines()]
    assert len(rows)==6 and all(r['audit_passed'] for r in rows)
    assert len(identity['launches'])==6 and identity['source_hashes']==bindings()
    assert identity['candidate_binary_sha256']==sha(BUILD/'ExactEBRP.exe')
    assert fleet in ['FLEET-ROOT','FLEET-SUBMIT']
    assert not (ROOT/'reference/round101_confirmation').exists()
    budget=account();assert not budget['reserved'] and budget['within_limits']
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    write(OUT/'candidate_freeze.json',dict(fleet_arm=fleet,
        mode='submit',range='root' if fleet=='FLEET-ROOT' else 'tree',
        family='distinct-station pickup/delivery threshold ranks on existing VD-P state selectors',
        prover='complete necessary subset DP <=9 and conservative directional eligibility/cardinality slot upper ranks at all prefix sizes',
        uniform_thresholds='q=1..maxQ, mass-ordered positive station prefixes; no case dispatch',
        mixed_mass_levels=[.5,.75,.9],maximum_rows_per_optimal_callback=2,
        station_overlap='no majority support overlap',small_support=9,standalone_support=10,
        small_proof_cache_entries=256,cache_eviction_does_not_skip=True,
        numerical_contract='audited original rows, common physical/imported lower coefficients, outward IEEE operations, safe horizon, raw activity lower bound >10*readback FeasTol',
        native=dict(version='13.0.2',Threads=1,Seed=0,Presolve=-1,PreCrush=1,MIPGap=0,MIPGapAbs=0,
            FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6),
        candidate_binary_sha256=sha(BUILD/'ExactEBRP.exe'),source_hashes=bindings(),helper_hashes=helpers(),
        archived_build_manifest_sha256=sha(OUT/'builds/post_cost_revision/manifest.json'),
        dll_sha256=sha('D:/gurobi1302/win64/bin/gurobi130.dll'),delivery_head_at_freeze=head,
        inherited_base='541c032f04b35f90d750c83e4938e02df3ebf008',
        selection_evidence=dict(isolation_sha256=sha(OUT/'isolation01/summary.jsonl'),
            development_sha256=sha(campaign/'summary.jsonl'),development_protocol_sha256=sha(OUT/'development_protocol01.json')),
        confirmation_generator_sha256=sha(ROOT/'scripts/round101_confirmation.py'),
        candidate_frozen_before_confirmation_inputs=True,
        prior_confirmation_inputs_observed=False,
        no_default_promotion=True,no_MB_stacking=True,no_historical_or_cross_arm_answers=True,
        no_production_time_Work_restart_or_frequency_policy=True,
        remaining_budget=budget['remaining_after_current_plan_seconds']))
    print(json.dumps(dict(frozen=fleet,confirmation_inputs_exist=False,Optimize=0)))
