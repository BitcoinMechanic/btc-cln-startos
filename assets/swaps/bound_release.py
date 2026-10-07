"""Add a hash-bound release RPC around the unchanged pinned quote gate."""
import hashlib
import json
from pathlib import Path
import re
import runpy
import sys

SOURCE_HASH = '5073f0d7a6d5357b49a03eaa4d4a43a9668e87d6199bb979d5b5b9f3d651705e'
METHOD = 'xbt-release-bound'


def requests(namespace, lines):
    """The same single-threaded gate loop owns validation and durable release."""
    globals_ = namespace['main'].__globals__
    original_reply = globals_['reply']
    def reply(request, result):
        if request.get('method') == 'getmanifest':
            result = dict(result, rpcmethods=[*result['rpcmethods'], dict(
                name=METHOD, usage='payment_hash preimage',
                description='Release only the HTLC matching this hash and preimage')])
        original_reply(request, result)
    globals_['reply'] = reply
    try:
        for line in lines:
            if not line.strip():
                yield line; continue
            request = json.loads(line)
            if request.get('method') == METHOD:
                params = request.get('params')
                valid = (type(params) is dict and set(params) == {'payment_hash', 'preimage'}
                         and all(type(params[k]) is str and re.fullmatch('[0-9a-f]{64}', params[k])
                                 for k in params))
                if valid:
                    valid = hashlib.sha256(bytes.fromhex(params['preimage'])).hexdigest() == params['payment_hash']
                if not valid:
                    print(json.dumps(dict(jsonrpc='2.0', id=request.get('id'),
                        error=dict(code=-32602, message='invalid bound release'))), end='\n\n', flush=True)
                    continue
                request = dict(request, method='xbt-release', params=dict(preimage=params['preimage']))
                line = json.dumps(request)+'\n'
            yield line
    finally:
        globals_['reply'] = original_reply


def run(source, journal_script):
    source = Path(source)
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_HASH:
        raise ValueError('gate_source_changed')
    namespace = runpy.run_path(str(source))
    namespace['main'].__globals__['__file__'] = str(journal_script)
    original = sys.stdin
    stream = requests(namespace, original)
    sys.stdin = stream
    try: namespace['main']()
    finally:
        sys.stdin = original
        stream.close()
