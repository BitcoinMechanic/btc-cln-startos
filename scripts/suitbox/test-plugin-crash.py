"""BTC-only 26.06.10 adapter; original crash assertions remain unchanged."""
import os,sys,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import test_plugin_crash as crash
import test_gate_engine as gate

baseline=sys.argv[1]=='baseline'
prefix=Path('/opt/btc-before' if baseline else '/opt/btc')
class Lab(gate.GateLab):
    engine_versions={crash.ci.BTC:('v26.06.10' if baseline else 'v26.06.10-suitbox1',)}
args=SimpleNamespace(results_parent=Path('/results'),btc_prefix=prefix,xbt_prefix=prefix,bitcoind=Path('/usr/local/bin/bitcoind'),bitcoin_cli=Path('/usr/bin/bitcoin-cli'))
os.umask(0o077)
lab=Lab(args)
try:
    backend,payer,receiver=crash.setup(lab,'btc',crash.ci.BTC)
    scenarios=[]
    # Upstream .10 already preserves important hook calls; require the same matrix on both binaries.
    if True:
        gate.ordinary_payment(lab,payer,receiver,'ordinary-before-crashes')
        with patch.object(gate,'restart_pair',crash.crash_restart),patch.object(gate,'make_quote',crash.core_quote):
            for interrupt_terminal in (False,True):
                for releasing in (True,False):
                    payer,receiver,receipt=gate.scenario(lab,payer,receiver,releasing=releasing,interrupt_terminal=interrupt_terminal)
                    scenarios.append(receipt)
        gate.ordinary_payment(lab,payer,receiver,'ordinary-after-crashes')
    control=crash.control(lab,payer,receiver,important=False)
    result=dict(regtest_only=True,mode='baseline' if baseline else 'patched',profile=crash.ci.BTC,scenarios=scenarios,control=control)
    (lab.root/'btc26-crash-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: BTC26 '+result['mode']+' plugin crash controls; scenarios='+str(len(scenarios)),flush=True)
finally:lab.close()
