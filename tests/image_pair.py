"""Run pinned cross-chain controller fixtures against both packaged binaries."""
import argparse
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
sys.path.insert(0, '/usr/local/libexec/cln-swap')
from smoke_regtest import Lab, wait_until
import importlib.util
_spec = importlib.util.spec_from_file_location("btc_image_check", "/usr/local/libexec/check-btc-swap-bundle.py")
_checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_checker)
check_bundle = _checker.check
import swap_regtest
import reverse_regtest

PIN = '81ba4099a63e5a0e83f55cead53c54f2a1b3c1fe'


class PairLab(Lab):
    def lightning(self, name, network, backend, expect_success=True, plugins=()):
        if network not in ('regtest', 'xbt-regtest') or not expect_success:
            raise ValueError('Pair fixture accepts successful regtest nodes only')
        prefix = '/opt/xbt' if network == 'xbt-regtest' else '/usr/local'
        expected = ('xbt-81ba4099a63e',) if network == 'xbt-regtest' else ('v26.06.8', '26.06.8')
        data = self.root / name
        data.mkdir(exist_ok=True, mode=0o700)
        port = self.port()
        logfile = data / 'console.log'
        args = [prefix+'/bin/lightningd', f'--lightning-dir={data}', '--conf=/dev/null',
                f'--network={network}', '--bitcoin-cli=/usr/bin/bitcoin-cli',
                f'--bitcoin-datadir={backend["data"]}', f'--bitcoin-rpcport={backend["port"]}',
                '--developer', '--dev-bitcoind-poll=1', '--disable-dns',
                '--autoconnect-seeker-peers=0', '--autolisten=false',
                f'--bind-addr=127.0.0.1:{port}', '--log-level=debug',
                '--disable-plugin=cln-grpc']
        if network == 'regtest':
            args += ['--disable-plugin='+p for p in ('clboss', 'sling', 'watchtower-client')]
        args += ['--plugin='+str(p) for p in plugins]
        proc = self.start(args, logfile, new_session=True)
        cli = [prefix+'/bin/lightning-cli', '--json', '--notifications=none',
               f'--lightning-dir={data}', f'--network={network}']
        info = wait_until(lambda: self.rpc(cli, 'getinfo'), proc, timeout=120)
        if info['network'] != network or info['version'] not in expected:
            raise ValueError('Unexpected packaged node network or version')
        def listening():
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=1): return True
            except OSError: return False
        wait_until(listening, proc)
        return dict(data=data, port=port, proc=proc, cli=cli, id=info['id'], log=logfile)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('forward', 'forward-failure', 'reverse', 'reverse-failure'))
    args = p.parse_args()
    if os.environ.get('BTC_XBT_DISPOSABLE_CONTAINER') != '1':
        raise RuntimeError('Use the isolated Docker launcher')
    os.umask(0o077)
    source = json.loads(Path('/opt/xbt/share/xbt-cln/source-lock.json').read_text())
    if source['cln_commit'] != PIN or source['network'] != 'xbt':
        raise ValueError('XBT image source pin differs from bundled controller')
    check_bundle('/usr/local/libexec/cln-swap')
    root = Path(tempfile.mkdtemp(prefix='pair-'+args.mode+'-', dir='/results'))
    print('Test directory: '+str(root), flush=True)
    lab = PairLab(root, '/test-bitcoind', '/usr/bin/bitcoin-cli')
    try:
        if args.mode.startswith('forward'):
            swap_regtest.run(lab, restart_pending=True,
                            pending_failure=args.mode == 'forward-failure')
        else:
            reverse_regtest.run(lab, recovery='gate-restart-failure' if args.mode == 'reverse-failure' else 'gate-restart')
        print('Packaged BTC/XBT pair OK ('+args.mode+'; controller recovery; regtest only)', flush=True)
    finally:
        lab.close()


if __name__ == '__main__': main()
