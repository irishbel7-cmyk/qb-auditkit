#!/usr/bin/env python3
"""Q92: FLAPJAX outflows from treasury during Nov 4 COT (UTC-5)."""
import json, urllib.request, time, datetime

RPCS = ["https://bsc-dataseed.binance.org", "https://rpc-bsc.48.club", "https://bsc.publicnode.com"]
TOKEN = "0x90c8889f428F9Ebb77BB8f15CAD3a50a9aC680df"
TREASURY = "0x7c34e9e21ee28a49ff0b84b61774119e6633359f"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOPIC_TREAS = "0x0000000000000000000000007c34e9e21ee28a49ff0b84b61774119e6633359f"

def rpc(method, params):
    global RPCS
    last=None
    for _ in range(3):
        for url in RPCS:
            try:
                body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
                req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
                r=json.loads(urllib.request.urlopen(req,timeout=25).read())
                if 'error' in r: last=Exception(str(r['error'])); continue
                return r['result']
            except Exception as e:
                last=e
        time.sleep(2)
    raise last

latest=int(rpc("eth_blockNumber",[]),16)
# binary search blocks for UTC window 2026-11-04 05:00 -> 2026-11-05 05:00
def ts_of(b):
    return int(rpc("eth_getBlockByNumber",[hex(b),False])["timestamp"],16)
def find_block(target):
    lo,hi=1,latest
    while lo<hi:
        mid=(lo+hi)//2
        if ts_of(mid)<target: lo=mid+1
        else: hi=mid
    return lo

t0=int(datetime.datetime(2026,11,4,5,0,tzinfo=datetime.timezone.utc).timestamp())
t1=int(datetime.datetime(2026,11,5,5,0,tzinfo=datetime.timezone.utc).timestamp())
b0=find_block(t0); b1=find_block(t1)
print(f"window UTC {t0}-{t1} blocks {b0}-{b1} (latest {latest})", flush=True)

outf=open(os.path.expanduser("~/.flapjax/audit/q92_transfers.json"),"w") if False else open("/home/agentuser/.flapjax/audit/q92_transfers.json","w")
all_log=[]
step=2000
b=b0
while b<=b1:
    end=min(b+step-1,b1)
    params=[{"fromBlock":hex(b),"toBlock":hex(end),"address":TOKEN,
             "topics":[TRANSFER_TOPIC,TOPIC_TREAS]}]
    logs=rpc("eth_getLogs",params)
    all_log.extend(logs)
    print(f"blocks {b}-{end}: +{len(logs)}", flush=True)
    b=end+1
    time.sleep(0.3)
json.dump(all_log,outf,indent=1)
outf.close()
print("TOTAL LOGS:",len(all_log))
