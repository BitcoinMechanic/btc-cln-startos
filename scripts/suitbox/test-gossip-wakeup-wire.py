#!/usr/bin/env python3
"""Disposable regtest: oversized gossip must not prevent the next encrypted ping.
Run inside the test harness, with pyln-proto wire/primitives in /wirelib.
"""
import argparse,json,os,shutil,socket,struct,subprocess,sys,tempfile,time,types
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--patched',action='store_true');p.add_argument('--expect-stall',action='store_true');a=p.parse_args()
package=types.ModuleType('wirelib');package.__path__=['/wirelib'];sys.modules['wirelib']=package
from wirelib.wire import connect,PrivateKey
bitcoin_cli=shutil.which('bitcoin-cli');assert bitcoin_cli
root=Path(tempfile.mkdtemp(prefix='gossip-wakeup-regtest-'));procs=[];logs=[]
def spawn(argv,name):
 log=(root/name).open('w');logs.append(log);proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT);procs.append(proc);return proc
def rpc(cli,*args):
 raw=subprocess.check_output([*cli,*args],stderr=subprocess.DEVNULL,timeout=10).decode().strip()
 try:return json.loads(raw)
 except json.JSONDecodeError:return raw
def wait(fn):
 end=time.monotonic()+40
 while time.monotonic()<end:
  try:
   v=fn()
   if v:return v
  except (OSError,subprocess.SubprocessError,ValueError):pass
  if any(p.poll() is not None for p in procs):raise RuntimeError('fixture_process_exited')
  time.sleep(.1)
 raise RuntimeError('fixture_startup_timeout')
try:
 if a.patched:shutil.copyfile('/patched/lightning_connectd','/usr/local/libexec/c-lightning/lightning_connectd')
 btc=root/'btc';btc.mkdir();ln=root/'ln';ln.mkdir()
 spawn(['/usr/local/bin/bitcoind',f'-datadir={btc}','-regtest','-server=1','-listen=0','-dnsseed=0','-connect=0','-rpcport=19443'],'bitcoin.log')
 bitcoin=[bitcoin_cli,f'-datadir={btc}','-regtest','-rpcport=19443'];wait(lambda:rpc(bitcoin,'getblockchaininfo'))
 rpc(bitcoin,'createwallet','fixture');rpc(bitcoin,'generatetoaddress','101',rpc(bitcoin,'getnewaddress'))
 command=['/usr/local/bin/lightningd',f'--lightning-dir={ln}','--network=regtest','--conf=/dev/null',f'--bitcoin-datadir={btc}','--bitcoin-rpcport=19443',f'--bitcoin-cli={bitcoin_cli}','--developer','--dev-bitcoind-poll=1','--disable-dns','--autoconnect-seeker-peers=0','--autolisten=false','--bind-addr=127.0.0.1:19735','--log-level=debug']
 for plugin in Path('/usr/local/libexec/c-lightning/plugins').iterdir():
  if plugin.name not in ('bcli','offers','topology','txprepare','spenderp'):command.append('--disable-plugin='+plugin.name)
 spawn(command,'lightning.log');cli=['/usr/local/bin/lightning-cli',f'--lightning-dir={ln}','--network=regtest']
 info=wait(lambda:rpc(cli,'getinfo'))
 def connection():return connect(PrivateKey(bytes.fromhex('11'*32)),bytes.fromhex(info['id']),'127.0.0.1',19735)
 peer=wait(connection);peer.connection.settimeout(3)
 init=peer.read_message();assert init[:2]==b'\x00\x10'
 peer.send_message(bytes.fromhex('001000000000'))
 time.sleep(.2)
 # A control ping proves handshake and framing are usable before discarded gossip.
 def pong():
  while True:
   msg=peer.read_message()
   if msg[:2]==b'\x00\x13':return msg
 peer.send_message(struct.pack('!HHH',18,1,0));assert pong()==bytes.fromhex('0013000100')
 for size in (2219,3739):
  peer.send_message(struct.pack('!H',257)+bytes(size-2))
  time.sleep(.1) # ensure the gossip handler has returned into its read wait
  peer.send_message(struct.pack('!HHH',18,1,0))
  try:reply=pong()
  except socket.timeout:
   assert a.expect_stall, 'discarded gossip stalled subsequent encrypted ping'
   assert 'Ignoring oversized gossip' in (root/'lightning.log').read_text()
   print('EXPECTED BASELINE FAILURE: encrypted pong unread after oversized gossip',flush=True);break
  assert reply==bytes.fromhex('0013000100')
 else:
  assert not a.expect_stall, 'baseline unexpectedly passed'
  print('PASS: real BOLT8 peer receives pongs after both oversized gossip messages',flush=True)
finally:
 for proc in reversed(procs):
  if proc.poll() is None:
   proc.terminate()
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:proc.kill();proc.wait()
 for log in logs:log.close()
 if sys.exc_info()[0]:
  for f in root.glob('*.log'):print(f.name, f.read_text()[-5000:],flush=True)
 print('Fixture logs:',root,flush=True)
