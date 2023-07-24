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


#%%veri oku
veri=pd.read_csv('veri.csv',encoding='utf-8-sig',sep=";", decimal=",",index_col=False)
veri['date']=pd.to_datetime(veri['date'])

#%% Sayfa 1 özet dataframe

data=veri[["date","organizationShortName","toplam","dogalgaz","ruzgar","linyit","ithalKomur","barajli","mcp"]]
data.columns=["Tarih","Katılımcı","Toplam KGÜP","Doğalgaz","Rüzgar","Linyit","İthal Kömür","Barajlı","PTF"]

#%%org multi filtre

selected_organizations = st.multiselect('Organizasyon Seçiniz', data['Katılımcı'].unique())

#%%day select

selected_days = st.slider('Tarih Seçiniz', min_value=min(data['Tarih']).date(), 
                          max_value=max(data['Tarih']).date(), 
                          value=(min(data['Tarih']).date(), max(data['Tarih']).date()))

#%% hour select

selected_hours = st.slider('Saat Seçiniz', min_value=0, max_value=23, value=(0, 23))

#%% tüm filtreler

filtered_data = data[(data['Katılımcı'].isin(selected_organizations)) &
                     (data['Tarih'].dt.date >= selected_days[0]) &
                     (data['Tarih'].dt.date <= selected_days[1]) &
                     (data['Tarih'].dt.hour >= selected_hours[0]) &
                     (data['Tarih'].dt.hour <= selected_hours[1])]
tabledata=filtered_data.copy()
filtered_data=filtered_data.loc[:, (filtered_data != 0).any(axis=0)]
#%% charts

if not filtered_data.empty:
    for fuel_type in filtered_data.columns[3:-1]:
        fig, ax = plt.subplots()
        
        # Filter data for the current fuel type
        fuel_data = filtered_data[['Tarih', 'Katılımcı', fuel_type]]
        
        # Plot the data for each organization
        for org in selected_organizations:
            org_data = fuel_data[fuel_data['Katılımcı'] == org]
            ax.plot(org_data['Tarih'], org_data[fuel_type], linewidth=2, label=org)
        
        # Rotate x-axis tick labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        # Set plot labels and title
        ax.set_xlabel('Tarih')
        ax.set_ylabel('KGÜP')
        ax.set_title(f'KGÜP {fuel_type}')
        
        # Add separate legends for each organization
        ax.legend(loc='upper left')
        
        # Format x-axis as readable date values
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        
        # Display the chart
        st.pyplot(fig)


daily = None  # Initialize daily DataFrame
if not tabledata.empty:
    daily = tabledata.groupby(filtered_data['Tarih'].dt.date).agg({"Toplam KGÜP":"sum","Doğalgaz":"sum","Rüzgar":"sum","Linyit":"sum","İthal Kömür":"sum","Barajlı":"sum","PTF":"mean"})
    daily[0:] = daily[0:].astype(int)
    daily = daily.reset_index()
    daily=daily.loc[:, (daily != 0).any(axis=0)]
if daily is not None:
    st.write(daily, full_width=True)
