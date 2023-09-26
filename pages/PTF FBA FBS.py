# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 09:14:30 2023

@author: mustafayarici
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
import datetime
import xlsxwriter
from io import BytesIO,StringIO
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

#%% yükle

veri= pd.read_csv('C:/marketdata/PTF.csv',encoding='utf-8-sig',sep=";", decimal=",",index_col=False)
veri['date']=pd.to_datetime(veri['date'])
veri.drop(columns = ['createIp','modifyIp','day','hour'],inplace=True)
veri.rename(columns = {'date':'Tarih'}, inplace = True)

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
if not filtered_data.empty:
    fig = go.Figure()
    if not filtered_data.empty:
        fig.add_trace(go.Bar(x=filtered_data['Tarih'], y=filtered_data['FBA']-filtered_data['FBS'], name='FBA-FBS'))
        #fig.add_trace(go.Bar(x=filtered_data['Tarih'], y=filtered_data['FBS'], name='FBS', marker_color='green'))
        
        fig.add_trace(go.Scatter(x=filtered_data['Tarih'], y=filtered_data['PTF'], name='PTF', marker_color='red', mode='lines',yaxis="y2"))#+markers

        fig.update_layout(barmode='group', title="(FBA-FBS) ve PTF", height=500, yaxis=dict(title=dict(text="MWh"),side="left"), 
                          yaxis2=dict(title=dict(text="TL/MWh"),side="right",overlaying="y"))
        fig.update_xaxes(tickformat='%Y-%m-%d %H')
        st.plotly_chart(fig,use_container_width=True)
    
    fig = go.Figure()
    if not filtered_data.empty:
        fig.add_trace(go.Bar(x=filtered_data['Tarih'], y=filtered_data['FBA'], name='FBA'))
        fig.add_trace(go.Scatter(x=filtered_data['Tarih'], y=filtered_data['YTP'], name='YTP', marker_color='red', mode='lines',yaxis="y2"))#+markers
        fig.update_layout(barmode='group', title="FBA-YTP", height=500, yaxis=dict(title=dict(text="FBA - MWh"),side="left"), 
                          yaxis2=dict(title=dict(text="YTP - MWh"),side="right",overlaying="y"))
        fig.update_xaxes(tickformat='%Y-%m-%d %H')
        st.plotly_chart(fig,use_container_width=True)
    
    fig = go.Figure()
    if not filtered_data.empty:
        fig.add_trace(go.Bar(x=filtered_data['Tarih'], y=filtered_data['FBS'], name='FBS'))
        fig.add_trace(go.Scatter(x=filtered_data['Tarih'], y=filtered_data['Ritm'], name='Ritm', marker_color='red', mode='lines',yaxis="y2"))#+markers
        fig.update_layout(barmode='group', title="FBS-Ritm", height=500, yaxis=dict(title=dict(text="FBS - MWh"),side="left"), 
                          yaxis2=dict(title=dict(text="Ritm - MWh"),side="right",overlaying="y"))
        fig.update_xaxes(tickformat='%Y-%m-%d %H')
        st.plotly_chart(fig,use_container_width=True)

    fig = go.Figure()
    if not filtered_data.empty:
        fig.add_trace(go.Bar(x=filtered_data['Tarih'], y=filtered_data['Blok Alış Eşleşme']*-1, name='Blok Alış'))
        fig.add_trace(go.Bar(x=filtered_data['Tarih'], y=filtered_data['Blok Satış Eşleşme'], name='Blok Satış',))
        fig.add_trace(go.Scatter(x=filtered_data['Tarih'], y=filtered_data['PTF'], name='PTF', marker_color='red', mode='lines',yaxis="y2"))#+markers
        fig.update_layout(barmode='relative', title="Blok", height=500,yaxis=dict(title=dict(text="MWh"),side="left"), 
                          yaxis2=dict(title=dict(text="TL/MWh"),side="right",overlaying="y",range=[0, 3000]))
        fig.update_xaxes(tickformat='%Y-%m-%d %H')
        st.plotly_chart(fig,use_container_width=True)
