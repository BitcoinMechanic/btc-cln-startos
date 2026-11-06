"""Disposable real BTC history + synthetic legacy envelopes; no cross-chain claim."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
from types import SimpleNamespace
import test_engine as engine
import test_gate_engine as gate
import chain_identity as ci
import validate_upgrade as v


class Lab(engine.Lab):
    engine_versions = {ci.BTC: ('v26.06.10', 'v26.06.10-suitbox1')}
    updated = False

    def start(self, command, log):
        if str(command[0]) == '/opt/btc/bin/lightningd':
            root = next(str(x).split('=', 1)[1] for x in command if str(x).startswith('--lightning-dir='))
            args = [str(x) for x in command[1:] if not str(x).startswith(('--network=', '--lightning-dir='))]
            command = ['/usr/local/libexec/swap-node/package_node.py', '--disposable-regtest', '--profile', ci.BTC, '--root', root, 'launch', *args]
        return super().start(command, log)

    def lightning(self, name, profile, backend, **kwargs):
        self.args.btc_prefix = Path('/opt/btc' if self.updated and name == 'target' else '/opt/btc-before')
        n = super().lightning(name, profile, backend, **kwargs)
        n.update(name=name, profile=profile, backend=backend)
        return n


def write(root, rel, obj):
    p = root/rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, sort_keys=True))


def channel_pin(ch):
    return {k:ch[k] for k in v.pc.FIELDS}


def run(lab):
    gate.AMOUNT = 1000000
    backend = lab.backend('backend', False)
    peer = lab.lightning('peer', ci.BTC, backend)
    target = lab.lightning('target', ci.BTC, backend)
    root = target['root']; node_id = target['identity']['node_id']
    lab.rpc(backend['cli'], 'sendtoaddress', engine.funding_address(lab, peer), '0.02')
    lab.mine(backend); lab.synced(backend, peer, target)

    def open_channel():
        lab.rpc(peer['cli'], 'connect', node_id, '127.0.0.1', target['port'])
        lab.rpc_named(peer['cli'], 'fundchannel', dict(id=node_id, amount=300000, push_msat=50000000), timeout=90)
        lab.mine(backend); lab.synced(backend, peer, target); gate.connect(lab, peer, target)
        return channel_pin(gate.channel(lab, target))

    gates = {}; records = []
    def envelope(pin, label, expired=False):
        if expired:
            payment = hashlib.sha256(b'synthetic-expired-legacy-invoice').hexdigest()
            secret = 'ab'*32; preimage = None
        else:
            gate.ordinary_payment(lab, peer, target, label)
            invoice = lab.rpc(target['cli'], 'listinvoices', label)['invoices'][0]
            payment = invoice['payment_hash']; preimage = invoice['payment_preimage']
            secret = lab.rpc(target['cli'], 'decode', invoice['bolt11'])['payment_secret']
        xp = dict(pin, channel_id='66'*32, funding_txid='77'*32, peer_id=peer['identity']['node_id'])
        c = dict(profile=v.pc.PROFILE, source_commit=v.PIN, nonce=hashlib.sha256(label.encode()).hexdigest(),
                 nodes={'btc':node_id, 'xbt':'02'+'33'*32}, channels={'btc':pin, 'xbt':xp},
                 invoice='lnxbt-synthetic-envelope-'+label, payment_hash=payment, payment_secret=secret,
                 recipient=peer['identity']['node_id'], created_at=1, admission_until=1801)
        v.pc.validate(c)
        terms = dict(payment_hash=payment, expires_at=2)
        r = dict(schema=1, role='btc', pilot_id=v.pc.digest(c), contract=c, publish={'terms':terms})
        g = dict(terms=terms, phase='expired' if expired else 'resolved')
        if expired:
            r['retire'] = True
        else:
            h = next(h for h in lab.rpc(target['cli'], 'listhtlcs')['htlcs'] if h['payment_hash'] == payment)
            binding = [pin['short_channel_id'], h['id']]
            r['release'] = {'binding':binding}; g.update(binding=binding, preimage=preimage)
        records.append(r); gates[payment] = g

    old_pin = open_channel()
    envelope(old_pin, 'old-channel-payment')
    envelope(old_pin, 'old-channel-expired', expired=True)
    lab.rpc(peer['cli'], 'close', node_id, timeout=90)
    lab.mine(backend, 110); lab.synced(backend, peer, target)
    lab.wait(lambda:any(c['channel_id'] == old_pin['channel_id'] for c in lab.rpc(target['cli'], 'listclosedchannels')['closedchannels']), timeout=120)
    new_pin = open_channel()
    envelope(new_pin, 'current-channel-payment')
    write(root, 'store.json', {'restore':False, 'rescan':-123, 'custom':'preserve'})
    write(root, 'coordinator-preparation.json', dict(schema=1,scope='preparation-only',network='bitcoin',source_commit=v.PIN,node_id=node_id))
    write(root, 'btc-gate-activation.json', dict(schema=1,profile='live-pilot-v1',source_commit=v.PIN,
          source_sha256='2dcd0e828b8e34acec3ba906c673c8882a3ae526f3ddd9e857b10d473a4f381c',node_id=node_id,
          secret_sha256=hashlib.sha256((root/'regtest/hsm_secret').read_bytes()).hexdigest()))
    for r in records: write(root, 'forward-swaps/'+r['pilot_id']+'.json', r)
    write(root, 'regtest/swap-gate/quote_plugin.quotes.json', gates)
    saved = {str(p.relative_to(root)):p.read_bytes() for rel in ('coordinator-preparation.json', 'btc-gate-activation.json', 'store.json', 'forward-swaps', 'regtest/swap-gate') for p in ([root/rel] if (root/rel).is_file() else (root/rel).rglob('*')) if p.is_file()}
    lab.stop(target['proc'])
    # Only this disposable fixture maps regtest storage to the production
    # directory name and passes its genesis explicitly. The shipped CLI has
    # neither a network override nor a regtest-admission option.
    snapshot = Path(tempfile.mkdtemp(prefix='legacy-admission-', dir=lab.root))
    (snapshot/'bitcoin').mkdir()
    for name in ('hsm_secret', 'lightningd.sqlite3'):
        shutil.copy2(root/'regtest'/name, snapshot/'bitcoin'/name)
    for name in ('lightningd.sqlite3-wal', 'lightningd.sqlite3-journal'):
        if (root/'regtest'/name).exists(): shutil.copy2(root/'regtest'/name,snapshot/'bitcoin'/name)
    shutil.copytree(root/'regtest/swap-gate', snapshot/'bitcoin/swap-gate')
    for rel in ('coordinator-preparation.json', 'btc-gate-activation.json', 'store.json'):
        shutil.copy2(root/rel, snapshot/rel)
    shutil.copytree(root/'forward-swaps', snapshot/'forward-swaps')
    genesis = bytes.fromhex(lab.rpc(backend['cli'], 'getblockhash', 0))[::-1]
    result = v.validate(snapshot, genesis=genesis)
    engine.require(result['records'] == 3 and result['archived'] == 2 and result['retired'] == 1, 'legacy_readback_failed')
    print('PASS: real CLN schema, secret derivation, terminal HTLC and fully archived funding; synthetic legacy envelopes', flush=True)
    lab.updated = True
    target = lab.lightning('target', ci.BTC, backend); gate.connect(lab, peer, target)
    engine.require(target['identity']['node_id'] == node_id, 'node_identity_changed')
    engine.require(channel_pin(gate.channel(lab, target)) == new_pin, 'funded_channel_changed')
    engine.require(not (root/'regtest/swap-coordinator-v1').exists(), 'implicit_new_authority')
    methods = {r['command'].split()[0] for r in lab.rpc(target['cli'], 'help')['help']}
    engine.require(not methods & {'swap-session-call','swap-reverse-call','xbt-quote-status'}, 'legacy_plugins_reactivated')
    gate.ordinary_payment(lab, peer, target, 'after-update-incoming')
    gate.ordinary_payment(lab, target, peer, 'after-update-outgoing')
    prepared = subprocess.run(['/usr/local/libexec/swap-node/package_node.py','--disposable-regtest','--profile',ci.BTC,'--root',str(root),'prepare'],input='{"confirmed":true}',capture_output=True,text=True,check=True)
    engine.require(json.loads(prepared.stdout)['initialized'], 'explicit_setup_failed')
    lab.stop(target['proc']); target = lab.lightning('target', ci.BTC, backend); gate.connect(lab, peer, target)
    gate.ordinary_payment(lab, peer, target, 'after-explicit-setup-restart')
    engine.require(channel_pin(gate.channel(lab,target)) == new_pin, 'funding_changed_after_setup')
    for rel,raw in saved.items(): engine.require((root/rel).read_bytes()==raw, 'legacy_record_rewritten')
    report = dict(regtest_only=True, synthetic_legacy_envelopes=True, ordinary_payments=5, legacy_records_validated=3,
                  real_archived_channel=True, same_volume_update=True, current_funding_preserved=True,
                  identity_preserved=True, legacy_records_unchanged=True, legacy_authority_reactivated=False,
                  explicit_new_setup_and_restart=True, live_StartOS_acceptance=False, cross_chain_swaps_rerun=False)
    (lab.root/'legacy-upgrade-result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


os.umask(0o077)
args=SimpleNamespace(results_parent=Path('/results'),bitcoind=Path('/usr/local/bin/bitcoind'),bitcoin_cli=Path('/usr/bin/bitcoin-cli'),btc_prefix=Path('/opt/btc-before'),xbt_prefix=Path('/opt/xbt'))
lab=Lab(args)
try:run(lab)
finally:lab.close()
