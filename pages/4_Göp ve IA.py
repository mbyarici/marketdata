# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 08:26:20 2023

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

@st.cache_data
def load_and_preprocess_data():
    veri=pd.read_csv('piyasa.csv',encoding='utf-8-sig',sep=";", decimal=",",index_col=False)  #C:/marketdata/
    veri['date'] = pd.to_datetime(veri['date'])
    veri=veri.fillna(0)
    veri[["SAM","İAAlış"]]=veri[["SAM","İAAlış"]]*-1
    veri.rename(columns = {'date':'Tarih','organizationShortName':'Katılımcı','SAM':'GÖP Alış','SSM':'GÖP Satış',
                                'İAAlış':'İA Alış','İASatış':'İA Satış'}, inplace = True)
    

    katilimci = veri['Katılımcı'].unique()
    minvalue = min(veri['Tarih'].dt.date)
    maxvalue = max(veri['Tarih'].dt.date)
   
    return veri, katilimci,minvalue,maxvalue

veri, katilimci, minvalue, maxvalue = load_and_preprocess_data()

#%%
minvalue = min(veri['Tarih']).date()
maxvalue = max(veri['Tarih']).date()
selected_days = st.slider('Tarih Seçiniz', min_value=minvalue, 
                          max_value=maxvalue, 
                          value=(maxvalue-timedelta(days=35), maxvalue))

#%% filter

filtered_data = veri[(veri['Tarih'].dt.date >= selected_days[0]) &
                     (veri['Tarih'].dt.date <= selected_days[1])] #(veri['Katılımcı'] == selected_organizations) &

#%%

filtered_data['Tarih'] = pd.to_datetime(filtered_data['Tarih'])

numeric_columns = ['GÖP Alış', 'GÖP Satış', 'İA Alış', 'İA Satış']
custom_colors = ['rgb(255, 0, 0)',  # Red
                 'rgb(0, 255, 0)',  # Green
                 'rgb(255, 255, 0)',  # Blue
                 'rgb(0, 0, 255)',]  # Yellow
if not filtered_data.empty:
    
    

    for org in katilimci:
        
        org_data = filtered_data.loc[filtered_data["Katılımcı"]==org]
        
        fig = go.Figure()
        for index,col in enumerate(numeric_columns):
            
            fig.add_trace(go.Bar(x=org_data['Tarih'], y=org_data[col], name=col, marker_color=custom_colors[index]))
    
        fig.update_layout(barmode='relative', title=org,height=400, width=1000)
        fig.update_xaxes(tickformat='%Y-%m-%d %H:%M:%S')
        # Display
        st.plotly_chart(fig,use_container_width=True)    


