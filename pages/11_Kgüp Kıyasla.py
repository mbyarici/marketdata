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

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.set_page_config(page_title="EMBA", page_icon=":chart_with_upwards_trend:", layout="centered")

st.markdown(hide_st_style, unsafe_allow_html=True)

#%%veri

veri=pd.read_csv('main.csv',encoding='utf-8-sig',sep=";", decimal=",",index_col=False)
veri['date']=pd.to_datetime(veri['date'])

#%% data

data=veri[["date","organizationShortName","dogalgaz","ruzgar","linyit","ithalKomur","barajli"]]
data.columns=["Tarih","Katılımcı","Doğalgaz","Rüzgar","Linyit","İthal Kömür","Barajlı"]

#%%filter

selected_organization = st.selectbox('Organizasyon Seçimi', data['Katılımcı'].unique())
selected_day1 = st.date_input('Gün 1 Seçimi', key="day1", min_value=min(data['Tarih']).date(),
                             max_value=max(data['Tarih']).date(),
                             value=min(data['Tarih']).date())
selected_day2 = st.date_input('Gün 2 Seçimi', key="day2", min_value=min(data['Tarih']).date(),
                             max_value=max(data['Tarih']).date(),
                             value=max(data['Tarih']).date())

#%% filter

# Filter data Day 1
data_day1 = data[(data['Katılımcı'] == selected_organization) & (data['Tarih'].dt.date == selected_day1)]

# Filter data Day 2
data_day2 = data[(data['Katılımcı'] == selected_organization) & (data['Tarih'].dt.date == selected_day2)]

# Filter data days and organization
data_all = data[(data['Katılımcı'] == selected_organization) &
                ((data['Tarih'].dt.date == selected_day1) | (data['Tarih'].dt.date == selected_day2))]

# Combine 
data_combined = pd.concat([data_day1, data_day2])

# Convert datetime format
data_combined['Tarih'] = pd.to_datetime(data_combined['Tarih'])

# Sort hour then the date
data_combined = data_combined.sort_values(by=['Tarih', 'Katılımcı'])

# unique hours
hours = data_combined['Tarih'].dt.hour.unique()

#%% 
# set colors
def get_colors():
    return ['blue', 'red']
# Get color
colors = get_colors()

# Create a mapping between days and their corresponding colors
day_color_mapping = dict(zip([selected_day1, selected_day2], colors))


#%%chart
non_zero_fuel_types = []
for fuel_type in data_combined.columns[2:]:
    non_zero_values_day1 = data_combined[(data_combined['Tarih'].dt.date == selected_day1) & (data_combined[fuel_type] != 0)]
    non_zero_values_day2 = data_combined[(data_combined['Tarih'].dt.date == selected_day2) & (data_combined[fuel_type] != 0)]
    if len(non_zero_values_day1) > 0 or len(non_zero_values_day2) > 0:
        non_zero_fuel_types.append(fuel_type)

# Create a figure and axis
if len(non_zero_fuel_types) > 1:
    fig, axes = plt.subplots(len(non_zero_fuel_types), 1, figsize=(10, 5 * len(non_zero_fuel_types)))
else:
    fig, ax = plt.subplots(figsize=(10, 6))
    axes = [ax]

# Plot the bars
for i, fuel_type in enumerate(non_zero_fuel_types):
    ax = axes[i]

    for day in [selected_day1, selected_day2]:
        data_day = data_combined[data_combined['Tarih'].dt.date == day]
        data_day = data_day.sort_values(by='Tarih')

        x_offset = np.arange(len(hours)) - 0.2 + (day_color_mapping[day] == 'red') * 0.4
        ax.bar(x_offset, data_day[fuel_type], width=0.4, label=f'{fuel_type} - Gün {day.day}', color=day_color_mapping[day])

    ax.set_xticks(np.arange(len(hours)))
    ax.set_xticklabels(hours)
    ax.set_xlabel('Saatler')
    ax.set_ylabel('KGÜP MWh')
    ax.set_title(f'{fuel_type} Seçilen Günler Saatlik Üretim Karşılaştırması')
    ax.legend(title='Yakıt Tipi', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=0, ha='right')
    plt.tight_layout()

# Display
st.pyplot(fig)



