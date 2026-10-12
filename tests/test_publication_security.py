"""All samples are expressly fake placeholders, assembled only in memory."""
import gzip
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import publication_security as gate

def fake_key():
    return ('AI' + 'za' + '0' * 35).encode()  # NONREAL placeholder, not incident material.

def fake_tar(data, name='source.json'):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:gz') as archive:
        member = tarfile.TarInfo(name)
        member.size = len(data)
        archive.addfile(member, io.BytesIO(data))
    return stream.getvalue()

class PublicationTests(unittest.TestCase):
    def test_nested_cookie_and_url_are_fingerprint_only(self):
        data = json.dumps({'snapshot': {'headers': {'Set-Cookie': 'NONREAL_SESSION_PLACEHOLDER'}},
                           'url': 'https://example.invalid/source?' + 'signature=' + 'NONREAL_SIGNATURE'}).encode()
        result = gate.scan_items([('receipt.json', data)])
        self.assertFalse(result['passed'])
        encoded = json.dumps(result)
        self.assertNotIn('NONREAL_SESSION_PLACEHOLDER', encoded)
        self.assertNotIn('NONREAL_SIGNATURE', encoded)

    def test_complete_split_archive_is_inspected(self):
        data = fake_tar(fake_key())
        result = gate.scan_items([('evidence.tar.gz.part001', data[:50]), ('evidence.tar.gz.part002', data[50:])])
        self.assertFalse(result['passed'])
        self.assertEqual(result['archive_members'], 1)
        self.assertEqual(result['findings'][0]['category'], 'google_api_key')
        self.assertNotIn(fake_key().decode(), json.dumps(result))

    def test_truncated_and_traversal_carriers_fail_closed(self):
        self.assertFalse(gate.scan_items([('evidence.tar.gz.part002', b'broken')])['passed'])
        self.assertFalse(gate.scan_items([('evidence.tar.gz', fake_tar(b'safe', '../escape'))])['passed'])

    def test_text_extract_removes_runtime_and_preserves_license(self):
        data = b'<html><body><main><h1>License</h1><p>non-commercial purposes</p></main><script>{"CREDENTIALS_FRONTEND_GOOGLE_MAPS_KEY":"' + fake_key() + b'"}</script></body></html>'
        extracted = gate.extract_html(data, 'https://example.invalid/source?' + 'key=' + 'NONREAL_PARAMETER')
        self.assertIn(b'non-commercial purposes', extracted)
        self.assertNotIn(fake_key(), extracted)
        self.assertNotIn(b'<script', extracted)
        self.assertNotIn(b'NONREAL_PARAMETER', extracted)
        self.assertTrue(gate.scan_items([('safe.response', extracted)])['passed'])
        self.assertEqual(gate.safe_headers({'Set-Cookie': 'NONREAL', 'Authorization': 'NONREAL', 'Content-Type': 'text/html'}), {'content-type': 'text/html'})

    def test_static_recording_only_saves_research_fields(self):
        body = json.dumps({'version': '2.3', 'data': {'stations': [{'station_id': '0007', 'capacity': 12, 'lat': 38.0, 'lon': -77.0, 'irrelevant_config': 'NONREAL'}]}}).encode()
        with tempfile.TemporaryDirectory() as d:
            receipt = gate.record_research_response(d, '01', 'stations', body,
                       {'Set-Cookie': 'NONREAL', 'Content-Type': 'application/json'}, 'https://example.invalid/static', '2000-01-01T00:00:00Z')
            saved = (Path(d) / '01.response').read_bytes()
            self.assertNotIn(b'irrelevant_config', saved)
            self.assertNotIn('set-cookie', receipt['headers'])
            self.assertEqual(json.loads(saved)['data']['stations'][0]['station_id'], '0007')

    def test_staged_index_overrides_worktree(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(['git', 'init', '-q', d], check=True)
            path = Path(d) / 'payload.txt'
            path.write_bytes(fake_key())
            subprocess.run(['git', '-C', d, 'add', 'payload.txt'], check=True)
            path.write_bytes(b'safe worktree')
            self.assertFalse(gate.scan_items(gate.staged_items(d))['passed'])

if __name__ == '__main__':
    unittest.main()
