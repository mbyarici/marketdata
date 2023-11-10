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
    veri=pd.read_csv('fark.csv',encoding='utf-8-sig',sep=";", decimal=",",index_col=False) #C:/marketdata/ 
    veri['date'] = pd.to_datetime(veri['date'])    
    veri.rename(columns = {'date':'Tarih','organizationShortName':'Katılımcı','toplam':'Toplam','dogalgaz':'Doğalgaz',
                                'linyit':'Linyit','akarsu':'Akarsu','barajli':'Barajlı','ithalKomur':'İthal Kömür',
                                'ruzgar':'Rüzgar','diger':'Diğer','mcp':'PTF','smp':'SMF'}, inplace = True)
    
    katilimci = veri['Katılımcı'].unique()
   
    return veri, katilimci

veri, katilimci = load_and_preprocess_data()

#%%

selected_organizations = st.selectbox('Organizasyon Seçiniz', katilimci)


#%%week

weeks = veri['Tarih'].dt.isocalendar().week.unique()

selected_weeks = st.slider('Hafta Seçimi', min_value=int(min(weeks)), max_value=int(max(weeks)), value=(int(min(weeks)), int(max(weeks))))

veri = veri[veri['Tarih'].dt.isocalendar().week.between(selected_weeks[0], selected_weeks[1])]

#%%
minvalue = min(veri['Tarih']).date()
maxvalue = max(veri['Tarih']).date()
selected_days = st.slider('Tarih Seçiniz', min_value=minvalue, 
                          max_value=maxvalue, 
                          value=(minvalue, maxvalue))

#%% filter

filtered_data = veri[(veri['Katılımcı'] == selected_organizations) &
                     (veri['Tarih'].dt.date >= selected_days[0]) &
                     (veri['Tarih'].dt.date <= selected_days[1])] 

#%%

import plotly.graph_objects as go

KGUP = ['Toplam', 'Doğalgaz', 'Linyit', 'Barajlı', 'Akarsu', 'İthal Kömür', 'Rüzgar', 'Diğer']
KUDUPdev = ['KUDÜP Değişim', 'Gaz KUDÜP Değişim', 'Linyit KUDÜP Değişim', 'Barajlı KUDÜP Değişim', 'Akarsu KUDÜP Değişim', 'İthal Kömür KUDÜP Değişim', 'Rüzgar KUDÜP Değişim', 'Diğer KUDÜP Değişim']
Verisdev = ['Veriş Değişim', 'Gaz Veriş Değişim', 'Linyit Veriş Değişim', 'Barajlı Veriş Değişim', 'Akarsu Veriş Değişim', 'İthal Kömür Veriş Değişim', 'Rüzgar Veriş Değişim', 'Diğer Veriş Değişim']


charttable = pd.DataFrame()
if not filtered_data.empty:
    #fig = go.Figure()

    for KGUP, KUDUPdev, Verisdev in zip(KGUP, KUDUPdev, Verisdev):
        fig = go.Figure()
        if not filtered_data[KGUP].sum() == 0:
            fig.add_trace(go.Bar(x=filtered_data['Tarih'], y=filtered_data[KGUP], name='KGÜP',  offset=0))
            fig.add_trace(go.Bar(x=filtered_data['Tarih'], y=filtered_data[KUDUPdev], name='KUDÜP-KGÜP', marker_color='green',  offset=0))
            fig.add_trace(go.Bar(x=filtered_data['Tarih'], y=filtered_data[Verisdev], name='Veriş-KUDÜP', marker_color='red',  offset=0))

            fig.update_layout(barmode='relative', title=KGUP, height=500, width=1700)
            fig.update_xaxes(tickformat='%Y-%m-%d %H')

            st.plotly_chart(fig,use_container_width=True)
            charttable=pd.concat([charttable,filtered_data[KGUP],filtered_data[KUDUPdev],filtered_data[Verisdev]], axis=1)
            
    charttable.set_index(filtered_data['Tarih'], inplace=True)  # Set Date as the index
    st.dataframe(charttable, height=600, use_container_width=True)
    st.download_button(
       "İndir",
       filtered_data.to_csv(sep=";", decimal=",",index=False).encode('utf-8-sig'),
       "Kudüp.csv",
       "text/csv",
       key='download-kudüp'
    )

