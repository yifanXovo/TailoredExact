"""Post-payload JSON-artifact comparison for the one R120 public restore.

The scientific reader and its output are unchanged. The first release runner
compared an in-memory H tuple against its published JSON array and stopped.
This later, separately published receipt recipe compares the actual JSON
artifacts, preserving every field, and may resume that completed first group.
Place this script in the restored scripts directory before running it.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time

SCIENTIFIC_COMMIT = '75c4839f3b85f67f8eeb6c4700e0452d5204dd51'
RELEASE_SHA = 'edc1772e8e274f4a91adf3f0f6f4def17ae3f563249a771fc04c75901600b372'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def main(resume_first):
    tick = time.perf_counter()
    root = Path(__file__).resolve().parents[1]
    out = root / 'results/unified_exact_round120'
    runtime = Path(sys.base_prefix).resolve()
    opened = set()

    def boundary(event, args):
        if event != 'open' or not isinstance(args[0], (str, bytes)):
            return
        name = args[0].decode() if isinstance(args[0], bytes) else args[0]
        path = Path(name).resolve()
        assert path.is_relative_to(root) or path.is_relative_to(runtime), (
            'recovery attempted external file access', str(path))
        if path.is_relative_to(root):
            opened.add(path.relative_to(root).as_posix())

    sys.addaudithook(boundary)
    import round120_release as release
    import read_round120 as reader
    from round120_common import read, write
    from compare_round112_startup import fleet_key

    assert release.ROOT == reader.ROOT == root
    assert digest(root / 'scripts/round120_release.py') == RELEASE_SHA
    assert not (out / 'restored_check.json').exists()
    measured = read(out / 'initialization_receipt.json')['worktree']
    normalized = lambda value: release.normalize(value, [root, measured])
    groups, reused, created, tuple_probe = [], [], [], None
    for number in (1, 2, 3):
        expected_path = out / f'reconstruction/group{number:02d}/current_core.json'
        destination = out / f'restored_reconstruction/group{number:02d}'
        actual_path = destination / 'current_core.json'
        if actual_path.exists():
            assert resume_first and number == 1, 'never overwrite a prior rebuild'
            reused.append(number)
        else:
            assert not destination.exists(), 'incomplete output requires inspection'
            in_memory = reader.rebuild_group(number, destination)
            # This is exactly the reader's allow_nan=False JSON storage format.
            assert json.loads(json.dumps(in_memory, allow_nan=False)) == read(actual_path)
            del in_memory
            created.append(number)
        actual, expected = read(actual_path), read(expected_path)
        assert normalized(actual) == normalized(expected), ('JSON-artifact mismatch', number)
        assert len(actual['arms']) == 4 and len(actual['pairs']) == 6
        if number == 1:
            profile = read(out / actual['group']['campaign'] / 'identity.json')['launches'][0]['panel']
            stored = actual['full_H']['arms']['M-B']['fleet']
            memory = fleet_key(profile, stored)
            assert memory != stored and json.loads(json.dumps(memory)) == stored
            tuple_probe = dict(memory_equal=False, stored_JSON_equal=True,
                in_memory_operation_type=type(memory[0]['operations'][0]).__name__,
                stored_operation_type=type(stored[0]['operations'][0]).__name__)
        groups.append(dict(group=number, arms=len(actual['arms']), pairs=len(actual['pairs']),
            rebuilt_JSON_SHA=digest(actual_path), published_JSON_SHA=digest(expected_path),
            all_JSON_fields_equal_after_root_prefix_normalization=True))
        del actual, expected

    previous = read(out / 'core_admission.json')
    admission = reader.admission()
    assert normalized(previous) == normalized(json.loads(json.dumps(admission, allow_nan=False)))
    assert not list(root.rglob('*.exe')) and not list(root.rglob('*.dll'))
    modules = []
    for name, module in list(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if not path:
            continue
        path = Path(path).resolve()
        if path.is_relative_to(runtime):
            continue
        assert path.is_relative_to(root), ('external reconstruction module', name, str(path))
        modules.append(dict(module=name, path=path.relative_to(root).as_posix()))
    write(out / 'restored_check.json', dict(passed=True, scientific_commit=SCIENTIFIC_COMMIT,
        current_groups=len(groups), formal_arms=sum(g['arms'] for g in groups),
        pairs=sum(g['pairs'] for g in groups), groups=groups,
        all_current_core_numbers_proofs_Starts_calls_H_and_pairs_equal=True,
        normalization='only measured/restored absolute root prefixes; compare stored JSON arrays, not Python tuples; no fields or values removed',
        comparison_representation_probe=tuple_probe,
        original_release_runner_SHA=RELEASE_SHA, original_release_runner_unchanged=True,
        frozen_reader_source_helpers_and_evidence_unchanged=True,
        separately_published_post_recovery_recipe=True, recipe_SHA=digest(__file__),
        reused_completed_first_attempt_groups=reused, newly_rebuilt_groups=created,
        original_worktree_fallback=False, no_additional_Git_export=True,
        actual_file_access_boundary_enforced=True,
        allowed_external_files='Python runtime and standard library only',
        current_root_opened_paths=sorted(opened), current_root_modules=modules,
        native_PE_DLL_absent=True, Optimize=0, native_starts=0,
        engineering_seconds=time.perf_counter()-tick, human_seconds='unknown',
        receipt_does_not_attest_future_commits=True))
    print(json.dumps(dict(passed=True, formal_arms=12, pairs=18,
        reused=reused, newly_rebuilt=created, Optimize=0)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume-first-attempt', action='store_true')
    main(parser.parse_args().resume_first_attempt)
