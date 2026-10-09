"""Incoming BOLT11 hint encoding against the pinned image-owned invoice codec."""
import importlib.util
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'assets/swaps'),'/usr/local/libexec/btc-controller']
import routed_invoice

class HintTests(unittest.TestCase):
    def alias_fixture(self):
        pin=dict(channel_id='1'*64,short_channel_id='110x1x0',funding_txid='2'*64,funding_outnum=0,peer_id='02'+'3'*64)
        c=dict(profile='startos-forward-routed-v1',incoming_channels=[pin])
        ch=dict(pin,state='CHANNELD_NORMAL',peer_connected=True,receivable_msat=1000000,private=True,
            features=['option_static_remotekey','option_scid_alias'],alias={'local':'16000000x1x0','remote':'16000001x2x3'},
            updates={'remote':dict(fee_base_msat=1000,fee_proportional_millionths=100,cltv_expiry_delta=34,
                                  htlc_minimum_msat=0,htlc_maximum_msat=10000000)})
        return c,ch
    def test_private_alias_uses_remote_identifier_without_changing_funding_pin(self):
        c,ch=self.alias_fixture();before=copy.deepcopy(c)
        hint=routed_invoice.hints(c,[ch])[0]
        self.assertEqual(hint['short_channel_id'],ch['alias']['remote'])
        self.assertNotEqual(hint['short_channel_id'],ch['alias']['local'])
        self.assertNotEqual(hint['short_channel_id'],ch['short_channel_id'])
        self.assertEqual(c,before)
    def test_alias_feature_never_falls_back_to_real_scid_or_local_alias(self):
        c,ch=self.alias_fixture()
        for remote in (None,'not-a-scid','16777216x0x0','0x16777216x0','0x0x65536',True):
            with self.subTest(remote=remote):
                ch['alias']={'local':'16000000x1x0'}
                if remote is not None:ch['alias']['remote']=remote
                with self.assertRaisesRegex(ValueError,'incoming_route_hints_unavailable'):
                    routed_invoice.hints(c,[ch])
    def test_private_legacy_channel_prefers_remote_alias(self):
        c,ch=self.alias_fixture();ch['features']=[]
        self.assertEqual(routed_invoice.hints(c,[ch])[0]['short_channel_id'],ch['alias']['remote'])
    def test_legacy_without_alias_and_public_channels_can_use_funding_scid(self):
        c,ch=self.alias_fixture();ch['features']=[]
        ch['private']=False
        self.assertEqual(routed_invoice.hints(c,[ch])[0]['short_channel_id'],ch['short_channel_id'])
        ch['private']=True;ch['alias']={}
        self.assertEqual(routed_invoice.hints(c,[ch])[0]['short_channel_id'],ch['short_channel_id'])
    def test_alias_requirement_is_not_bypassed_by_public_flag(self):
        c,ch=self.alias_fixture();ch['private']=False
        self.assertEqual(routed_invoice.hints(c,[ch])[0]['short_channel_id'],ch['alias']['remote'])
        ch['alias']={}
        with self.assertRaisesRegex(ValueError,'incoming_route_hints_unavailable'):
            routed_invoice.hints(c,[ch])
    def test_alias_does_not_bypass_original_funding_pin(self):
        c,ch=self.alias_fixture();ch['funding_txid']='f'*64
        with self.assertRaisesRegex(ValueError,'channel_changed'):routed_invoice.hints(c,[ch])
    def test_policy_and_funding_bound_hints(self):
        pin=dict(channel_id='1'*64,short_channel_id='5x6x7',funding_txid='2'*64,funding_outnum=0,peer_id='02'+'3'*64)
        c=dict(profile='startos-forward-routed-v1',incoming_channels=[pin])
        ch=dict(pin,state='CHANNELD_NORMAL',peer_connected=True,receivable_msat=1000000,
            updates={'remote':dict(fee_base_msat=1000,fee_proportional_millionths=100,cltv_expiry_delta=34,
                                  htlc_minimum_msat=0,htlc_maximum_msat=10000000)})
        result=routed_invoice.hints(c,[ch]);self.assertEqual(result[0]['pubkey'],pin['peer_id'])
        for updates in ({'peer_connected':False},{'receivable_msat':999999},{'updates':{}},{'funding_txid':'f'*64}):
            with self.assertRaises(ValueError):routed_invoice.hints(c,[dict(ch,**updates)])
    def test_encoded_hint_preserves_hash_amount_and_no_mpp(self):
        candidates=[Path('/usr/local/libexec/cln-swap/swap_invoice.py'),ROOT.parent/'lightning/tools/blake2b/swap_invoice.py',
                    ROOT.parent.parent/'cln/tools/blake2b/swap_invoice.py']
        source=next((p for p in candidates if p.exists()),None)
        if source is None:self.skipTest('pinned invoice encoder checked in packaged BTC image')
        spec=importlib.util.spec_from_file_location('swap_invoice',source);codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
        c,ch=self.alias_fixture();hint=routed_invoice.hints(c,[ch])[0]
        unsigned=codec.unsigned_invoice('a'*64,'b'*64,1000000,120,currency='bc',final_cltv=300)
        with patch.dict(sys.modules,swap_invoice=codec):result=routed_invoice.add(unsigned,[hint])
        hrp,data=result.rsplit('1',1);self.assertEqual(hrp,unsigned.rsplit('1',1)[0])
        words=[codec.CHARSET.index(ch) for ch in data]
        self.assertEqual(codec.polymod([ord(c)>>5 for c in hrp]+[0]+[ord(c)&31 for c in hrp]+words),1)
        def tags(encoded):
            data=[codec.CHARSET.index(ch) for ch in encoded.rsplit('1',1)[1]][7:-110];result=[]
            while data:
                size=(data[1]<<5)|data[2];result.append((codec.CHARSET[data[0]],data[3:3+size]));data=data[3+size:]
            return result
        before=tags(unsigned);after=tags(result);self.assertEqual(after[:-1],before)
        self.assertEqual(after[-1][0],'r')
        bits=''.join(f'{v:05b}' for v in after[-1][1]);raw=bytes(int(bits[i:i+8],2) for i in range(0,408,8))
        self.assertEqual(len(raw),51);self.assertEqual(raw[:33].hex(),hint['pubkey'])
        self.assertEqual(int.from_bytes(raw[33:41],'big'),(16000001<<40)|(2<<16)|3)
        self.assertEqual(int.from_bytes(raw[41:45],'big'),1000)
        self.assertEqual(int.from_bytes(raw[45:49],'big'),100)
        self.assertEqual(int.from_bytes(raw[49:51],'big'),34)

if __name__=='__main__':unittest.main()
