"""Independent final R103 metadata review, launched only by a paid idle receipt.

Standard library only. Reads CSV/JSON/source hashes, never an LP model, never
imports a solver, never calls Optimize, DP, a native child, or a report helper.
Missing/failed records are retained as findings rather than reconstructed.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'results/unified_exact_round103'
HERE = Path(__file__).resolve().parent


def truth(v):
    return v is True or str(v).lower()=='true'


def number(v):
    if v is None or v=='':
        return None
    result = float(v)
    if not math.isfinite(result):
        raise ValueError('Nonfinite metadata number retained as a failed review: '+str(v))
    return result


def same_number(a, b):
    # The report is a serialization of the same binary64 value, not a new fit.
    return number(a)==number(b)


def close(a, b, tol=1e-9):
    return a is not None and b is not None and abs(a-b)<=tol*max(1., abs(a), abs(b))


def key(r):
    return r['campaign'], int(r['number']), r.get('role', r.get('id')), r['arm']


class Review:
    def __init__(self, args):
        self.args = args
        self.cache = {}
        self.hashes = {}
        self.context = {}
        self.observations = {}
        self.endpoint_rows = {}
        self.checkpoint_rows = {}
        self.expected_fees = {}
        self.reviewed_call_ledgers = set()
        self.inherited_DP_cache = {}
        self.started = time.perf_counter()
        self.result = dict(schema='round103-final-independent-review-v2-inherited-DP', status='RUNNING',
                           source_sha256=self.sha(Path(__file__)),
                           inputs=dict(reports=args.reports, clocks=args.clocks,
                                       fees=args.fees, decision=args.decision,
                                       final_decision=args.final_decision),
                           Optimize_calls=0, DP_calls=0, native_B_and_B_runs=0,
                           Gurobi_imports=0, model_reads=0,
                           errors=[], warnings=[], missing=[], checks=0,
                           comparisons=[], checkpoint_findings=[], run_accounting=[],
                           independent_scope='Independent metadata arithmetic and provenance checks only. '
                           'Existing paid mathematical review is retained; no new support, plan, route, '
                           'Gurobi model, native-scope replay, rational optimum or native B&B validation.')

    def path(self, p):
        p = Path(p)
        return p if p.is_absolute() else OUT/p

    def sha(self, p):
        p = Path(p)
        if p not in self.hashes:
            h = hashlib.sha256()
            with p.open('rb') as stream:
                for chunk in iter(lambda:stream.read(1024*1024), b''):
                    h.update(chunk)
            self.hashes[p] = h.hexdigest()
        return self.hashes[p]

    def load(self, p, required=True):
        p = self.path(p)
        if p not in self.cache:
            if not p.exists():
                if required:
                    self.result['missing'].append(str(p))
                return None
            self.sha(p)
            self.cache[p] = json.loads(p.read_text(encoding='utf-8-sig'))
        return self.cache[p]

    def lines(self, p, required=True):
        p = self.path(p)
        if not p.exists():
            if required:
                self.result['missing'].append(str(p))
            return []
        self.sha(p)
        return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines() if s.strip()]

    def table(self, p, required=True):
        p = self.path(p)
        if not p.exists():
            if required:
                self.result['missing'].append(str(p))
            return []
        self.sha(p)
        with p.open(newline='', encoding='utf-8-sig') as stream:
            return list(csv.DictReader(stream))

    def check(self, condition, message, **evidence):
        self.result['checks'] += 1
        if not condition:
            self.result['errors'].append(dict(message=message, **evidence))

    def warning(self, message, **evidence):
        self.result['warnings'].append(dict(message=message, **evidence))

    def section(self, name, call):
        try:
            call()
        except Exception:
            self.result['errors'].append(dict(section=name, exception=traceback.format_exc()))
        self.save()

    def save(self):
        self.result['elapsed_reader_seconds'] = time.perf_counter()-self.started
        self.result['metadata_files_hashed'] = len(self.hashes)
        self.result['metadata_digests'] = {str(p):value for p,value in self.hashes.items()}
        self.target.write_text(json.dumps(self.result, ensure_ascii=False, indent=2,
                                         allow_nan=False), encoding='utf-8')

    def run_metadata(self):
        identity = self.load(Path(self.args.reports)/'reporting_identity.json')
        if identity is None:
            return
        self.check(identity['Optimize_calls']==0 and identity['no_recovery_overlay'],
                   'Reporter must be read-only without reconstructed recovery overlays')
        if self.args.campaigns:
            self.check(set(identity['campaigns'])==set(self.args.campaigns), 'Report campaign scope differs from final authorized list')
        for p in OUT.glob('*/identity.json'):
            q = self.load(p)
            if q and 'launches' in q and not p.parent.name.startswith('native'):
                self.check(p.parent.name in identity['campaigns'], 'A complete performance campaign was omitted from final reporting',
                           campaign=p.parent.name)
        freeze = self.load('production_freeze.json')
        protocol = self.load('protocol.json')
        if freeze is None or protocol is None:
            return
        self.protocol = protocol
        self.material = protocol['materiality']
        self.check(protocol['protected_default']=='ENS-C' and protocol['main_benchmark']=='P-GRB',
                   'Protected default or principal benchmark changed')
        for name, expected in freeze['source_bindings'].items():
            p = ROOT/name
            self.check(p.exists() and self.sha(p)==expected, 'Measured source differs from frozen source', path=name)
        report = self.table(Path(self.args.reports)/'runs.csv')
        reported = {key(r):r for r in report}
        self.check(len(reported)==len(report), 'Duplicate per-arm report keys')
        expected = set()
        for name in identity['campaigns']:
            campaign = OUT/name
            q = self.load(campaign/'identity.json')
            if q is None:
                continue
            records = self.lines(campaign/'summary.jsonl')
            self.check(len(records)==len(q['launches']), 'Campaign is pending/incomplete', campaign=name,
                       completed=len(records), planned=len(q['launches']))
            self.check([int(r['number']) for r in records]==list(range(1, len(records)+1)),
                       'Campaign lacks a serial contiguous completed prefix', campaign=name)
            if name!='native01':
                self.check(q['candidate_binary_sha256']==freeze['PE_sha256'] and
                           q['source_hashes']==freeze['source_bindings'],
                           'Performance arm differs from frozen same-build candidate', campaign=name)
            for r in records:
                k = (name, int(r['number']), r['id'], r['arm'])
                expected.add(k)
                a = q['launches'][int(r['number'])-1]
                d = Path(r['destination'])
                audit = self.load(d/'audit.json')
                completion = self.load(d/'completion.json')
                if audit is None or completion is None:
                    continue
                self.check(completion==r['completion'], 'Completion disagrees with campaign summary', run=k)
                self.check(r['audit_passed'] and audit['passed'], 'Failed campaign audit retained in final report', run=k)
                ep = r['endpoint']
                if audit.get('endpoint') is not None:
                    self.check(ep==audit['endpoint'], 'Final endpoint differs from native completion audit',run=k)
                row = reported.get(k)
                self.context[k] = dict(destination=d, audit=audit, completion=completion, endpoint=ep,
                                       launch=a, campaign_identity=q, row=row)
                if row is None:
                    self.check(False, 'Completed arm missing from runs.csv', run=k)
                    continue
                self.endpoint_rows[k] = row
                self.check(row['input_sha256']==a['panel']['input_sha256'], 'Input identity differs', run=k)
                self.check(row['binary_sha256']==q['candidate_binary_sha256'], 'Binary identity differs', run=k)
                for field in ('U', 'L', 'gap'):
                    self.check(same_number(row[field], ep[field]), 'Endpoint field/sign changed', run=k, field=field)
                self.check(truth(row['certificate'])==bool(ep['certificate']), 'Certificate status changed', run=k)
                if ep['U'] is not None:
                    self.check(close(ep['gap'], ep['U']-ep['L'], 1e-12), 'Gap arithmetic incorrect', run=k)
                    self.check(ep['gap']>=-1e-7, 'Material endpoint lower/upper contradiction', run=k)
                    relative = ep['gap']/max(abs(ep['U']), 1e-12)
                    self.check(same_number(row['relative_gap'], relative), 'Relative gap changed', run=k)
                else:
                    self.check(row['gap']=='' and row['relative_gap']=='', 'Missing physical UB was filled', run=k)
                for field, original in [('outer_seconds','process_wall_seconds'),
                                        ('end_to_end_seconds','end_to_end_seconds')]:
                    self.check(same_number(row[field], completion[original]), 'Whole completion clock substituted', run=k, field=field)
                self.check(int(row['optimizer_calls'])==audit['native_calls_started'] and
                           int(row['native_calls_returned'])==audit['native_calls_returned'],
                           'Native call counts disagree', run=k)
                self.check(row['receipt_sha256']==self.sha(d/'completion.json') and
                           row['original_audit_sha256']==self.sha(d/'audit.json'),
                           'Receipt/audit digest differs', run=k)
                end = completion['end_to_end_seconds']
                self.check(close(end, completion['prelaunch_seconds']+completion['process_wall_seconds']),
                           'End-to-end cost does not include admission plus process', run=k)
                self.check(completion['within_cap'] and end<=a['cap_seconds']+1e-7,
                           'Whole run cap exceeded', run=k)
                normal = completion['stop_reason']=='normal_return'
                result = self.load(d/'result.json', required=normal)
                self.check(truth(row['normal_result_available'])==bool(result), 'Normal/censored result availability changed', run=k)
                if not normal:
                    self.check(result is None and not ep['certificate'], 'Censored arm acquired an endpoint certificate/result', run=k)
                if ep['certificate']:
                    self.check(normal and bool(result) and ep['gap'] is not None and abs(ep['gap'])<=1e-7,
                               'Complete certificate lacks finalized result or has a material proof gap',run=k)
                if result:
                    preset = {'ENS-C':'research-round83-vds-equal-net-exchange',
                              'H-SUBMIT':'research-round103-ensc-hull-submit-root',
                              'H-SHADOW':'research-round103-ensc-hull-shadow-root',
                              'J-SUBMIT':'research-round102-ensc-service-submit-root', 'P-GRB':'custom'}
                    self.check(result['algorithm_preset']==preset[r['arm']], 'Preset attribution differs', run=k)
                    if r['arm']=='P-GRB':
                        self.check(result['gurobi_hga_start_requested'] is False and result['gurobi_optimize_count']==1,
                                   'P-GRB Start or native Optimize policy changed', run=k)
                        reference = a['panel']['reference']
                        for field, original in [('gurobi_model_fingerprint','fingerprint'),
                                                ('gurobi_num_vars','columns'),('gurobi_num_constrs','rows')]:
                            self.check(result[field]==reference[original], 'P-GRB original model identity/dimensions changed',
                                       run=k,field=field)
                command = list(map(str, a['command']))
                for option in ('--round101-fleet-cuts','--round102-service-cuts','--round103-resource-hull'):
                    if r['arm'] in ('P-GRB','ENS-C'):
                        self.check(option not in command or command[command.index(option)+1]=='off',
                                   'Protected reference received an active R101/R102/R103 policy', run=k, option=option)
        self.check(set(reported)==expected, 'runs.csv omits or invents campaign arms', missing=list(expected-set(reported)),
                   extra=list(set(reported)-expected))

    def observations_for(self, k):
        if k not in self.observations:
            self.observations[k] = self.load(self.context[k]['destination']/'observations.json') or []
        return self.observations[k]

    def clocks(self):
        rows = self.table(Path(self.args.clocks)/'checkpoints.csv')
        for row in rows:
            k, cp = key(row), number(row['checkpoint_full_seconds'])
            if k not in self.context:
                self.check(False, 'Checkpoint refers to unknown arm', run=k)
                continue
            ctx = self.context[k]
            ep, c = ctx['endpoint'], ctx['completion']
            end, pre = c['end_to_end_seconds'], c['prelaunch_seconds']
            self.check(cp<=ctx['launch']['cap_seconds'], 'Checkpoint exceeds common arm budget', run=k, checkpoint=cp)
            ck = k+(cp,)
            self.check(ck not in self.checkpoint_rows, 'Duplicate checkpoint', run=k, checkpoint=cp)
            self.checkpoint_rows[ck] = row
            self.check(same_number(row['actual_full_exit_seconds'], end), 'Checkpoint exit clock differs', run=k)
            if end<=cp:
                if ep['certificate']:
                    self.check(truth(row['covered']) and truth(row['certificate']), 'Completed certificate not carried honestly', run=k, checkpoint=cp)
                    for field in ('U','L','gap'):
                        self.check(same_number(row[field], ep[field]), 'Carried certificate endpoint changed', run=k, field=field)
                else:
                    self.check(not truth(row['covered']) and not truth(row['certificate']) and
                               all(row[f]=='' for f in ('U','L','gap')),
                               'Unproved exit extrapolated to a later checkpoint', run=k, checkpoint=cp)
            else:
                self.check(truth(row['covered']) and not truth(row['certificate']),
                           'Unfinished prefix must not carry a later certificate', run=k, checkpoint=cp)
                obs = self.observations_for(k)
                eligible = [v for v in obs if v['effective_available_seconds']+pre<=cp]
                seq = {v['sequence'] for v in eligible}
                witness = [w['F'] for w in ctx['audit'].get('witnesses', []) if w.get('sequence') in seq]
                upper = min(witness) if witness else None
                lower = max([0.]+[v['payload']['global_bound'] for v in eligible
                                  if v['payload']['kind']=='bound' and v['payload'].get('global_available')])
                gap = upper-lower if upper is not None else None
                for field, val in [('U',upper),('L',lower),('gap',gap)]:
                    self.check(same_number(row[field], val), 'Prefix uses future/foreign/interpolated evidence', run=k,
                               checkpoint=cp, field=field, expected=val, reported=row[field])
            u, g = number(row['U']), number(row['gap'])
            relative = g/max(abs(u),1e-12) if u is not None and g is not None else None
            self.check(same_number(row['relative_gap'], relative), 'Checkpoint relative gap/sign differs', run=k, checkpoint=cp)
            self.check(row['observations_sha256']==self.sha(ctx['destination']/'observations.json'),
                       'Checkpoint observation digest differs', run=k)
        timing = self.table(Path(self.args.clocks)/'discovery_certification.csv')
        star = {}
        for k, ctx in self.context.items():
            if ctx['endpoint']['certificate']:
                h = ctx['launch']['panel']['input_sha256']
                u = ctx['endpoint']['U']
                self.check(h not in star or abs(star[h]-u)<=1e-7, 'Certified arms disagree on numerical optimum', input_sha256=h)
                star[h] = u
        self.check({key(r) for r in timing}==set(self.context), 'Timing table incomplete or invents arms')
        for row in timing:
            k = key(row)
            if k not in self.context:
                continue
            ctx = self.context[k]
            ep, c = ctx['endpoint'], ctx['completion']
            end, pre = c['end_to_end_seconds'], c['prelaunch_seconds']
            known = star.get(ctx['launch']['panel']['input_sha256'])
            qualified = [w for w in ctx['audit'].get('witnesses', []) if known is not None and abs(w['F']-known)<=1e-7]
            obs = {v['sequence']:v for v in self.observations_for(k)}
            upper = min((w['available']+pre for w in qualified), default=None)
            publication = min((obs[w['sequence']]['data_close_seconds']+pre for w in qualified), default=None)
            cert = end if ep['certificate'] else None
            for field, val in [('t_find_full_safe_lower_seconds',pre if upper is not None else None),
                               ('t_find_full_observation_upper_seconds',upper),
                               ('journal_publication_full_conservative_lower_seconds',publication),
                               ('journal_receipt_full_observation_upper_seconds',upper),
                               ('t_cert_full_completion_observation_upper_seconds',cert),
                               ('complete_certification_time_seconds',cert),
                               ('observed_full_exit_seconds',end)]:
                self.check(same_number(row[field], val), 'Discovery/certification clock attribution differs', run=k, field=field)
            self.check(row['exact_engine_find_instant']=='' and row['exact_engine_certificate_instant']=='',
                       'Reader inferred an exact native discovery/certificate instant', run=k)
            self.check('offline independent audit separately engineering' not in row['scope'],
                       'Postexit numerical audit was mislabeled as free engineering', run=k)
            if upper is not None:
                self.check(pre<=publication<=upper<=end+1e-7, 'Observation milestone ordering invalid', run=k)
            lower = number(row['t_cert_full_completion_conservative_lower_seconds'])
            if lower is not None:
                self.check(ep['certificate'] and lower<=end+1e-6, 'Certification interval exceeds completion', run=k)
            result = self.load(ctx['destination']/'result.json',required=False)
            snapshot = result.get('final_process_wall_time_seconds') if result else None
            expected_lower = pre+snapshot if ep['certificate'] and snapshot is not None else None
            self.check(same_number(lower, expected_lower), 'Certification lower milestone changed',run=k)
            find_low = pre if upper is not None else None
            expected = {
                't_tail_safe_lower_seconds':max(0.,lower-upper) if lower is not None and upper is not None else None,
                't_tail_safe_upper_seconds':cert-find_low if cert is not None and find_low is not None else None,
                'post_publication_to_full_completion_lower_seconds':max(0.,lower-upper) if lower is not None and upper is not None else None,
                'post_publication_to_full_completion_upper_seconds':cert-publication if cert is not None and publication is not None else None,
                'unproved_observed_post_find_seconds':end-upper if not ep['certificate'] and upper is not None else None,
                'offline_validation_seconds':ctx['audit'].get('offline_audit_seconds'),
                'wrapper_postexit_seconds':c['postexit_drain_and_restore_seconds']}
            for field, val in expected.items():
                self.check(same_number(row[field],val), 'Tail/validation timing is not the declared observation interval',run=k,field=field)
            if not ep['certificate']:
                self.check(all(row[f]=='' for f in ('complete_certification_time_seconds',
                                                   't_cert_full_completion_observation_upper_seconds',
                                                   't_tail_safe_lower_seconds','t_tail_safe_upper_seconds')),
                           'Censored time replaced by a complete proof time/tail', run=k)

    def derived_pair(self, a, b):
        m = self.material
        ac, bc = truth(a['certificate']), truth(b['certificate'])
        at, bt = number(a['end_to_end_seconds']), number(b['end_to_end_seconds'])
        both = ac and bc
        delta, ratio = (bt-at, bt/at) if both else (None, None)
        au, bu, ag, bg = number(a['U']), number(b['U']), number(a['gap']), number(b['gap'])
        advantage = bc and not ac and at-bt>=m['time_absolute'] and bt/at<=1-m['time_relative']
        regression = ac and not bc and bt-at>=m['time_absolute'] and bt/at>=1+m['time_relative']
        return dict(reference_certified=ac, candidate_certified=bc,
                    censoring='both_certified' if both else 'reference_only' if ac else 'candidate_only' if bc else 'both_unproved',
                    certified_time_delta=delta, certified_time_ratio=ratio,
                    material_time_change=both and abs(delta)>=m['time_absolute'] and abs(ratio-1)>=m['time_relative'],
                    severe_time_regression=both and delta>=m['severe_time_absolute'] and ratio>=1+m['severe_time_relative'],
                    eventual_time_order_known=both or (bc and bt<at) or (ac and at<bt),
                    time_delta_upper_bound=bt-at if bc and not ac else None,
                    time_delta_lower_bound=bt-at if ac and not bc else None,
                    material_one_sided_time_advantage=bool(advantage), material_one_sided_time_regression=bool(regression),
                    severe_one_sided_time_regression=ac and not bc and
                        bt-at>=m['severe_time_absolute'] and bt/at>=1+m['severe_time_relative'],
                    material_budget_U_change=au is not None and bu is not None and
                        abs(bu-au)>=m['UB_absolute'] and abs(bu-au)/max(abs(au),1e-12)>=m['UB_relative'],
                    material_budget_gap_change=ag is not None and bg is not None and
                        abs(bg-ag)>=m['gap_absolute'] and abs(bg-ag)/max(abs(ag),1e-12)>=m['gap_relative'],
                    signed_U_delta=bu-au if bu is not None and au is not None else None,
                    signed_gap_delta=bg-ag if bg is not None and ag is not None else None)

    def comparisons(self):
        grouped = {}
        for k, row in self.endpoint_rows.items():
            grouped.setdefault((k[0], k[2]), {})[k[3]] = row
        inherited_pairs = self.table(Path(self.args.reports)/'pairs.csv')
        complete_pairs = self.table(Path(self.args.reports)/'complete_pairs.csv')
        pairs = inherited_pairs+complete_pairs
        complete_keys = {(r['campaign'],r['role'],r['reference'],r['candidate']) for r in complete_pairs}
        self.check(len(complete_keys)==len(complete_pairs), 'Duplicate complete pair records')
        for row in pairs:
            g = grouped.get((row['campaign'], row['role']), {})
            a, b = g.get(row['reference']), g.get(row['candidate'])
            if a is None or b is None:
                self.check(False, 'Pair contains missing arm', pair=row)
                continue
            own = self.derived_pair(a, b)
            for prefix, arm in [('reference',a),('candidate',b)]:
                for field in ('U','L','gap','relative_gap'):
                    self.check(same_number(row[prefix+'_'+field],arm[field]), 'Pair endpoint values differ from per-arm report',
                               pair=row,field=prefix+'_'+field)
            for field, val in own.items():
                if field not in row:
                    continue
                observed = truth(row[field]) if isinstance(val, bool) else row[field] if isinstance(val,str) else number(row[field])
                self.check(observed==val, 'Complete/censored/material pair claim differs', field=field, pair=row,
                           independent=val)
        for (camp, role), group in grouped.items():
            if 'H-SUBMIT' not in group:
                continue
            for reference in ('P-GRB','ENS-C','J-SUBMIT'):
                if reference not in group:
                    continue
                a, b = group[reference], group['H-SUBMIT']
                self.check((camp,role,reference,'H-SUBMIT') in complete_keys,
                           'Complete attribution/protection pair is missing',campaign=camp,role=role,reference=reference)
                self.check(a['input_sha256']==b['input_sha256'] and number(a['cap'])==number(b['cap']),
                           'Performance comparison lacks identical input/common budget', campaign=camp, role=role, reference=reference)
                self.result['comparisons'].append(dict(campaign=camp, role=role, reference=reference,
                                                       candidate='H-SUBMIT', qualification_only=(camp=='native01'),
                                                       **self.derived_pair(a,b)))
        pairs = self.table(Path(self.args.reports)/'checkpoint_pairs.csv')
        groups = {}
        for k, row in self.checkpoint_rows.items():
            if truth(row['covered']):
                groups.setdefault((k[0],k[2],k[4]),{})[k[3]] = row
        for row in pairs:
            g = groups.get((row['campaign'],row['role'],number(row['checkpoint_full_seconds'])),{})
            a, b = g.get(row['reference']), g.get(row['candidate'])
            if a is None or b is None:
                self.check(False, 'Checkpoint pair uses an uncovered prefix', pair=row)
                continue
            au, bu, ag, bg = number(a['U']), number(b['U']), number(a['gap']), number(b['gap'])
            ud = bu-au if au is not None and bu is not None else None
            gd = bg-ag if ag is not None and bg is not None else None
            mu = ud is not None and abs(ud)>=self.material['UB_absolute'] and abs(ud)/max(abs(au),1e-12)>=self.material['UB_relative']
            mg = gd is not None and abs(gd)>=self.material['gap_absolute'] and abs(gd)/max(abs(ag),1e-12)>=self.material['gap_relative']
            for field,val in [('U_delta',ud),('gap_delta',gd)]:
                self.check(same_number(row[field],val), 'Checkpoint material delta/sign differs', field=field, pair=row)
            for prefix, arm in [('reference',a),('candidate',b)]:
                for field in ('U','L','gap'):
                    self.check(same_number(row[prefix+'_'+field],arm[field]), 'Checkpoint pair copied a different point',
                               pair=row,field=prefix+'_'+field)
            self.check(truth(row['material_U_change'])==mu and truth(row['material_gap_change'])==mg,
                       'Checkpoint materiality threshold differs', pair=row)
            if row['candidate']=='H-SUBMIT':
                self.result['checkpoint_findings'].append(dict(campaign=row['campaign'],role=row['role'],
                    reference=row['reference'], checkpoint=number(row['checkpoint_full_seconds']),
                    signed_U_delta=ud,signed_gap_delta=gd,material_U=mu,material_gap=mg))

    def hull_accounting(self, destination):
        totals = dict(auxiliary_Optimize_calls=0, DP_calls=0, unmatched_Optimize_returns=0,
                      unmatched_DP_returns=0, noncached_batches=0, cache_hits=0)
        folder = destination/'external/native_logs'
        paths = sorted(folder.glob('*.round103.calls.jsonl'))
        summaries = sorted(folder.glob('*.round103.summary.json'))
        summary_by_prefix = {str(p).removesuffix('.summary.json'):p for p in summaries}
        for path in paths:
            self.reviewed_call_ledgers.add(path)
            prefix = str(path).removesuffix('.calls.jsonl')
            events = self.lines(path)
            ob = [r for r in events if r['event']=='Optimize_begin']
            orr = [r for r in events if r['event']=='Optimize_return']
            db = [r for r in events if r['event']=='DP_begin']
            dr = [r for r in events if r['event']=='DP_return']
            totals['auxiliary_Optimize_calls'] += len(ob)
            totals['DP_calls'] += len(db)
            totals['unmatched_Optimize_returns'] += len(ob)-len(orr)
            totals['unmatched_DP_returns'] += len(db)-len(dr)
            self.check(len(ob)>=len(orr) and len(db)>=len(dr), 'Auxiliary returns exceed attempts', path=str(path))
            self.check([r['serial'] for r in orr]==[r['serial'] for r in ob[:len(orr)]],
                       'Auxiliary serial return order differs', path=str(path))
            self.check([r['serial'] for r in ob]==list(range(1,len(ob)+1)),
                       'Auxiliary attempts have missing/duplicated serials',path=str(path))
            for begin, end in zip(db,dr):
                self.check(begin['vehicle']==end['proof']['vehicle'], 'DP returned a different vehicle',path=str(path))
            sp = summary_by_prefix.get(prefix)
            if sp is None:
                self.warning('Unfinished/orphan auxiliary attempt log retained; must remain billed', path=str(path),
                             Optimize_attempts=len(ob), DP_attempts=len(db))
            else:
                summary = self.load(sp)
                self.check(not summary['cache_hit'] and summary['Optimize_calls']==len(ob) and summary['DP_calls']==len(db),
                           'Auxiliary summary counts differ from actual begin records', path=str(sp))
        for path in summaries:
            summary = self.load(path)
            if summary['cache_hit']:
                totals['cache_hits'] += 1
                self.check(summary.get('Optimize_calls',0)==0 and summary.get('DP_calls',0)==0,
                           'Cache hit charged new auxiliary calls', path=str(path))
                paid = self.load(summary['paid_evidence'])
                if paid:
                    self.check(summary['canonical_sha256']==paid['canonical_sha256'], 'Cache paid identity differs', path=str(path))
            else:
                totals['noncached_batches'] += 1
                self.check(Path(str(path).removesuffix('.summary.json')+'.calls.jsonl') in paths,
                           'Noncached auxiliary summary lacks actual attempt log', path=str(path))
        return totals

    def inherited_R102_accounting(self, destination):
        destination = Path(destination)
        if destination in self.inherited_DP_cache:
            return self.inherited_DP_cache[destination]
        records = []
        for path in sorted((destination/'external/native_logs').glob('*.round102.summary.json')):
            saved = self.load(path)
            if saved is None:
                continue
            count = saved['dp_calls']
            directions,cache = saved['directions'],saved['cache_hits']
            self.check(isinstance(count,int) and count>=0 and isinstance(directions,int) and directions>=0 and
                       isinstance(cache,int) and cache>=0, 'Inherited R102 counters are invalid',path=str(path))
            self.check(directions==count+cache, 'Inherited R102 direction/cache accounting differs',path=str(path))
            self.check(saved['mode']=='submit' and saved['range']=='root' and not saved['failure'],
                       'Inherited R102 summary lacks completed same-arm attribution',path=str(path))
            records.append(dict(path=str(path),sha256=self.sha(path),dp_calls=count,directions=directions,
                                cache_hits=cache,submitted=saved['submitted'],
                                scope='Production-returned R102 summary counter only; no BEGIN ledger reconstructed or independent repricing.'))
        result = dict(inherited_R102_DP_calls=sum(r['dp_calls'] for r in records),summaries=records)
        self.inherited_DP_cache[destination] = result
        return result

    def costs(self):
        rows = self.table(Path(self.args.reports)/'whole_run_costs.csv')
        by = {key(r):r for r in rows}
        self.check(set(by)==set(self.context), 'Whole-cost table omits or invents arms')
        for k, ctx in self.context.items():
            audit, completion = ctx['audit'], ctx['completion']
            observations = self.observations_for(k)
            native = sum(v['payload']['kind']=='call' for v in observations)
            returned = sum(v['payload']['kind']=='returned' for v in observations)
            self.check(native==audit['native_calls_started'] and returned==audit['native_calls_returned'],
                       'Native attempt/return ledger differs from committed observations', run=k)
            hull = self.hull_accounting(ctx['destination'])
            inherited = self.inherited_R102_accounting(ctx['destination'])
            declared = audit.get('resource_hull', {})
            self.check(hull['auxiliary_Optimize_calls']==declared.get('auxiliary_Optimize_calls',0) and
                       hull['DP_calls']==declared.get('DP_calls',0), 'Actual auxiliary attempts omitted from audit accounting', run=k,
                       actual=hull, declared=declared)
            post = audit.get('offline_audit_seconds',0)
            charged = completion['end_to_end_seconds']+post
            row = by.get(k)
            if row:
                for field,val in [('native_Optimize_calls',native),('auxiliary_Optimize_calls',hull['auxiliary_Optimize_calls']),
                                  ('DP_calls',hull['DP_calls']),('postexit_audit_seconds',post),
                                  ('process_and_admission_seconds',completion['end_to_end_seconds']),('charged_seconds',charged)]:
                    self.check(same_number(row[field],val), 'Whole cost omits calls or double-adds nested time', run=k, field=field)
            label = f'{k[0]}/{k[1]}/{k[2]}/{k[3]}'
            self.expected_fees[label] = dict(seconds=charged, starts=1, failed=not ctx['audit']['passed'],
                                             native_Optimize_calls=native,auxiliary_Optimize_calls=hull['auxiliary_Optimize_calls'],
                                             resource_hull_DP_calls=hull['DP_calls'],
                                             inherited_R102_DP_calls=inherited['inherited_R102_DP_calls'],
                                             DP_calls=hull['DP_calls']+inherited['inherited_R102_DP_calls'])
            self.result['run_accounting'].append(dict(run=list(k), charged_seconds=charged,
                                                      postexit_audit_seconds=post,native_Optimize_calls=native,**hull,
                                                      resource_hull_DP_calls=hull['DP_calls'],
                                                      inherited_R102_DP_calls=inherited['inherited_R102_DP_calls'],
                                                      all_DP_calls=hull['DP_calls']+inherited['inherited_R102_DP_calls'],
                                                      inherited_R102_summaries=inherited['summaries']))
            if inherited['summaries']:
                self.check(k==('protection01',4,'F2','J-SUBMIT') and len(inherited['summaries'])==2 and
                           sorted(r['dp_calls'] for r in inherited['summaries'])==[0,52],
                           'Additional inherited R102 accounting differs from the newly identified same-arm evidence',run=k,
                           inherited=inherited)
                self.warning('Preserved whole_run_costs.csv DP_calls is the R103-hull subset; corrected fees include inherited R102 DP separately.',
                             run=k,resource_hull_DP_calls=hull['DP_calls'],inherited_R102_DP_calls=inherited['inherited_R102_DP_calls'])
        # The per-batch seconds are included in these complete outer receipts.
        native_table = self.table(Path(self.args.reports)/'hull_native_calls.csv', required=False)
        for row in native_table:
            p = ROOT/row['path']
            self.check(p.exists() and self.sha(p)==row['sha256'], 'Hull report summary digest differs', path=row['path'])
            if p.exists():
                saved = self.load(p)
                for field in ('seconds','Optimize_calls','DP_calls','submitted'):
                    if field in saved:
                        self.check(same_number(row.get(field),saved[field]), 'Hull report changed batch seconds/calls', path=row['path'],field=field)
        self.warning('Nested preparation/master/DP seconds are descriptive subsets; only complete outer receipts plus postexit audit are billed.')

    def diagnostic_counts(self, label):
        name = label.removeprefix('fees/')
        result = dict(native_Optimize_calls=0,auxiliary_Optimize_calls=0,DP_calls=0,
                      model_read_attempts=None)
        d = OUT/'diagnostics'/name.removeprefix('point_')
        launch = self.load(OUT/'fees'/name/'launch.json')
        argv = list(map(str,launch['command'])) if launch else []
        for index,arg in enumerate(argv):
            if Path(arg).name in ('round103_verify_evidence.py','round103_small_hull.py'):
                self.check(index+1<len(argv), 'Diagnostic launch lacks its actual artifact label',label=label)
                if index+1<len(argv):
                    d = OUT/'diagnostics'/argv[index+1]
                break
        if name=='independent_review01':
            calls = self.lines('review/independent_review01.calls.jsonl')
            self.reviewed_call_ledgers.add(self.path('review/independent_review01.calls.jsonl'))
            self.check(any(e.get('event')=='audit_failure' for e in calls),
                       'Original independent review assertion failure log missing')
            q = self.load('review/independent_review01.conclusion.json')
            if q:
                result['DP_calls'] = q['independent_counts']['DP_attempts']
                result['model_read_attempts'] = q['independent_counts']['model_read_attempts']
                self.check(q['receipt_preserved']['exit_code']==1 and not q['receipt_preserved']['rerun'],
                           'Original mathematical review failure was hidden or rerun')
            return result
        if not d.exists():
            command = ' '.join(argv)
            self.check(any(s in command for s in ('round103_results.py','round103_verify_evidence.py','round103_final_review.py')),
                       'Unknown fee batch cannot be assigned zero calls by assumption', label=label)
            return result
        if name=='root_faults01':
            q = self.load(d/'summary.json')
            if q:
                records = q['records']
                result.update(native_Optimize_calls=sum(r['required_LP_Optimize'] for r in records),
                              auxiliary_Optimize_calls=sum(r['auxiliary_Optimize_calls'] for r in records),
                              DP_calls=sum(r['DP_calls'] for r in records))
                for record in records:
                    child = d/record['case']
                    launch = self.load(child/'launch.json')
                    collision = Path(launch['collision']) if launch else None
                    events = []
                    for path in (child/'external/native_logs').glob('*.round103.calls.jsonl'):
                        self.reviewed_call_ledgers.add(path)
                        if path==collision:
                            self.sha(path)
                            self.check(path.read_text(encoding='utf-8')=='exclusive intentional fault marker\n',
                                       'Declared collision marker changed',path=str(path))
                            continue
                        events.extend(self.lines(path))
                    self.check(sum(e['event']=='Optimize_begin' for e in events)==record['auxiliary_Optimize_calls'] and
                               sum(e['event']=='DP_begin' for e in events)==record['DP_calls'],
                               'Paid fault qualification omitted actual auxiliary attempts',case=record['case'])
                    for kind in ('Optimize','DP'):
                        begun = sum(e['event']==kind+'_begin' for e in events)
                        ended = sum(e['event']==kind+'_return' for e in events)
                        self.check(ended<=begun, 'Fault qualification contains orphan auxiliary returns',case=record['case'],kind=kind)
                        if begun!=ended:
                            self.warning('Actual failed preparation has unpaired auxiliary BEGIN records; attempts remain charged',
                                         case=record['case'],kind=kind,attempts=begun,returned=ended)
            return result
        begins = returned = 0
        for path in list(d.rglob('master_calls.jsonl'))+list(d.glob('outer_calls.jsonl'))+list(d.glob('enum_master_calls.jsonl')):
            self.reviewed_call_ledgers.add(path)
            events = self.lines(path)
            nb = sum(e.get('event')=='begin' for e in events)
            nr = sum(e.get('event')!='begin' for e in events)
            begins += nb
            returned += nr
            result['auxiliary_Optimize_calls'] += max(nb,nr)
            if nb:
                bp = [e for e in events if e.get('event')=='begin']
                rp = [e for e in events if e.get('event')!='begin']
                self.check(nr<=nb, 'Diagnostic LP has an orphan return',label=label,path=str(path))
                if all('call' in e for e in bp+rp):
                    self.check([e['call'] for e in rp]==[e['call'] for e in bp[:nr]],
                               'Diagnostic LP return serial lacks its BEGIN',label=label,path=str(path))
                if nb!=nr:
                    self.warning('Diagnostic LP retains an unmatched BEGIN',label=label,path=str(path),attempts=nb,returned=nr)
        if (d/'Optimize_begin.json').exists():
            result['auxiliary_Optimize_calls'] += 1
            begins += 1
            returned += int((d/'Optimize_return.json').exists())
        db = dr = 0
        for path in d.rglob('oracle_attempts.jsonl'):
            events = self.lines(path)
            begun = [e for e in events if e.get('event')=='begin']
            ended = [e for e in events if e.get('event')=='return']
            db += len(begun)
            self.check(len(ended)<=len(begun) and [e['call'] for e in ended]==[e['call'] for e in begun[:len(ended)]],
                       'Diagnostic DP return lacks matching BEGIN',label=label,path=str(path))
            for b,e in zip(begun,ended):
                self.check(b['vehicle']==e['vehicle'], 'Diagnostic DP return changed vehicle',label=label,path=str(path))
            if len(begun)!=len(ended):
                self.warning('Diagnostic DP retains unpaired BEGIN attempts',label=label,path=str(path),
                             attempts=len(begun),returned=len(ended))
        for path in d.rglob('oracle_calls.jsonl'):
            self.reviewed_call_ledgers.add(path)
            dr += len(self.lines(path))
        result['DP_calls'] = max(db,dr)
        if begins!=returned or db!=dr:
            self.warning('Historical return-only/unfinished diagnostic counts remain weaker attempt evidence',
                         label=label,LP_begin=begins,LP_return=returned,DP_begin=db,DP_return=dr)
        summary = self.load(d/'summary.json',required=False) or {}
        for field in ('total_Optimize_calls','Optimize_calls'):
            if field in summary:
                self.check(result['auxiliary_Optimize_calls']==summary[field],
                           'Diagnostic LP summary differs from preserved attempts/returns',label=label,field=field)
        if 'outer_Optimize_calls' in summary:
            self.check(result['auxiliary_Optimize_calls']==summary['outer_Optimize_calls']+summary['master_Optimize_calls'],
                       'Diagnostic outer/master LP calls differ',label=label)
        for field in ('total_DP_calls','DP_calls'):
            if field in summary:
                self.check(result['DP_calls']==summary[field], 'Diagnostic DP summary differs from logs',label=label)
        if (d/'model_reads.jsonl').exists():
            reads = self.lines(d/'model_reads.jsonl')
            rb = [e for e in reads if e.get('event')=='begin']
            rr = [e for e in reads if e.get('event')=='return']
            result['model_read_attempts'] = len(rb)
            self.check(len(rr)<=len(rb) and [e['call'] for e in rr]==[e['call'] for e in rb[:len(rr)]],
                       'Model-read returns lack matching attempts',label=label)
            self.check([e['call'] for e in rb]==list(range(1,len(rb)+1)),
                       'Model-read attempts have missing/duplicate serials',label=label)
            if len(rb)!=len(rr):
                self.warning('Unpaired model-read attempts remain billed and unsuccessful',label=label,
                             attempts=len(rb),returned=len(rr))
            if 'successful_model_reads' in summary:
                self.check(summary['successful_model_reads']==sum(truth(e.get('success')) for e in rr),
                           'Successful model-read summary differs',label=label)
        if 'model_read_attempts' in summary:
            self.check(result['model_read_attempts'] is None or result['model_read_attempts']==summary['model_read_attempts'],
                       'Model-read summary omitted an attempt',label=label)
            result['model_read_attempts'] = summary['model_read_attempts']
        if result['model_read_attempts'] is None and (d/'matrix.txt').exists():
            result['model_read_attempts'] = 1
            self.warning('Legacy model read evidenced only by its produced matrix; no begin ledger reconstructed',label=label)
        return result

    def call_ledger_inventory(self):
        paths = set(OUT.rglob('*calls.jsonl'))
        unassigned = []
        for path in sorted(paths-self.reviewed_call_ledgers):
            records = self.lines(path)
            entry = dict(path=str(path),records=len(records),
                         begin_records=sum(str(e.get('event','')).lower().endswith('begin') for e in records),
                         return_records=sum(str(e.get('event','')).lower().endswith('return') for e in records))
            unassigned.append(entry)
            self.check(False, 'Orphan call ledger has no reviewed paid receipt association; do not silently assign zero cost',**entry)
        self.result['call_ledger_inventory'] = dict(actual_files=len(paths),reviewed_files=len(paths & self.reviewed_call_ledgers),
                                                  orphan_ledgers=unassigned)

    def fees(self):
        table = self.table(Path(self.args.fees)/'fees.csv')
        reconciled = self.load(Path(self.args.fees)/'fee_reconciliation.json')
        if reconciled is None:
            return
        by = {r['label']:r for r in table}
        self.check(len(by)==len(table), 'Duplicate billed labels/double billing')
        # Account all prepared campaigns, including qualification and failures,
        # independently of the subset chosen for performance reporting.
        for identity_path in sorted(OUT.glob('*/identity.json')):
            q = self.load(identity_path)
            if 'launches' not in q:
                continue
            camp = identity_path.parent
            done = {int(r['number']):r for r in self.lines(camp/'summary.jsonl',required=False)}
            for a in q['launches']:
                label = f'{camp.name}/{a["number"]}/{a["id"]}/{a["arm"]}'
                if int(a['number']) not in done:
                    self.check(False, 'Prepared campaign has an unclosed or reserved arm at final review', label=label)
                    continue
                r = done[int(a['number'])]
                audit = self.load(Path(a['destination'])/'audit.json')
                if audit is None:
                    continue
                hull = self.hull_accounting(Path(a['destination']))
                inherited = self.inherited_R102_accounting(Path(a['destination']))
                self.expected_fees[label] = dict(seconds=r['completion']['end_to_end_seconds']+audit.get('offline_audit_seconds',0),
                    starts=1,failed=not r['audit_passed'],native_Optimize_calls=audit['native_calls_started'],
                    auxiliary_Optimize_calls=hull['auxiliary_Optimize_calls'],resource_hull_DP_calls=hull['DP_calls'],
                    inherited_R102_DP_calls=inherited['inherited_R102_DP_calls'],
                    DP_calls=hull['DP_calls']+inherited['inherited_R102_DP_calls'])
            ref = self.load(camp/'reference_batch_receipt.json',required=False)
            if ref:
                self.check(ref['optimizer_calls']==0 and ref['outer_seconds']+1e-7>=ref['child_seconds'],
                           'Reference batch counted nested seconds twice or launched Optimize',campaign=camp.name)
                self.expected_fees[camp.name+'/reference_batch'] = dict(seconds=ref['outer_seconds'],starts=ref['actual_children'],
                                                                        native_Optimize_calls=0,auxiliary_Optimize_calls=0,DP_calls=0)
        current = OUT/'fees'/self.args.receipt_label
        current_launch = self.load(current/'launch.json')
        self.check(current_launch is not None and not (current/'receipt.json').exists(),
                   'Final review must run once inside its own currently open exclusive receipt',label=self.args.receipt_label)
        own_cap = current_launch['cap_seconds'] if current_launch else 0
        for launch_path in sorted((OUT/'fees').glob('*/launch.json')):
            if launch_path.parent==current:
                continue
            receipt = self.load(launch_path.parent/'receipt.json',required=False)
            allowance = self.load(launch_path.parent/'failure_allowance.json',required=False)
            label = 'fees/'+launch_path.parent.name
            if receipt:
                counts = self.diagnostic_counts(label)
                self.expected_fees[label] = dict(seconds=receipt['outer_seconds'],starts=1,failed=receipt['exit_code']!=0,**counts)
            elif allowance:
                self.expected_fees[allowance['label']] = allowance
            else:
                self.result['missing'].append(str(launch_path.parent/'receipt.json'))
        allowances = self.load('additional_fee_allowances.json',required=False)
        if allowances:
            for record in allowances['fees']:
                self.check(record['label'] not in self.expected_fees, 'Allowance double-counts an existing complete receipt',label=record['label'])
                self.expected_fees[record['label']] = record
        self.check(set(by)==set(self.expected_fees), 'Whole-round fee table omissions or invented duplicate scopes',
                   missing=list(set(self.expected_fees)-set(by)),extra=list(set(by)-set(self.expected_fees)))
        for label, expected in self.expected_fees.items():
            row = by.get(label)
            if row is None:
                continue
            for field in ('seconds','starts','native_Optimize_calls','auxiliary_Optimize_calls','DP_calls',
                          'resource_hull_DP_calls','inherited_R102_DP_calls','model_read_attempts'):
                val = expected.get(field, expected.get('Optimize_calls',0) if field=='native_Optimize_calls' else 0)
                if field in row:
                    if field in ('resource_hull_DP_calls','inherited_R102_DP_calls') and (
                            field not in expected or (row[field]=='' and not expected.get('inherited_R102_DP_calls',0))):
                        continue
                    if field=='model_read_attempts' and (field not in expected or val is None):
                        continue
                    self.check(same_number(row[field] or 0,val), 'Fee row changed actual cost/attempts',label=label,field=field,independent=val)
            if 'failed' in expected:
                self.check(truth(row.get('failed'))==expected['failed'], 'Failed billed experiment was hidden',label=label)
            if expected.get('inherited_R102_DP_calls',0):
                self.check(all(field in row and row[field]!='' for field in ('resource_hull_DP_calls','inherited_R102_DP_calls')),
                           'Inherited R102 DP fee correction lacks explicit new/inherited classification',label=label)
                self.check(number(row['DP_calls'])==number(row['resource_hull_DP_calls'])+number(row['inherited_R102_DP_calls']),
                           'Same-arm total DP fee counter omits or double counts inherited calls',label=label)
        total = math.fsum(number(r['seconds']) for r in table)
        starts = sum(int(float(r.get('starts') or 1)) for r in table)
        self.check(close(total,reconciled['completed_seconds']), 'Fee total does not equal unique outer receipts')
        self.check(starts==reconciled['completed_starts'], 'Experimental start total differs')
        for field, rec_field in [('native_Optimize_calls','actual_native_Optimize_calls'),
                                 ('auxiliary_Optimize_calls','actual_auxiliary_Optimize_calls'),('DP_calls','actual_DP_calls')]:
            actual = sum(int(float(r.get(field) or 0)) for r in table)
            self.check(actual==reconciled[rec_field], 'Actual call reconciliation total differs',field=field)
        self.check(not reconciled['reserved'] and not reconciled['incomplete'], 'Fee snapshot retains pending/unclosed runs')
        failed = {r['label'] for r in table if truth(r.get('failed'))}
        self.check(failed==set(reconciled['experimental_failures']), 'Failure list changed')
        self.check(starts+1<=self.protocol['max_starts'] and total+own_cap<=self.protocol['max_outer_seconds'],
                   'Whole-round budget lacks room for this separately billed final review',base_starts=starts,base_seconds=total,own_cap=own_cap)
        self.result['fee_snapshot'] = dict(completed_starts_before_this_review=starts,completed_seconds_before_this_review=total,
            current_review_receipt=self.args.receipt_label,current_review_cap_reserved=own_cap,
            current_review_not_in_snapshot=True,
            final_action_required='After this receipt closes, perform pure-engineering fee reconciliation including its actual seconds and failure status. Do not add nested call seconds.')
        inherited_total = sum(e.get('inherited_R102_DP_calls',0) for e in self.expected_fees.values())
        actual_DP_total = sum(int(float(r.get('DP_calls') or 0)) for r in table)
        prior = self.load('review/round103_final_review01.json')
        prior_receipt = self.load('fees/independent_final01/receipt.json')
        old_fees = self.load('fees_prefinal01/fee_reconciliation.json')
        self.check(inherited_total==52, 'Whole-round inherited DP correction differs from the two original J summaries',inherited_total=inherited_total)
        if prior and prior_receipt and old_fees:
            self.check(prior['status']=='PASSED_METADATA_WITH_DECLARED_LIMITATIONS' and prior_receipt['exit_code']==0,
                       'Prior completed metadata review was overwritten or its status changed')
            self.check(actual_DP_total==old_fees['actual_DP_calls']+52,
                       'Supplementary actual DP total changed beyond the newly found 52 inherited calls')
            self.check(starts==old_fees['completed_starts']+1 and
                       close(total,old_fees['completed_seconds']+prior_receipt['outer_seconds']),
                       'Inherited DP correction added time/starts beyond the already-paid prior metadata reader')
            self.result['inherited_DP_correction'] = dict(prior_review_preserved=True,
                prior_snapshot_actual_DP_calls=old_fees['actual_DP_calls'],inherited_R102_DP_calls=inherited_total,
                corrected_actual_DP_calls=actual_DP_total,added_DP_seconds=0,added_DP_starts=0,
                scope='52 production-returned inherited R102 DP calls were omitted by the former R103-only counter scope. '
                      'The two old summaries are read only; no invented BEGINs, repricing, model read, Optimize or B&B rerun. '
                      'The separately billed supplementary reader remains an additional start and its own outer seconds.')

    def decision(self):
        decision = self.load(self.args.decision)
        if decision is None:
            return
        required = ('decision','reason','protected_default','main_benchmark','candidate_default_enabled',
                    'no_candidate_revision','confirmation','long')
        for field in required:
            self.check(field in decision, 'Conditional decision lacks an explicit field',field=field)
        if any(field not in decision for field in required):
            return
        self.check(decision['protected_default']=='ENS-C' and decision['main_benchmark']=='P-GRB' and
                   decision['candidate_default_enabled'] is False and decision['no_candidate_revision'] is True,
                   'Decision alters protected default/benchmark or frozen candidate')
        self.check(bool(decision['reason']), 'Admission/cancellation reason is absent')
        self.check(decision['decision'] in ('admit','cancel'), 'Unknown conditional decision; do not infer an outcome')
        # Admission is immutable historical evidence. New confirmation losses
        # affect final recommendation; they cannot invalidate that past choice.
        for field in ('evidence_report','evidence_clocks','completed_development_arms','qualification_arms_separate'):
            self.check(field in decision, 'Admission lacks its dated development evidence scope',field=field)
        report_name = decision.get('evidence_report')
        clocks_name = decision.get('evidence_clocks')
        stage_rows = self.table(Path(report_name)/'runs.csv') if report_name else []
        stage_identity = self.load(Path(report_name)/'reporting_identity.json') if report_name else None
        if stage_identity:
            self.check(stage_identity['Optimize_calls']==0 and stage_identity['no_recovery_overlay'],
                       'Admission report used reconstructed evidence or Optimize')
        stage_keys = {key(r) for r in stage_rows}
        development = [r for r in stage_rows if r['campaign']!='native01']
        qualification = [r for r in stage_rows if r['campaign']=='native01']
        self.check(len(stage_keys)==len(stage_rows), 'Admission snapshot duplicates arms')
        self.check(len(development)==decision.get('completed_development_arms') and
                   len(qualification)==decision.get('qualification_arms_separate'),
                   'Admission completed/qualification arm counts changed',development=len(development),qualification=len(qualification))
        self.check({r['role'] for r in development}=={'F2','R98-C2','R99-N2','R98-C3'},
                   'Historical admission omitted a development/protection role')
        stages = ('confirmation01','confirmation_long01','long_tail01')
        self.check(not any(r['campaign'] in stages for r in stage_rows),
                   'Historical admission snapshot contains later confirmation results')
        for row in stage_rows:
            k = key(row)
            final_row = self.endpoint_rows.get(k)
            self.check(final_row is not None, 'Historical completed arm omitted from final evidence',run=k)
            if final_row:
                for field in ('U','L','gap','relative_gap','outer_seconds','end_to_end_seconds'):
                    self.check(same_number(row[field],final_row[field]), 'Final report rewrites historical admission evidence',run=k,field=field)
                for field in ('input_sha256','binary_sha256','receipt_sha256','original_audit_sha256','certificate'):
                    self.check(row[field]==final_row[field], 'Historical identity/certificate changed',run=k,field=field)
        stage_groups = {}
        for row in development:
            stage_groups.setdefault((row['campaign'],row['role']),{})[row['arm']] = row
        stage_comparisons = []
        for (camp,role),group in stage_groups.items():
            if 'H-SUBMIT' not in group:
                continue
            for ref in ('P-GRB','ENS-C','J-SUBMIT'):
                if ref in group:
                    stage_comparisons.append(dict(campaign=camp,role=role,reference=ref,candidate='H-SUBMIT',
                                                  **self.derived_pair(group[ref],group['H-SUBMIT'])))
        stage_checkpoints = self.table(Path(clocks_name)/'checkpoints.csv') if clocks_name else []
        cp_groups = {}
        for row in stage_checkpoints:
            k,cp = key(row),number(row['checkpoint_full_seconds'])
            self.check(k in stage_keys, 'Admission checkpoint refers outside completed snapshot',run=k)
            final_cp = self.checkpoint_rows.get(k+(cp,))
            self.check(final_cp is not None, 'Final report omits historical admission checkpoint',run=k,checkpoint=cp)
            if final_cp:
                for field in ('U','L','gap','relative_gap'):
                    self.check(same_number(row[field],final_cp[field]), 'Final report rewrites admission checkpoint',run=k,checkpoint=cp,field=field)
                self.check(row['covered']==final_cp['covered'], 'Historical checkpoint coverage changed',run=k,checkpoint=cp)
            if truth(row['covered']) and row['campaign']!='native01':
                cp_groups.setdefault((row['campaign'],row['role'],cp),{})[row['arm']] = row
        stage_prefix = []
        for (camp,role,cp),group in cp_groups.items():
            if 'H-SUBMIT' not in group or 'ENS-C' not in group:
                continue
            a,b = group['ENS-C'],group['H-SUBMIT']
            au,bu,ag,bg = number(a['U']),number(b['U']),number(a['gap']),number(b['gap'])
            ud = bu-au if au is not None and bu is not None else None
            gd = bg-ag if ag is not None and bg is not None else None
            stage_prefix.append(dict(campaign=camp,role=role,reference='ENS-C',checkpoint=cp,
                signed_U_delta=ud,signed_gap_delta=gd,
                material_U=ud is not None and abs(ud)>=self.material['UB_absolute'] and abs(ud)/max(abs(au),1e-12)>=self.material['UB_relative'],
                material_gap=gd is not None and abs(gd)>=self.material['gap_absolute'] and abs(gd)/max(abs(ag),1e-12)>=self.material['gap_relative']))
        severe = [r for r in stage_comparisons if r['reference']=='ENS-C' and
                  (r['severe_time_regression'] or r['severe_one_sided_time_regression'])]
        wins = [r for r in stage_comparisons if r['reference']=='ENS-C' and
                ((r['certified_time_delta'] is not None and r['certified_time_delta']<0 and r['material_time_change']) or
                 r['material_one_sided_time_advantage'])]
        prefix_wins = [r for r in stage_prefix if (r['material_U'] and r['signed_U_delta']<0) or
                       (r['material_gap'] and r['signed_gap_delta']<0)]
        self.result['admission_context'] = dict(evidence_report=report_name,evidence_clocks=clocks_name,
            development_arms=len(development),qualification_arms_separate=len(qualification),
            severe_ENS_regressions=severe,all_development_comparisons=stage_comparisons,
            material_ENS_certification_advantages=wins,material_ENS_common_checkpoint_advantages=prefix_wins,
            reason=decision['reason'],decision=decision['decision'],admission_sha256=self.sha(self.path(self.args.decision)),
            scope='Only evidence completed before confirmation. Historical pending recommendation is preserved, not a final conclusion.')
        for field in ('paid_row_replay','small_domain_qualification'):
            if field in decision:
                paid = self.load(decision[field])
                if paid:
                    self.check(paid['passed'], 'Admission numerical qualification/replay did not pass',field=field)
        if decision['decision']=='cancel':
            self.check(decision['confirmation']=='cancelled' and decision['long']=='cancelled',
                       'Cancellation does not explicitly cancel conditional stages')
            for stage in stages:
                self.check(not (OUT/stage/'identity.json').exists(), 'Cancelled conditional stage was nevertheless launched/prepared',stage=stage)
            if wins or prefix_wins:
                self.warning('Cancellation has isolated material advantages; final reason must discuss tradeoffs rather than claim no advantages.',
                             complete_advantages=len(wins),checkpoint_advantages=len(prefix_wins))
            self.warning('Cancellation/negative result applies to this frozen candidate and measured panel; it does not establish universal hull weakness.')
        elif decision['decision']=='admit':
            self.check(decision['confirmation']=='run' and decision['long']=='run', 'Admission omitted required conditional stages')
            self.check(bool(wins or prefix_wins), 'Admission lacks material performance advantage over ENS; diagnostic LP improvement alone is insufficient')
            if severe:
                self.warning('Historical research admission has serious protection tradeoffs; it is not default promotion.',regressions=severe)
            plan = self.load('confirmation_batch_plan.json')
            if plan:
                self.check(plan['admission_sha256']==self.sha(self.path(self.args.decision)),
                           'Historical admission bytes changed after confirmation launch')
                budget = plan['budget_before_batch']
                for field,recorded in [('completed_starts','observed_completed_starts_before_confirmation'),
                                       ('completed_seconds','observed_completed_seconds_before_confirmation')]:
                    if recorded in decision:
                        self.check(same_number(budget[field],decision[recorded]), 'Admission cutoff budget differs from launch plan',field=field)
            manifest = self.load('confirmation_freeze.json')
            if manifest:
                self.check(manifest['before_any_confirmation_search'] and manifest['no_redraw'] and manifest['Optimize_calls']==0,
                           'Confirmation roles were not frozen without search/redraw')
            long_groups = 0
            positive_medium_large = False
            role_hashes = set()
            for stage in stages:
                q = self.load(OUT/stage/'identity.json')
                records = self.lines(OUT/stage/'summary.jsonl')
                if q is None:
                    continue
                self.check(len(records)==len(q['launches']), 'Admitted conditional group incomplete',stage=stage)
                arms = {r['arm'] for r in records}
                self.check({'P-GRB','ENS-C','H-SUBMIT'}<=arms, 'Conditional group omitted a protected comparison arm',stage=stage)
                caps = {a['cap_seconds'] for a in q['launches']}
                self.check(len(caps)==1, 'Conditional group budget is not common',stage=stage)
                if stage in ('confirmation_long01','long_tail01'):
                    self.check(len(caps)==1 and 3600<=next(iter(caps))<=7200, 'Long group is not a complete common 3600-7200s group',stage=stage)
                    long_groups += 1
                if stage!='long_tail01' and q['launches']:
                    role = q['launches'][0]['panel']
                    self.check(role.get('design_isolated_in_R103') is True and role['input_sha256'] not in role_hashes,
                               'Confirmation role repeated or not design-isolated',stage=stage)
                    role_hashes.add(role['input_sha256'])
                    positive_medium_large |= role['V'] in (30,50) and role.get('zero_excluded_by_stock_shortage') is True
            self.check(len(role_hashes)>=2 and positive_medium_large and long_groups>=2,
                       'Admission did not complete two isolated confirmations and two long groups')
        final = self.load(self.args.final_decision)
        if final:
            final_fields = ('recommendation','protected_default','candidate_default_enabled','no_candidate_revision',
                            'completed_groups','cancelled_groups','reason')
            for field in final_fields:
                self.check(field in final, 'Final recommendation lacks an explicit field',field=field)
            if all(field in final for field in final_fields):
                self.check(final['protected_default']=='ENS-C' and final['candidate_default_enabled'] is False and
                           final['no_candidate_revision'] is True, 'Final recommendation changed protected default/frozen candidate')
                self.check(final['recommendation'] in ('not_promote','research_only','cancel','promote'),
                           'Final recommendation is pending or unknown')
                self.check(bool(final['reason']), 'Final recommendation reason absent')
                completed = final['completed_groups']
                cancelled = final['cancelled_groups']
                self.check(isinstance(completed,list) and isinstance(cancelled,list), 'Final group disposition is not explicit lists')
                if isinstance(completed,list) and isinstance(cancelled,list):
                    self.check(set(completed).isdisjoint(cancelled) and set(completed)|set(cancelled)==set(stages),
                               'Final group disposition omits or duplicates frozen groups',completed=completed,cancelled=cancelled)
                    for stage in stages:
                        exists = (OUT/stage/'identity.json').exists()
                        self.check(exists==(stage in completed), 'Final disposition hides an actually launched group',stage=stage)
                performances = [r for r in self.result['comparisons'] if not r['qualification_only']]
                final_severe = [r for r in performances if r['reference']=='ENS-C' and
                                (r['severe_time_regression'] or r['severe_one_sided_time_regression'])]
                confirmation_severe = [r for r in final_severe if r['campaign'] in stages]
                endpoint_losses = [r for r in performances if
                    (r['material_budget_U_change'] and r['signed_U_delta']>0) or
                    (r['material_budget_gap_change'] and r['signed_gap_delta']>0)]
                prefix_losses = [r for r in self.result['checkpoint_findings'] if
                    (r['material_U'] and r['signed_U_delta']>0) or
                    (r['material_gap'] and r['signed_gap_delta']>0)]
                if final_severe:
                    self.check(final['recommendation'] in ('not_promote','research_only','cancel'),
                               'Severe actual ENS regression did not prevent promotion',regressions=final_severe)
                declared_severe = final.get('severe_ENS_regression_groups')
                if declared_severe is not None:
                    self.check(set(declared_severe)=={r['campaign'] for r in final_severe},
                               'Final recommendation hides or invents a severe ENS regression group')
                self.result['final_recommendation_context'] = dict(recommendation=final['recommendation'],reason=final['reason'],
                    completed_groups=completed,cancelled_groups=cancelled,all_actual_comparisons=performances,
                    all_severe_ENS_regressions=final_severe,new_confirmation_severe_ENS_regressions=confirmation_severe,
                    all_material_budget_endpoint_regressions=endpoint_losses,
                    all_material_common_checkpoint_regressions=prefix_losses,
                    protected_default='ENS-C',candidate_default_enabled=False,
                    scope='New counterexamples influence final recommendation without rewriting past experimental admission. '
                          'Observed negative result applies to this implementation/panel, not universal hull weakness or pure-cut causality.')
                self.warning('Independent metadata review cannot establish a pure-cut causal estimate, universal hull weakness or stability from this finite panel.')
        prior = self.load('review/independent_review01.conclusion.json')
        raw = self.load('review/independent_review01.json')
        receipt = self.load('fees/independent_review01/receipt.json')
        if prior and raw and receipt:
            self.check(receipt['exit_code']==1 and raw['status']=='FAILED_PRESERVED_ATTEMPT' and
                       prior['receipt_preserved']['exit_code']==1, 'Independent mathematical review failure provenance rewritten')
            self.check(prior['independent_counts']['Optimize_attempts']==0 and prior['independent_counts']['DP_attempts']==40,
                       'Original paid mathematical review scope changed')
            self.result['retained_mathematical_review'] = dict(status=prior['status'],receipt_exit_code=receipt['exit_code'],
                signed_F5_base_bracket=prior['numeric_full_matrix_checks']['F5_base_signed_upper_minus_reported_outer_LB'],
                signed_F5_anchor_bracket=prior['numeric_full_matrix_checks']['F5_anchor_signed_upper_minus_reported_outer_LB'],
                numerical_checks_not_rerun=True,remaining_limitations=prior['representation_findings'])

    def run(self):
        self.target = HERE/(self.args.output+'.json')
        if self.target.exists():
            raise FileExistsError('Fresh output label required; prior failed review must remain: '+str(self.target))
        self.save()
        for name, call in [('run_metadata',self.run_metadata),('clocks',self.clocks),
                           ('comparisons',self.comparisons),('actual_calls_costs',self.costs),
                           ('whole_round_fees',self.fees),('all_call_ledger_inventory',self.call_ledger_inventory),
                           ('conditional_decision_scope',self.decision)]:
            self.section(name,call)
        self.result['status'] = ('FAIL_OR_MISSING_PRESERVED' if self.result['errors'] or self.result['missing']
                                 else 'PASSED_METADATA_WITH_DECLARED_LIMITATIONS')
        self.save()
        summary = dict(status=self.result['status'],checks=self.result['checks'],errors=len(self.result['errors']),
                       missing=len(self.result['missing']),warnings=len(self.result['warnings']),
                       Optimize_calls=0,DP_calls=0,native_B_and_B_runs=0,output=str(self.target))
        print(json.dumps(summary),flush=True)
        return 1 if self.result['errors'] or self.result['missing'] else 0


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reports',default='reports_final01')
    p.add_argument('--clocks',default='reports_final01_clocks')
    p.add_argument('--fees',default='fees_final01')
    p.add_argument('--decision',default='stage_decision.json')
    p.add_argument('--final-decision',default='final_decision.json')
    p.add_argument('--output',default='round103_final_review01')
    p.add_argument('--receipt-label',required=True)
    p.add_argument('--campaigns',nargs='+',help='Explicit final authorized report campaigns; otherwise use reporting_identity.json')
    args = p.parse_args()
    if Path(args.output).name!=args.output:
        p.error('--output is a fresh simple label, not a path')
    sys.exit(Review(args).run())
