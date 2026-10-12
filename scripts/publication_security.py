"""Small offline publication gate; never prints credential values or tests APIs.

Scan index blobs with --staged and decompressed publication carriers with
--paths. Split carriers are joined in numbered order before inspection.
The scope is explicit; this is not a claim that Git history was purged.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import html
from html.parser import HTMLParser
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import zipfile

VERSION = 'round117-publication-security-v1'
HEADER_ALLOWLIST = {'content-type', 'content-length', 'date', 'last-modified', 'cache-control'}
SENSITIVE_FIELDS = {'cookie', 'set-cookie', 'authorization', 'proxy-authorization',
                    'x-api-key', 'x-auth-token', 'access_token', 'refresh_token',
                    'id_token', 'client_secret', 'password', 'private_key'}
SENSITIVE_QUERY = {'key', 'api_key', 'apikey', 'token', 'access_token', 'refresh_token',
                   'signature', 'sig', 'x-amz-signature', 'x-amz-credential',
                   'x-goog-signature', 'x-goog-credential'}
PATTERNS = {
    'google_api_key': re.compile(rb'AIza[0-9A-Za-z_-]{35}'),
    'github_token': re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{60,255})'),
    'private_key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----\s+[A-Za-z0-9+/=\s]{32,}-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'jwt': re.compile(rb'eyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}'),
    'aws_access_key': re.compile(rb'(?:AKIA|ASIA)[A-Z0-9]{16}'),
    'slack_token': re.compile(rb'xox[baprs]-[0-9A-Za-z-]{20,}'),
    'client_credential': re.compile(rb'["\']CREDENTIALS_[A-Z0-9_]+["\']\s*:\s*["\']([^"\']{8,})["\']'),
}
PART = re.compile(r'(.+)\.part(\d+)$')
MAX_MEMBER_BYTES = 512 * 1024 * 1024

def sha(data):
    return hashlib.sha256(data).hexdigest()

def safe_url(value):
    """Remove userinfo, fragments and credential/signature query parameters."""
    u = urlsplit(value)
    if u.scheme not in ('https', 'http') or not u.hostname:
        raise ValueError('unsupported source URL')
    host = u.hostname + (':' + str(u.port) if u.port else '')
    query = [(k, v) for k, v in parse_qsl(u.query) if k.lower() not in SENSITIVE_QUERY]
    return urlunsplit((u.scheme, host, u.path, urlencode(query), ''))

def safe_headers(headers):
    return {k.lower(): str(v) for k, v in headers.items() if k.lower() in HEADER_ALLOWLIST}

class ResearchText(HTMLParser):
    """Extract visible main/article/body text and official provenance links."""
    def __init__(self, tag):
        super().__init__(convert_charrefs=True)
        self.tag = tag
        self.active = 0
        self.suppressed = []
        self.text = []
        self.links = set()

    def handle_starttag(self, tag, attrs):
        if tag == self.tag:
            self.active += 1
        if tag in ('script', 'style', 'noscript', 'svg', 'template'):
            self.suppressed.append(tag)
        if self.active and not self.suppressed and tag == 'a':
            href = dict(attrs).get('href', '')
            if href.startswith('https://'):
                u = urlsplit(href)
                if u.hostname in {'capitalbikeshare.com', 'www.capitalbikeshare.com',
                                   'gbfs.capitalbikeshare.com', 'gbfs.lyft.com'}:
                    self.links.add(safe_url(href))
        if self.active and not self.suppressed and tag in ('p', 'div', 'li', 'br', 'h1', 'h2', 'h3', 'section'):
            self.text.append('\n')

    def handle_endtag(self, tag):
        if self.suppressed and tag == self.suppressed[-1]:
            self.suppressed.pop()
        if tag == self.tag:
            self.active = max(0, self.active - 1)
        if self.active and not self.suppressed and tag in ('p', 'div', 'li', 'h1', 'h2', 'h3'):
            self.text.append('\n')

    def handle_data(self, data):
        if self.active and not self.suppressed:
            self.text.append(data)

def extract_html(data, source_url):
    text = data.decode('utf-8')
    tag = 'main' if re.search(r'<main[\s>]', text, re.I) else 'article' if re.search(r'<article[\s>]', text, re.I) else 'body'
    parser = ResearchText(tag)
    parser.feed(text)
    lines = [' '.join(x.split()) for x in ''.join(parser.text).splitlines()]
    visible = '\n'.join(x for x in lines if x)
    if not visible:
        raise ValueError('no research text extracted')
    links = '\n'.join(f'<li><a href="{html.escape(x, quote=True)}">{html.escape(x)}</a></li>' for x in sorted(parser.links))
    result = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>Safe source text extract</title></head><body>\n'
              '<p>[REDACTED: scripts, runtime configuration, client credentials, tracking and non-text attributes removed]</p>\n'
              f'<p>Source: {html.escape(safe_url(source_url))}</p>\n'
              f'<main><pre>{html.escape(visible)}</pre></main>\n<ul>{links}</ul>\n</body></html>\n').encode()
    report = scan_items([(source_url, result)])
    if not report['passed']:
        raise ValueError('extracted source still fails publication gate')
    return result

def record_research_response(folder, name, kind, body, headers, url, fetched_utc):
    """Safe future recording entry point; caller fetches using its approved policy.

    HTML is text-only. Static JSON retains explicitly required research fields.
    This function performs no network request and saves no raw credential copy.
    Existing R116 static station bytes are handled separately, without rewriting.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    if kind == 'html':
        published = extract_html(body, url)
    else:
        obj = json.loads(body)
        top = {k: obj[k] for k in ('last_updated', 'ttl', 'version') if k in obj}
        if kind == 'stations':
            fields = ('station_id', 'name', 'capacity', 'lat', 'lon', 'is_virtual_station')
            top['data'] = {'stations': [{k: r[k] for k in fields if k in r} for r in obj['data']['stations']]}
        elif kind == 'system':
            fields = ('system_id', 'name', 'language', 'timezone', 'url', 'license_url')
            top['data'] = {k: obj['data'][k] for k in fields if k in obj['data']}
        elif kind == 'discovery':
            top['data'] = {'en': {'feeds': [{'name': f['name'], 'url': safe_url(f['url'])} for f in obj['data']['en']['feeds'] if f['name'] in ('station_information', 'system_information')]}}
        else:
            raise ValueError('unsupported research response kind')
        published = (json.dumps(top, indent=2, ensure_ascii=False) + '\n').encode()
    receipt = {'source_url': safe_url(url), 'fetched_utc': fetched_utc,
               'original_response_sha256': sha(body), 'original_bytes': len(body),
               'published_response_sha256': sha(published), 'published_bytes': len(published),
               'headers': safe_headers(headers), 'tool_version': VERSION,
               'raw_response_saved': False}
    meta = (json.dumps(receipt, indent=2) + '\n').encode()
    if not scan_items([(name + '.response', published), (name + '.json', meta)])['passed']:
        raise ValueError('response fails publication gate')
    for suffix, data in [('.response', published), ('.json', meta)]:
        with (folder / (name + suffix)).open('xb') as f:
            f.write(data)
    return receipt

class Scanner:
    def __init__(self):
        self.findings = []
        self.errors = []
        self.files = 0
        self.members = 0
        self.bytes = 0
        self.archives = []

    def hit(self, path, category, value, line=None, field=None):
        self.findings.append({'path': path, 'category': category,
                              'value_sha256': sha(value), 'line': line, 'field': field})

    def fields(self, obj, path, prefix=''):
        if isinstance(obj, dict):
            for k, v in obj.items():
                field = prefix + '/' + str(k)
                if str(k).lower() in SENSITIVE_FIELDS and v and not str(v).startswith('[REDACTED'):
                    self.hit(path, 'sensitive_field', str(v).encode(), field=field)
                self.fields(v, path, field)
        elif isinstance(obj, list):
            for n, v in enumerate(obj):
                self.fields(v, path, prefix + '/' + str(n))

    def content(self, data, path):
        self.bytes += len(data)
        for category, pattern in PATTERNS.items():
            for match in pattern.finditer(data):
                value = match[1] if category == 'client_credential' else match[0]
                if value.startswith(b'[REDACTED'):
                    continue
                self.hit(path, category, value, data[:match.start()].count(b'\n') + 1)
        if b'\0' in data[:2048]:
            return
        lower = data.lower()
        if any(k.encode() in lower for k in SENSITIVE_FIELDS):
            try:
                self.fields(json.loads(data), path)
            except (ValueError, UnicodeError):
                pass
        if re.search(rb'<(?:!doctype\s+html|html)[\s>]', data[:1024], re.I):
            if re.search(rb'<script\b|\son[a-z]+\s*=', data, re.I):
                self.hit(path, 'html_runtime_material', b'HTML executable runtime', field='script_or_event_attribute')
        for match in re.finditer(rb'https?://[^\s"<>\\]+', data):
            try:
                u = urlsplit(match[0].decode('utf-8'))
                if u.username or u.password:
                    self.hit(path, 'url_userinfo', (u.username or '').encode(), field='userinfo')
                for k, v in parse_qsl(u.query):
                    if k.lower() in SENSITIVE_QUERY and v and not v.startswith(('[REDACTED', '{')):
                        self.hit(path, 'sensitive_url_parameter', v.encode(), field=k)
            except (ValueError, UnicodeError):
                pass

    def payload(self, data, path, depth=0):
        if depth > 6:
            raise ValueError('archive recursion limit')
        if data.startswith(b'\x1f\x8b'):
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
                prefix = stream.read(512)
                if len(prefix) > 262 and prefix[257:262] == b'ustar':
                    # Reopen for streamed tar traversal; never extract to disk.
                    self.tar(io.BytesIO(data), path, depth + 1)
                else:
                    plain = prefix + stream.read(MAX_MEMBER_BYTES + 1)
                    if len(plain) > MAX_MEMBER_BYTES:
                        raise ValueError('compressed member size limit')
                    self.payload(plain, path + '!gunzip', depth + 1)
        elif data.startswith(b'PK\x03\x04'):
            count = 0
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    self.member_name(member.filename)
                    if member.file_size > MAX_MEMBER_BYTES:
                        raise ValueError('archive member size limit')
                    self.members += 1
                    count += 1
                    self.payload(archive.read(member), path + '!' + member.filename, depth + 1)
            self.archives.append({'path': path, 'members': count})
        elif len(data) > 262 and data[257:262] == b'ustar':
            self.tar(io.BytesIO(data), path, depth + 1)
        else:
            if path.lower().endswith(('.zip', '.gz', '.tgz', '.tar', '.7z', '.xz', '.bz2', '.zst')):
                raise ValueError('unrecognized or unsupported archive; do not publish unchecked')
            self.content(data, path)

    @staticmethod
    def member_name(name):
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in p.parts[0]:
            raise ValueError('unsafe archive path')

    def tar(self, stream, path, depth):
        count = 0
        with tarfile.open(fileobj=stream, mode='r|*') as archive:
            for member in archive:
                self.member_name(member.name)
                if member.isdir():
                    continue
                if not member.isfile() or member.size > MAX_MEMBER_BYTES:
                    raise ValueError('unsupported archive member')
                data = archive.extractfile(member).read()
                if len(data) != member.size:
                    raise ValueError('truncated archive member')
                self.members += 1
                count += 1
                self.payload(data, path + '!' + member.name, depth)
        self.archives.append({'path': path, 'members': count})

def scan_items(items):
    tick = time.perf_counter()
    scanner = Scanner()
    groups = {}
    for path, data in items:
        path = str(path)
        match = PART.fullmatch(path)
        if match:
            groups.setdefault(match[1], []).append((int(match[2]), data))
            scanner.files += 1
            continue
        scanner.files += 1
        try:
            scanner.payload(data, path)
        except Exception as exc:
            scanner.errors.append({'path': path, 'error_class': type(exc).__name__})
    for path, parts in groups.items():
        numbers = sorted(n for n, _ in parts)
        try:
            if numbers != list(range(1, len(parts) + 1)):
                raise ValueError('missing or duplicate archive part')
            scanner.payload(b''.join(data for _, data in sorted(parts)), path)
        except Exception as exc:
            scanner.errors.append({'path': path, 'error_class': type(exc).__name__})
    return {'tool_version': VERSION, 'passed': not scanner.findings and not scanner.errors,
            'files': scanner.files, 'archive_members': scanner.members,
            'bytes_scanned': scanner.bytes, 'archives': scanner.archives,
            'findings': scanner.findings, 'errors': scanner.errors,
            'raw_values_emitted': False, 'network_requests': 0,
            'native_starts': 0, 'Optimize': 0, 'engineering_seconds': time.perf_counter() - tick}

def staged_items(root):
    """Use the actual index, even when worktree bytes differ or are absent."""
    root = Path(root)
    paths = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMRT', '-z'], cwd=root).decode().split('\0')
    paths = {p for p in paths if p}
    indexed = [p for p in subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0') if p]
    bases = {PART.fullmatch(p)[1] for p in paths if PART.fullmatch(p)}
    paths.update(p for p in indexed if PART.fullmatch(p) and PART.fullmatch(p)[1] in bases)
    for p in sorted(paths):
        data = subprocess.check_output(['git', 'show', ':' + p], cwd=root)
        yield p, data

def file_items(root, paths):
    root = Path(root).resolve()
    names = set()
    for name in paths:
        p = root / name
        if p.is_dir():
            names.update(q for q in p.rglob('*') if q.is_file())
        else:
            names.add(p)
    for p in sorted(names):
        p = p.resolve()
        if not p.is_relative_to(root):
            raise ValueError('scan path outside publication root')
        yield p.relative_to(root).as_posix(), p.read_bytes()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--staged', action='store_true')
    mode.add_argument('--paths', nargs='+')
    parser.add_argument('--out')
    args = parser.parse_args()
    report = scan_items(staged_items(args.root) if args.staged else file_items(args.root, args.paths))
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('passed', 'files', 'archive_members', 'bytes_scanned', 'findings', 'errors')}))
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
