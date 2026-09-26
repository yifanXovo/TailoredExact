"""Build-only canonical identity audit: no environment or optimizer is opened."""
import json, os, subprocess
import round59_research as r

env = dict(os.environ)
env['PATH'] = 'D:/msys64/ucrt64/bin;' + env['PATH']
rows = []
for item in json.loads((r.OUT/'panel.json').read_text())['panel']:
    if item['id'] not in ['D2', 'D3', 'D4']:
        continue
    dest = r.RAW/'identity_current_f0_verified'/item['id']
    cmd = [str(r.ROOT/'build/round59-core/Round50IntervalMipExperiment.exe'),
           '--mode', 'build', '--state-id', item['id'], '--input', item['instance_path'],
           '--T', str(item['T_seconds']), '--artifact-dir', str(dest),
           '--policy', 'interval-mip-core-no-exhaustive-subset-duration',
           '--round59-empty-state', '--round59-current-f0']
    subprocess.run(cmd, env=env, check=True, capture_output=True)
    main = r.RAW/'screen120'/item.get('artifact_id', item['id'])/'K1-S/external/models/L0.lp'
    diag = dest/'canonical_model.lp'
    rows.append(dict(id=item['id'], command=cmd, scope='build_only_no_optimizer',
                     main_sha256=r.sha(main), diagnostic_sha256=r.sha(diag),
                     byte_identical=main.read_bytes()==diag.read_bytes()))
r.write(r.OUT/'current_f0_identity.json', rows)
assert all(row['byte_identical'] for row in rows), rows
print('All three current K1-S canonical LP files are byte-identical.')
