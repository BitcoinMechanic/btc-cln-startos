"""Exercise the adapter with the real pinned gate and its durable journal."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'assets/swaps'),'/usr/local/libexec/btc-controller']
import bound_release as b
SOURCE=Path(os.environ.get('BTC_GATE_TEST_SOURCE','/usr/local/libexec/cln-swap/quote_plugin.py'))

class BoundTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.script=Path(self.tmp.name)/'quote_plugin.py';self.journal=self.script.with_suffix('.quotes.json')
        self.preimage='ab'*32;self.hash=hashlib.sha256(bytes.fromhex(self.preimage)).hexdigest()
        self.init=dict(id=1,method='init',params=dict(configuration=dict(network='regtest'),options={}))
        terms=dict(payment_hash=self.hash,payment_secret='cd'*32,btc_amount_msat=1000000,xbt_amount_msat=2000000,
                   xbt_invoice='lnxbtrt-fixture',expires_at=int(time.time())+100,min_cltv_delta=100,max_cltv_delta=2000)
        self.hook=dict(id=3,method='htlc_accepted',params=dict(
            htlc=dict(short_channel_id='1x1x1',id=7,payment_hash=self.hash,amount_msat=1000000,cltv_expiry=1000,cltv_expiry_relative=300),
            onion=dict(payment_secret='cd'*32,forward_msat=1000000,total_msat=1000000,type='tlv',outgoing_cltv_value=1000)))
        self.run_gate([self.init,dict(id=2,method='xbt-register',params=dict(quote=terms)),self.hook])
    def run_gate(self,messages):
        output=io.StringIO()
        with patch.object(sys,'stdin',io.StringIO('\n'.join(map(json.dumps,messages)))),contextlib.redirect_stdout(output):
            b.run(SOURCE,self.script)
        return [json.loads(line) for line in output.getvalue().splitlines() if line.strip()]
    def release(self,params):return dict(id=4,method=b.METHOD,params=params)
    def test_manifest_and_legacy_preserved(self):
        result=self.run_gate([dict(id=9,method='getmanifest')])[0]['result']
        methods={m['name']:m for m in result['rpcmethods']}
        self.assertEqual(methods[b.METHOD]['usage'],'payment_hash preimage')
        self.assertIn('xbt-release',methods)
    def test_mismatched_hash_and_malformed_params_leave_journal_unchanged(self):
        before=self.journal.read_bytes()
        for params in (dict(payment_hash='00'*32,preimage=self.preimage),
                       dict(payment_hash=self.hash,preimage='00'*32),
                       dict(payment_hash=self.hash,preimage=self.preimage,extra=1),
                       dict(preimage=self.preimage),[self.hash,self.preimage],
                       dict(payment_hash=self.hash,preimage=True)):
            replies=self.run_gate([self.init,self.hook,self.release(params)])
            self.assertEqual(replies[-1]['error']['message'],'invalid bound release')
            self.assertFalse(any(r.get('result',{}).get('result')=='resolve' for r in replies))
            self.assertEqual(self.journal.read_bytes(),before)
    def test_resolve_persist_restart_replay_and_no_second_release(self):
        params=dict(payment_hash=self.hash,preimage=self.preimage)
        replies=self.run_gate([self.init,self.hook,self.release(params)])
        self.assertEqual(replies[-1]['result'],dict(released=1))
        self.assertEqual(json.loads(self.journal.read_text())[self.hash]['phase'],'resolved')
        before=self.journal.read_bytes()
        replies=self.run_gate([self.init,self.hook,self.release(params)])
        self.assertEqual(replies[1]['result'],dict(result='resolve',payment_key=self.preimage))
        self.assertIn('error',replies[-1]);self.assertEqual(self.journal.read_bytes(),before)
    def test_source_change_refused(self):
        bad=self.script.with_name('bad.py');bad.write_text('raise AssertionError("must not execute")')
        with self.assertRaisesRegex(ValueError,'gate_source_changed'):b.run(bad,self.script)

if __name__=='__main__':unittest.main()
