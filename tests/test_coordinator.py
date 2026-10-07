import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
spec = importlib.util.spec_from_file_location('btc_coordinator', Path(__file__).resolve().parents[1]/'assets/swaps/coordinator.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.bundle = self.root/'bundle'; self.bundle.mkdir()
        (self.bundle/'SOURCE_COMMIT').write_text(m.PIN)
        for n in ('quote_plugin.py','reverse_activation.py','receive_activation.py'): (self.bundle/n).touch()
        self.info = dict(id='02'+'a'*64, network='bitcoin', version='v26.06.9')
        self.channels = []; self.calls = []
        self.worker = m.Preparation(self.root, rpc=self.rpc, bundle=self.bundle)

    def rpc(self, method):
        self.calls.append(method)
        if method == 'getinfo': return self.info
        if method == 'listpeerchannels': return dict(channels=self.channels)
        self.fail('Unexpected RPC '+method)

    def test_status_has_no_write_or_private_identity(self):
        _, result = self.worker.inspect()
        self.assertFalse(result['prepared'])
        self.assertNotIn(self.info['id'], json.dumps(result))
        self.assertFalse((self.root/m.RECORD).exists())

    def test_confirmation_precedes_rpc(self):
        with self.assertRaises(m.Blocked): self.worker.prepare(False)
        self.assertEqual(self.calls, [])

    def test_repeat_preserves_exact_binding_and_bytes(self):
        result = self.worker.prepare(True)
        p=self.root/m.RECORD; before=(p.read_bytes(),p.stat().st_mtime_ns)
        self.assertTrue(result['prepared'])
        self.assertFalse(result['live_activation_enabled_by_package'])
        self.worker.prepare(True)
        self.assertEqual(before,(p.read_bytes(),p.stat().st_mtime_ns))
        self.assertEqual(p.stat().st_mode & 0o777,0o600)

    def test_changed_identity_preserved(self):
        self.worker.prepare(True); p=self.root/m.RECORD; before=p.read_bytes()
        self.info['id']='03'+'b'*64
        with self.assertRaises(m.Blocked): self.worker.prepare(True)
        self.assertEqual(p.read_bytes(),before)

    def test_wrong_network_or_version(self):
        for key,value in (('network','xbt'),('version','unexpected')):
            with self.subTest(key=key):
                old=self.info[key]; self.info[key]=value
                with self.assertRaises(m.Blocked): self.worker.prepare(True)
                self.info[key]=old
                self.assertFalse((self.root/m.RECORD).exists())

    def test_warning_and_pending_htlc(self):
        self.info['warning_lightningd_sync']='sync'
        with self.assertRaises(m.Blocked): self.worker.prepare(True)
        del self.info['warning_lightningd_sync']
        self.channels=[dict(htlcs=[{}])]
        with self.assertRaises(m.Blocked): self.worker.prepare(True)

    def test_restore_and_rescan_pending_before_rpc(self):
        for settings in (dict(restore=True),dict(rescan=-800000)):
            (self.root/'store.json').write_text(json.dumps(settings))
            with self.assertRaises(m.Blocked): self.worker.prepare(True)
        self.assertEqual(self.calls,[])

    def test_cleared_restore_flags_allow_preparation(self):
        (self.root/'store.json').write_text(json.dumps(dict(restore=False)))
        self.assertTrue(self.worker.prepare(True)['prepared'])

    def test_symlink_record_or_store_refused(self):
        for name in (m.RECORD,'store.json'):
            p=self.root/name;p.symlink_to(self.bundle/'SOURCE_COMMIT')
            with self.assertRaises(m.Blocked): self.worker.prepare(True)
            p.unlink()

    def test_source_pin_and_missing_module(self):
        p=self.bundle/'SOURCE_COMMIT';p.write_text('wrong')
        with self.assertRaises(m.Blocked): self.worker.prepare(True)
        p.write_text(m.PIN);(self.bundle/'quote_plugin.py').unlink()
        with self.assertRaises(m.Blocked): self.worker.prepare(True)
        self.assertEqual(self.calls,[])

    def test_malformed_store_preserved(self):
        p=self.root/'store.json';p.write_text('invalid')
        with self.assertRaises(ValueError): self.worker.prepare(True)
        self.assertEqual(p.read_text(),'invalid')
        self.assertFalse((self.root/m.RECORD).exists())


if __name__ == '__main__': unittest.main()
