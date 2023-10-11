# -*- coding: utf-8 -*-
"""
Created on Fri Aug 18 15:46:10 2023

@author: mustafayarici
"""

from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import xlsxwriter
from io import BytesIO,StringIO

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.set_page_config(page_title="EMBA", page_icon=":chart_with_upwards_trend:", layout="wide")

st.markdown(hide_st_style, unsafe_allow_html=True)

#%%load

@st.cache_data  # Allow caching DataFrame
def load_and_preprocess_data():
    veri=pd.read_csv('main.csv',encoding='utf-8-sig',sep=";", decimal=",",index_col=False)#C:/marketdata/
    veri['date'] = pd.to_datetime(veri['date'])
    
    kaynak=pd.DataFrame(pd.read_excel("kaynak.xlsx", 'secim', index_col=None, na_values=['NA']))
    
    data = veri[["date","organizationShortName","toplam","mcp"]]
    data.columns = ["Tarih","Katılımcı","Toplam KGÜP","PTF"]
    
    daily = data.groupby([data['Tarih'].dt.date,"Katılımcı"]).agg({"Toplam KGÜP":"mean","PTF":"mean"})
    daily = daily.reset_index()
    daily=daily.merge(kaynak[["Katılımcı","Kaynak"]], how='left',on=['Katılımcı'])
    
    kaynak = daily['Kaynak'].unique()
    katilimci = daily['Katılımcı'].unique()
    minvalue = min(data['Tarih'].dt.date)
    maxvalue = max(data['Tarih'].dt.date)


    return daily, katilimci, minvalue, maxvalue, kaynak

daily, katilimci, minvalue, maxvalue,kaynak = load_and_preprocess_data()

#%%day select
# radio button
selected_category = st.radio("Yakıt Tipi", kaynak)

selected_days = st.slider('Tarih Seçiniz', min_value=minvalue, 
                          max_value=maxvalue, 
                          value=(minvalue, maxvalue))

filtered_data = daily[(daily['Tarih'] >= selected_days[0]) &
                     (daily['Tarih'] <= selected_days[1]) & 
                     (daily['Kaynak'] == selected_category)]

katilimci=filtered_data['Katılımcı'].unique()

# Filter Data

tabledata=filtered_data.copy()
filtered_data=filtered_data.loc[:, (filtered_data != 0).any(axis=0)]

#%%

if not filtered_data.empty:
    for org in katilimci:
        fig = go.Figure()
        org_data = filtered_data.loc[filtered_data["Katılımcı"]==org]
        if not org_data.empty:
            fig.add_trace(go.Bar(x=org_data["Tarih"], y=org_data['Toplam KGÜP'], name='KGÜP'))
            
            fig.add_trace(go.Scatter(x=org_data['Tarih'], y=org_data['PTF'], name='PTF', marker_color='red', mode='lines+markers',yaxis="y2"))#+markers
    
            fig.update_layout(barmode='group', title=org, height=500, yaxis=dict(title=dict(text="MWh"),side="left"), 
                              yaxis2=dict(title=dict(text="TL/MWh"),side="right",overlaying="y"))
            fig.update_xaxes(tickformat='%Y-%m-%d')
            st.plotly_chart(fig,use_container_width=True)