"""Validate forward market terms before the pinned gate admits them."""
from pilot_contract import validate, incoming_pins
import market_terms as mt

def validate_terms(t):
    mt.require(type(t) is dict and set(t)=={'payment_hash','payment_secret','btc_amount_msat','xbt_amount_msat',
        'xbt_invoice','expires_at','min_cltv_delta','max_cltv_delta','pilot','contract'})
    c=validate(t['contract']);mt.require(c['profile']==mt.FORWARD and t['pilot']==mt.GATE)
    mt.require(t['payment_hash']==c['payment_hash'] and t['xbt_invoice']==c['invoice'])
    for k in ('btc','xbt'):mt.require(type(t[k+'_amount_msat']) is int and t[k+'_amount_msat']==mt.amounts(c)[k])
    mt.require(t['expires_at']==c['pricing']['expires_at'] and t['min_cltv_delta']==288 and t['max_cltv_delta']==2016)
    return t
