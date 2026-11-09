#!/usr/bin/env python3
import json, urllib.request, time, datetime

RPCS=["https://bsc-dataseed.binance.org","https://rpc-bsc.48.club","https://bsc.publicnode.com"]
TREASURY="0x7c34e9e21ee28a49ff0b84b61774119e6633359f"
def rpc(method,params):
    last=None
    for _ in range(3):
        for url in RPCS:
            try:
                req=urllib.request.Request(url,data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
                r=json.loads(urllib.request.urlopen(req,timeout=25).read())
                if 'error' in r: last=Exception(str(r['error'])); continue
                return r['result']
            except Exception as e: last=e
        time.sleep(1)
    raise last

logs=json.load(open('/home/agentuser/.flapjax/audit/q92_transfers.json'))
rows=[]
for lg in logs:
    to='0x'+lg['topics'][2][-40:]
    amt=int(lg['data'],16)/1e18
    blk=int(lg['blockNumber'],16)
    ts=int(rpc("eth_getBlockByNumber",[lg['blockNumber'],False])["timestamp"],16)
    cot=datetime.datetime.fromtimestamp(ts,datetime.timezone(datetime.timedelta(hours=-5)))
    rows.append({"tx":lg['transactionHash'],"block":blk,"time_cot":cot.strftime('%Y-%m-%d %H:%M:%S COT'),"recipient":to,"amount":amt})
print(f"total transfers: {len(rows)}, total sent: {sum(r['amount'] for r in rows):,.0f} FLAPJAX, distinct recipients: {len(set(r['recipient'] for r in rows))}")
json.dump(rows,open('/home/agentuser/.flapjax/audit/q92_rows.json','w'),indent=1)

# first BNB funder: earliest incoming BNB tx to each recipient
# use eth_getLogs on native transfers? Native BNB transfers have no logs. Use block scan backwards is expensive.
# Strategy: scan blocks from genesis-ish recent range backwards per recipient via topic-less? Too heavy.
# Instead: use BscScan-style heuristic via binary search on each recipient nonce... Simplest robust: scan blocks backwards from recipient's first FLAPJAX receipt block, looking for txs with to=recipient via eth_getBlockByNumber full txs. Backward until found, cap 300k blocks.
def first_bnb_funder(addr, start_blk, max_back=400000):
    b=start_blk
    while b>0 and start_blk-b<max_back:
        blk=rpc("eth_getBlockByNumber",[hex(b),True])
        for tx in blk.get('transactions') or []:
            if (tx.get('to') or '').lower()==addr.lower() and int(tx.get('value','0x0'),16)>0:
                return {"funder":tx['from'],"tx":tx['hash'],"block":b}
        b-=1
        if b%500==0: time.sleep(0.05)
    return None

results={}
for r in rows:
    to=r['recipient']
    if to not in results:
        print('scanning first funder for',to[:10],'from block',r['block'],flush=True)
        results[to]=first_bnb_funder(to,r['block'])
        print('  ->',results[to],flush=True)
json.dump(results,open('/home/agentuser/.flapjax/audit/q92_funders.json','w'),indent=1)
for to,f in results.items():
    print(to[:14], '->', (f or {}).get('funder','NOT FOUND in window'))
