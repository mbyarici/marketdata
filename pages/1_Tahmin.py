# -*- coding: utf-8 -*-
"""
Created on Tue Aug 29 13:50:56 2023

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

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.set_page_config(page_title="EMBA", page_icon=":chart_with_upwards_trend:", layout="wide")

st.markdown(hide_st_style, unsafe_allow_html=True)

#%%

veri=pd.DataFrame(pd.read_excel("Tahmin.xlsx", "Sayfa1",index_col=None, na_values=['NA']))#C:/marketdata/
veri['Tarih']=pd.to_datetime(veri['Tarih'])

#%%

arsiv=pd.DataFrame(pd.read_excel("Tahmin.xlsx", "arsiv",index_col=None, na_values=['NA']))#C:/marketdata/
arsiv['Tarih']=pd.to_datetime(arsiv['Tarih'])

#%%
daily = veri[['Tarih','rüzgar','talep','PTF']]

daily.insert(1,"solar",(veri["lisanslı"]+veri["lisanssız"]))

daily = daily.groupby(daily['Tarih'].dt.date)[["solar","rüzgar",'talep','PTF']].agg("mean")

daily = daily.reset_index()

#%%GÜNLÜK ORTALAMA TAHMİN

tahminbaslangic=date.today()
#tahminbaslangic=pd.to_datetime(tahminbaslangic, format="%Y.%m.%d")# + timedelta(days=1)

tahmingecmis='20230531'
#tahmingecmis=pd.to_datetime(tahmingecmis, format="%Y.%m.%d")
tahmingecmis = pd.Timestamp(tahmingecmis)
tahmingecmis=tahmingecmis.date()
PTF=pd.DataFrame(daily[(daily['Tarih'] <= tahminbaslangic)& (daily['Tarih'] > tahmingecmis)]['PTF'],columns =['PTF'])


#%%

trainparametre=st.number_input("Değer Giriniz : ", value=14)
one_day = timedelta(days=1)

#%% ort tahmin ve grafiği
try:
    X_train=daily[(daily['Tarih'] <= tahminbaslangic)& (daily['Tarih'] > tahminbaslangic-timedelta(days=trainparametre))][['talep', 'rüzgar']]
    y_train=daily[(daily['Tarih'] <= tahminbaslangic)& (daily['Tarih'] > tahminbaslangic-timedelta(days=trainparametre))]['PTF']

    model = LinearRegression()
    model.fit(X_train, y_train)

    X_pred = daily[daily['Tarih'] > tahminbaslangic][['talep', 'rüzgar']]
    y_pred = model.predict(X_pred)

    sonuc=pd.merge(daily[daily['Tarih'] > tahminbaslangic][['Tarih']].reset_index(drop=True),pd.DataFrame(y_pred,columns =['PTF']),left_index=True, right_index=True, how='inner')
    sonuc["PTF"]=round(sonuc["PTF"],0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sonuc['Tarih'], y=sonuc['PTF'], name='Tahmin', mode='lines+markers',text=sonuc['PTF']))
    for i, row in sonuc.iterrows():
        fig.add_annotation(
            text=f'PTF={row["PTF"]}',  
            x=row["Tarih"],         
            y=row["PTF"] + 50,   
            showarrow=False    
        )

    fig.update_layout(title="PTF-Tahmin", height=500, yaxis=dict(title=dict(text="TL/ MWh"),side="left") )
    fig.update_xaxes(tickformat='%Y-%m-%d')
    st.plotly_chart(fig,use_container_width=True)
    st.download_button(
       "Ort. PTF İndir",
       sonuc.to_csv(sep=";", decimal=",",index=False).encode('utf-8-sig'),
       "Ortalama PTF.csv",
       "text/csv",
       key='download-Ort'
    )
    
except:
    st.write("Ort. PTF Verisi Güncel Değil")
    pass


#%%Arşiv perfrmans

df = pd.DataFrame(columns=["Tarih", "Tahmin"])

try:
    while tahmingecmis <= tahminbaslangic:
        
        X_train=daily[(daily['Tarih'] <= tahmingecmis)& (daily['Tarih'] > tahmingecmis-timedelta(days=trainparametre))][['talep', 'rüzgar']]
        y_train=daily[(daily['Tarih'] <= tahmingecmis)& (daily['Tarih'] > tahmingecmis-timedelta(days=trainparametre))]['PTF']
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        X_pred = daily[daily['Tarih'] == tahmingecmis+timedelta(days=1)][['talep', 'rüzgar']]
        y_pred = model.predict(X_pred)
        
        df = pd.concat([df, pd.DataFrame({"Tarih": [(tahmingecmis+timedelta(days=1)).strftime("%Y-%m-%d")], "Tahmin": [y_pred[0]]})], ignore_index=True)
    
        tahmingecmis += one_day

#%%
    
    kiyas=pd.merge(df.reset_index(drop=True),PTF.reset_index(drop=True),left_index=True, right_index=True, how='inner')
    
    #%%
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(x=kiyas['Tarih'], y=kiyas['Tahmin'], name='Tahmin', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=kiyas['Tarih'], y=kiyas['PTF'], name='PTF', marker_color='red', mode='lines+markers'))
    fig.update_layout(title="Geçmiş Dönem PTF-Tahmin Karşılaştırma", height=500, yaxis=dict(title=dict(text="TL/MWh"),side="left") )
    fig.update_xaxes(tickformat='%Y-%m-%d')
    st.plotly_chart(fig,use_container_width=True)

    st.write("R^2 = ",r2_score(kiyas['PTF'], kiyas['Tahmin']))
    kiyas[["Tahmin","PTF"]]=round(kiyas[["Tahmin","PTF"]],0)
    st.download_button(
       "Karşılaştırma İndir",
       kiyas.to_csv(sep=";", decimal=",",index=False).encode('utf-8-sig'),
       "Karşılaştırma.csv",
       "text/csv",
       key='download-arsiv')

except:
    st.write("Arşiv Verisi Güncel Değil")
    pass


#%%
#SAATLİK TAHMİN BÖLÜMÜ
#%% seçili eğitim günleri

# Calculate the date range for the last 7 days
end_date = date.today()+ timedelta(days=1)
start_date = end_date - timedelta(days=7)
date_range = [start_date + timedelta(days=x) for x in range(8)]

# filter
selected_dates = st.multiselect("Tahmin ve Eğitim Günleri",  sorted(date_range), default=date_range)
selected_dates.sort()

#%%

#Tahmin günü
fbs_limit=14500

songun = selected_dates[-1]#tahmini yapılacak gün listedeki son gün default :yarın

ptf_tavan=3400

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
except:
    st.write("Veri Güncel Değil")
    pass

#%%

#PTF TAHMİN BÖLÜMÜ

#%% 

#veri tablosu
ptf_saat=veri.loc[veri['gunler'].isin(ptf_days), ["Saat","talep","rüzgar",	"Solar", "Yenilenebilir","FBA","FBS","FBA-FBS","PTF"]]

#zaman aralıkları dumy
ptf_saat["Saat"].loc[ptf_saat["Saat"]<5]=0
ptf_saat["Saat"].loc[(ptf_saat["Saat"]>=5) & (ptf_saat["Saat"]<12)]=1
ptf_saat["Saat"].loc[(ptf_saat["Saat"]>=12) & (ptf_saat["Saat"]<14)]=2
ptf_saat["Saat"].loc[(ptf_saat["Saat"]>=14) & (ptf_saat["Saat"]<18)]=3
ptf_saat["Saat"].loc[ptf_saat["Saat"]>17]=4

ptf_saat["Saat"]=ptf_saat["Saat"].replace(to_replace=[0,1,2,3,4], value=["grup1","grup2","grup3","grup4","grup5"])
ptf_saat=pd.get_dummies(ptf_saat)



try:
    #train ve predict 
    ptf_saat_in=ptf_saat.loc[(veri["gunler"]<songun)]
    ptf_saat_out=ptf_saat.loc[(veri["gunler"]==songun)][["Saat_grup1","Saat_grup2","Saat_grup3","Saat_grup4","Saat_grup5"]].reset_index(drop=True)#sadece gruplar - tahmin edilen fba ve fbs ile doldurulacak
    ptf_saat_out=ptf_saat_out[["Saat_grup1","Saat_grup2","Saat_grup3","Saat_grup4","Saat_grup5"]].reset_index(drop=True).merge((pd.DataFrame((fba_result-fbs_result),columns =['FBA-FBS'])),left_index=True, right_index=True, how='inner')
    
    #PTF train data tablosu
    print("PTF Tahmin Bölümü")
    x_train=ptf_saat_in[["Saat_grup1","Saat_grup2","Saat_grup3","Saat_grup4","Saat_grup5","FBA-FBS"]]
    y_train=ptf_saat_in["PTF"]
    
    
    
    #model
    regressor_ptf = LinearRegression()
    regressor_ptf.fit(x_train,y_train)
    
    #PTF TAHMİNİ - Tavan Fiyat Uygulaması
    PTF_result_model1= regressor_ptf.predict(ptf_saat_out)
    PTF_result_model1=pd.DataFrame((PTF_result_model1),columns =['PTF'])
    PTF_result_model1['PTF'].loc[PTF_result_model1['PTF']>ptf_tavan]=ptf_tavan
    
    PTF_result_model1["PTF"]=round(PTF_result_model1["PTF"],0)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=PTF_result_model1.index, y=PTF_result_model1['PTF'], name='Tahmin', mode='lines+markers',text=PTF_result_model1['PTF']))
    for i, row in PTF_result_model1.iterrows():
        fig.add_annotation(
            text=f'{row["PTF"]}',  
            x=i,
            y=row["PTF"] + 50,   
            showarrow=False    
        )
    
    fig.update_layout(title=str(songun) + " Ortalama PTF: " + str(round(PTF_result_model1["PTF"].mean(),2)), height=500, yaxis=dict(title=dict(text="TL/ MWh"),side="left") )
    
    st.plotly_chart(fig,use_container_width=True)
    st.download_button(
       "Saatlik PTF İndir",
       PTF_result_model1.to_csv(sep=";", decimal=",",index=False).encode('utf-8-sig'),
       "Saatlik PTF.csv",
       "text/csv",
       key='download-Saatlik')



    
    
    #%%
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=arsiv['Tarih'], y=arsiv['Tahmin'], name='Tahmin', mode='lines'))#+markers
    fig.add_trace(go.Scatter(x=arsiv['Tarih'], y=arsiv['PTF'], name='PTF', marker_color='red', mode='lines'))
    fig.update_layout(title="Geçmiş Dönem PTF-Tahmin Karşılaştırma", height=500, yaxis=dict(title=dict(text="TL/MWh"),side="left") )
    fig.update_xaxes(tickformat='%Y-%m-%d')
    st.plotly_chart(fig,use_container_width=True)
    st.write("R^2 = ",r2_score(arsiv['PTF'], arsiv['Tahmin']))

except:
    st.write("Veri Güncel Değil")
    pass




