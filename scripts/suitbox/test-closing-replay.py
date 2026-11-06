"""BTC .10 closing-channel replay with actual held HTLC and same funding."""
import os,json,hashlib,time
from pathlib import Path
from types import SimpleNamespace
import test_deadline_engine as d
ci,hg=d.ci,d.hg
import test_engine as engine
native_start=engine.Lab.start
def full_builtin_start(self,command,log):
    # .10 registers clnrest as a builtin; duplicate explicit registration is rejected.
    command=[arg for arg in command if not (str(arg).startswith('--important-plugin=') and str(arg).endswith('/clnrest'))]
    return native_start(self,command,log)
engine.Lab.start=full_builtin_start
class Lab(d.Lab):engine_versions={ci.BTC:('v26.06.10-suitbox1',)}
os.umask(0o077)
args=SimpleNamespace(results_parent=Path('/results'),bitcoind=Path('/usr/local/bin/bitcoind'),bitcoin_cli=Path('/usr/bin/bitcoin-cli'),btc_prefix=Path('/opt/btc'),xbt_prefix=Path('/opt/xbt'))
lab=Lab(args)
try:
    backend,nodes,clients=d.customer.topology(lab,'closing-btc',ci.BTC,grant_amount_msat=50000000,grant_setup=d.grant_setup)
    incoming=clients[1];g=incoming.call('info')['grant'];preimage=os.urandom(32).hex();ph=hashlib.sha256(bytes.fromhex(preimage)).hexdigest()
    q=dict(chain=nodes[-1]['identity'],payment_hash=ph,payment_secret=os.urandom(32).hex(),amount_msat=8000000,expires_at=int(time.time())+1800,min_cltv_delta=350,max_cltv_delta=2016,approved_channels=g['channels'])
    eid=incoming.call('enroll',dict(data=q,confirmation=d.ba.digest(q)))['entry_id']
    incoming.call('publish',dict(entry_id=eid));bolt=incoming.call('invoice',dict(entry_id=eid))['invoice']
    decoded=ci.invoice(lab.rpc(nodes[0]['cli'],'decode',bolt),ci.BTC,'regtest')
    lab.rpc_named(nodes[0]['cli'],'sendpay',dict(route=d.customer.payer_route(lab,nodes,decoded),payment_hash=ph,payment_secret=q['payment_secret'],bolt11=bolt,groupid=1,partid=0))
    held=d.routes.gate.held(lab,nodes[-1],ph)
    incoming.call('evidence',dict(entry_id=eid));incoming.call('arm',dict(entry_id=eid))
    pin=held['binding']['channel']
    lab.mine(backend,held['cltv_expiry']-72-lab.rpc(nodes[-1]['cli'],'getinfo')['blockheight']);lab.synced(backend,*nodes)
    lab.wait(lambda:d.pinned_row(lab,nodes[-1],pin)['state'] in hg.CLOSING_STATES,nodes[-1]['proc'])
    lab.wait(lambda:incoming.mutations().count('close')==1,nodes[-1]['proc'])
    nodes[-1]=d.restart_node(lab,nodes[-1])
    replay=d.routes.gate.held(lab,nodes[-1],ph)
    d.require(replay['binding']==held['binding'] and replay['cltv_expiry']==held['cltv_expiry'],'closing_replay_binding_changed')
    d.require(lab.rpc_named(nodes[-1]['cli'],'listinvoices',dict(payment_hash=ph))['invoices']==[],'core_invoice_created')
    d.require(incoming.mutations().count('close')==1,'duplicate_close')
    (lab.root/'closing-replay-result.json').write_text(json.dumps(dict(regtest_only=True,final_held_HTLC_replayed=True,same_binding_and_expiry=True,core_invoice_absent=True,one_close=True))+'\n')
    print('PASS: BTC closing-channel restart retains final held HTLC and original binding',flush=True)
finally:lab.close()
