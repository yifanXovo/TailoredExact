"""Plot audited long-run checkpoints; no model solve or live-data inspection."""
import hashlib
import json
import math
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified_exact_round81'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started = time.perf_counter()
    campaign = OUT / 'campaign'
    assert not (campaign / 'active_run.lock').exists()
    assert read(campaign / 'audit.json')['all_checks_passed']
    assert read(campaign / 'mechanism_audit.json')['all_checks_passed']
    assert read(campaign / 'replication_audit.json')['all_checks_passed']
    destination = OUT / 'figures'
    assert not destination.exists(), 'Do not overwrite a completed plot namespace'
    points = [r for r in read(campaign / 'checkpoints.json') if r['id'] in ['D6', 'D7']]
    endpoints = read(campaign / 'endpoint_checks.json')
    for row in points:
        if row['available']:
            assert all(math.isfinite(row[k]) for k in ['U', 'L', 'gap'])

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'svg.fonttype': 'none', 'svg.hashsalt': 'round81-frozen-checkpoints'})
    colors = {'P-GRB': '#575E68', 'BDS-C': '#C45112', 'K1-R': '#2267A5'}
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.1))
    for axis, identity, title in zip(axes, ['D6', 'D7'],
                                    ['D6: 30 stations, primary deficit',
                                     'D7: 50 stations, K1 protection']):
        values = []
        arms = ['P-GRB', 'BDS-C'] if identity == 'D6' else ['P-GRB', 'BDS-C', 'K1-R']
        for arm in arms:
            rows = sorted([r for r in points if r['id'] == identity and r['arm'] == arm],
                          key=lambda r: r['seconds'])
            assert [r['seconds'] for r in rows] == [300, 600, 1200, 1800, 2400, 3600]
            x = [r['seconds'] for r in rows]
            y = [r['gap'] if r['available'] else math.nan for r in rows]
            values.extend(v for v in y if math.isfinite(v))
            axis.plot(x, y, color=colors[arm], label=arm, marker='o', markersize=4,
                      linewidth=1.5, linestyle='--')
            end = next(r for r in endpoints if r['id'] == identity and r['arm'] == arm)
            if end['stop_reason'] != 'normal_return' and rows[-1]['available']:
                axis.scatter([3600], [y[-1]], s=85, marker='s', facecolors='none',
                             edgecolors=colors[arm], linewidths=1.5, zorder=5)
        axis.set(title=title, xlabel='Whole-run elapsed time (seconds)',
                 ylabel='Absolute gap: physical U minus global L')
        axis.set_xticks([300, 600, 1200, 1800, 2400, 3600])
        axis.tick_params(axis='x', labelrotation=35)
        axis.set_xlim(180, 3720)
        axis.set_ylim(min(0, min(values) * 1.10), max(values) * 1.10)
        axis.grid(axis='y', color='#DFE3E8', linewidth=0.7)
        axis.spines[['top', 'right']].set_visible(False)
        axis.legend(frameon=False, loc='upper right')
        axis.ticklabel_format(axis='y', style='plain', useOffset=False)
    fig.suptitle('Round81: frozen BDS-C at common 3600-second caps', fontsize=14, y=0.98)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.86, bottom=0.29, wspace=0.25)
    fig.text(0.075, 0.11,
             'Markers are audited checkpoints; dashed lines only guide the eye. Missing physical U means no plotted gap.\n'
             'An outlined square marks committed evidence after a whole-run hard stop; it is not a certificate.\n'
             'D6 has no fresh K1 control. These are exposed development roles, not independent confirmation.',
             fontsize=9, va='top', linespacing=1.5)
    destination.mkdir()
    fig.savefig(destination / 'long_window_gaps.svg', metadata={'Date': None})
    fig.savefig(destination / 'long_window_gaps.png', dpi=180)
    plt.close(fig)
    (destination / 'plotted_checkpoints.json').write_text(json.dumps(points, indent=2) + '\n', encoding='utf-8')
    outputs = [destination / name for name in ['long_window_gaps.svg', 'long_window_gaps.png',
                                               'plotted_checkpoints.json']]
    receipt = dict(optimizer_calls=0, wall_seconds=time.perf_counter() - started,
                   matplotlib_version=matplotlib.__version__, script_sha256=sha(Path(__file__)),
                   checkpoint_sha256=sha(campaign / 'checkpoints.json'),
                   endpoint_sha256=sha(campaign / 'endpoint_checks.json'),
                   output_sha256={p.name: sha(p) for p in outputs},
                   scope='Presentation of the existing audited observations only; no new performance selection or inference.')
    (destination / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
