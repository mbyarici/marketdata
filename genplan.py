# -*- coding: utf-8 -*-
"""
Created on Tue May 23 17:08:22 2023

@author: mustafayarici
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
import time

veri=pd.read_csv('veri.csv',encoding='utf-8-sig',sep=";", decimal=",",index_col=False)
#%%
veri['date']=pd.to_datetime(veri['date'])
print("veri alındı")

#%%

print(veri['date'].head(5))
print(veri[['date']].dtypes)

min_date = veri['date'].dt.date.min()
max_date = veri['date'].dt.date.max()
#%%
#min_date = datetime.date(veri['date'][0].year,veri['date'][0].month,veri['date'][0].day)
#max_date = datetime.date(veri['date'].iloc[-1].year,veri['date'].iloc[-1].month,veri['date'].iloc[-1].day)
date1 = st.date_input('Gün 1',value=min_date,min_value=min_date,max_value=max_date)
date2 = st.date_input('Gün 2',value=min_date, min_value=min_date,max_value=max_date)

date1=str(date1)
date2=str(date2)
#%%

orglist = veri['organizationShortName'].drop_duplicates()

#%%

org_choice = st.sidebar.multiselect("Org:", orglist, default=None)

#%%
org_select = veri[veri['organizationShortName'].isin(org_choice)]

#%%

st.dataframe(org_select)

