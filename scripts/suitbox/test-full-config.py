"""Real generated config + full built-in plugins, disposable network only."""
import json,os
from pathlib import Path
from types import SimpleNamespace
import test_engine as engine
import chain_identity as ci
class Lab(engine.Lab):
    engine_versions={ci.BTC:('v26.06.10-suitbox1',)}
    def start(self,command,log):
        if Path(command[0]).name=='lightningd':
            config=Path('/opt/generated-config.ini').read_text().replace('network=bitcoin','network=regtest')
            config=''.join(line+'\n' for line in config.splitlines() if not line.startswith(('bitcoin-datadir=','bind-addr=')))
            conf=log.parent/'config';conf.write_text(config)
            command=[arg for arg in command if not str(arg).startswith(('--disable-plugin=','--conf=','--network=','--lightning-dir='))]
            command=['/usr/local/libexec/swap-node/package_node.py','--disposable-regtest','--profile',ci.BTC,'--root',str(log.parent),'launch','--conf='+str(conf),*command[1:]]
        return super().start(command,log)
os.umask(0o077)
args=SimpleNamespace(results_parent=Path('/results'),bitcoind=Path('/usr/local/bin/bitcoind'),bitcoin_cli=Path('/usr/bin/bitcoin-cli'),btc_prefix=Path('/opt/btc'),xbt_prefix=Path('/opt/xbt'))
lab=Lab(args)
try:
    backend=lab.backend('backend',False)
    node=lab.lightning('full-config',ci.BTC,backend)
    original=node['identity']
    for iteration in range(2):
        plugins=lab.rpc(node['cli'],'plugin','list')['plugins']
        for name in ('cln-grpc','clnrest'):
            engine.require(any(Path(p['name']).name==name and p.get('active') is True for p in plugins),'native_plugin_not_active_'+name)
        engine.require(node['identity']==original,'identity_changed')
        lab.stop(node['proc'])
        if iteration==0:node=lab.lightning('full-config',ci.BTC,backend)
    (lab.root/'full-config-result.json').write_text(json.dumps(dict(regtest_only=True,generated_config=True,all_builtin_plugins=True,grpc_active=True,clnrest_active=True,restart_identity_preserved=True))+'\n')
    print('PASS: generated config; full builtins; gRPC/REST active; same identity after restart',flush=True)
finally:lab.close()
