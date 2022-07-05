import time
import hmac
import requests
import json
import plotly.graph_objects as go
import pandas as pd
import os
from dotenv import load_dotenv 

load_dotenv()

signature=os.environ.get("signature")
key=os.environ.get("api_key")

ts = int(time.time() * 1000)

request = requests.Request('GET', 'https://ftx.com/api/futures')
prepared = request.prepare()
signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
signature = hmac.new(signature.encode(), signature_payload, 'sha256').hexdigest()

prepared.headers['FTX-KEY'] = key
prepared.headers['FTX-SIGN'] = signature
prepared.headers['FTX-TS'] = str(ts)

s = requests.Session()
resp = s.send(prepared)

parsedResult = json.loads(resp.text)

markets = []
dailyChange = []
for i in parsedResult["result"]:
    if i["volumeUsd24h"] > 10000000:
        markets.append(i["name"])
        dailyChange.append(round(i["change24h"]*100, 2))

fig = go.Figure(data=[go.Table(header=dict(values=['Market', '24h change (%)']),
                 cells=dict(values=[markets, dailyChange]))
                     ])

d = {'Markets': markets, 'Daily pct change': dailyChange}
df = pd.DataFrame(data=d)
print(df.head())

ts2 = int(time.time() * 1000)

resolution = 300
# friday july 1st 18:00 EST
start_time = 1656712800
# monday july 4th 11:00 EST
end_time = 1656946800

pctChangePerCandle = []

for market_name in markets:
    request2 = requests.Request('GET', 'https://ftx.com/api/markets/'+market_name+'/candles?resolution='+str(resolution)+'&start_time='+str(start_time)+'&end_time='+str(end_time))
    prepared2 = request2.prepare()
    signature_payload2 = f'{ts2}{prepared2.method}{prepared2.path_url}'.encode()
    signature2 = hmac.new(signature.encode(), signature_payload2, 'sha256').hexdigest()

    prepared2.headers['FTX-KEY'] = key
    prepared2.headers['FTX-SIGN'] = signature2
    prepared2.headers['FTX-TS'] = str(ts2)

    resp2 = s.send(prepared2)

    parsedResult2 = json.loads(resp2.text)

    pctChanges = []
    for i in parsedResult2["result"]:
        pctChange = round((i['close'] - i['open'])/i['open'], 4)
        pctChanges.append(pctChange)
    
    pctChangePerCandle.append(pctChanges)

dd = pd.DataFrame(pctChangePerCandle).T
# print(dd)
corr = dd.corr()
corr = corr.set_axis(markets, axis=1)
corr.index = markets
# print(corr)

c = []
for i in corr.loc["BTC-PERP"]:
    c.append(i)

corrDictZip = zip(markets, c)
corrDict = dict(corrDictZip)

cc=dict(sorted(corrDict.items(), key=lambda item: item[1]))
fig2 = go.Figure(data=[go.Table(header=dict(values=['Market', 'Correlation']), cells=dict(values=[list(cc.keys()), list(cc.values())]))])

fig2.show()