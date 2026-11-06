"""Real official-to-candidate BTC update on a disposable funded regtest channel."""
import json,os,subprocess,hashlib
from pathlib import Path
from types import SimpleNamespace
import test_engine as engine
import test_gate_engine as gate
import chain_identity as ci
import held_gate as hg
import node_bootstrap as boot

class UpgradeLab(engine.Lab):
    engine_versions={ci.BTC:('v26.06.10','v26.06.10-suitbox1')}
    updated=False
    def start(self,command,log):
        if str(command[0])=='/opt/btc/bin/lightningd':
            root=next(str(x).split('=',1)[1] for x in command if str(x).startswith('--lightning-dir='))
            args=[str(x) for x in command[1:] if not str(x).startswith(('--network=','--lightning-dir='))]
            command=['/usr/local/libexec/swap-node/package_node.py','--disposable-regtest','--profile',ci.BTC,'--root',root,'launch',*args]
        return super().start(command,log)
    def lightning(self,name,profile,backend,**kwargs):
        self.args.btc_prefix=Path('/opt/btc' if self.updated and name=='target' else '/opt/btc-before')
        node=super().lightning(name,profile,backend,**kwargs)
        node.update(name=name,profile=profile,backend=backend)
        return node

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(lab):
    backend=lab.backend('backend',False)
    payer=lab.lightning('peer',ci.BTC,backend);target=lab.lightning('target',ci.BTC,backend)
    lab.rpc(backend['cli'],'sendtoaddress',engine.funding_address(lab,payer),'0.01');lab.mine(backend);lab.synced(backend,payer,target)
    lab.rpc(payer['cli'],'connect',target['identity']['node_id'],'127.0.0.1',target['port'])
    lab.rpc_named(payer['cli'],'fundchannel',dict(id=target['identity']['node_id'],amount=300000,push_msat=50000000),timeout=90)
    lab.mine(backend);lab.synced(backend,payer,target);gate.connect(lab,payer,target)
    gate.ordinary_payment(lab,payer,target,'before-update')
    old_id=target['identity'];old_pin=hg.channel_pin(gate.channel(lab,target),ci.BTC)
    sentinel={'.commando-env':'DISPOSABLE-UI-CREDENTIAL-SENTINEL\n','store.json':'{"restore":false,"rescan":-123,"sentinel":"preserved"}', 'data/app/config.json':'{"password":"disposable-sentinel"}', '.watchtower/watchtowers_db.sql3':'disposable-watchtower-sentinel'}
    for rel,data in sentinel.items():
        p=target['root']/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
    secret_hash=digest(target['root']/'regtest/hsm_secret')
    lab.stop(target['proc']);engine.require(target['proc'].returncode in (0,-15),'ungraceful_original_shutdown')
    lab.updated=True;target=lab.lightning('target',ci.BTC,backend);gate.connect(lab,payer,target)
    def retained():
        engine.require(target['identity']==old_id,'identity_changed')
        engine.require(hg.channel_pin(gate.channel(lab,target),ci.BTC)==old_pin,'channel_funding_changed')
        engine.require(digest(target['root']/'regtest/hsm_secret')==secret_hash,'wallet_secret_changed')
        engine.require(lab.rpc(target['cli'],'listclosedchannels')['closedchannels']==[],'channel_closed')
        for rel,data in sentinel.items():engine.require((target['root']/rel).read_text()==data,'settings_changed')
    retained()
    engine.require(not (target['root']/'regtest'/boot.DIRECTORY).exists(),'authority_implicitly_created')
    gate.ordinary_payment(lab,payer,target,'after-update-incoming')
    gate.ordinary_payment(lab,target,payer,'after-update-outgoing')
    command=['/usr/local/libexec/swap-node/package_node.py','--disposable-regtest','--profile',ci.BTC,'--root',str(target['root']),'prepare']
    def prepare():
        p=subprocess.run(command,input='{"confirmed":true}',capture_output=True,text=True,check=True)
        return json.loads(p.stdout)
    engine.require(prepare()['initialized'] is True,'explicit_bootstrap_failed')
    namespace=target['root']/'regtest'/boot.DIRECTORY
    saved={str(p.relative_to(namespace)):p.read_bytes() for p in namespace.rglob('*') if p.is_file()}
    engine.require(prepare()['existing_records'] is True,'repeat_bootstrap_changed')
    lab.stop(target['proc']);target=lab.lightning('target',ci.BTC,backend);gate.connect(lab,payer,target);retained()
    methods={r['command'].split()[0] for r in lab.rpc(target['cli'],'help')['help']}
    engine.require({'swap-gate-status','swap-customer-call','swap-customer-credential'}<=methods,'coordinator_plugins_missing')
    for rel,raw in saved.items():engine.require((namespace/rel).read_bytes()==raw,'coordinator_state_rewritten')
    gate.ordinary_payment(lab,payer,target,'after-coordinator-restart')
    retained()
    result=dict(regtest_only=True,official_version='v26.06.10',candidate_version='v26.06.10-suitbox1',ordinary_payments=4,identity_preserved=True,original_channel_funding_preserved=True,wallet_secret_preserved=True,ui_settings_and_watchtower_sentinels_preserved=True,no_implicit_authority=True,explicit_setup_and_restart=True,coordinator_journals_preserved=True,closed_channels=0,live_StartOS_acceptance=False)
    (lab.root/'upgrade-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)

os.umask(0o077)
args=SimpleNamespace(results_parent=Path('/results'),bitcoind=Path('/usr/local/bin/bitcoind'),bitcoin_cli=Path('/usr/bin/bitcoin-cli'),btc_prefix=Path('/opt/btc-before'),xbt_prefix=Path('/opt/xbt'))
lab=UpgradeLab(args)
try:run(lab)
finally:lab.close()
