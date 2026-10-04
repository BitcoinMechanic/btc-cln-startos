#!/usr/bin/env python3
"""BTC coordinator preparation only; not gate activation or spending authority."""
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

PIN = '81ba4099a63e5a0e83f55cead53c54f2a1b3c1fe'
RECORD = 'coordinator-preparation.json'


class Blocked(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Blocked(reason)


def load(path):
    require(stat.S_ISREG(path.lstat().st_mode), 'nonregular_record')
    return json.loads(path.read_text())


def save(path, data):
    fd, temporary = tempfile.mkstemp(prefix='.coordinator-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


class Preparation:
    def __init__(self, root, rpc=None, bundle='/usr/local/libexec/cln-swap'):
        self.root = Path(root)
        self.bundle = Path(bundle)
        self.rpc = rpc or self.call

    def call(self, method):
        require(method in ('getinfo', 'listpeerchannels'), 'unexpected_rpc')
        result = subprocess.run(['lightning-cli', '--lightning-dir='+str(self.root),
                                 '--network=bitcoin', '--json', '--notifications=none', method],
                                capture_output=True, text=True, timeout=30)
        require(result.returncode == 0, 'node_rpc_unavailable')
        value = json.loads(result.stdout)
        require('error' not in value, 'node_rpc_unavailable')
        return value

    def inspect(self):
        require((self.bundle / 'SOURCE_COMMIT').read_text().strip() == PIN, 'source_revision_mismatch')
        for name in ('quote_plugin.py', 'reverse_activation.py', 'receive_activation.py'):
            require((self.bundle / name).is_file(), 'swap_module_missing')
        store = self.root / 'store.json'
        if os.path.lexists(store):
            settings = load(store)
            require(settings.get('restore') in (None, False), 'restore_pending')
            require(settings.get('rescan') is None, 'rescan_pending')
        info = self.rpc('getinfo')
        require(info.get('network') == 'bitcoin', 'wrong_network')
        require(info.get('version') in ('v26.06.8', '26.06.8'), 'unexpected_cln_version')
        require(re.fullmatch(r'0[23][0-9a-f]{64}', info.get('id', '')), 'invalid_node_identity')
        require(not any(k.startswith('warning_') for k in info), 'node_sync_warning')
        channels = self.rpc('listpeerchannels')['channels']
        require(not any(c.get('htlcs') for c in channels), 'pending_htlcs')
        expected = dict(schema=1, scope='preparation-only', network='bitcoin',
                        node_id=info['id'], source_commit=PIN, cln_version='26.06.8')
        path = self.root / RECORD
        prepared = os.path.lexists(path)
        if prepared:
            require(load(path) == expected, 'preparation_binding_changed')
        return expected, dict(prepared=prepared, network='bitcoin', cln_version='26.06.8',
                             source_commit=PIN, controller_pairing_required=True,
                             live_activation_enabled_by_package=False, payment_started=False)

    def prepare(self, confirmed):
        require(confirmed is True, 'confirmation_required')
        record, status = self.inspect()
        if not status['prepared']: save(self.root / RECORD, record)
        return dict(status, prepared=True)


def main():
    try:
        root = Path(sys.argv[1])
        request = json.load(sys.stdin)
        fd = os.open(root / 'coordinator-preparation.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'a') as lock:
            require(stat.S_ISREG(os.fstat(lock.fileno()).st_mode), 'nonregular_lock')
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            worker = Preparation(root)
            if request.get('operation') == 'status': result = worker.inspect()[1]
            elif request.get('operation') == 'prepare': result = worker.prepare(request.get('confirmed'))
            else: raise Blocked('unknown_operation')
        print(json.dumps(result))
    except Exception as error:
        print(json.dumps(dict(error='Coordinator preparation unavailable; no gate activated.',
                              reason=str(error) if isinstance(error, Blocked) else 'private_details_withheld')))
        raise SystemExit(1)


if __name__ == '__main__': main()
