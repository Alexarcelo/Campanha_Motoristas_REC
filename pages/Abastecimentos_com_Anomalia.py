import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from st_aggrid import AgGrid, GridOptionsBuilder
import gspread 
from google.cloud import secretmanager 
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from datetime import date
import json

def puxar_aba_simples(id_gsheet, nome_aba, nome_df):

    nome_credencial = st.secrets["CREDENCIAL_SHEETS"]
    credentials = service_account.Credentials.from_service_account_info(nome_credencial)
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = credentials.with_scopes(scope)
    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(id_gsheet)
    
    sheet = spreadsheet.worksheet(nome_aba)

    sheet_data = sheet.get_all_values()

    st.session_state[nome_df] = pd.DataFrame(sheet_data[1:], columns=sheet_data[0])

def transformar_coluna_em_numerica(df, coluna):

    df[coluna] = df[coluna].str.replace(',', '.')

    df[coluna] = pd.to_numeric(df[coluna], errors='coerce')

    return df

def ajustar_coluna_em_real(df, coluna):

    df[coluna] = df[coluna].str.replace('R$ ', '')

    df[coluna] = df[coluna].str.replace('.', '')

    df[coluna] = df[coluna].str.replace(',', '.')

    df[coluna] = pd.to_numeric(df[coluna], errors='coerce')

    return df

def tratar_colunas_df_abastecimentos():

    lista_colunas_numericas = ['Consumo real', 'Consumo estimado', 'Quantidade', 'Distância de abastecimento']

    for coluna in lista_colunas_numericas:

        st.session_state.df_abastecimentos = transformar_coluna_em_numerica(st.session_state.df_abastecimentos, coluna)

    lista_colunas_real = ['Valor unitário', 'Valor total']

    for coluna in lista_colunas_real:

        st.session_state.df_abastecimentos = ajustar_coluna_em_real(st.session_state.df_abastecimentos, coluna)

    st.session_state.df_abastecimentos['Veículo'] = st.session_state.df_abastecimentos['Veículo'].astype(str)

    st.session_state.df_abastecimentos = st.session_state.df_abastecimentos[st.session_state.df_abastecimentos['Veículo']!='Total'].reset_index(drop=True)

    st.session_state.df_abastecimentos['Data'] = pd.to_datetime(st.session_state.df_abastecimentos['Data'], format='%d/%m/%Y %H:%M:%S')

    st.session_state.df_abastecimentos['ano'] = st.session_state.df_abastecimentos['Data'].dt.year

    st.session_state.df_abastecimentos['mes'] = st.session_state.df_abastecimentos['Data'].dt.month

    for index in range(len(st.session_state.df_abastecimentos)):

        if st.session_state.df_abastecimentos.at[index, 'Veículo']=='':

            st.session_state.df_abastecimentos.at[index, 'Veículo']=st.session_state.df_abastecimentos.at[index-1, 'Veículo']

    st.session_state.df_abastecimentos['ano_mes'] = st.session_state.df_abastecimentos['mes'].astype(str) + '/' + st.session_state.df_abastecimentos['ano'].astype(str).str[-2:]

    st.session_state.df_abastecimentos['meta_batida'] = st.session_state.df_abastecimentos.apply(lambda row: 1 if row['Consumo real'] >= row['Consumo estimado'] else 0, axis = 1)

    lista_motoristas_historico = st.session_state.df_abastecimentos['Colaborador'].unique().tolist()

    for motorista in lista_motoristas_historico:

        if motorista in st.session_state.df_motoristas['Motorista Sofit'].unique().tolist():

            st.session_state.df_abastecimentos.loc[st.session_state.df_abastecimentos['Colaborador']==motorista, 'Colaborador']=\
                st.session_state.df_motoristas.loc[st.session_state.df_motoristas['Motorista Sofit']==motorista, 'Motorista Análise'].values[0]

def puxar_dados_google_drive():

    puxar_aba_simples(st.session_state.id_gsheet, 'Motoristas', 'df_motoristas')

    puxar_aba_simples(st.session_state.id_gsheet, 'Abastecimentos Sofit', 'df_abastecimentos')

    tratar_colunas_df_abastecimentos()

st.set_page_config(layout='wide')

if not 'id_gsheet' in st.session_state:

    st.session_state.id_gsheet = '1SGTth5faSNNtAlU_4a_ehohqHAeGUf-dsILc7qqgpms'

if not 'df_motoristas' in st.session_state:

    with st.spinner('Puxando dados do Google Drive...'):

        puxar_dados_google_drive()

st.title('Abastecimentos com Anomalias')

st.divider()

row0 = st.columns(1)

with row0[0]:

    atualizar_dfs_excel = st.button('Atualizar Dados Google Drive')

    percentual_anomalias = st.number_input('Variação Percentual p/ Anomalia', step=1, value=30)

    percentual_anomalias = percentual_anomalias/100

if atualizar_dfs_excel:

    with st.spinner('Puxando dados do Google Drive...'):

        puxar_dados_google_drive()

df_filtro_colunas = st.session_state.df_abastecimentos.copy()

df_filtro_colunas['Percentual do Estimado'] = round(df_filtro_colunas['Consumo real']/df_filtro_colunas['Consumo estimado']-1, 2)

df_filtro_colunas = df_filtro_colunas[['Data', 'Nome', 'Veículo', 'Consumo real', 'Consumo estimado', 'Percentual do Estimado']]

df_filtro_colunas.loc[(df_filtro_colunas['Percentual do Estimado'] > percentual_anomalias) | (df_filtro_colunas['Percentual do Estimado'] < -percentual_anomalias), 'Anomalia']='X'

df_filtro_colunas = df_filtro_colunas[df_filtro_colunas['Anomalia']=='X'].reset_index(drop=True)

df_filtro_colunas = df_filtro_colunas.rename(columns={'Consumo real': 'Média km/l', 'Consumo estimado': 'Meta km/l', 'Nome': 'Despesa'})

container_dataframe = st.container()

container_dataframe.dataframe(df_filtro_colunas[['Data', 'Despesa', 'Veículo', 'Média km/l', 'Meta km/l']], hide_index=True, use_container_width=True)
