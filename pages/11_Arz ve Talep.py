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
import pytz

#%%sayfa düzeni
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.set_page_config(page_title="EMBA", page_icon=":chart_with_upwards_trend:", layout="wide")

st.markdown(hide_st_style, unsafe_allow_html=True)

#%%arz talep cash
@st.cache_data  # Allow caching DataFrame
def loading(date1):

    suplydemand_url= "https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/supply-demand"
    try:
        suplydemand = pd.DataFrame()
        
        for hour in range(24):

            print(hour)
            current_datetime = datecopy.replace(hour=hour)
            current_datetime = current_datetime.strftime("%Y-%m-%dT%H:%M:%S%z")
            current_datetime = current_datetime[:19] + current_datetime[-5:-2] + ":" + current_datetime[-2:]
            
            payload = {"date": current_datetime}
            resp1 = req.post(suplydemand_url,json=payload, headers=headers, timeout=15)
            hourdata=pd.DataFrame(resp1.json()["items"])
            suplydemand = pd.concat([suplydemand, hourdata], ignore_index=True)

        suplydemand["date"]=pd.to_datetime(suplydemand["date"].str[0:-3], format='%Y-%m-%dT%H:%M:%S.%f')
        suplydemand["date"]=suplydemand["date"].dt.tz_localize(None)
        suplydemand['hour']=suplydemand["date"].apply(lambda x:x.hour)
        suplydemand["kesisim"]=suplydemand["demand"]+suplydemand["supply"]

    except:
        st.write("Arz-Talep okunamadı")        
                   
    #%%
    demand_pv=pd.pivot_table(suplydemand, values='demand', index=['price'], columns=['hour'], aggfunc=np.mean)
    demand_pv=demand_pv.interpolate(method='index')#fark interpolasyonları 
    
    suply_pv=pd.pivot_table(suplydemand, values='supply', index=['price'], columns=['hour'], aggfunc=np.mean)
    suply_pv=suply_pv.interpolate(method='index')#fark interpolasyonları
    
    #diff_pv=pd.pivot_table(suplydemand, values='kesisim', index=['price'], columns=['hour'], aggfunc=np.mean)
    #diff_pv=diff_pv.interpolate(method='index')#fark interpolasyonları  
   
    return demand_pv, suply_pv,suplydemand#,diff_pv

date1 = st.date_input('Baz gün',value=date.today())

datecopy=date1

#
selected_datetime = datetime.datetime(datecopy.year, datecopy.month, datecopy.day, 0, 0, 0)

# Get your local time zone (Istanbul)
local_timezone = pytz.timezone('Europe/Istanbul')

# 
datecopy = selected_datetime.astimezone(local_timezone)
date1=str(date1)
print(date1)

#%%
auth_url = "https://giris.epias.com.tr/cas/v1/tickets"  # TGT almak için kullanacağınız URL
auth_payload = "username=mustafayarici@embaenergy.com&password=Seffaf.3406"
auth_headers = {"Content-Type": "application/x-www-form-urlencoded","Accept": "text/plain"}

# TGT isteğini yap
try:
    auth_response = req.post(auth_url, data=auth_payload, headers=auth_headers)
    auth_response.raise_for_status()  # Eğer istek başarısız olursa hata
    tgt = auth_response.text  # TGT'yi yanıt metninden al
    print("TGT : başarılı")
except Exception as e:
    print("TGT alma hatası:", e)
    tgt = None  # TGT alınamazsa devam edemeyiz  

headers = {
        "TGT": tgt,  # Aldığımız TGT burada kullanılıyor
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
#%%


# Cache teki arz talebi değiştir. 
demand_pv, suply_pv,suplydemand = loading(datecopy)#,diff_pv

veri=pd.DataFrame(pd.read_excel("Tahmin.xlsx", "Sayfa1",index_col=None, na_values=['NA']))#C:/marketdata/
veri['Tarih']=pd.to_datetime(veri['Tarih'])
veri['shortdate']=pd.to_datetime(veri['Tarih']).dt.strftime("%Y-%m-%d")
azami=3400
asgari=0

#%%
#FBA ve FBS tahmin bölümü

#%% Gün parametreleri

date2 = st.date_input('Tahmin Edilecek Gün',value=date.today()+ timedelta(days=1))

#fba fbs güb parametreleri
start_date = date2 - timedelta(days=7)
date_range = [start_date + timedelta(days=x) for x in range(8)]
date2=str(date2)

#%% seçili eğitim günleri

selected_dates = st.multiselect("Eğitim Günleri",  sorted(date_range), default=date_range)
selected_dates.sort()

#%%

fbs_limit=14500

songun = selected_dates[-1]#tahmini yapılacak gün ytp ve ritm okunacak son gün

ptf_tavan=3400

fbs_days=selected_dates#

fbs_days = [pd.to_datetime(date).date() for date in fbs_days]

veri['gunler']= veri['Tarih'].dt.date
#Tahminlerde kullanılacak genel veriler
secilengunveri=veri.loc[veri['gunler'].isin(fbs_days), ["talep", "rüzgar", "Solar", "Yenilenebilir", "Talep-Yenilenebilir", "FBA", "FBS", "FBA-FBS","Eşleşen Blok", "PTF"]]

#%% 

#FBS TAHMİN BÖLÜMÜ

#%%

FBS_input=secilengunveri.loc[(veri["gunler"]<songun)]
FBS_predict_input=secilengunveri[["rüzgar",	"Solar"]].loc[(veri["gunler"]==songun)]

#%%train

print("FBS")

x_train=FBS_input[["rüzgar",	"Solar"]]
y_train=FBS_input["FBS"]
#%%
try:
    regressor = LinearRegression()
    regressor.fit(x_train,y_train)
    fbs_result= regressor.predict(FBS_predict_input)#FBS TAHMİNİ
    fbs_result=pd.DataFrame(fbs_result,columns=["Üretim"])
except:
    st.write("Üretim Veri Güncel Değil")
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
    fba_result=pd.DataFrame(fba_result,columns=["Tüketim"])
except:
    st.write("Tületim Veri Güncel Değil")
    pass

#%% 

#Blok TAHMİN BÖLÜMÜ

#%%

Blok_input=secilengunveri.loc[(veri["gunler"]<songun)]
Blok_predict_input=pd.DataFrame((fba_result["Tüketim"]-fbs_result["Üretim"]),columns =['FBA-FBS'])


#%%train

print("Blok")

x_train=Blok_input[["FBA-FBS"]]
y_train=Blok_input["Eşleşen Blok"]

#%%

try:
    regressor = LinearRegression()
    regressor.fit(x_train,y_train)
    blok_result= regressor.predict(Blok_predict_input[['FBA-FBS']])
    blok_result=pd.DataFrame(blok_result,columns=["Blok"])
except:
    st.write("Blok Veri Güncel Değil")
    pass

#%%

base1=veri[veri['shortdate']==date1][["Tarih","shortdate","talep","Yenilenebilir","FBA","FBS","Eşleşen Blok","PTF"]].reset_index(drop=True)
base2=veri[veri['shortdate']==date2][["Tarih","shortdate","talep","Yenilenebilir","FBA","FBS","Eşleşen Blok","PTF"]].reset_index(drop=True)

#%% baz gün ile fark hesapla 

fbs_diff=pd.DataFrame(fbs_result["Üretim"]-base1["FBS"],columns=["Üretim Fark"])
fba_diff=pd.DataFrame(fba_result["Tüketim"]-base1["FBA"],columns=["Tüketim Fark"])
blok_diff=pd.DataFrame(blok_result["Blok"]-base1["Eşleşen Blok"],columns=["Blok Fark"])

#%% baz gün Tahmin tablosu 

# baz ve tahmin günü tüketimi ve farkı base1 ve 2 den gelir
summary_df=pd.DataFrame(base1["talep"])
summary_df.columns=["Baz Tüketim"]
summary_df["Tüketim Tahmini"]=base2["talep"]

#baz ve tahmin günü alış 

summary_df["Baz Alış"]=base1["FBA"]
summary_df["Alış Tahmini"]=pd.DataFrame(fba_result["Tüketim"])


#farklar
summary_df["Tüketim Değişimi"]=summary_df["Tüketim Tahmini"]-summary_df["Baz Tüketim"]
summary_df["Alış Değişimi"]=summary_df["Alış Tahmini"]-summary_df["Baz Alış"]

#baz ve tahmin günü  res ges değerleri ve farkı
summary_df["Baz Yenilenebilir"]=base1["Yenilenebilir"]
summary_df["Yenilenebilir Tahmini"]=base2["Yenilenebilir"]

#baz ve tahmin günü satış

summary_df["Baz Satış"]=base1["FBS"]
summary_df["Satış Tahmini"]=pd.DataFrame(fbs_result["Üretim"])

#farklar
summary_df["Yenilenebilir Değişimi"]=summary_df["Yenilenebilir Tahmini"]-summary_df["Baz Yenilenebilir"]
summary_df["Satış Değişimi"]=summary_df["Satış Tahmini"]-summary_df["Baz Satış"]

st.dataframe(summary_df.astype(int),height=880,use_container_width=True)
st.download_button(
   "İndir",
   summary_df.astype(int).to_csv(sep=";", decimal=",",index=False).encode('utf-8-sig'),
   "Alış Satış.csv",
   "text/csv",
   key='download-fbafbs')

#%%değişim grafikleri
        
col1, col2 = st.columns(2)
with col1:
    if not summary_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=summary_df["Baz Tüketim"], name='Baz Tüketim' ,mode='lines'))
        fig.add_trace(go.Scatter(y=summary_df["Tüketim Tahmini"], name='Tüketim Tahmini' ,mode='lines',marker_color='red'))
        fig.update_layout( title="Tüketim Değişimi", height=500, yaxis=dict(title=dict(text="MWh"),side="left"))#barmode='group',,overlaying="y"
        st.plotly_chart(fig,use_container_width=True)

with col2:
    if not summary_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=summary_df["Baz Alış"], name='Baz Alış' ,mode='lines'))
        fig.add_trace(go.Scatter(y=summary_df["Alış Tahmini"], name='Alış Tahmini' ,mode='lines',marker_color='red'))
        fig.update_layout( title="Alış Değişimi", height=500, yaxis=dict(title=dict(text="MWh"),side="left"))#barmode='group',,overlaying="y"
        st.plotly_chart(fig,use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    if not summary_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=summary_df["Baz Yenilenebilir"], name='Baz Yenilenebilir' ,mode='lines'))
        fig.add_trace(go.Scatter(y=summary_df["Yenilenebilir Tahmini"], name='Yenilenebilir Tahmini' ,mode='lines',marker_color='red'))
        fig.update_layout( title="Yenilenebilir Değişimi", height=500, yaxis=dict(title=dict(text="MWh"),side="left"))#barmode='group',,overlaying="y"
        st.plotly_chart(fig,use_container_width=True)        
with col2:
    if not summary_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=summary_df["Baz Satış"], name='Baz Satış' ,mode='lines'))
        fig.add_trace(go.Scatter(y=summary_df["Satış Tahmini"], name='Satış Tahmini' ,mode='lines',marker_color='red'))
        fig.update_layout( title="Satış Değişimi", height=500, yaxis=dict(title=dict(text="MWh"),side="left"))#barmode='group',,overlaying="y"
        st.plotly_chart(fig,use_container_width=True)              

#%% eklenecek veri tablosu***************blok arza eklenecek
edited_df=pd.DataFrame()

col1, col2 = st.columns(2)
#col1
with col1:
    st.title("Üretim Tüketim Değişimi")
    st.write("Excel tablosundan yapıştırarak tüm tabloyu bir kerede güncelleyebilirsiniz.")
    try:
        data=pd.concat([fbs_diff,fba_diff,blok_diff], axis=1)
        data[["Üretim Fark","Tüketim Fark","Blok Fark"]] = data[["Üretim Fark","Tüketim Fark","Blok Fark"]].astype(int)
        edited_df = st.data_editor(data,height=880)
    except:
        st.write("Üretim Tüketim ve Blok veri güncel değil")
        pass
    
    edited_df=edited_df.fillna(0)
    
    
    st.download_button(
       "Farkları İndir",
       edited_df.to_csv(sep=";", decimal=",",index=False).encode('utf-8-sig'),
       "Farklar.csv",
       "text/csv",
       key='download-Fark'
    )


#%%

#ARZ TALEP Kesiştir

#%% Arz Talep İnterpolasyon

suplydemand["kesisim"]=suplydemand["demand"]+suplydemand["supply"]

sd_pivot=pd.pivot_table(suplydemand, values='kesisim', index=['price'], columns=['hour'], aggfunc=np.mean)
sd_pivot=sd_pivot.interpolate(method='index')#fark interpolasyonları bul #deneme2=x.interpolate(method='values')#aynısı
sd_pivot_abs=sd_pivot.abs()#mutlak değerleri olan kopya ile kesişim noktasının alt yada üst noktası bulunur.

minindeks=sd_pivot_abs.idxmin()#her min değerin satır adı "price" indexi #fiyatın belirlendiği segmentleri bul

qx=pd.pivot_table(suplydemand,values='demand', index=['price'], columns=['hour'], aggfunc=np.mean)#miktar için aynı yöntem
qx=qx.interpolate(method='index')#miktar interpolasyonu

qxs=pd.pivot_table(suplydemand,values='supply', index=['price'], columns=['hour'], aggfunc=np.mean)#talep kesintisinde kullanılır
qxs=qxs.interpolate(method='index').abs()#tavan fiyatta eşleşme maks arz olur

pitifi=pd.DataFrame()

temp1=sd_pivot.copy()

for j in range(0,2,2):
    
    temp1=sd_pivot.copy()
    tempptf=pd.DataFrame()
    tempqx=qx.copy()
    tempqxs=qxs.copy()#aynı boyutta olsun diye boş dataframe değil?

    for i in range(0,24):
        temp1[i]=sd_pivot[i]-edited_df.iloc[i,j]+edited_df.iloc[i,j+1]-edited_df.iloc[i,j+2]#arz - talep +
        tempqx[i]=qx[i]+edited_df.iloc[i,j+1]#talep değişimi talep tablosuna
        tempqxs[i]=qxs[i]+edited_df.iloc[i,j]+edited_df.iloc[i,j+2]#arz değişimi azr tablosuna

    temp2=temp1.abs()
    tempindeks=temp2.idxmin()
    
    for i in range(0,24):
       
        if temp1.loc[tempindeks[i],i]<0 and tempindeks[i] != asgari:#arz fazlası sebebiyle fiyat 0 çıkıyosa başka adıma git
            xp =[temp1.loc[tempindeks[i],i],temp1.shift(+1, axis = 0).loc[tempindeks[i],i]]
            fp=[tempindeks[i],temp1.index[temp1[i]==(temp1.shift(+1, axis = 0).loc[tempindeks[i],i])].tolist()[0]]
            tempptf.loc[i,0]=np.interp(0, xp, fp)
            fp.sort()
            xp.sort(reverse=True)
            xpqx =[tempqx.shift(+1, axis = 0).loc[tempindeks[i],i],tempqx.loc[tempindeks[i],i]]
            tempptf.loc[i,1]=np.interp(tempptf.loc[i,0],  fp, xpqx)
            #print("üst")
            
        elif tempindeks[i]== azami:#fiyat arz yetmezliği sebebiyle maks çıktıysa
            tempptf.loc[i,0]=azami
            tempptf.loc[i,1]=tempqxs.loc[tempindeks[i],i]
        
        elif tempindeks[i]== asgari:#arz fazlası fiyat 0 ise burası
            tempptf.loc[i,0]=asgari
            tempptf.loc[i,1]=tempqx.loc[tempindeks[i],i]
        
        else:
            xp =[temp1.loc[tempindeks[i],i],temp1.shift(-1, axis = 0).loc[tempindeks[i],i]]
            fp=[tempindeks[i],temp1.index[temp1[i]==(temp1.shift(-1, axis = 0).loc[tempindeks[i],i])].tolist()[0]]
            fp.sort()
            xp.sort()
            tempptf.loc[i,0]=np.interp(0, xp, fp)
            xpqx=[tempqx.loc[tempindeks[i],i],tempqx.shift(-1, axis = 0).loc[tempindeks[i],i]]
            tempptf.loc[i,1]=np.interp(tempptf.loc[i,0], fp, xpqx)

    pitifi=pd.concat([pitifi, tempptf],axis=1)

#%%
pitifi.columns=["PTF","Eşleşme Miktarı"]
pitifi["PTF"] = pitifi["PTF"].astype(int)
pitifi["Eşleşme Miktarı"] = pitifi["Eşleşme Miktarı"].astype(int)
pitifi.insert(1,"Baz PTF",base1["PTF"].astype(int))
pitifi.insert(2,"PTF Değişim",pitifi["PTF"]-pitifi["Baz PTF"])


#%%
#col2
with col2:
    st.title(date2+ " PTF Tahmini: " +str( pitifi["PTF"].mean().astype(int)))
    st.write("Yandaki tablo verilerini değiştirerek yeniden tahmin yapabilirsiniz.")
    st.dataframe(pitifi,height=880)
    st.download_button(
       "PTF İndir",
       pitifi.to_csv(sep=";", decimal=",",index=False).encode('utf-8-sig'),
       "PTF.csv",
       "text/csv",
       key='download-PTF'
    )

#%%
#grafikler
#%%

#st.button("Grafikler", type="primary")
if st.button('Grafikler'):
    
    try:
        url_ptf="https://seffaflik.epias.com.tr/transparency/service/market/day-ahead-mcp"
        ptf_resp=req.get(url_ptf,params={"startDate":date2,"endDate":date2})
        df_ptf=pd.DataFrame(ptf_resp.json()["body"]["dayAheadMCPList"])
        df_ptf["date"]=pd.to_datetime(df_ptf["date"].str[0:-3], format='%Y-%m-%dT%H:%M:%S.%f')
        df_ptf["date"]=df_ptf["date"].dt.tz_localize(None)
    except:
        st.write("PTF yayınlanmadı.")
        pass
    
    try:
        block_url= "https://seffaflik.epias.com.tr/transparency/service/market/amount-of-block"
        blok_resp = req.get(block_url,params={"startDate":date2,"endDate":date2})
        df_blok=pd.DataFrame(blok_resp.json()["body"]["amountOfBlockList"])
    except:
        st.write("PTF yayınlanmadı.")
        pass    
    
    try:
        marketvolume_url= "https://seffaflik.epias.com.tr/transparency/service/market/day-ahead-market-volume"
        market_resp = req.get(marketvolume_url,params={"startDate":date2,"endDate":date2})
        df_market=pd.DataFrame(market_resp.json()["body"]["dayAheadMarketVolumeList"])
        df_market["date"]=pd.to_datetime(df_market["date"].str[0:-3], format='%Y-%m-%dT%H:%M:%S.%f')
        df_market["date"]=df_market["date"].dt.tz_localize(None)
        df_market.drop(columns = ['period','periodType'],inplace=True)
    except:
        st.write("PTF yayınlanmadı.")
        pass    
    
    try:    
        fbafbs=pd.concat([df_market[["priceIndependentBid","priceIndependentOffer"]],df_blok[["amountOfSalesTowardsMatchBlock"]],df_ptf["price"]],axis=1)
        fbafbs["Gerçekleşen Alış Değişim"]=fbafbs['priceIndependentBid']-summary_df["Baz Alış"]
        fbafbs["Gerçekleşen Satış Değişim"]=fbafbs['priceIndependentOffer']-summary_df["Baz Satış"]
        #PTF Grafiği
        if not fbafbs.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=fbafbs['price'], name='PTF Gerçekleşen' ,mode='lines'))
            fig.add_trace(go.Scatter(y=pitifi["PTF"], name='PTF Tahmin' ,mode='lines',marker_color='red'))
            fig.update_layout( title="PTF Gerçekleşen ve Tahmin", height=500, yaxis=dict(title=dict(text="MWh"),side="left"))#barmode='group',,overlaying="y"
            st.plotly_chart(fig,use_container_width=True)
    
        #yeni alış    
        grf_fba=pd.DataFrame(base1["FBA"]+edited_df["Tüketim Fark"],columns=["Alış Tahmin"])
        #Alış Grafiği
        if not fbafbs.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=fbafbs['priceIndependentBid'], name='Alış Gerçekleşen' ,mode='lines'))
            fig.add_trace(go.Scatter(y=grf_fba["Alış Tahmin"], name='Alış Tahmin' ,mode='lines',marker_color='red'))
            fig.update_layout( title="Alış Gerçekleşen ve Tahmin", height=500, yaxis=dict(title=dict(text="MWh"),side="left"))#barmode='group',,overlaying="y"
            st.plotly_chart(fig,use_container_width=True)

        #farklar
        #alis=pd.concat([fbafbs["Gerçekleşen Alış Değişim"],summary_df["Tüketim Değişimi"],summary_df["Alış Değişimi"]],axis=1)
        #st.dataframe(alis,height=880)  
        
        #farklar grafik 

        if not fbafbs.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=fbafbs["Gerçekleşen Alış Değişim"], name='Gerçekleşen Fark' ,mode='lines'))
            fig.add_trace(go.Scatter(y=summary_df["Tüketim Değişimi"], name='Tüketim Değişimi' ,mode='lines',marker_color='red'))
            fig.add_trace(go.Scatter(y=summary_df["Alış Değişimi"], name='Alış Değişimi' ,mode='lines',marker_color='black'))            
            fig.update_layout( title="Alış Farklar", height=500, yaxis=dict(title=dict(text="MWh"),side="left"))#barmode='group',,overlaying="y"
            st.plotly_chart(fig,use_container_width=True)   

 
        #yeni satış    
        grf_fbs=pd.DataFrame(base1["FBS"]+edited_df["Üretim Fark"],columns=["Satış Tahmin"])
        #Üretim Grafiği
        if not fbafbs.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=fbafbs['priceIndependentOffer'], name='Satış Gerçekleşen' ,mode='lines'))
            fig.add_trace(go.Scatter(y=grf_fbs["Satış Tahmin"], name='Satış Tahmin' ,mode='lines',marker_color='red'))
            fig.update_layout( title="Üretim Gerçekleşen ve Tahmin", height=500, yaxis=dict(title=dict(text="MWh"),side="left"))#barmode='group',,overlaying="y"
            st.plotly_chart(fig,use_container_width=True)

        #farklar grafik
        if not fbafbs.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=fbafbs['Gerçekleşen Satış Değişim'], name='Gerçekleşen Satış Değişim' ,mode='lines'))
            fig.add_trace(go.Scatter(y=summary_df["Yenilenebilir Değişimi"], name='Yenilenebilir Değişimi' ,mode='lines',marker_color='red'))
            fig.add_trace(go.Scatter(y=summary_df["Satış Değişimi"], name='Satış Değişimi' ,mode='lines',marker_color='black'))            
            fig.update_layout( title="Üretim Farklar", height=500, yaxis=dict(title=dict(text="MWh"),side="left"))#barmode='group',,overlaying="y"
            st.plotly_chart(fig,use_container_width=True) 


        #satis=pd.concat([fbafbs['Gerçekleşen Satış Değişim'],summary_df["Yenilenebilir Değişimi"],summary_df["Satış Değişimi"]],axis=1)
        #st.dataframe(satis,height=880)


        
        #yeni blok   
        grf_blok=pd.DataFrame(base1["Eşleşen Blok"]+edited_df["Blok Fark"],columns=["Blok Tahmin"])
        #Blok Grafiği
        if not fbafbs.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=fbafbs['amountOfSalesTowardsMatchBlock'], name='Blok Gerçekleşen' ,mode='lines'))
            fig.add_trace(go.Scatter(y=grf_blok["Blok Tahmin"], name='Blok Tahmin' ,mode='lines',marker_color='red'))
            fig.update_layout( title="Blok Gerçekleşen ve Tahmin", height=500, yaxis=dict(title=dict(text="MWh"),side="left"))#barmode='group',,overlaying="y"
            st.plotly_chart(fig,use_container_width=True)
 
            

            
            
    except:
        st.write("PTF yayınlanmadı.")
        pass   
else:
    st.title('Grafikler oluşturulmadı.')

#%%

