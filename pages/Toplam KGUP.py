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
import numpy as np


st.markdown('<link rel="stylesheet" href="styles.css">', unsafe_allow_html=True)
st.set_page_config(layout="centered")
#%%veri
kgupsum=pd.read_csv('genel.csv',encoding='utf-8-sig',sep=";", decimal=",",index_col=False)
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

selected_hours = st.slider('Saat Seçiniz', min_value=0, max_value=23, value=(0, 23))

#%% filter

filtered_data = data[(data['Tarih'].dt.date >= selected_days[0]) &
                     (data['Tarih'].dt.date <= selected_days[1]) &
                     (data['Tarih'].dt.hour >= selected_hours[0]) &
                     (data['Tarih'].dt.hour <= selected_hours[1])]
tabledata=filtered_data.copy()
filtered_data=filtered_data.loc[:, (filtered_data != 0).any(axis=0)]
#%% charts

for fuel_type in filtered_data.columns[1:]:
    fig, ax = plt.subplots()
    
    # Filter data
    fuel_data = filtered_data[['Tarih',  fuel_type]]
    ax.plot(fuel_data['Tarih'], fuel_data[fuel_type], linewidth=2, label=fuel_type)

    
    # better readability
    plt.xticks(rotation=45, ha='right')
    
    # Set plot labels and title
    ax.set_xlabel('Tarih')
    ax.set_ylabel('KGÜP')
    ax.set_title(f'{fuel_type} KGÜP')
    
    # separate legends
    ax.legend(loc='upper left')
    
    # Format
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    
    # Display
    st.pyplot(fig)

daily = tabledata.groupby(filtered_data['Tarih'].dt.date).agg({"Toplam":"sum","Doğalgaz":"sum","Rüzgar":"sum","Linyit":"sum","İthal Kömür":"sum","Barajlı":"sum","Akarsu":"sum","Diğer":"sum"})
daily[0:] = daily[0:].astype(int)
daily = daily.reset_index()
daily=daily.loc[:, (daily != 0).any(axis=0)]

st.dataframe(daily,height=600,use_container_width=True)
