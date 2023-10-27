# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 14:42:02 2023

@author: mustafayarici
"""


"""
import pandas as pd
import requests as req
from datetime import datetime
import numpy as np

#%%PARAMETRE GİRİŞİ
date1="2023-09-26"
tomorrow="2023-09-27"
#%%


suplydemand_url= "https://seffaflik.epias.com.tr/transparency/service/market/supply-demand-curve"

resp1 = req.get(suplydemand_url,params={"period":date1})

print("arz talep okundu")
#%%
block_url= "https://seffaflik.epias.com.tr/transparency/service/market/amount-of-block"
blok_resp = req.get(block_url,params={"startDate":date1,"endDate":date1})
df_blok=pd.DataFrame(blok_resp.json()["body"]["amountOfBlockList"])
df_blok["date"]=pd.to_datetime(df_blok["date"].str[0:-3], format='%Y-%m-%dT%H:%M:%S.%f')
df_blok["date"]=df_blok["date"].dt.tz_localize(None)
#%%
#df_blok=df_blok[['amountOfSalesTowardsBlock','amountOfSalesTowardsMatchBlock']]
#%%
print("eşleşmeler")
marketvolume_url= "https://seffaflik.epias.com.tr/transparency/service/market/day-ahead-market-volume"

market_resp = req.get(marketvolume_url,params={"startDate":date1,"endDate":date1})
df_market=pd.DataFrame(market_resp.json()["body"]["dayAheadMarketVolumeList"])
df_market["date"]=pd.to_datetime(df_market["date"].str[0:-3], format='%Y-%m-%dT%H:%M:%S.%f')
df_market["date"]=df_market["date"].dt.tz_localize(None)
df_market.drop(columns = ['period','periodType'],inplace=True)

#%%

df_market["matchedBids"]




#%%

suplydemand=pd.DataFrame(resp1.json()["body"]["supplyDemandCurves"])
suplydemand["date"]=pd.to_datetime(suplydemand["date"].str[0:-3], format='%Y-%m-%dT%H:%M:%S.%f')
suplydemand["date"]=suplydemand["date"].dt.tz_localize(None)
suplydemand['hour']=suplydemand["date"].apply(lambda x:x.hour)

suplydemand["kesisim"]=suplydemand["demand"]+suplydemand["supply"]

print("arz talep işlendi")
#%%
demand_pv=pd.pivot_table(suplydemand, values='demand', index=['price'], columns=['hour'], aggfunc=np.mean)
demand_pv=demand_pv.interpolate(method='index')#fark interpolasyonları bul #deneme2=x.interpolate(method='values')#aynısı

suply_pv=pd.pivot_table(suplydemand, values='supply', index=['price'], columns=['hour'], aggfunc=np.mean)
suply_pv=suply_pv.interpolate(method='index')#fark interpolasyonları bul #deneme2=x.interpolate(method='values')#aynısı

diff_pv=pd.pivot_table(suplydemand, values='kesisim', index=['price'], columns=['hour'], aggfunc=np.mean)
diff_pv=diff_pv.interpolate(method='index')#fark interpolasyonları bul #deneme2=x.interpolate(method='values')#aynısı
diff_pv["24"]=diff_pv.index# indexteki fiyat kolona yaz

#%%Excelde min değer bulma işlemi için yapılıyor
#diff_pv=diff_pv.abs()#excel manuel işlemler için yapılıyor

#%%
pathseviye='C:/seffaf/seviye.xlsx'
seviye=pd.DataFrame(pd.read_excel(pathseviye, index_col=None, na_values=['NA']))

#%%
demand_diff=demand_pv.shift(1, axis = 0)-demand_pv
demand_diff.iloc[0]=demand_pv.iloc[0]
demand_diff=demand_diff.round(0).astype(int)
demand_diff["price_level"]=demand_diff.index# indexteki fiyat kolona yaz
#%%
suply_diff=-suply_pv+suply_pv.shift(1, axis = 0)
suply_diff.iloc[0]=suply_pv.iloc[0]*-1
suply_diff=suply_diff.round(0).astype(int)
suply_diff["price_level"]=suply_diff.index# indexteki fiyat kolona yaz

#%%
suplysummery=pd.DataFrame()
suplysummery['FBS']=suply_pv.iloc[0]*-1
suplysummery['FBS']=suplysummery['FBS']-df_blok['amountOfSalesTowardsMatchBlock']
suplysummery['BlokEşleşme']=df_blok['amountOfSalesTowardsMatchBlock']

#%%
suplysummery['0-300TL']=suply_diff[(suply_diff['price_level'] > 0) & (suply_diff['price_level'] <= 300)].sum()
suplysummery['300-600TL']=suply_diff[(suply_diff['price_level'] > 300) & (suply_diff['price_level'] <= 600)].sum()
suplysummery['600-1000']=suply_diff[(suply_diff['price_level'] > 600) & (suply_diff['price_level'] <= 1000)].sum()
suplysummery['1000-1500TL']=suply_diff[(suply_diff['price_level'] > 1000) & (suply_diff['price_level'] <= 1500)].sum()
suplysummery['1500-1750TL']=suply_diff[(suply_diff['price_level'] > 1500) & (suply_diff['price_level'] <= 1750)].sum()
suplysummery['1750-2000TL']=suply_diff[(suply_diff['price_level'] > 1750) & (suply_diff['price_level'] <= 2000)].sum()
suplysummery['2000-2250']=suply_diff[(suply_diff['price_level'] > 2000) & (suply_diff['price_level'] <= 2250)].sum()
suplysummery['2250-2500']=suply_diff[(suply_diff['price_level'] > 2250) & (suply_diff['price_level'] <= 2500)].sum()
suplysummery['2500-2600']=suply_diff[(suply_diff['price_level'] > 2500) & (suply_diff['price_level'] <= 2600)].sum()

#suplysummery['4500-4800TL']=suply_diff[(suply_diff['price_level'] > 4500) ].sum()
#suplysummery['2450-2600TL']=suply_diff[(suply_diff['price_level'] > 2450) & (suply_diff['price_level'] <= 2600)].sum()
#suplysummery['2600-2999TL']=suply_diff[(suply_diff['price_level'] > 2600) & (suply_diff['price_level'] <= 2999)].sum()
#suplysummery['2999-3200TL']=suply_diff[(suply_diff['price_level'] > 2999) & (suply_diff['price_level'] <= 3200)].sum()
#suplysummery['3200-3750TL']=suply_diff[(suply_diff['price_level'] > 3200)].sum()
print("arz ")
#%%

demandsummery=pd.DataFrame()
demandsummery['MaksAlış']=demand_diff.iloc[0]

demandsummery['0-600TL']=demand_diff[(demand_diff['price_level'] > 0) & (demand_diff['price_level'] <= 600)].sum()
demandsummery['600-1000TL']=demand_diff[(demand_diff['price_level'] > 600) & (demand_diff['price_level'] <= 1000)].sum()
demandsummery['1000-1250TL']=demand_diff[(demand_diff['price_level'] > 1000) & (demand_diff['price_level'] <= 1250)].sum()
demandsummery['1250-1500TL']=demand_diff[(demand_diff['price_level'] > 1250) & (demand_diff['price_level'] <= 1500)].sum()
demandsummery['1500-1750TL']=demand_diff[(demand_diff['price_level'] > 1500) & (demand_diff['price_level'] <= 1750)].sum()
demandsummery['1750-2000TL']=demand_diff[(demand_diff['price_level'] > 1750) & (demand_diff['price_level'] <= 2000)].sum()
demandsummery['2000-2250TL']=demand_diff[(demand_diff['price_level'] > 2000) & (demand_diff['price_level'] <= 2250)].sum()
demandsummery['2250-2600TL']=demand_diff[(demand_diff['price_level'] > 2250) ].sum()
#demandsummery['2450-2600TL']=demand_diff[(demand_diff['price_level'] > 2450) & (demand_diff['price_level'] <= 2600)].sum()
#demandsummery['2600-2999TL']=demand_diff[(demand_diff['price_level'] > 2600) & (demand_diff['price_level'] <= 2999)].sum()
#demandsummery['2999-3200TL']=demand_diff[(demand_diff['price_level'] > 2999) & (demand_diff['price_level'] <= 3200)].sum()
#demandsummery['3200-3750']=demand_diff[(demand_diff['price_level'] > 3200) ].sum()
demandsummery.drop('price_level',inplace=True)

#%%
print(" talep ")

kesinti=pd.DataFrame()
kesinti['Saatlik FBA']=demand_pv.iloc[-1]-df_blok["amountOfPurchasingTowardsMatchBlock"]
#%%
kesinti["Saatlik Eşleşen Alış"]=df_market["matchedBids"]-df_blok["amountOfPurchasingTowardsMatchBlock"]
#%%

kesinti["Kesinti"]=kesinti["Saatlik Eşleşen Alış"]-kesinti['Saatlik FBA']
#%%
for i in range(0,24):
    
    if kesinti["Kesinti"][i]<0:
        kesinti["Kesinti"][i]=kesinti["Kesinti"][i]
    else:
        kesinti["Kesinti"][i]=0

kesinti["KesintiOranı"]=kesinti["Kesinti"]/kesinti['Saatlik FBA']

print("kesinti")
#%%

url_ptf="https://seffaflik.epias.com.tr/transparency/service/market/day-ahead-mcp"
ptf_resp=req.get(url_ptf,params={"startDate":date1,"endDate":date1})
df_ptf=pd.DataFrame(ptf_resp.json()["body"]["dayAheadMCPList"])
df_ptf["date"]=pd.to_datetime(df_ptf["date"].str[0:-3], format='%Y-%m-%dT%H:%M:%S.%f')
df_ptf["date"]=df_ptf["date"].dt.tz_localize(None)

df_blok["amountOfSalesTowardsBlock"]=df_blok["amountOfSalesTowardsBlock"]-df_blok["amountOfSalesTowardsMatchBlock"]

fbafbs=pd.concat([df_market[["priceIndependentBid","priceIndependentOffer"]],df_blok[["amountOfSalesTowardsMatchBlock","amountOfSalesTowardsBlock"]],df_ptf["price"]],axis=1)

#%%
writer = pd.ExcelWriter(date1+'Arz_Talep_Kesinti'+'.xlsx',engine ='xlsxwriter')
#writer = pd.ExcelWriter('KGUPIAtest'+'.xlsx',engine ='xlsxwriter')
#pd.DataFrame(demand_pv).to_excel(writer, sheet_name='demand_pv')
#pd.DataFrame(suply_pv).to_excel(writer, sheet_name='suply_pv')
pd.DataFrame(diff_pv).to_excel(writer, sheet_name='diff_pv')
pd.DataFrame(demand_diff).to_excel(writer, sheet_name='demand_diff')
#pd.DataFrame(diff_pv).to_excel(writer, sheet_name='diff_pv')
pd.DataFrame(suply_diff).to_excel(writer, sheet_name='suply_diff')
pd.DataFrame(suplysummery).to_excel(writer, sheet_name='Arz Özet')
pd.DataFrame(demandsummery).to_excel(writer, sheet_name='Talep Özet')
pd.DataFrame(kesinti).to_excel(writer, sheet_name='Kesinti')
pd.DataFrame(fbafbs).to_excel(writer, sheet_name='fbafbsptf')
writer.save()
writer.close()








































try:
    block_url= "https://seffaflik.epias.com.tr/transparency/service/market/amount-of-block"
    blok_resp = req.get(block_url,params={"startDate":"2023-09-26","endDate":"2023-09-26"})
    df_blok=pd.DataFrame(blok_resp.json()["body"]["amountOfBlockList"])
    st.dataframe(df_blok,height=600,use_container_width=True)

except:
    st.write("şeffaflık veri çekilemiyor")
    pass

"""