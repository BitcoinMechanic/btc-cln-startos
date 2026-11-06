"""Read-only, stopped-wallet admission for retained legacy BTC journals.

Pinned CLN v26.06.10 database schema 284. No RPC, writes, daemon startup,
authority import, record deletion, or wallet restoration. Execute only with
the service stopped and its main volume mounted read-only by StartOS.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import sys
import time
import market_terms as mt
import pilot_contract as pc
import reverse_contract as rc

PIN = pc.PIN
GENESIS = bytes.fromhex('000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f')[::-1]
RESTORE = ('node-restored.json', 'swap-restored.json', 'btc-gate-restored.json',
           'xbt-gate-restored.json', 'forward-pilot-restored.json', 'reverse-pilot-restored.json')
FOREIGN = ('xbt', 'xbt-regtest', 'regtest', 'testnet', 'signet', 'swap-coordinator-v1',
           'swap-gate-v1', 'bounded-authority-v1', 'customer-remote-v1',
           'customer-invoices-v1', 'coordinator-admin-v1')


class Refused(Exception):
    pass


def need(ok, reason):
    if not ok:
        raise Refused(reason)


def unique(pairs):
    obj = {}
    for key, value in pairs:
        need(key not in obj, 'duplicate_json_key')
        obj[key] = value
    return obj


class Records:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.hashes = {}
        self.dirs = {}
        self.directory('')
        self.directory('bitcoin')

    def directory(self, rel):
        p = self.root / rel
        need(stat.S_ISDIR(p.lstat().st_mode), 'unsafe_directory')
        return p

    def exists(self, rel):
        return os.path.lexists(self.root / rel)

    def open(self, rel):
        p = Path(rel)
        need(not p.is_absolute() and '..' not in p.parts, 'unsafe_path')
        for ancestor in p.parents:
            self.directory(str(ancestor))
        fd = os.open(self.root / rel, os.O_RDONLY | os.O_NOFOLLOW)
        f = os.fdopen(fd, 'rb')
        meta = os.fstat(f.fileno())
        if not (stat.S_ISREG(meta.st_mode) and meta.st_nlink == 1):
            f.close()
            raise Refused('unsafe_file')
        return f

    def digest(self, rel, limit):
        with self.open(rel) as f:
            need(os.fstat(f.fileno()).st_size <= limit, 'oversize_file')
            digest = hashlib.file_digest(f, 'sha256').hexdigest()
        if rel in self.hashes:
            need(self.hashes[rel] == digest, 'state_changed_during_validation')
        self.hashes[rel] = digest
        return digest

    def read(self, rel, limit=262144):
        with self.open(rel) as f:
            data = f.read(limit + 1)
        need(len(data) <= limit, 'oversize_record')
        digest = hashlib.sha256(data).hexdigest()
        if rel in self.hashes:
            need(self.hashes[rel] == digest, 'state_changed_during_validation')
        self.hashes[rel] = digest
        return data

    def json(self, rel, limit=262144):
        return json.loads(self.read(rel, limit), object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(Refused('invalid_json_number')))

    def listing(self, rel, optional=False):
        if optional and not self.exists(rel):
            self.dirs[rel] = None
            return []
        names = sorted(p.name for p in self.directory(rel).iterdir())
        need(len(names) <= 10000, 'too_many_records')
        self.dirs[rel] = names
        return names

    def stable(self):
        for rel, digest in list(self.hashes.items()):
            need(self.digest(rel, 4 * 1024**3) == digest, 'state_changed_during_validation')
        for rel, names in list(self.dirs.items()):
            if names is None:
                need(not self.exists(rel), 'state_changed_during_validation')
            else:
                need(self.listing(rel) == names, 'state_changed_during_validation')


class Wallet:
    def __init__(self, records, genesis=GENESIS):
        self.records = records
        rel = 'bitcoin/lightningd.sqlite3'
        # immutable=1 cannot replay WAL; refuse it rather than silently ignoring it.
        for suffix in ('-wal', '-journal'):
            if records.exists(rel + suffix):
                with records.open(rel + suffix) as f:
                    need(os.fstat(f.fileno()).st_size == 0, 'wallet_requires_clean_shutdown')
                records.read(rel + suffix, 1)
        records.digest(rel, 4 * 1024**3)
        self.db = sqlite3.connect((records.root / rel).as_uri() + '?mode=ro&immutable=1', uri=True)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA query_only=ON')
        need(self.db.execute('PRAGMA quick_check(1)').fetchall()[0][0] == 'ok', 'wallet_integrity_failed')
        need([tuple(x) for x in self.db.execute('SELECT version FROM version')] == [(284,)], 'unsupported_wallet_schema')
        need(self.variable('genesis_hash') == genesis, 'wrong_wallet_network')
        self.node = self.variable('node_id')
        need(type(self.node) is bytes and len(self.node) == 33 and self.node[0] in (2, 3), 'invalid_wallet_identity')
        need(self.db.execute('SELECT count(*) FROM payments WHERE status NOT IN (1,2)').fetchone()[0] == 0, 'pending_or_unknown_payment')
        need(self.db.execute('SELECT count(*) FROM channel_htlcs WHERE NOT ((direction=0 AND hstate=19) OR (direction=1 AND hstate=9))').fetchone()[0] == 0, 'pending_or_unknown_htlc')
        need(self.db.execute('SELECT count(*) FROM channels WHERE state NOT IN (3,10)').fetchone()[0] == 0, 'channel_transition_or_recovery_in_progress')

    def variable(self, name):
        rows = self.db.execute('SELECT blobval FROM vars WHERE name=?', (name,)).fetchall()
        need(len(rows) == 1, 'wallet_binding_unavailable')
        return rows[0][0]

    def channel(self, pin):
        rows = self.db.execute('SELECT c.id,c.state,c.scid,c.alias_local,c.full_channel_id,c.funding_tx_id,c.funding_tx_outnum,p.node_id FROM channels c LEFT JOIN peers p ON p.id=c.peer_id WHERE c.full_channel_id=?', (bytes.fromhex(pin['channel_id']),)).fetchall()
        need(len(rows) == 1, 'original_channel_unavailable')
        ch = dict(rows[0])
        scid = ch['scid'] if ch['scid'] is not None else ch['alias_local']
        need(type(scid) is int, 'channel_scid_unavailable')
        scid &= 2**64-1
        actual = dict(channel_id=ch['full_channel_id'].hex(), short_channel_id=f'{scid >> 40}x{(scid >> 16) & 0xffffff}x{scid & 0xffff}',
                      funding_txid=ch['funding_tx_id'][::-1].hex(), funding_outnum=ch['funding_tx_outnum'], peer_id=ch['node_id'].hex() if ch['node_id'] else None)
        need(actual == pin and ch['state'] in (3, 10), 'original_channel_funding_changed')
        return ch

    def htlcs(self, ch, payment):
        return [dict(r) for r in self.db.execute('SELECT channel_htlc_id,direction,msatoshi,cltv_expiry,payment_hash,payment_key,hstate FROM channel_htlcs WHERE channel_id=? AND payment_hash=?', (ch['id'], bytes.fromhex(payment)))]

    def payments(self, payment):
        return [dict(r) for r in self.db.execute('SELECT status,payment_hash,destination,msatoshi,msatoshi_sent,payment_preimage,groupid,partid FROM payments WHERE payment_hash=?', (bytes.fromhex(payment),))]


def validate_record(r, direction, gates, wallet, now):
    contract = (pc if direction == 'forward' else rc)
    c = contract.validate(r['contract'])
    need(r.get('schema') == 1 and type(r['schema']) is int and r.get('role') == 'btc', 'legacy_record_schema_unknown')
    need(r.get('pilot_id') == contract.digest(c), 'legacy_contract_digest_changed')
    need(c['nodes']['btc'] == wallet.node.hex(), 'legacy_node_identity_changed')
    need('close' not in r, 'onchain_protection_requires_separate_review')
    payment = c['payment_hash']
    g = gates.get(payment)
    incoming = direction == 'forward'
    retired = 'retire' in r or 'unpublished_retired' in r
    pin = c['channels']['btc']
    if incoming and not retired and contract.routed(c):
        need(r.get('incoming_pin') in contract.incoming_pins(c), 'incoming_channel_not_in_contract')
        need(g is not None and r.get('incoming_binding') == g.get('binding'), 'incoming_binding_changed')
        pin = r['incoming_pin']
    ch = wallet.channel(pin)
    hs = wallet.htlcs(ch, payment)
    attempts = wallet.payments(payment)
    failed_self_attempts = 0
    if retired:
        need(r.get('retire') is True and not any(k in r for k in ('send', 'release', 'fail', 'close')), 'contradictory_retirement')
        need(not hs, 'retired_invoice_has_htlc')
        if r.get('unpublished_retired') is True:
            need(mt.market(c) and 'publish' not in r and g is None and not attempts, 'unpublished_retirement_changed')
            need(c['pricing']['expires_at'] <= now, 'retirement_not_expired')
        elif incoming:
            need(g is not None and r.get('publish', {}).get('terms') == g['terms'], 'retirement_terms_changed')
            need(g['terms']['payment_hash'] == payment and g.get('phase') == 'expired' and g.get('binding') is None
                 and 'accepted' not in g and 'preimage' not in g and g['terms']['expires_at'] <= now, 'retirement_not_verified')
            # A legacy incoming BTC invoice can have failed attempts by this
            # same BTC node. These do not imply the gate ever accepted it.
            # No generic exception for pending/complete, another destination,
            # another amount, a preimage, or an outgoing-coordinator record.
            for p in attempts:
                need(p['status'] == 2 and p['payment_preimage'] is None and p['payment_hash'].hex() == payment
                     and p['destination'] == wallet.node and p['msatoshi'] == mt.amounts(c)['btc'], 'retired_payment_attempt_not_failed_self_payment')
            failed_self_attempts = len(attempts)
        else:
            need(not attempts and 'send' not in r, 'retired_outgoing_attempt_exists')
        return dict(archived=ch['state'] == 10, retired=True, failed_self_attempts=failed_self_attempts)
    if incoming:
        need(g is not None and r.get('publish', {}).get('terms') == g['terms'] and g['terms']['payment_hash'] == payment, 'gate_terms_changed')
        need(g.get('phase') in ('resolved', 'failed'), 'gate_not_terminal')
        binding = g.get('binding')
        need(type(binding) is list and len(binding) == 2 and binding[0] == pin['short_channel_id'] and type(binding[1]) is int, 'gate_binding_changed')
        action, other = ('release', 'fail') if g['phase'] == 'resolved' else ('fail', 'release')
        need(r.get(action) == {'binding': binding} and other not in r, 'resolution_intent_changed')
        preimage = bytes.fromhex(g['preimage']) if g['phase'] == 'resolved' and pc.hex32(g.get('preimage')) else None
        if g['phase'] == 'resolved':
            need(preimage is not None and hashlib.sha256(preimage).hexdigest() == payment, 'gate_preimage_invalid')
        else:
            need(g.get('preimage') is None, 'failed_gate_has_preimage')
        expected = dict(direction=0, hstate=19, msatoshi=mt.amounts(c)['btc'], channel_htlc_id=binding[1])
        if contract.routed(c):
            need(type(r.get('incoming_expiry')) is int, 'incoming_expiry_missing')
            expected['cltv_expiry'] = r['incoming_expiry']
    else:
        need('send' in r and len(attempts) == 1, 'outgoing_attempt_unknown')
        p = attempts[0]
        need(p['status'] in (1, 2) and p['groupid'] == 1 and p['partid'] == 0 and p['msatoshi_sent'] == contract.sent_amount(c), 'outgoing_attempt_changed')
        if p['status'] == 1:
            need(type(p['payment_preimage']) is bytes and len(p['payment_preimage']) == 32 and hashlib.sha256(p['payment_preimage']).hexdigest() == payment, 'outgoing_preimage_invalid')
        else:
            need(p['payment_preimage'] is None, 'failed_outgoing_has_preimage')
        preimage = p['payment_preimage']
        expected = dict(direction=1, hstate=9, msatoshi=contract.sent_amount(c))
    # Closed-channel HTLC rows are pruned on the next daemon restart. If
    # still retained, verify them just as strictly as an open channel's rows.
    if ch['state'] == 3 or hs:
        need(len(hs) == 1 and all(type(hs[0].get(k)) is type(v) and hs[0][k] == v for k, v in expected.items()), 'wallet_htlc_evidence_changed')
        # CLN wallet_htlc_update scrubs payment_key on terminal states 9/19.
        # The preimage proof above comes from the retained gate/payment record.
        # If a key remains in the HTLC row, it must not contradict that proof.
        need(hs[0]['payment_key'] is None or hs[0]['payment_key'] == preimage, 'wallet_htlc_preimage_contradiction')
    return dict(archived=ch['state'] == 10, retired=False, failed_self_attempts=0)


def validate(root, *, genesis=GENESIS, hsmtool='/usr/local/bin/lightning-hsmtool'):
    records = Records(root)
    for base in ('', 'bitcoin/'):
        for name in RESTORE + FOREIGN:
            need(not records.exists(base + name), 'restore_or_foreign_authority_present')
    need(not any(n.startswith('.swap-setup-') for n in records.listing('bitcoin')), 'unfinished_coordinator_setup')
    store = records.json('store.json')
    need(type(store) is dict and (store.get('restore') is None or store.get('restore') is False), 'restore_pending')
    prep = records.json('coordinator-preparation.json')
    activation = records.json('btc-gate-activation.json')
    need(prep.get('schema') == 1 and prep.get('scope') == 'preparation-only' and prep.get('network') == 'bitcoin' and prep.get('source_commit') == PIN, 'legacy_preparation_unknown')
    need(set(activation) == {'schema', 'profile', 'source_commit', 'source_sha256', 'node_id', 'secret_sha256'} and activation['schema'] == 1
         and activation['profile'] in ('live-pilot-v1', 'startos-fixed-repeat-v1', mt.GATE) and activation['source_commit'] == PIN
         and activation['source_sha256'] in ('2dcd0e828b8e34acec3ba906c673c8882a3ae526f3ddd9e857b10d473a4f381c', '5073f0d7a6d5357b49a03eaa4d4a43a9668e87d6199bb979d5b5b9f3d651705e', '19a91416b5f6edc2a8c651463185f7676483c1b59367ea54e9e449c546853b5d'), 'legacy_activation_unknown')
    secret = records.read('bitcoin/hsm_secret', 4096)
    need(hashlib.sha256(secret).hexdigest() == activation['secret_sha256'], 'legacy_wallet_secret_changed')
    wallet = Wallet(records, genesis)
    try:
        need(prep.get('node_id') == activation['node_id'] == wallet.node.hex(), 'legacy_wallet_identity_changed')
        result = subprocess.run([hsmtool, 'getnodeid', str(records.root/'bitcoin/hsm_secret')], capture_output=True, text=True, timeout=20)
        need(result.returncode == 0 and result.stdout.strip() == wallet.node.hex(), 'wallet_identity_derivation_failed')
        gate_names = records.listing('bitcoin/swap-gate')
        need(set(gate_names) <= {'gate.lock', 'quote_plugin.quotes.json'}, 'unknown_gate_journal_files')
        gates = records.json('bitcoin/swap-gate/quote_plugin.quotes.json', 16*1024**2)
        need(type(gates) is dict and all(pc.hex32(h) for h in gates), 'invalid_gate_journal')
        seen_hashes = set(); forward_hashes = set(); counts = dict(records=0, archived=0, retired=0, failed_self_attempts=0)
        now = int(time.time())
        for direction in ('forward', 'reverse'):
            ids = {}; session_bindings = {}
            paths = []
            for name in records.listing(direction+'-swaps', optional=True):
                need(re.fullmatch('[0-9a-f]{64}[.]json', name), 'unknown_swap_record_file')
                paths.append(direction+'-swaps/'+name)
            single = direction+'-pilot.json'
            if records.exists(single):
                paths.append(single)
            for rel in paths:
                r = records.json(rel)
                outcome = validate_record(r, direction, gates, wallet, now)
                swap_id = r['pilot_id']; payment = r['contract']['payment_hash']
                if rel != single:
                    need(Path(rel).stem == swap_id, 'swap_filename_changed')
                need(swap_id not in ids and payment not in seen_hashes, 'duplicate_swap_record')
                ids[swap_id] = payment; seen_hashes.add(payment)
                if 'session_id' in r:
                    need(pc.hex32(r['session_id']), 'invalid_session_reference')
                    session_bindings[swap_id] = r['session_id']
                if direction == 'forward' and not r.get('unpublished_retired'):
                    forward_hashes.add(payment)
                counts['records'] += 1
                for key in ('archived', 'retired', 'failed_self_attempts'):
                    counts[key] += outcome[key]
            session_ids = set(); enrolled_ids = set()
            for name in records.listing(direction+'-sessions', optional=True):
                need(re.fullmatch('[0-9a-f]{64}[.]json', name), 'unknown_session_file')
                s = records.json(direction+'-sessions/'+name)
                sid = Path(name).stem
                need(s.get('schema') == 1 and s.get('session_id') == sid and s.get('role') == 'btc' and s.get('node_id') == wallet.node.hex(), 'session_identity_changed')
                need(type(s.get('enrolled')) is dict, 'session_enrollment_unknown')
                for swap_id, payment in s['enrolled'].items():
                    need(ids.get(swap_id) == payment and session_bindings.get(swap_id) == sid and swap_id not in enrolled_ids, 'session_enrollment_changed')
                    enrolled_ids.add(swap_id)
                session_ids.add(sid)
            need(set(session_bindings) <= enrolled_ids, 'swap_session_enrollment_missing')
            selector = direction+'-session.json'
            if records.exists(selector):
                s = records.json(selector)
                need(set(s) == {'session_id'} and s['session_id'] in session_ids, 'session_selector_changed')
        need(set(gates) == forward_hashes, 'unaccounted_gate_entry')
        records.stable()
        return dict(admitted=True, legacy_records_preserved=True, legacy_authority_imported=False, **counts)
    finally:
        wallet.db.close()


if __name__ == '__main__':
    try:
        need(len(sys.argv) == 2, 'invalid_arguments')
        print(json.dumps(validate(sys.argv[1]), sort_keys=True))
    except Exception as error:
        reason = str(error) if isinstance(error, Refused) else 'legacy_state_unverified'
        print(json.dumps(dict(admitted=False, reason=reason)))
        sys.exit(1)
