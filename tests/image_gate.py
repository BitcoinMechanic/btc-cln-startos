"""Funded upstream BTC gate compatibility, isolated regtest only; no XBT leg."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import sys
import tempfile
import time
sys.path.insert(0, '/usr/local/libexec/cln-swap')
from smoke_regtest import Lab, wait_until
from swap_invoice import unsigned_invoice


def check(value, message):
    if not value:
        raise AssertionError(message)


class ImageLab(Lab):
    def lightning(self, name, backend, plugin=None):
        data = self.root / name
        data.mkdir(exist_ok=True, mode=0o700)
        port = self.port()
        logfile = data / ('restart.log' if (data / 'console.log').exists() else 'console.log')
        args = ['lightningd', f'--lightning-dir={data}', '--conf=/dev/null',
                '--network=regtest', '--bitcoin-cli=/usr/bin/bitcoin-cli',
                f'--bitcoin-datadir={backend["data"]}', f'--bitcoin-rpcport={backend["port"]}',
                '--developer', '--dev-bitcoind-poll=1', '--disable-dns',
                '--autoconnect-seeker-peers=0', '--autolisten=false',
                f'--bind-addr=127.0.0.1:{port}', '--log-level=debug']
        args += ['--disable-plugin='+p for p in ('cln-grpc', 'clboss', 'sling', 'watchtower-client')]
        if plugin: args.append('--plugin='+str(plugin))
        proc = self.start(args, logfile)
        cli = ['lightning-cli', f'--lightning-dir={data}', '--network=regtest',
               '--json', '--notifications=none']
        info = wait_until(lambda: self.rpc(cli, 'getinfo'), proc, timeout=120)
        check(info['network'] == 'regtest', 'Wrong network')
        check(info['version'] in ('v26.06.9', '26.06.9'), 'Wrong BTC binary')
        def listening():
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=1): return True
            except OSError: return False
        wait_until(listening, proc)
        return dict(cli=cli, proc=proc, port=port, id=info['id'])


def run(lab, fail):
    rpc = lambda n, *args: lab.rpc(n['cli'], *args)
    backend = lab.node('backend', False)
    mining = rpc(backend, 'getnewaddress')
    def mine(n):
        rpc(backend, 'generatetoaddress', n, mining)
    plugin = lab.root / 'quote_plugin.py'
    plugin.write_text('#!/usr/bin/python3\n' + Path('/usr/local/libexec/cln-swap/quote_plugin.py').read_text())
    plugin.chmod(0o700)
    payer = lab.lightning('payer', backend)
    operator = lab.lightning('operator', backend, plugin)
    address = rpc(payer, 'newaddr', 'bech32')['bech32']
    rpc(backend, 'sendtoaddress', address, '0.02')
    mine(6)
    wait_until(lambda: any(o['status'] == 'confirmed' for o in rpc(payer, 'listfunds')['outputs']), payer['proc'], timeout=120)
    rpc(payer, 'connect', operator['id'], '127.0.0.1', operator['port'])
    lab.rpc([*payer['cli'], '-k'], 'fundchannel', 'id='+operator['id'],
            'amount=1000000', 'feerate=2000perkb', 'announce=false')
    mine(6)
    def channel(node):
        channels = rpc(node, 'listpeerchannels')['channels']
        check(len(channels) == 1, 'Expected one fixture channel')
        return channels[0]
    for node in (payer, operator):
        wait_until(lambda: channel(node)['state'] == 'CHANNELD_NORMAL', node['proc'], timeout=120)
    initial = {n['id']: channel(n)['to_us_msat'] for n in (payer, operator)}
    print('PASS: upstream BTC image funded a private regtest channel', flush=True)
    preimage, secret = secrets.token_hex(32), secrets.token_hex(32)
    payment_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
    terms = dict(payment_hash=payment_hash, payment_secret=secret,
                 btc_amount_msat=100000000, xbt_amount_msat=200000000,
                 xbt_invoice='lnxbtrt-compatibility-fixture-no-xbt-leg', expires_at=int(time.time())+3600,
                 min_cltv_delta=100, max_cltv_delta=2000)
    check(rpc(operator, 'xbt-register', json.dumps(terms))['registered'], 'Registration failed')
    invoice = rpc(operator, 'signinvoice', unsigned_invoice(payment_hash, secret))['bolt11']
    decoded = rpc(payer, 'decode', invoice)
    check(decoded['valid'] and decoded['currency'] == 'bcrt'
          and decoded['payment_hash'] == payment_hash and decoded['payee'] == operator['id']
          and decoded['amount_msat'] == 100000000, 'Signed invoice mismatch')
    paying = lab.start([*payer['cli'], 'pay', invoice], lab.root / 'payment.log')
    wait_until(lambda: bool(rpc(operator, 'xbt-held')['held']), paying, timeout=120)
    journal = plugin.with_suffix('.quotes.json')
    before = journal.read_bytes()
    saved = json.loads(before)[payment_hash]
    check(saved['phase'] == 'held' and saved['terms'] == terms, 'Quote not durably bound')
    check(paying.poll() is None, 'Payment completed before resolution')
    old_id = operator['id']
    lab.stop(operator['proc'])
    operator = lab.lightning('operator', backend, plugin)
    check(operator['id'] == old_id, 'Restart changed identity')
    rpc(payer, 'connect', operator['id'], '127.0.0.1', operator['port'])
    wait_until(lambda: bool(rpc(operator, 'xbt-held')['held']), paying, timeout=120)
    check(journal.read_bytes() == before, 'Restart changed original quote or binding')
    print('PASS: held BTC hook replayed after coordinator restart; original binding preserved', flush=True)
    if fail:
        rpc(operator, 'xbt-fail', payment_hash, json.dumps(saved['binding']))
    else:
        rpc(operator, 'xbt-release', preimage)
    paying.wait(timeout=120)
    check((paying.returncode != 0) == fail, 'Unexpected payer outcome')
    terminal = 'failed' if fail else 'resolved'
    for _ in range(2):
        status = rpc(operator, 'xbt-quote-status', payment_hash)
        check(status['phase'] == terminal and status['binding'] == saved['binding'], 'Terminal binding mismatch')
    delta = 0 if fail else 100000000
    for node, change in ((payer, -delta), (operator, delta)):
        wait_until(lambda: not channel(node).get('htlcs') and
                   channel(node)['to_us_msat'] == initial[node['id']]+change, node['proc'], timeout=120)
    attempts = [p for p in rpc(payer, 'listsendpays')['payments'] if p['payment_hash'] == payment_hash]
    check(len(attempts) == 1 and attempts[0]['status'] == ('failed' if fail else 'complete'), 'Duplicate or unexpected attempt')
    if not fail:
        check(attempts[0]['payment_preimage'] == preimage, 'Settlement proof mismatch')
        # Exercise the outgoing sendpay/waitsendpay RPCs used by the controller.
        incoming = rpc(payer, 'invoice', 15000000, 'outgoing-check', 'BTC image test')
        c = channel(operator)
        route = [dict(id=payer['id'], channel=c['short_channel_id'], amount_msat=15000000, delay=40)]
        lab.rpc([*operator['cli'], '-k'], 'sendpay', 'route='+json.dumps(route),
                'payment_hash='+incoming['payment_hash'], 'payment_secret='+incoming['payment_secret'])
        result = rpc(operator, 'waitsendpay', incoming['payment_hash'])
        check(result['status'] == 'complete' and result['amount_sent_msat'] == 15000000, 'Outgoing result mismatch')
        check(hashlib.sha256(bytes.fromhex(result['payment_preimage'])).hexdigest() == incoming['payment_hash'], 'Outgoing preimage mismatch')
        for node, change in ((payer, -85000000), (operator, 85000000)):
            wait_until(lambda: not channel(node).get('htlcs') and
                       channel(node)['to_us_msat'] == initial[node['id']]+change, node['proc'], timeout=120)
        check(rpc(payer, 'listinvoices', 'outgoing-check')['invoices'][0]['status'] == 'paid', 'Outgoing recipient unpaid')
        print('PASS: outgoing sendpay/waitsendpay returned matching preimage; balances verified', flush=True)
    print('BTC image gate compatibility OK ('+('failure' if fail else 'settlement')+'; regtest only; no XBT leg or live activation)', flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fail', action='store_true')
    args = p.parse_args()
    check(os.environ.get('BTC_DISPOSABLE_CONTAINER') == '1', 'Use the Docker launcher')
    os.umask(0o077)
    root = Path(tempfile.mkdtemp(prefix='btc-gate-', dir='/results'))
    print('Test directory: '+str(root), flush=True)
    lab = ImageLab(root, '/test-bitcoind', '/usr/bin/bitcoin-cli')
    try: run(lab, args.fail)
    finally: lab.close()


if __name__ == '__main__': main()
