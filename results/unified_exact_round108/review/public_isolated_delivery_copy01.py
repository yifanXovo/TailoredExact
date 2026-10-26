#!/usr/bin/env python3
"""Deliver new public-review supplements by exact bytes; never reread old evidence."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time


PREFIX = Path('results/unified_exact_round108/review')
NEW_FILES = (
    'public_isolated_crosscheck01.py',
    'public_isolated_copy_public_metadata01.py',
    'public_isolated_finalize01.py',
    'public_isolated_review01.json',
    'public_isolated_review01.md',
)
NEW_DIRS = (
    'public_isolated_raw_audit01',
    'public_isolated_crosscheck01',
    'public_isolated_finalize01',
    'public_isolated_copy_public_metadata01',
    'public_primary_comparison_metadata01',
)
LABEL = 'public_isolated_delivery_copy01'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def inside(base, path, must_exist=True, plain_file=False):
    p = Path(os.path.abspath(path))
    assert p == p.resolve(), ('noncanonical path or link', str(p))
    rel = p.relative_to(base)
    current = base
    assert not current.is_symlink()
    for component in rel.parts:
        current /= component
        assert not current.is_symlink(), ('symlink', str(current))
    if must_exist:
        assert p.exists(), ('missing', str(p))
    if plain_file:
        assert p.is_file(), ('not plain file', str(p))
    return p


def write_json(path, obj):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--destination-root', required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    root = Path(os.path.abspath(args.root))
    destination = Path(os.path.abspath(args.destination_root))
    assert root == root.resolve() and destination == destination.resolve()
    assert root.is_dir() and destination.is_dir() and root != destination
    assert root == Path('E:/round108-public-recovered-20261009-v1')
    assert destination == Path('E:/codes/ExactEBRP-round108')
    assert Path.cwd().resolve() == root
    source = inside(root, Path(__file__), plain_file=True)
    assert source == root / PREFIX / (LABEL + '.py')
    source_sha = sha(source)
    fresh_review = inside(root, root / PREFIX)
    delivered_review = inside(destination, destination / PREFIX)
    output = inside(root, fresh_review / LABEL, must_exist=False)
    assert not output.exists(), ('exclusive run output already exists', str(output))
    output.mkdir()
    launch = {
        'schema': 'round108-independent-exact-supplement-copy-v1',
        'actual_command': [sys.executable] + sys.argv,
        'cwd': str(Path.cwd()),
        'evidence_read_root': str(root),
        'delivery_destination_root': str(destination),
        'source_SHA': source_sha,
        'started_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'sealed_carrier_modified': False,
        'original_workspace_evidence_reads': False,
        'destination_reads_are_new_delivery_hash_readbacks_only': True,
        'Optimize': 0, 'LP_solve': 0, 'native_environment': 0, 'compiler': 0,
    }
    write_json(output / 'launch.json', launch)
    try:
        for name in ('public_isolated_finalize01', 'public_isolated_copy_public_metadata01'):
            receipt_path = inside(root, fresh_review / name / 'receipt.json', plain_file=True)
            receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
            actual_source = inside(root, fresh_review / (name + '.py'), plain_file=True)
            assert sha(actual_source) == receipt['source_SHA']
            snapshot = inside(root, fresh_review / name / 'source_at_execution.py', must_exist=False)
            assert not snapshot.exists()
            with actual_source.open('rb') as inp, snapshot.open('xb') as out:
                shutil.copyfileobj(inp, out)
            assert sha(snapshot) == receipt['source_SHA']

        entries = []
        stats = {}
        for name in NEW_FILES:
            path = inside(root, fresh_review / name, plain_file=True)
            entries.append((path, Path(name), 'review_root_files'))
        for name in NEW_DIRS:
            directory = inside(root, fresh_review / name)
            assert directory.is_dir()
            for path in sorted(directory.rglob('*')):
                inside(root, path)
                assert '__pycache__' not in path.parts
                if path.is_dir():
                    continue
                assert path.suffix.lower() not in ('.exe', '.dll', '.pyc')
                inside(root, path, plain_file=True)
                entries.append((path, path.relative_to(fresh_review), name))

        # Every destination is checked absent before copying any supplement.
        for name in NEW_FILES + NEW_DIRS + (LABEL + '.py', LABEL):
            target = inside(destination, delivered_review / name, must_exist=False)
            assert not target.exists(), ('refuse overwrite', str(target))

        files = []
        for path, relative, group in entries:
            target = inside(destination, delivered_review / relative, must_exist=False)
            digest = sha(path)
            size = path.stat().st_size
            target.parent.mkdir(parents=True, exist_ok=True)
            inside(destination, target.parent)
            with path.open('rb') as inp, target.open('xb') as out:
                shutil.copyfileobj(inp, out, length=1024 * 1024)
            assert target.stat().st_size == size and sha(target) == digest
            files.append({'path': relative.as_posix(), 'bytes': size, 'SHA': digest})
            row = stats.setdefault(group, {'files': 0, 'bytes': 0, 'max_file_bytes': 0})
            row['files'] += 1
            row['bytes'] += size
            row['max_file_bytes'] = max(row['max_file_bytes'], size)

        # Copy the delivery source/snapshot/launch before writing the closing receipt.
        own_target = delivered_review / (LABEL + '.py')
        with source.open('rb') as inp, own_target.open('xb') as out:
            shutil.copyfileobj(inp, out)
        assert sha(own_target) == source_sha
        snapshot = output / 'source_at_execution.py'
        with source.open('rb') as inp, snapshot.open('xb') as out:
            shutil.copyfileobj(inp, out)
        delivery_output = delivered_review / LABEL
        delivery_output.mkdir()
        for name in ('launch.json', 'source_at_execution.py'):
            with (output / name).open('rb') as inp, (delivery_output / name).open('xb') as out:
                shutil.copyfileobj(inp, out)
            assert sha(output / name) == sha(delivery_output / name)

        assert sha(fresh_review / 'public_isolated_review01.json') == '7313ba6538f8f5ad2f2b630c2b8fe824dfa94fe9b5fc883b08ad9aaa878a5991'
        assert sha(delivered_review / 'public_isolated_review01.json') == '7313ba6538f8f5ad2f2b630c2b8fe824dfa94fe9b5fc883b08ad9aaa878a5991'
        receipt = dict(launch, exit_code=0, decision='ACCEPT', seconds=time.perf_counter() - started,
                       exact_copied_files=len(files), exact_copied_bytes=sum(x['bytes'] for x in files),
                       groups=stats, exact_files=files, delivery_source_exact_copy=True,
                       delivery_receipt_copied_after_seal=True)
        write_json(output / 'receipt.json', receipt)
        with (output / 'receipt.json').open('rb') as inp, (delivery_output / 'receipt.json').open('xb') as out:
            shutil.copyfileobj(inp, out)
        receipt_sha = sha(output / 'receipt.json')
        assert sha(delivery_output / 'receipt.json') == receipt_sha
        closing_sizes = [p.stat().st_size for p in delivery_output.iterdir()]
        print(json.dumps({'decision': 'ACCEPT', 'source_SHA': source_sha, 'receipt_SHA': receipt_sha,
                          'seconds': receipt['seconds'], 'supplements': stats,
                          'main_copied_files': len(files), 'main_copied_bytes': receipt['exact_copied_bytes'],
                          'delivery_receipt_dir': {'files': len(closing_sizes), 'bytes': sum(closing_sizes),
                                                   'max_file_bytes': max(closing_sizes)},
                          'delivery_source_bytes': source.stat().st_size,
                          'review_SHA': '7313ba6538f8f5ad2f2b630c2b8fe824dfa94fe9b5fc883b08ad9aaa878a5991'},
                         ensure_ascii=False, allow_nan=False))
    except Exception as error:
        failure = dict(launch, exit_code=1, decision='HOLD', seconds=time.perf_counter() - started,
                       error_type=type(error).__name__, error=str(error))
        write_json(output / 'receipt.json', failure)
        raise


if __name__ == '__main__':
    run()
