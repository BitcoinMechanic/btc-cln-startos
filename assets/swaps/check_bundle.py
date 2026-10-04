#!/usr/bin/env python3
"""Offline BTC image check. Does not start lightningd or use a wallet/backend."""
import importlib
import json
from pathlib import Path
import subprocess
import sys

PIN = '81ba4099a63e5a0e83f55cead53c54f2a1b3c1fe'


def check(bundle, check_binary=True):
    bundle = Path(bundle).resolve()
    if (bundle / 'SOURCE_COMMIT').read_text().strip() != PIN:
        raise ValueError('Swap source revision mismatch')
    sys.path.insert(0, str(bundle))
    for name in ('quote_plugin', 'reverse_gate', 'reverse_activation',
                 'receive_activation', 'live_receive', 'swap_controller', 'reverse_controller'):
        module = importlib.import_module(name)
        if Path(module.__file__).resolve().parent != bundle:
            raise ValueError('Unexpected module location')
    activation = importlib.import_module('reverse_activation')
    if activation.ACTIVE.get():
        raise ValueError('Live reverse activation unexpectedly enabled')
    for plugin in ('quote_plugin.py', 'reverse_gate.py'):
        result = subprocess.run([sys.executable, str(bundle / plugin)],
            input=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'getmanifest', 'params': {}})+'\n',
            capture_output=True, text=True, timeout=15, check=True)
        manifest = json.loads(result.stdout)['result']
        if not manifest.get('rpcmethods') or not manifest.get('hooks'):
            raise ValueError('Missing gate manifest')
        if (Path('/usr/local/libexec/c-lightning/plugins') / plugin).exists():
            raise ValueError('Swap gate installed in plugin discovery directory')
    if check_binary:
        version = subprocess.run(['lightningd', '--version'], capture_output=True,
                                 text=True, timeout=15, check=True).stdout.strip()
        if version not in ('v26.06.8', '26.06.8'):
            raise ValueError('Unexpected BTC CLN version: ' + version)
        subprocess.run(['bitcoin-cli', '--version'], capture_output=True,
                       text=True, timeout=15, check=True)
    print('BTC swap bundle OK (pinned imports and gate manifests; no live activation)')


if __name__ == '__main__':
    check('/usr/local/libexec/cln-swap')
