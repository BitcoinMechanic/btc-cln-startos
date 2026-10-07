"""Real patched gate protocol: explicit opt-in, retained journals and one active quote."""
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
import bound_release

class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.script=Path(self.temp.name)/'quote_plugin.py'
        self.source=Path(os.environ.get('BTC_GATE_TEST_SOURCE','/usr/local/libexec/cln-swap/quote_plugin.py'))
    def run_gate(self,profile,requests):
        init=dict(id=1,method='init',params={'configuration':{'network':'bitcoin'},'options':{'xbt-live-pilot':profile}})
        output=io.StringIO()
        with patch.object(sys,'stdin',io.StringIO('\n'.join(json.dumps(x) for x in [init,*requests]))),contextlib.redirect_stdout(output):
            bound_release.run(self.source,self.script)
        return [json.loads(x) for x in output.getvalue().splitlines() if x.strip()]
    def terms(self,n,profile):
        preimage='%064x'%n;h=hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
        return dict(payment_hash=h,payment_secret='c'*64,btc_amount_msat=1000000,xbt_amount_msat=2000000,
                    xbt_invoice='lnxbt-fixture',expires_at=int(time.time())+100,min_cltv_delta=288,max_cltv_delta=2016,pilot=profile),preimage
    def register(self,q):return dict(id=2,method='xbt-register',params={'quote':q})
    def settle(self,q,preimage):
        h=dict(id=3,method='htlc_accepted',params={'htlc':dict(short_channel_id='1x1x0',id=3,payment_hash=q['payment_hash'],amount_msat=1000000,cltv_expiry=1000,cltv_expiry_relative=300),'onion':dict(payment_secret=q['payment_secret'],forward_msat=1000000,total_msat=1000000,type='tlv',outgoing_cltv_value=1000)})
        return [h,dict(id=4,method='xbt-release-bound',params={'payment_hash':q['payment_hash'],'preimage':preimage})]
    def test_existing_v1_requires_explicit_profile_change_and_keeps_original(self):
        q,preimage=self.terms(1,'live-pilot-v1');self.run_gate('live-pilot-v1',[self.register(q),*self.settle(q,preimage)])
        path=self.script.with_suffix('.quotes.json');old=json.loads(path.read_text())[q['payment_hash']]
        q2,p2=self.terms(2,'startos-fixed-repeat-v1')
        denied=self.run_gate('live-pilot-v1',[self.register(q2)])
        self.assertIn('error',denied[-1])
        result=self.run_gate('startos-fixed-repeat-v1',[self.register(q2),*self.settle(q2,p2)])
        self.assertTrue(any(x.get('result',{}).get('released')==1 for x in result))
        self.assertEqual(json.loads(path.read_text())[q['payment_hash']],old)
        self.assertEqual(len(json.loads(path.read_text())),2)
    def test_second_quote_blocked_until_first_terminal_and_amount_cannot_increase(self):
        profile='startos-fixed-repeat-v1';q,p=self.terms(1,profile);q2,p2=self.terms(2,profile)
        self.run_gate(profile,[self.register(q)])
        self.assertIn('error',self.run_gate(profile,[self.register(q2)])[-1])
        self.run_gate(profile,self.settle(q,p))
        q2['xbt_amount_msat']=4000000
        self.assertIn('error',self.run_gate(profile,[self.register(q2)])[-1])
    def test_retirement_is_durable_idempotent_and_never_reopens_old_invoice(self):
        profile='startos-fixed-repeat-v1';q,preimage=self.terms(1,profile)
        self.run_gate(profile,[self.register(q)])
        retire=dict(id=5,method='xbt-retire-repeat',params={'payment_hash':q['payment_hash']})
        self.assertIn('error',self.run_gate(profile,[retire])[-1])
        with patch.object(time,'time',lambda:q['expires_at']+1):
            self.assertEqual(self.run_gate(profile,[retire])[-1]['result'],{'retired':True})
            path=self.script.with_suffix('.quotes.json');before=path.read_bytes()
            self.run_gate(profile,[retire]);self.assertEqual(before,path.read_bytes())
        # Even a wall-clock rollback must not admit a retired invoice.
        result=self.run_gate(profile,[self.settle(q,preimage)[0]])
        self.assertEqual(result[-1]['result']['result'],'fail')
        self.assertEqual(json.loads(path.read_text())[q['payment_hash']]['phase'],'expired')
    def test_held_quote_cannot_be_retired(self):
        profile='startos-fixed-repeat-v1';q,p=self.terms(1,profile)
        self.run_gate(profile,[self.register(q),self.settle(q,p)[0]])
        with patch.object(time,'time',lambda:q['expires_at']+1):
            result=self.run_gate(profile,[dict(id=5,method='xbt-retire-repeat',params={'payment_hash':q['payment_hash']})])
        self.assertIn('error',result[-1]);self.assertEqual(json.loads(self.script.with_suffix('.quotes.json').read_text())[q['payment_hash']]['phase'],'held')
    def test_old_profile_still_allows_only_one_quote(self):
        q,p=self.terms(1,'live-pilot-v1');q2,_=self.terms(2,'live-pilot-v1')
        self.run_gate('live-pilot-v1',[self.register(q),*self.settle(q,p)])
        self.assertIn('error',self.run_gate('live-pilot-v1',[self.register(q2)])[-1])

if __name__=='__main__':unittest.main()
