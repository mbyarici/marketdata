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
from datetime import timedelta

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.set_page_config(page_title="EMBA", page_icon=":chart_with_upwards_trend:", layout="wide")

st.markdown(hide_st_style, unsafe_allow_html=True)



#%% veri yükle

@st.cache_data  # Allow caching DataFrame
def load_and_preprocess_data():
    veri=pd.read_csv('main.csv',encoding='utf-8-sig',sep=";", decimal=",",index_col=False)#C:/marketdata/
    veri['date'] = pd.to_datetime(veri['date'])
    
    data = veri[["date","organizationShortName","toplam","dogalgaz","ruzgar","linyit","ithalKomur","barajli","mcp"]]
    data.columns = ["Tarih","Katılımcı","Toplam KGÜP","Doğalgaz","Rüzgar","Linyit","İthal Kömür","Barajlı","PTF"]
    
    katilimci = data['Katılımcı'].unique()
    minvalue = min(data['Tarih']).date()
    maxvalue = max(data['Tarih']).date()
    
    return data, katilimci, minvalue, maxvalue

data, katilimci, minvalue, maxvalue = load_and_preprocess_data()

#%%
selected_organizations = st.multiselect('Organizasyon Seçiniz', katilimci)

#%%day select

selected_days = st.slider('Tarih Seçiniz', min_value=minvalue, 
                          max_value=maxvalue, 
                          value=(maxvalue-timedelta(days=35), maxvalue))

#%% hour select

selected_hours = st.slider('Saat Seçiniz', min_value=0, max_value=23, value=(0, 23))

#%% filter

filtered_data = data[(data['Katılımcı'].isin(selected_organizations)) &
                     (data['Tarih'].dt.date >= selected_days[0]) &
                     (data['Tarih'].dt.date <= selected_days[1]) &
                     (data['Tarih'].dt.hour >= selected_hours[0]) &
                     (data['Tarih'].dt.hour <= selected_hours[1])]

tabledata=filtered_data.copy()
filtered_data=filtered_data.loc[:, (filtered_data != 0).any(axis=0)]

#%%chart
if not filtered_data.empty:
    for fuel_type in filtered_data.columns[3:-1]:
        fig = go.Figure()
        fuel_data = filtered_data[['Tarih', 'Katılımcı', fuel_type]]
        if not fuel_data.empty:
            for org in selected_organizations:
                org_data = fuel_data[fuel_data['Katılımcı'] == org]
    
                fig.add_trace(go.Scatter(x=org_data['Tarih'], y=org_data[fuel_type], name=fuel_type,mode='lines'))
        
                fig.update_layout(title=fuel_type, height=500, yaxis=dict(title=dict(text="MWh"),side="left") )
                
                fig.update_xaxes(tickformat='%Y-%m-%d %H')
                st.plotly_chart(fig,use_container_width=True)

daily = None
if not tabledata.empty:
    daily = tabledata.groupby(filtered_data['Tarih'].dt.date).agg({"Toplam KGÜP":"sum","Doğalgaz":"sum","Rüzgar":"sum","Linyit":"sum","İthal Kömür":"sum","Barajlı":"sum","PTF":"mean"})
    daily[0:] = daily[0:].astype(int)
    daily = daily.reset_index()
    daily=daily.loc[:, (daily != 0).any(axis=0)]
if daily is not None:
    st.dataframe(daily,height=600,use_container_width=True)

st.download_button(
   "Veri İndir",
   filtered_data.to_csv(sep=";", decimal=",",index=False).encode('utf-8-sig'),
   "Saatlik KGUP.csv",
   "text/csv",
   key='download-KGUP'
)