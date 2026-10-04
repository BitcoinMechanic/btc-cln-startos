"""Real-image read-only rune, TLS verification and revocation tests."""
import json
import os
from pathlib import Path
import ssl
import sys
import tempfile
import urllib.error
import urllib.request
sys.path.insert(0, '/test-assets')
from read_only_rpc import Client, ProbeError, RESTRICTIONS
from controller_credential import Credentials
from image_pair import PairLab, PIN, check_bundle
from smoke_regtest import wait_until


class RpcLab(PairLab):
    def start(self, args, logfile, new_session=False):
        if str(args[0]).endswith('/bin/lightningd'):
            port = self.port()
            data = Path(next(x.split('=', 1)[1] for x in args if x.startswith('--lightning-dir=')))
            certs = data/'rest-certs'
            self.rest[data.name] = (port, certs)
            args = [*args, '--clnrest-host=127.0.0.1', '--clnrest-protocol=https',
                    '--clnrest-port='+str(port), '--clnrest-certs='+str(certs)]
        return super().start(args, logfile, new_session)


def rejected(url, ca, method, token=None, params=None):
    # This bypass is confined to the disposable test. Production Client has no
    # arbitrary-method entry point. Assert CLN itself rejects these requests.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=str(ca))))
    headers = {'Content-Type':'application/json'}
    if token is not None: headers['Rune'] = token
    request = urllib.request.Request(url+'/v1/'+method, data=json.dumps(params or {}).encode(), headers=headers)
    try:
        with opener.open(request, timeout=10): pass
    except urllib.error.HTTPError as error:
        body = json.loads(error.read()); error.close()
        expected_codes = (-32602,) if token == 'invalid-rune' else (1501,1502,1503)
        assert error.code in (401,403) and body.get('code') in expected_codes
        return
    raise AssertionError('Request was not rejected by rune authorization')


def main():
    assert os.environ.get('BTC_XBT_DISPOSABLE_CONTAINER') == '1'
    source = json.loads(Path('/opt/xbt/share/xbt-cln/source-lock.json').read_text())
    assert source['cln_commit'] == PIN and source['network'] == 'xbt'
    check_bundle('/usr/local/libexec/cln-swap')
    os.umask(0o077)
    root = Path(tempfile.mkdtemp(prefix='rpc-pair-', dir='/results'))
    print('Test directory: '+str(root), flush=True)
    lab = RpcLab(root, '/test-bitcoind', '/usr/bin/bitcoin-cli');lab.rest={}
    try:
        for name, network, fork in (('btc','regtest',False),('xbt','xbt-regtest',True)):
            backend = lab.node('backend-'+name, fork)
            node = lab.lightning(name, network, backend)
            port, certs = lab.rest[name]; ca=certs/'ca.pem'; url='https://127.0.0.1:'+str(port)
            wait_until(lambda: ca.exists(), node['proc'])
            token = lab.rpc([*node['cli'],'-k'], 'createrune', 'restrictions='+json.dumps(RESTRICTIONS))
            client=Client(url,token['rune'],str(ca))
            def ready():
                try: return client.inspect(node['id'],network)
                except ProbeError: return False
            report=wait_until(ready,node['proc'],timeout=90)
            assert report['identity_matches'] and report['pending_htlcs']==0
            rejected(url,ca,'getinfo')
            rejected(url,ca,'getinfo','invalid-rune')
            rejected(url,ca,'newaddr',token['rune'])
            rejected(url,ca,'listpeerchannels',token['rune'],{'id':node['id']})
            for bad_client,bad_id,bad_network in (
                (Client(url,token['rune']),node['id'],network),
                (client,'02'+'00'*32,network),
                (client,node['id'],'bitcoin' if network=='regtest' else 'xbt'),
            ):
                try: bad_client.inspect(bad_id,bad_network)
                except ProbeError: pass
                else: raise AssertionError('Untrusted certificate or changed identity accepted')
            # No RPC invocation can reach pay/withdraw through this client.
            try: client.call('pay')
            except ProbeError as error: assert str(error)=='method_not_allowed'
            else: raise AssertionError('Client allowed a write method')
            lab.rpc([*node['cli'],'-k'],'blacklistrune', 'start='+token['unique_id'], 'end='+token['unique_id'])
            rejected(url,ca,'getinfo',token['rune'])
            if name == 'btc':
                class FixturePreparation:
                    def inspect(self):
                        return dict(node_id=node['id']), dict(prepared=True)
                def credential_rpc(method, **params):
                    return lab.rpc([*node['cli'], '-k'], method,
                        *[k+'='+(v if isinstance(v,str) else json.dumps(v)) for k,v in params.items()])
                worker=Credentials(node['data'],credential_rpc,FixturePreparation(),network='regtest')
                credential=worker.create(True)
                assert worker.create(True)==credential
                action_client=Client(url,credential['rune'],str(ca))
                assert action_client.inspect(node['id'],network)['identity_matches']
                assert worker.status()['phase']=='active' and 'rune' not in worker.status()
                assert worker.revoke(True)['phase']=='revoked'
                assert worker.revoke(True)['phase']=='revoked'
                rejected(url,ca,'getinfo',credential['rune'])
                print('PASS: BTC credential helper created once, exported verified read-only access, and revoked exact rune; repeated actions safe',flush=True)
            print('PASS: '+name+' verified HTTPS and exact node identity; restricted rune accepts reads, refuses writes/parameters, and revokes',flush=True)
        print('Packaged read-only RPC OK (both images; regtest only; no live interface changes)',flush=True)
    finally: lab.close()


if __name__=='__main__': main()
