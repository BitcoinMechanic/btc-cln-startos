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
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'assets/swaps'))
sys.path.append('/usr/local/libexec/btc-controller')
import gate as g

NODE = '02' + '11'*32
class Preparation:
    def inspect(self): return {'node_id': NODE}, {'prepared': True}

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'bitcoin').mkdir()
        (self.root/'bitcoin/hsm_secret').write_bytes(b'k'*32)
        self.active = False
        self.channels = [dict(state='CHANNELD_NORMAL',peer_connected=True,htlcs=[])]
        self.calls = []
        self.worker = g.Gate(self.root, self.rpc, Preparation())
    def rpc(self, method):
        self.calls.append(method)
        if method == 'getinfo': return dict(id=NODE,network='bitcoin')
        if method == 'listpeerchannels': return dict(channels=self.channels)
        if method == 'plugin': return dict(plugins=[dict(name=g.PLUGIN,active=True)] if self.active else [])
        if method == 'xbt-pilot-info': return dict(profile=g.PROFILE, registered_quotes=0)
        raise AssertionError(method)
    def activate(self):
        with patch.object(g, 'source_check'): return self.worker.activate(True)
    def test_optin_and_repeat_no_rewrite(self):
        with self.assertRaises(g.Blocked): self.worker.activate(False)
        self.assertFalse((self.root/g.RECORD).exists())
        result = self.activate()
        self.assertTrue(result['restart_required'])
        path = self.root/g.RECORD
        before = path.stat().st_mtime_ns, path.read_bytes()
        self.activate()
        self.assertEqual(before, (path.stat().st_mtime_ns,path.read_bytes()))
        self.assertFalse(result['payment_started'])
    def test_requires_connected_quiescent_channel(self):
        for channels in ([], [dict(state='CHANNELD_NORMAL',peer_connected=False,htlcs=[])], [dict(state='CHANNELD_NORMAL',peer_connected=True,htlcs=[{}])]):
            self.channels = channels
            with self.assertRaises(g.Blocked): self.activate()
            self.assertFalse((self.root/g.RECORD).exists())
    def test_changed_secret_and_symlink_refused(self):
        self.activate()
        key = self.root/'bitcoin/hsm_secret'
        key.write_bytes(b'x'*32)
        with self.assertRaises(g.Blocked): g.record(self.root)
        key.unlink(); key.symlink_to('/dev/null')
        with self.assertRaises(g.Blocked): g.key_hash(self.root)
    def test_restored_barrier_and_old_journal_refused(self):
        (self.root/g.BARRIER).write_text('{}')
        with self.assertRaises(g.Blocked): self.activate()
        (self.root/g.BARRIER).unlink()
        path = g.journal_path(self.root); path.parent.mkdir(); path.write_text('{}')
        with self.assertRaises(g.Blocked): self.activate()
        self.assertEqual(path.read_text(),'{}')
    def test_status_checks_running_gate(self):
        self.assertFalse(self.worker.status()['active'])
        self.activate(); self.active=True
        self.assertTrue(self.worker.status()['active'])
        self.assertIn('xbt-pilot-info',self.calls)
        self.assertTrue(set(self.calls) <= {'getinfo','listpeerchannels','plugin','xbt-pilot-info'})
    def test_launch_inert_by_default_bound_when_enabled(self):
        with patch.object(g.os,'execvp') as execute:
            g.launch(self.root,['lightningd','--conf=/dev/null'])
            self.assertEqual(execute.call_args.args[1],['lightningd','--conf=/dev/null'])
        self.activate()
        with patch.object(g,'source_check'), patch.object(g.os,'execvp') as execute, patch.dict(os.environ):
            g.launch(self.root,['lightningd'])
            self.assertIn('--plugin='+g.PLUGIN,execute.call_args.args[1])
            self.assertEqual(os.environ['BTC_GATE_ROOT'],str(self.root))
        (self.root/g.BARRIER).write_text('{}')
        with patch.object(g,'source_check'), patch.object(g.os,'execvp') as execute:
            with self.assertRaises(g.Blocked): g.launch(self.root,['lightningd'])
            execute.assert_not_called()
    def test_bad_source_refused(self):
        path = self.root/'bad.py'; path.write_text('pass')
        with self.assertRaises(g.Blocked): g.source_check(path)
    def test_gate_directory_symlink_refused(self):
        (self.root/'bitcoin/swap-gate').symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(g.Blocked): self.activate()

    def test_pinned_live_protocol_persists_and_replays(self):
        source = Path(os.environ['BTC_GATE_TEST_SOURCE'])
        g.source_check(source)
        self.activate()
        g.journal_path(self.root).parent.mkdir()
        preimage = 'ab'*32
        payment_hash = hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
        terms=dict(payment_hash=payment_hash,payment_secret='cd'*32,btc_amount_msat=1000000,
                   xbt_amount_msat=2000000,xbt_invoice='lnxbt-fixture',expires_at=int(time.time())+100,
                   min_cltv_delta=288,max_cltv_delta=2016,pilot=g.PROFILE)
        init=dict(id=1,method='init',params={'configuration':{'network':'bitcoin'},'options':{'xbt-live-pilot':g.PROFILE}})
        hook=dict(id=3,method='htlc_accepted',params={'htlc':dict(short_channel_id='1x1x1',id=7,payment_hash=payment_hash,amount_msat=1000000,cltv_expiry=1000,cltv_expiry_relative=300),'onion':dict(payment_secret='cd'*32,forward_msat=1000000,total_msat=1000000,type='tlv',outgoing_cltv_value=1000)})
        def run(messages):
            output=io.StringIO()
            with patch.object(g,'SOURCE',source),patch.object(g,'source_check',lambda:None),patch.dict(os.environ,BTC_GATE_ROOT=str(self.root)),patch.object(sys,'stdin',io.StringIO('\n'.join(map(json.dumps,messages)))),contextlib.redirect_stdout(output):
                g.plugin()
            return [json.loads(line) for line in output.getvalue().splitlines() if line.strip()]
        run([init,dict(id=2,method='xbt-register',params={'quote':terms}),hook])
        journal=g.journal_path(self.root)
        self.assertEqual(json.loads(journal.read_text())[payment_hash]['phase'],'held')
        replies=run([init,hook,dict(id=4,method='xbt-release',params={'preimage':preimage})])
        self.assertTrue(any(r.get('result',{}).get('result')=='resolve' for r in replies))
        self.assertEqual(json.loads(journal.read_text())[payment_hash]['phase'],'resolved')
        replies=run([init,hook])
        self.assertTrue(any(r.get('result',{}).get('result')=='resolve' for r in replies))
        unknown=json.loads(json.dumps(hook)); unknown['params']['htlc']['payment_hash']='ef'*32
        self.assertEqual(run([init,unknown])[-1]['result'],{'result':'continue'})
        init['params']['configuration']['network']='regtest'
        with self.assertRaises(g.Blocked): run([init])

if __name__=='__main__': unittest.main()
