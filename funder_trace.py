#!/usr/bin/env python3
"""Q92 funder resolution: archive binary search of first BNB balance>0 block, then find funder in that block (external tx or internal trace via Tatum 5/min)."""
import json, urllib.request, time, os

TREASURY="0x7c34e9e21ee28a49ff0b84b61774119e6633359f"
OUT='/home/agentuser/.flapjax/audit/q92_funders_resolved.json'
EPS=[
 "https://bsc-mainnet.gateway.tatum.io",
 "https://api.zan.top/bsc-mainnet/public",
 "https://rpc-bsc.48.club",
]
def rpc(method,params,tries=6):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last=None
    for i in range(tries):
        ep=EPS[i%len(EPS)]
        try:
            r=json.loads(urllib.request.urlopen(urllib.request.Request(ep,body,{"Content-Type":"application/json","User-Agent":"Mozilla/5.0"}),timeout=30).read())
            if "error" in r: raise Exception(r["error"])
            return r["result"]
        except Exception as e:
            last=e; time.sleep(13)
    raise Exception(f"rpc fail {method}: {last}")

def tatum(method,params,tries=8):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last=None
    for i in range(tries):
        try:
            r=json.loads(urllib.request.urlopen(urllib.request.Request("https://bsc-mainnet.gateway.tatum.io",body,{"Content-Type":"application/json"}),timeout=40).read())
            if "error" in r: raise Exception(r["error"])
            return r["result"]
        except Exception as e:
            last=e; time.sleep(13)  # respect 5/min
    raise Exception(f"tatum fail {method}: {last}")

rows=json.load(open('/home/agentuser/.flapjax/audit/q92_rows.json'))
first={}
for r in rows:
    to=r['recipient'].lower()
    if to not in first or r['block']<first[to]:
        first[to]=r['block']

latest=int(rpc("eth_blockNumber",[]),16)
LO=130000000
results={}
for to,blk in sorted(first.items(), key=lambda x:-x[1]):
    # binary search: first block where balance>0 (checked atblk -> within)
    def bal(b):
        return int(rpc("eth_getBalance",[to,hex(b)]),16)
    # quick check: balance at LO (should be 0) and latest
    lo,hi=LO,latest
    if bal(latest)==0:
        results[to]={"status":"no_bnb_ever","funder":None}
        print(to[:14],"never held BNB",flush=True)
        json.dump(results,open(OUT,'w'),indent=1)
        continue
    # find first b with bal>0
    while lo<hi:
        mid=(lo+hi)//2
        if bal(mid)==0: lo=mid+1
        else: hi=mid
    fb=lo
    # find funder in block fb: external txs
    blkdata=rpc("eth_getBlockByNumber",[hex(fb),True])
    found=None
    for tx in blkdata.get('transactions') or []:
        if (tx.get('to') or '').lower()==to and int(tx.get('value','0x0'),16)>0:
            found={"funder":tx['from'].lower(),"tx":tx['hash'],"block":fb,"type":"external"}
            break
    if not found:
        # internal transfer via Tatum trace_block (rate-limited)
        try:
            traces=tatum("trace_block",[hex(fb)])
            for t in traces or []:
                act=t.get('action',{})
                if act.get('to','').lower()==to and int(act.get('value','0x0') or 0,16)>0:
                    found={"funder":act.get('from','').lower(),"tx":t.get('transactionHash'),"block":fb,"type":"internal"}
                    break
        except Exception as e:
            found={"funder":None,"block":fb,"note":f"internal funding suspected, trace unavailable: {str(e)[:50]}"}
    results[to]=found or {"status":"unresolved","first_bnb_block":fb}
    print(to[:14],'->',json.dumps(results[to])[:150],flush=True)
    json.dump(results,open(OUT,'w'),indent=1)
print('ALL DONE')
