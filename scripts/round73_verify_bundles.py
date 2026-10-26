"""Verify every submitted raw evidence member without extraction or optimization."""
import json
from round73_bundle_formal import OUT, verify
if __name__=='__main__':
    manifest=json.loads((OUT/'bundle_manifest.json').read_text())
    for bundle in manifest['bundles']:
        bundle['path']=bundle['path'].replace('\\','/')
    print('Verified original evidence files:',verify(manifest))
