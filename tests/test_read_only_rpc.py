import io
import json
from pathlib import Path
import ssl
import sys
import unittest
from unittest.mock import Mock, patch
import urllib.error
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'assets/swaps'))
from read_only_rpc import Client, ProbeError, NoRedirect, endpoint

NODE = '02'+'12'*32

class ProbeTests(unittest.TestCase):
    def client(self):
        c = Client('https://localhost:3010', 'test-rune')
        c.opener = Mock()
        return c

    def response(self, c, body):
        c.opener.open.return_value = io.BytesIO(body)

    def test_endpoint_rejects_insecure_or_credential_urls(self):
        for url in ('http://localhost', 'https://u:p@localhost', 'https://localhost/path',
                    'https://localhost?q=1', 'https://localhost#x', 'https://localhost:0',
                    'https://localhost:65536', 'https://localhost\n', 'https://'):
            with self.subTest(url=url), self.assertRaises(ProbeError): endpoint(url)
        self.assertEqual(endpoint('https://localhost:3010/'), 'https://localhost:3010')

    def test_tls_verification_and_no_proxy(self):
        with patch('read_only_rpc.urllib.request.build_opener') as build:
            Client('https://localhost', 'test-rune')
        handlers = build.call_args.args
        self.assertEqual(handlers[0].proxies, {})
        self.assertEqual(handlers[1]._context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(handlers[1]._context.check_hostname)
        self.assertIsInstance(handlers[2], NoRedirect)

    def test_write_methods_refused_before_transport(self):
        c = self.client()
        for method in ('pay', 'withdraw', 'createrune', 'stop', 'getinfo/../pay'):
            with self.assertRaisesRegex(ProbeError, '^method_not_allowed$'): c.call(method)
        c.opener.open.assert_not_called()

    def test_parameterless_post(self):
        c = self.client(); self.response(c, b'{}')
        c.call('getinfo')
        request = c.opener.open.call_args.args[0]
        self.assertEqual(request.data, b'{}')
        self.assertEqual(request.full_url, 'https://localhost:3010/v1/getinfo')
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(request.get_header('Rune'), 'test-rune')

    def test_identity_mismatch_prevents_channel_read(self):
        for info in ({'id':NODE, 'network':'bitcoin'}, {'id':'03'+'34'*32, 'network':'xbt'}):
            c=self.client(); c.call=Mock(return_value=info)
            with self.assertRaisesRegex(ProbeError, '^operator_identity_mismatch$'): c.inspect(NODE, 'xbt')
            c.call.assert_called_once_with('getinfo')

    def test_filtered_report(self):
        c=self.client(); c.call=Mock(side_effect=[{'id':NODE,'network':'xbt','private':'secret'},
            {'channels':[{'state':'CHANNELD_NORMAL','htlcs':[{'secret':'hidden'}]}]}])
        report=c.inspect(NODE,'xbt')
        self.assertEqual(report['pending_htlcs'],1)
        self.assertFalse(report['payment_started'])
        self.assertNotIn(NODE,json.dumps(report))
        self.assertNotIn('secret',json.dumps(report))

    def test_redirect_refused(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,'',{},'https://other'))
        c=self.client()
        c.opener.open.side_effect=urllib.error.HTTPError('https://private',302,'secret',{},io.BytesIO(b'secret'))
        with self.assertRaisesRegex(ProbeError,'^http_request_rejected$'): c.call('getinfo')
        self.assertEqual(c.opener.open.call_count,1)

    def test_transport_errors_private_and_no_retry(self):
        c=self.client(); c.opener.open.side_effect=RuntimeError('credential secret')
        with self.assertRaisesRegex(ProbeError,'^tls_or_transport_failed$'): c.call('getinfo')
        self.assertEqual(c.opener.open.call_count,1)

    def test_response_limits_and_shape(self):
        for body in (b'x'*(1024*1024+1), b'[]', b'{"error":"secret"}', b'not json'):
            c=self.client(); self.response(c,body)
            with self.assertRaises(ProbeError): c.call('getinfo')

    def test_bad_credentials_rejected(self):
        for rune in ('', 'rune\nsecret', 'x'*8193):
            with self.assertRaisesRegex(ProbeError,'^invalid_rune_format$'): Client('https://localhost',rune)

if __name__=='__main__': unittest.main()
