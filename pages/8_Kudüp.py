# -*- coding: utf-8 -*-
"""
Created on Mon Aug 28 11:02:14 2023

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
import plotly.graph_objects as go

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
    veri=pd.read_csv('fark.csv',encoding='utf-8-sig',sep=";", decimal=",",index_col=False)#C:/marketdata/  
    veri['date'] = pd.to_datetime(veri['date'])    
    veri.rename(columns = {'date':'Tarih','organizationShortName':'Katılımcı','toplam':'Toplam','dogalgaz':'Doğalgaz',
                                'linyit':'Linyit','akarsu':'Akarsu','barajli':'Barajlı','ithalKomur':'İthal Kömür',
                                'ruzgar':'Rüzgar','diger':'Diğer','mcp':'PTF','smp':'SMF'}, inplace = True)
    
    katilimci = veri['Katılımcı'].unique()
   
    return veri, katilimci

veri, katilimci = load_and_preprocess_data()

#%%
minvalue = min(veri['Tarih']).date()
maxvalue = max(veri['Tarih']).date()
selected_days = st.slider('Tarih Seçiniz', min_value=minvalue, 
                          max_value=maxvalue, 
                          value=(minvalue, maxvalue))

#%% filter

filtered_data = veri[(veri['Tarih'].dt.date >= selected_days[0]) &
                     (veri['Tarih'].dt.date <= selected_days[1])] 

#%%



charttable = pd.DataFrame()
if not filtered_data.empty:

    for org in katilimci:  
        org_data = filtered_data.loc[filtered_data["Katılımcı"]==org]
        fig = go.Figure()
        if not org_data.empty:
            fig.add_trace(go.Bar(x=org_data['Tarih'], y=org_data['Toplam'], name='KGÜP',  offset=0))
            fig.add_trace(go.Bar(x=org_data['Tarih'], y=org_data['KUDÜP Değişim'], name='KUDÜP-KGÜP', marker_color='green',  offset=0))
            fig.add_trace(go.Bar(x=org_data['Tarih'], y=org_data['Veriş Değişim'], name='Veriş-KUDÜP', marker_color='red',  offset=0))
    
            fig.update_layout(barmode='relative', title=org, height=500, width=1700)
            fig.update_xaxes(tickformat='%Y-%m-%d %H')
    
            st.plotly_chart(fig,use_container_width=True)
            print(org_data['Katılımcı'][1:2])
            print(org_data['KUDÜP Değişim'][1:2])
            print(org_data['Veriş Değişim'][1:2])
