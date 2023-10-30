# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 14:42:02 2023

@author: mustafayarici
"""


import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
import datetime
import xlsxwriter
from datetime import date
from datetime import timedelta

from io import BytesIO,StringIO
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.linear_model import LinearRegression
import requests as req


#%%sayfa düzeni


#%%arz talep cash
@st.cache_data  # Allow caching DataFrame
def load_and_preprocess_data(date1):

    suplydemand_url= "https://seffaflik.epias.com.tr/transparency/service/market/supply-demand-curve"
    try:
        resp1 = req.get(suplydemand_url,params={"period":date1})
        suplydemand=pd.DataFrame(resp1.json()["body"]["supplyDemandCurves"])
        suplydemand["date"]=pd.to_datetime(suplydemand["date"].str[0:-3], format='%Y-%m-%dT%H:%M:%S.%f')
        suplydemand["date"]=suplydemand["date"].dt.tz_localize(None)
        suplydemand['hour']=suplydemand["date"].apply(lambda x:x.hour)
        suplydemand["kesisim"]=suplydemand["demand"]+suplydemand["supply"]

    except:
        st.write("Arz-Talep okunamadı")
            
    #%%
    demand_pv=pd.pivot_table(suplydemand, values='demand', index=['price'], columns=['hour'], aggfunc=np.mean)
    demand_pv=demand_pv.interpolate(method='index')#fark interpolasyonları bul #deneme2=x.interpolate(method='values')#aynısı
    
    suply_pv=pd.pivot_table(suplydemand, values='supply', index=['price'], columns=['hour'], aggfunc=np.mean)
    suply_pv=suply_pv.interpolate(method='index')#fark interpolasyonları bul #deneme2=x.interpolate(method='values')#aynısı
    
    diff_pv=pd.pivot_table(suplydemand, values='kesisim', index=['price'], columns=['hour'], aggfunc=np.mean)
    diff_pv=diff_pv.interpolate(method='index')#fark interpolasyonları bul #deneme2=x.interpolate(method='values')#aynısı    
   
    return demand_pv, suply_pv,diff_pv#diff pv gerek olmayabilir tamamen arz ve talep ve ikisini kesiştirme olabilir

date1 = st.date_input('Baz gün',value=date.today())
date1=str(date1)

# Cache teki arz talebi değiştir. 
demand_pv, suply_pv,diff_pv = load_and_preprocess_data(date1)

print("seçilen baz günün arz talebi okundu")

veri=pd.DataFrame(pd.read_excel("Tahmin.xlsx", "Sayfa1",index_col=None, na_values=['NA']))#C:/marketdata/
veri['Tarih']=pd.to_datetime(veri['Tarih'])
veri['shortdate']=pd.to_datetime(veri['Tarih']).dt.strftime("%Y-%m-%d")




#%%
#FBA ve FBS tahmin bölümü

#%% Gün parametreleri

date2 = st.date_input('Tahmin Edilecek Gün',value=date.today()+ timedelta(days=1))
#fba fbs güb parametreleri
start_date = date2 - timedelta(days=7)
date_range = [start_date + timedelta(days=x) for x in range(8)]
date2=str(date2)


#%% seçili eğitim günleri

# filter
selected_dates = st.multiselect("Eğitim Günleri",  sorted(date_range), default=date_range)
selected_dates.sort()

#%%

#Tahmin günü
fbs_limit=14500

songun = selected_dates[-1]#tahmini yapılacak gün ytp ve ritm okunacak son gün
#songun = datetime.strptime(songun, "%Y-%m-%d").date()

ptf_tavan=2700

fbs_days=selected_dates#,'29.01.2023 00:00','30.01.2023 00:00' #GEÇMİŞ GÜNLER ÇALIŞTIRILIRKEN GÜNCELLENECEK YER
ptf_days=selected_dates#model 3 ptf bölümü için için günler

fbs_days = [pd.to_datetime(date).date() for date in fbs_days]
ptf_days = [pd.to_datetime(date).date() for date in ptf_days]

#bugun2=pd.to_datetime(songun, format="%Y.%m.%d")- timedelta(days=1)#kgüp okunacak son gün ve göp sonucu okunacak son gün
veri['gunler']= veri['Tarih'].dt.date
#Tahminlerde kullanılacak genel veriler
secilengunveri=veri.loc[veri['gunler'].isin(fbs_days), ["talep", "rüzgar", "Solar", "Yenilenebilir", "Talep-Yenilenebilir", "FBA", "FBS", "FBA-FBS", "PTF"]]

#%% 

#FBS TAHMİN BÖLÜMÜ

#%%

FBS_input=secilengunveri.loc[(veri["gunler"]<songun)]
FBS_predict_input=secilengunveri[["rüzgar",	"Solar"]].loc[(veri["gunler"]==songun)]

#%%
#train
print("FBS")
#x_train=FBS_input[["Yenilenebilir"]]
x_train=FBS_input[["rüzgar",	"Solar"]]
y_train=FBS_input["FBS"]
#%%
try:
    regressor = LinearRegression()
    regressor.fit(x_train,y_train)
    fbs_result= regressor.predict(FBS_predict_input)#FBS TAHMİNİ
    st.dataframe(fbs_result)
    fbs_result=pd.DataFrame(fbs_result,columns=["Üretim"])
except:
    st.write("Veri Güncel Değil")
    pass
#%% 

#FBA TAHMİN BÖLÜMÜ

#%% 

print("FBA periyotlar")

#FBA seçilen günler
fba_start=songun- timedelta(days=6)
fba_veri=veri[["Saat","talep","FBA"]].loc[(veri["gunler"]>=fba_start)&(veri["gunler"]<=songun)]

#FBA zaman periyotları - dumy
fba_veri["Saat"]=fba_veri["Saat"].replace(to_replace=[0,1,2,3,4,5], value="grup1")
fba_veri["Saat"]=fba_veri["Saat"].replace(to_replace=[6,7,8,9,10], value="grup2")
fba_veri["Saat"]=fba_veri["Saat"].replace(to_replace=[11,12,13], value="grup3")
fba_veri["Saat"]=fba_veri["Saat"].replace(to_replace=[14,15,16,17,18,19,20,21], value="grup4")
fba_veri["Saat"]=fba_veri["Saat"].replace(to_replace=[22,23], value="grup5")
fba_veri=pd.get_dummies(fba_veri)

#train ve predict tabloları
fba_veri_in=fba_veri[['Saat_grup1', 'Saat_grup2', 'Saat_grup3', 'Saat_grup4', 'Saat_grup5',"talep"]].loc[veri["gunler"]==songun]#predict tablo
fba_veri=fba_veri.loc[(veri["gunler"]>=fba_start) & (veri["gunler"]<songun)]#train tablo

#train
x_train=fba_veri[['Saat_grup1', 'Saat_grup2', 'Saat_grup3', 'Saat_grup4', 'Saat_grup5',"talep"]]#grup saysı değişirse güncellenir
y_train=fba_veri["FBA"]

try:
    regressor = LinearRegression()
    regressor.fit(x_train,y_train)
    #predict
    fba_train = regressor.predict(x_train)
    fba_result = regressor.predict( fba_veri_in[['Saat_grup1', 'Saat_grup2', 'Saat_grup3', 'Saat_grup4', 'Saat_grup5',"talep"]])#FBA TAHMİNİ
    st.dataframe(fba_result)
    fba_result=pd.DataFrame(fba_result,columns=["Tüketim"])
except:
    st.write("Veri Güncel Değil")
    pass

#%%

base1=veri[veri['shortdate']==date1][["Tarih","shortdate","talep","Yenilenebilir","FBA","FBS","Eşleşen Blok","PTF"]].reset_index(drop=True)
base2=veri[veri['shortdate']==date2][["Tarih","shortdate","talep","Yenilenebilir","FBA","FBS","Eşleşen Blok","PTF"]].reset_index(drop=True)
st.dataframe(base1)
st.dataframe(base2)

#%% eklenecek veriler

try:
    data=pd.concat([fbs_result,fba_result], axis=1)
    data["Diğer"]=0
    edited_df = st.data_editor(data,height=880)
except:
    st.write("Veri Güncel Değil")
    pass


#%%
"""
#arz talep oku

#%%

suplydemand_url= "https://seffaflik.epias.com.tr/transparency/service/market/supply-demand-curve"

resp1 = req.get(suplydemand_url,params={"period":date1})

st.write("arz talep okundu")

#%%

suplydemand=pd.DataFrame(resp1.json()["body"]["supplyDemandCurves"])
suplydemand["date"]=pd.to_datetime(suplydemand["date"].str[0:-3], format='%Y-%m-%dT%H:%M:%S.%f')
suplydemand["date"]=suplydemand["date"].dt.tz_localize(None)
suplydemand['hour']=suplydemand["date"].apply(lambda x:x.hour)

suplydemand["kesisim"]=suplydemand["demand"]+suplydemand["supply"]

st.write("arz talep işlendi")

#%%
demand_pv=pd.pivot_table(suplydemand, values='demand', index=['price'], columns=['hour'], aggfunc=np.mean)
demand_pv=demand_pv.interpolate(method='index')#fark interpolasyonları bul #deneme2=x.interpolate(method='values')#aynısı

suply_pv=pd.pivot_table(suplydemand, values='supply', index=['price'], columns=['hour'], aggfunc=np.mean)
suply_pv=suply_pv.interpolate(method='index')#fark interpolasyonları bul #deneme2=x.interpolate(method='values')#aynısı

diff_pv=pd.pivot_table(suplydemand, values='kesisim', index=['price'], columns=['hour'], aggfunc=np.mean)
diff_pv=diff_pv.interpolate(method='index')#fark interpolasyonları bul #deneme2=x.interpolate(method='values')#aynısı

st.dataframe(diff_pv)
"""
#%%



#%%















#%%
"""

#%%

url_ptf="https://seffaflik.epias.com.tr/transparency/service/market/day-ahead-mcp"
ptf_resp=req.get(url_ptf,params={"startDate":date1,"endDate":date1})
df_ptf=pd.DataFrame(ptf_resp.json()["body"]["dayAheadMCPList"])
df_ptf["date"]=pd.to_datetime(df_ptf["date"].str[0:-3], format='%Y-%m-%dT%H:%M:%S.%f')
df_ptf["date"]=df_ptf["date"].dt.tz_localize(None)

#%%
block_url= "https://seffaflik.epias.com.tr/transparency/service/market/amount-of-block"
blok_resp = req.get(block_url,params={"startDate":date1,"endDate":date1})
df_blok=pd.DataFrame(blok_resp.json()["body"]["amountOfBlockList"])
df_blok["date"]=pd.to_datetime(df_blok["date"].str[0:-3], format='%Y-%m-%dT%H:%M:%S.%f')
df_blok["date"]=df_blok["date"].dt.tz_localize(None)

#%%
print("eşleşmeler")
marketvolume_url= "https://seffaflik.epias.com.tr/transparency/service/market/day-ahead-market-volume"

market_resp = req.get(marketvolume_url,params={"startDate":date1,"endDate":date1})
df_market=pd.DataFrame(market_resp.json()["body"]["dayAheadMarketVolumeList"])
df_market["date"]=pd.to_datetime(df_market["date"].str[0:-3], format='%Y-%m-%dT%H:%M:%S.%f')
df_market["date"]=df_market["date"].dt.tz_localize(None)
df_market.drop(columns = ['period','periodType'],inplace=True)

df_blok["amountOfSalesTowardsBlock"]=df_blok["amountOfSalesTowardsBlock"]-df_blok["amountOfSalesTowardsMatchBlock"]
fbafbs=pd.concat([df_market[["priceIndependentBid","priceIndependentOffer"]],df_blok[["amountOfSalesTowardsMatchBlock","amountOfSalesTowardsBlock"]],df_ptf["price"]],axis=1)



try:
    block_url= "https://seffaflik.epias.com.tr/transparency/service/market/amount-of-block"
    blok_resp = req.get(block_url,params={"startDate":"2023-09-26","endDate":"2023-09-26"})
    df_blok=pd.DataFrame(blok_resp.json()["body"]["amountOfBlockList"])
    st.dataframe(df_blok,height=600,use_container_width=True)

except:
    st.write("şeffaflık veri çekilemiyor")
    pass
"""
