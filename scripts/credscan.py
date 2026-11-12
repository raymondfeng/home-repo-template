#!/usr/bin/env python3
"""Credential-pattern scan over raw bytes and every zip member. Exit 1 on any hit.

    python3 -I scripts/credscan.py --controls          # prove each pattern can fire (one planted sample each, one in a zip)
    python3 -I scripts/credscan.py <dist> <list-file>  # scan the files the list names, relative to <dist>

Run it over the files you are about to commit or publish. It reads bytes, so a file with NUL bytes is scanned too.
A hit is a stop. An allowance is the owner's call: one exact string in ALLOW_EXACT, recorded in AGENTS.md before it ships.
Prints the first 12 characters of a match only, never a whole key."""
import io, os, re, sys, zipfile

PATS = {
    'aws': rb'AKIA[0-9A-Z]{16}',
    'google': rb'AIza[0-9A-Za-z_\-]{35}',
    'github': rb'(?:ghp|gho|ghu|ghs|ghr)_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{22,}',
    'anthropic': rb'sk-ant-[0-9A-Za-z_\-]{8,}',
    'openai': rb'sk-(?:proj-)?[0-9A-Za-z]{32,}',
    'slack': rb'xox[abposr]-[0-9A-Za-z-]{10,}',
    'jwt': rb'eyJ[0-9A-Za-z_\-]{10,}\.eyJ[0-9A-Za-z_\-]{10,}\.[0-9A-Za-z_\-]{10,}',
    'privkey': rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    'stripe': rb'(?:sk|rk)_live_[0-9A-Za-z]{20,}',
}
C = {k: re.compile(v) for k, v in PATS.items()}
# Allowances: exact test fixtures, allowed only with no key character on either side. Empty by default.
ALLOW_EXACT = set()
KEYCHAR = re.compile(rb'[0-9A-Za-z_\-]')


def allowed(b, m):
    return m.group(0) in ALLOW_EXACT and not (m.start() and KEYCHAR.match(b, m.start() - 1))


def scan_bytes(b, name, hits):
    for k, r in C.items():
        for m in r.finditer(b):
            if allowed(b, m):
                continue
            hits.append((k, name, m.group(0)[:12].decode('latin1') + '…'))
    if b[:2] == b'PK':
        try:
            with zipfile.ZipFile(io.BytesIO(b)) as z:
                for n in z.namelist():
                    scan_bytes(z.read(n), name + '!' + n, hits)
        except zipfile.BadZipFile:
            pass


def controls():
    samples = {'aws': b'AKIA' + b'Q' * 16, 'google': b'AIza' + b'B' * 35, 'github': b'ghp_' + b'a' * 36,
               'anthropic': b'sk-ant-' + b'x1' * 10, 'openai': b'sk-' + b'A1' * 20, 'slack': b'xoxb-' + b'1' * 12,
               'jwt': b'eyJ' + b'a' * 12 + b'.eyJ' + b'b' * 12 + b'.' + b'c' * 12,
               'privkey': b'-----BEGIN PRIVATE KEY-----', 'stripe': b'sk_live_' + b'z' * 24}
    ok = 0
    for k, s in samples.items():
        h = []
        scan_bytes(b' ' + s + b' ', 'ctl', h)
        ok += any(x[0] == k for x in h)
    buf = io.BytesIO()
    zipfile.ZipFile(buf, 'w').writestr('m.xml', samples['aws'])
    h = []
    scan_bytes(buf.getvalue(), 'z', h)
    ok += bool(h)
    # The allowance must pass a fixture alone and flag anything near it. The fixture is added for this check only.
    ALLOW_EXACT.add(b'sk-ant-api03-secret')
    near = [b'sk-ant-api03-secret1', b'xsk-ant-api03-secret', b'sk-ant-api03-secreT', b'sk-ant-api03-AbCdEf123456']
    h = []
    scan_bytes(b' "sk-ant-api03-secret" ', 'allow', h)
    ok += not h
    for s in near:
        h = []
        scan_bytes(b' ' + s + b' ', 'near', h)
        ok += bool(h)
    ALLOW_EXACT.discard(b'sk-ant-api03-secret')
    total = len(samples) + 2 + len(near)
    print(f'controls {ok}/{total}')
    return ok == total


def main():
    if sys.argv[1:] == ['--controls']:
        sys.exit(0 if controls() else 1)
    dist, lst = sys.argv[1], sys.argv[2]
    hits, n = [], 0
    for p in open(lst).read().split('\n'):
        f = os.path.join(dist, p)
        if p and os.path.isfile(f):
            n += 1
            scan_bytes(open(f, 'rb').read(), p, hits)
    print(f'scanned {n} files')
    for h in hits:
        print(*h)
    print(f'hits {len(hits)}')
    sys.exit(1 if hits else 0)


if __name__ == '__main__':
    main()
