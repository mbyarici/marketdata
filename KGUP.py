# -*- coding: utf-8 -*-
"""
Created on Tue May 23 17:08:22 2023

@author: mustafayarici
"""

from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import openpyxl
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from datetime import timedelta
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

#%%veri
kgupsum=pd.read_csv('genel.csv',encoding='utf-8-sig',sep=";", decimal=",",index_col=False)#C:/marketdata/
kgupsum['tarih']=pd.to_datetime(kgupsum['tarih'])

#%% data
kgupsum["diger"]=kgupsum["diger"]+kgupsum["jeotermal"]+kgupsum["biokutle"]
kgupsum["linyit"]=kgupsum["linyit"]+kgupsum["tasKomur"]

#%%
data=kgupsum[["tarih","toplam","dogalgaz","ruzgar","linyit","ithalKomur","barajli","akarsu","diger"]]
data.columns=["Tarih","Toplam","Doğalgaz","Rüzgar","Linyit","İthal Kömür","Barajlı","Akarsu","Diğer"]

#%%day select

selected_days = st.slider('Tarih Seçiniz', min_value=min(data['Tarih']).date(), 
                          max_value=max(data['Tarih']).date(), 
                          value=(min(data['Tarih']).date(), max(data['Tarih']).date()))

#%% hour select
#selected_hours = st.slider('Saat Seçiniz', min_value=0, max_value=23, value=(0, 23))

#%%

filtered_data = data[(data['Tarih'].dt.date >= selected_days[0]) &
                     (data['Tarih'].dt.date <= selected_days[1])]# &(data['Tarih'].dt.hour >= selected_hours[0]) &(data['Tarih'].dt.hour <= selected_hours[1])]

toplam = st.checkbox('Günlük Toplam')
#%%
if toplam:
    
    ort=st.checkbox('Saatlik Ortalama')
    if ort:
        filtered_data = filtered_data.groupby([data['Tarih'].dt.date]).agg("mean")
    else:
        filtered_data = filtered_data.groupby([data['Tarih'].dt.date]).agg("sum")

    filtered_data[0:] = filtered_data[0:].astype(int)
    filtered_data = filtered_data.reset_index()
    filtered_data=filtered_data.loc[:, (filtered_data != 0).any(axis=0)]
    for fuel_type in filtered_data.columns[1:]:
        fig = go.Figure()
        fuel_data = filtered_data[['Tarih',  fuel_type]]
        if not fuel_data.empty:
            fig.add_trace(go.Bar(x=fuel_data["Tarih"], y=fuel_data[fuel_type], name=fuel_type))
            fig.update_layout(title=fuel_type, height=500, yaxis=dict(title=dict(text="MWh"),side="left") )
            fig.update_xaxes(tickformat='%Y-%m-%d')
            st.plotly_chart(fig,use_container_width=True)
    daily=filtered_data.copy()   
else:
    tabledata=filtered_data.copy()
    filtered_data=filtered_data.loc[:, (filtered_data != 0).any(axis=0)]
    for fuel_type in filtered_data.columns[1:]:
        fig = go.Figure()
        fuel_data = filtered_data[['Tarih',  fuel_type]]
        if not fuel_data.empty:
            fig.add_trace(go.Scatter(x=fuel_data['Tarih'], y=fuel_data[fuel_type], name=fuel_type,mode='lines'))
            fig.update_layout(title=fuel_type, height=500, yaxis=dict(title=dict(text="MWh"),side="left") )
            fig.update_xaxes(tickformat='%Y-%m-%d %H')
            st.plotly_chart(fig,use_container_width=True)
    daily = tabledata.groupby(filtered_data['Tarih'].dt.date).agg({"Toplam":"sum","Doğalgaz":"sum","Rüzgar":"sum","Linyit":"sum","İthal Kömür":"sum","Barajlı":"sum","Akarsu":"sum","Diğer":"sum"})
    daily = daily.reset_index()

daily=daily.loc[:, (daily != 0).any(axis=0)]
st.dataframe(daily,height=600,use_container_width=True)












































