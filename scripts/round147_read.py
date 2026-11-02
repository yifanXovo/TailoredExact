"""R137 complete verification with independent STOCK/GD switches and zero-row GD."""
import collections
import re
import types
import round137_read as accepted
import round108_reader as parser
from round138_repair import scaled_rows
from round143_qualify import actual_spec
from round146_math import compiled
from round147_common import *

configure()


def root_context(models, panel, gd, target, audits, fixture_model=None):
    """A valid omitted block returns the original model, without a GD filename."""
    metadata = models / 'round146_root.json'
    paths = sorted(models.glob('*_round146_GD.lp'), key=lambda p: int(
        re.search(r'_generation_(\d+)_round146_GD\.lp$', p.name).group(1)))
    if not gd:
        assert not paths and not metadata.exists() and not audits
        return None, None, None
    if not metadata.exists():
        # Complete H can finish before any model is constructed. A later model
        # contract will reject a missing context if a formal call actually exists.
        assert not paths and not audits
        return None, None, None
    meta = read(metadata)
    assert meta['source_solves'] == meta['new_columns'] == 0
    assert meta['rows'] in (0, 1, 2)
    if meta['rows']:
        assert paths
        first = paths[0]
    else:
        assert not paths
        originals = sorted(models.glob('*_generation_*.lp'), key=lambda p: int(
            re.search(r'_generation_(\d+)\.lp$', p.name).group(1)))
        assert originals or fixture_model is not None
        first = originals[0] if originals else fixture_model
    model = parser.lp_model(first)
    total = panel['total_initial']
    spec = actual_spec(model, max(0, total - sum(panel['Q_vector'])), total)
    block = compiled(spec, target)  # Existing pure arithmetic PE, no Native load.
    assert len(block['rows']) == meta['rows']
    assert block['applicable'] == meta['applicable']
    assert meta['Bminus'] == spec['Bminus'] and meta['B'] == spec['B']
    assert all(a['PASS'] and a['source_solves'] == a['Optimize_extra'] == a['new_columns'] == 0
               for a in audits)
    support = {int(i): set(v) for i, v in spec['supports'].items()}
    return block, support, meta


def verify(launch, identity):
    configure()
    destination = Path(launch['destination'])
    method = launch['R147_method']
    gd, stock = method in ('GD', 'STOCK_GD'), method in ('STOCK', 'STOCK_GD')
    assert launch['panel']['round138_stock_rlt'] == stock
    command = launch['command']
    assert ('--round138-stock-rlt' in command) == stock
    assert command.count('--round146-gd') == 1
    assert command[command.index('--round146-gd') + 1] == ('on' if gd else 'off')
    if stock:
        assert read(destination / 'round138_parameters.json') == dict(
            stock_rlt=True, gurobi_seed=launch['seed'], H_seed=20260626, loaded_after_presets=True)
    else:
        assert not (destination / 'round138_parameters.json').exists()
    if gd:
        assert read(destination / 'round146_parameters.json') == dict(
            GD=True, conditional=True, root_once=True, new_columns=0,
            source_solves=0, stock=stock, Seed=launch['seed'], H_seed=20260626)
    else:
        assert not (destination / 'round146_parameters.json').exists()
    audits = [read(p) for p in destination.rglob('*.round146.native.json')]
    block, support, meta = root_context(destination / 'external/models', launch['panel'], gd,
        destination / 'round147_offline_root_rows.json', audits)
    facts = []

    class Models(accepted.ArmModels):
        def model_contract(self, root, panel, path, arm):
            fact, model = super().model_contract(root, panel, path, arm)
            total = panel['total_initial']
            lower = max(0, total - sum(panel['Q_vector']))
            counter = collections.Counter(model['rows'])
            expected = collections.Counter(scaled_rows(panel['V'], *model['bounds']['G'], lower, total))
            if stock:
                assert not expected - counter, ('missing STOCK rows', path)
            else:
                assert not expected & counter, ('unexpected STOCK rows', path)
            assert not any(k.startswith('rn_') for k in model['order'])
            if gd:
                assert block is not None and support is not None
                spec = actual_spec(model, lower, total)
                assert all(set(v) <= support[int(i)] for i, v in spec['supports'].items())
                rows = [dict(r, terms={k: v for k, v in r['terms'].items() if k in model['order']})
                        for r in block['rows']]
                for row in rows:
                    assert counter[(tuple(sorted(row['terms'].items())), '>=', 0.)] == 1
                matched = [a for a in audits if a['model_SHA'] == fact['SHA']]
                assert matched and all(a['GD_rows'] == len(rows) and a['GD_nonzeros'] ==
                    sum(len(r['terms']) for r in rows) for a in matched)
                if not rows:
                    assert 'r146_GD_' not in path.read_text(encoding='utf-8')
            else:
                rows = []
                assert 'r146_GD_' not in path.read_text(encoding='utf-8')
            facts.append(dict(model_SHA=fact['SHA'], GD_rows=len(rows),
                GD_nonzeros=sum(len(r['terms']) for r in rows), stock_rows=4 if stock else 0,
                new_columns=0, actual_scope_and_rows=True))
            return fact, model

    value = types.FunctionType(accepted.verify.__code__, dict(vars(accepted),
        ROOT=ROOT, OUT=OUT, ArmModels=Models))(launch, identity)
    write(destination / 'round147_control_audit.json', dict(PASS=True, method=method,
        STOCK=stock, GD=gd, models=facts, Native_audits=audits, root_generation=meta,
        all_H_Start_physical_scope_quality_lifecycle_inherited=True,
        independent_exact_root_coefficients=gd and block is not None,
        zero_rows_use_actual_original_model=True, no_model_H_completion_supported=True,
        Optimize=0, Native_load=0))
    return value
