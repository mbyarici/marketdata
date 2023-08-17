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

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.set_page_config( page_title="EMBA",layout="wide")

#%% yükle
result= pd.read_csv('PTF.csv',encoding='utf-8-sig',sep=";", decimal=",",index_col=False)
result['date']=pd.to_datetime(result['date'])

#%%
result['shortdate']=pd.to_datetime(result['date']).dt.strftime("%Y-%m-%d")

#%%
min_date = datetime.date(result['date'][0].year,result['date'][0].month,result['date'][0].day)
max_date = datetime.date(result['date'].iloc[-1].year,result['date'].iloc[-1].month,result['date'].iloc[-1].day)
date1 = st.date_input('Gün 1',value=min_date,min_value=min_date,max_value=max_date)
date2 = st.date_input('Gün 2',value=min_date, min_value=min_date,max_value=max_date)

date1=str(date1)
date2=str(date2)

#%%
base1=result[result['shortdate']==date2].reset_index(drop=True)
base1.drop(columns = ['date','day','hour','shortdate'],inplace=True)

base2=result[result['shortdate']==date1].reset_index(drop=True)
base2.drop(columns = ['date','day','hour','shortdate'],inplace=True)

substrc=base1-base2

#%%
summary=substrc.copy()
summary = summary[["PTF","Eşleşme", "FBS","FBA","Blok Satış Eşleşme","Blok Alış Eşleşme","YTP","Ritm"]]
summary=summary.rename(columns=lambda x: x+' Değişim')
summary.insert(0,str(date2)+" PTF",base1['PTF'].reset_index(drop=True))

st.write("Gün2 - Gün1 Farkı")
st.dataframe(summary.style.format("{:.2f}"),height=875,use_container_width=True)

#%%
def export_excel():
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine = 'xlsxwriter')
    summary.to_excel(writer, startrow = 1, merge_cells = False,header=False, index=True, sheet_name = date2)#header false -index-false
    workbook = writer.book
    worksheet = writer.sheets[date2]

    (max_row, max_col) = summary.shape
    column_settings = [{'header': column} for column in summary.columns]
    column_settings.insert(0, {'header':'Saat'})
    column_settings.insert(9, {'header':'Ritm Değişim'})
    worksheet.add_table('A1:J25', {'columns': column_settings,'autofilter': False})#
    worksheet.set_column(1, max_col - 1, 16)
    format = workbook.add_format()
    format.set_bg_color('#eeeeee')
    worksheet.set_column(0, 9, 28)
    writer.close()
    output.seek(0)
    exceldata=output.getvalue()
    return exceldata

df_xlsx = export_excel()
st.download_button(label='📥 Download Current Result',
                                data=df_xlsx ,
                                file_name= str(date2)+" "+str(date1)+' Farkı.xlsx')


