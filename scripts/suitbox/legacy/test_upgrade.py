"""Stopped-wallet migration controls; all fixtures and secrets are synthetic."""
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import validate_upgrade as v

NODE = '02'+'11'*32
PEER = '03'+'22'*32
XBT = '02'+'33'*32
PIN = dict(channel_id='44'*32, short_channel_id='100x2x0', funding_txid='55'*32, funding_outnum=0, peer_id=PEER)
XPIN = dict(channel_id='66'*32, short_channel_id='200x2x0', funding_txid='77'*32, funding_outnum=0, peer_id=PEER)
PREIMAGE = bytes.fromhex('88'*32)
PAYMENT = hashlib.sha256(PREIMAGE).hexdigest()
SECRET = bytes.fromhex('99'*32)
SESSION = 'aa'*32


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write('bitcoin/hsm_secret', SECRET)
        self.write('store.json', dict(restore=False, rescan=-500, custom='preserve'))
        self.write('.commando-env', b'private-credential-sentinel')
        self.write('coordinator-preparation.json', dict(schema=1, scope='preparation-only', network='bitcoin', source_commit=v.PIN, node_id=NODE))
        self.write('btc-gate-activation.json', dict(schema=1, profile='live-pilot-v1', source_commit=v.PIN,
                   source_sha256='2dcd0e828b8e34acec3ba906c673c8882a3ae526f3ddd9e857b10d473a4f381c', node_id=NODE,
                   secret_sha256=hashlib.sha256(SECRET).hexdigest()))
        self.c = dict(profile=v.pc.PROFILE, source_commit=v.PIN, nonce='bb'*32,
                      nodes={'btc': NODE, 'xbt': XBT}, channels={'btc': PIN, 'xbt': XPIN},
                      invoice='lnxbt-synthetic-fixture', payment_hash=PAYMENT, payment_secret='cc'*32,
                      recipient=PEER, created_at=1, admission_until=1801)
        self.swap = v.pc.digest(self.c)
        self.terms = dict(payment_hash=PAYMENT, expires_at=2)
        self.record = dict(schema=1, role='btc', pilot_id=self.swap, session_id=SESSION,
                           contract=self.c, publish={'terms': self.terms}, retire=True)
        self.gates = {PAYMENT: dict(phase='expired', terms=self.terms)}
        self.write('forward-swaps/'+self.swap+'.json', self.record)
        self.write('forward-sessions/'+SESSION+'.json', dict(schema=1, session_id=SESSION, role='btc', node_id=NODE, enrolled={self.swap: PAYMENT}))
        self.write('forward-session.json', {'session_id': SESSION})
        self.write('bitcoin/swap-gate/quote_plugin.quotes.json', self.gates)
        self.dbpath = self.root/'bitcoin/lightningd.sqlite3'
        db = sqlite3.connect(self.dbpath)
        db.executescript('''CREATE TABLE version(version INTEGER); INSERT INTO version VALUES(284);
          CREATE TABLE vars(name TEXT PRIMARY KEY, blobval BLOB);
          CREATE TABLE peers(id INTEGER PRIMARY KEY,node_id BLOB);
          CREATE TABLE channels(id INTEGER PRIMARY KEY,state INTEGER,scid INTEGER,alias_local INTEGER,full_channel_id BLOB,funding_tx_id BLOB,funding_tx_outnum INTEGER,peer_id INTEGER);
          CREATE TABLE channel_htlcs(channel_id INTEGER,channel_htlc_id INTEGER,direction INTEGER,msatoshi INTEGER,cltv_expiry INTEGER,payment_hash BLOB,payment_key BLOB,hstate INTEGER);
          CREATE TABLE payments(status INTEGER,payment_hash BLOB,destination BLOB,msatoshi INTEGER,msatoshi_sent INTEGER,payment_preimage BLOB,groupid INTEGER,partid INTEGER);''')
        db.executemany('INSERT INTO vars VALUES(?,?)', [('genesis_hash', v.GENESIS), ('node_id', bytes.fromhex(NODE))])
        db.execute('INSERT INTO peers VALUES(1,?)', (bytes.fromhex(PEER),))
        db.execute('INSERT INTO channels VALUES(1,10,?,NULL,?,?,0,1)', ((100<<40)+(2<<16), bytes.fromhex(PIN['channel_id']), bytes.fromhex(PIN['funding_txid'])[::-1]))
        db.commit(); db.close()
        self.hsmtool = self.root/'test-hsmtool'
        self.hsmtool.write_text('#!/bin/sh\nprintf "%s\\n" "'+NODE+'"\n')
        self.hsmtool.chmod(0o700)

    def write(self, path, value):
        p = self.root/path; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(value if type(value) is bytes else json.dumps(value).encode())

    def sql(self, query, params=()):
        with sqlite3.connect(self.dbpath) as db:
            db.execute(query, params)

    def attempt(self, status=2, destination=NODE, amount=1000000, preimage=None):
        self.sql('INSERT INTO payments VALUES(?,?,?,?,?,?,1,0)', (status, bytes.fromhex(PAYMENT), bytes.fromhex(destination), amount, amount, preimage))

    def run_validator(self):
        before = {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file() and not p.is_symlink()}
        try:
            return v.validate(self.root, hsmtool=str(self.hsmtool))
        finally:
            after = {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file() and not p.is_symlink()}
            self.assertEqual(before, after)

    def refused(self, reason):
        with self.assertRaisesRegex(v.Refused, '^'+reason+'$'):
            self.run_validator()

    def test_archived_expired_records_and_failed_self_attempts_preserved(self):
        for _ in range(3): self.attempt()
        r = self.run_validator()
        self.assertTrue(r['admitted']); self.assertFalse(r['legacy_authority_imported'])
        self.assertEqual(r['failed_self_attempts'], 3)
        self.assertEqual(r['archived'], 1)

    def test_pending_self_payment_refused(self):
        self.attempt(status=0); self.refused('pending_or_unknown_payment')

    def test_completed_self_payment_refused(self):
        self.attempt(status=1, preimage=PREIMAGE); self.refused('retired_payment_attempt_not_failed_self_payment')

    def test_failed_payment_to_other_node_refused(self):
        self.attempt(destination=PEER); self.refused('retired_payment_attempt_not_failed_self_payment')

    def test_failed_payment_wrong_amount_refused(self):
        self.attempt(amount=1000001); self.refused('retired_payment_attempt_not_failed_self_payment')

    def test_failed_payment_with_preimage_refused(self):
        self.attempt(preimage=PREIMAGE); self.refused('retired_payment_attempt_not_failed_self_payment')

    def test_changed_contract_digest_refused(self):
        self.record['contract']['nonce'] = 'dd'*32
        self.write('forward-swaps/'+self.swap+'.json', self.record)
        self.refused('legacy_contract_digest_changed')

    def test_changed_funding_refused(self):
        self.sql('UPDATE channels SET funding_tx_outnum=1'); self.refused('original_channel_funding_changed')

    def test_wallet_key_change_refused(self):
        self.write('bitcoin/hsm_secret', b'other-secret'); self.refused('legacy_wallet_secret_changed')

    def test_node_key_derivation_mismatch_refused(self):
        self.hsmtool.write_text('#!/bin/sh\necho different-node\n'); self.refused('wallet_identity_derivation_failed')

    def test_wal_never_silently_ignored(self):
        self.write('bitcoin/lightningd.sqlite3-wal', b'wal'); self.refused('wallet_requires_clean_shutdown')

    def test_restore_barrier_preserved(self):
        self.write('btc-gate-restored.json', {}); self.refused('restore_or_foreign_authority_present')

    def test_foreign_authority_refused(self):
        (self.root/'bitcoin/swap-coordinator-v1').mkdir(); self.refused('restore_or_foreign_authority_present')

    def test_session_missing_record_refused(self):
        self.write('forward-sessions/'+SESSION+'.json', dict(schema=1, session_id=SESSION, role='btc', node_id=NODE, enrolled={'ee'*32:PAYMENT}))
        self.refused('session_enrollment_changed')

    def test_gate_acceptance_on_retired_invoice_refused(self):
        self.gates[PAYMENT]['binding'] = [PIN['short_channel_id'], 1]
        self.write('bitcoin/swap-gate/quote_plugin.quotes.json', self.gates)
        self.refused('retirement_not_verified')

    def test_symlink_refused(self):
        p = self.root/'forward-swaps'/f'{self.swap}.json'
        p.rename(self.root/'saved-record'); p.symlink_to(self.root/'saved-record')
        with self.assertRaises(OSError): self.run_validator()

    def test_current_channel_terminal_htlc(self):
        self.sql('UPDATE channels SET state=3')
        self.record.pop('retire'); self.record['release'] = {'binding':[PIN['short_channel_id'], 7]}
        self.gates[PAYMENT].update(phase='resolved', binding=[PIN['short_channel_id'],7], preimage=PREIMAGE.hex())
        self.write('forward-swaps/'+self.swap+'.json', self.record)
        self.write('bitcoin/swap-gate/quote_plugin.quotes.json', self.gates)
        self.sql('INSERT INTO channel_htlcs VALUES(1,7,0,1000000,1000,?,?,19)', (bytes.fromhex(PAYMENT), PREIMAGE))
        self.assertTrue(self.run_validator()['admitted'])
        self.sql('UPDATE channel_htlcs SET payment_key=NULL')
        self.assertTrue(self.run_validator()['admitted'])
        self.sql('UPDATE channels SET state=10')
        self.assertTrue(self.run_validator()['admitted'])
        self.sql('UPDATE channel_htlcs SET payment_key=?', (bytes.fromhex('00'*32),))
        self.refused('wallet_htlc_preimage_contradiction')

    def test_pending_htlc_refused(self):
        self.sql('INSERT INTO channel_htlcs VALUES(1,7,0,1000000,1000,?,NULL,14)', (bytes.fromhex(PAYMENT),))
        self.refused('pending_or_unknown_htlc')

    def test_duplicate_json_key_refused(self):
        self.write('store.json', b'{"restore":true,"restore":false}')
        self.refused('duplicate_json_key')

    def test_wrong_database_version_refused(self):
        self.sql('UPDATE version SET version=285'); self.refused('unsupported_wallet_schema')

    def test_null_states_fail_closed(self):
        self.attempt(status=None); self.refused('pending_or_unknown_payment')
        self.sql('DELETE FROM payments')
        self.sql('UPDATE channels SET state=NULL'); self.refused('channel_transition_or_recovery_in_progress')
        self.sql('UPDATE channels SET state=10')
        self.sql('INSERT INTO channel_htlcs VALUES(1,7,0,1000000,1000,?,NULL,NULL)', (bytes.fromhex(PAYMENT),))
        self.refused('pending_or_unknown_htlc')

    def test_reverse_terminal_payment_and_htlc(self):
        for p in (self.root/'forward-swaps').iterdir(): p.unlink()
        for p in (self.root/'forward-sessions').iterdir(): p.unlink()
        (self.root/'forward-session.json').unlink()
        self.write('bitcoin/swap-gate/quote_plugin.quotes.json', {})
        c = copy.deepcopy(self.c)
        c.update(profile=v.rc.ROUTED_288, invoice='lnbc-synthetic-fixture', incoming_channels=[XPIN],
                 route=[dict(id=PEER, channel=PIN['short_channel_id'], amount_msat=1500000, delay=40)])
        sid = v.rc.digest(c)
        r = dict(schema=1, role='btc', pilot_id=sid, contract=c, send={'intent':True})
        self.write('reverse-swaps/'+sid+'.json', r)
        self.sql('UPDATE channels SET state=3')
        self.attempt(status=1, amount=1500000, destination=PEER, preimage=PREIMAGE)
        self.sql('INSERT INTO channel_htlcs VALUES(1,7,1,1500000,1000,?,?,9)', (bytes.fromhex(PAYMENT), PREIMAGE))
        self.assertTrue(self.run_validator()['admitted'])
        self.attempt(status=1, amount=1500000, destination=PEER, preimage=PREIMAGE)
        self.refused('outgoing_attempt_unknown')


if __name__ == '__main__':
    unittest.main()
