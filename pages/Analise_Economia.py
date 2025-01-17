import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import gspread 
from google.cloud import secretmanager 
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
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

def criar_df_merge(df_resumo_performance_tipo_veiculo, df_resumo_performance_tipo_veiculo_base, coluna_merge):
        
    df_resumo_performance_tipo_veiculo['Km/l | Período Atual'] = round(df_resumo_performance_tipo_veiculo['Distância de abastecimento'] / df_resumo_performance_tipo_veiculo['Quantidade'], 2)
    
    df_resumo_performance_tipo_veiculo_base['Km/l | Período Base'] = round(df_resumo_performance_tipo_veiculo_base['Distância de abastecimento'] / 
                                                                           df_resumo_performance_tipo_veiculo_base['Quantidade'], 2)
    
    df_resumo_performance_tipo_veiculo_geral = pd.merge(df_resumo_performance_tipo_veiculo, df_resumo_performance_tipo_veiculo_base, on=coluna_merge, how='left')
    
    df_resumo_performance_tipo_veiculo_geral['Economia em Litros'] = round((df_resumo_performance_tipo_veiculo_geral['Distância de abastecimento_x'] / 
                                                                            df_resumo_performance_tipo_veiculo_geral['Km/l | Período Base']) - 
                                                                            df_resumo_performance_tipo_veiculo_geral['Quantidade_x'], 0)
    
    df_resumo_performance_tipo_veiculo_geral['Valor Litro'] = round(df_resumo_performance_tipo_veiculo_geral['Valor total'] / df_resumo_performance_tipo_veiculo_geral['Quantidade_x'], 2)
    
    df_resumo_performance_tipo_veiculo_geral['Economia em R$'] = df_resumo_performance_tipo_veiculo_geral['Economia em Litros'] * df_resumo_performance_tipo_veiculo_geral['Valor Litro']
    
    df_resumo_performance_tipo_veiculo_geral_colunas = df_resumo_performance_tipo_veiculo_geral[[coluna_merge, 'Km/l | Período Base', 'Km/l | Período Atual', 'Economia em Litros', 'Valor Litro', 
                                                                                                 'Economia em R$']]
    
    return df_resumo_performance_tipo_veiculo_geral_colunas

st.set_page_config(layout='wide')

if not 'id_gsheet' in st.session_state:

    st.session_state.id_gsheet = '1SGTth5faSNNtAlU_4a_ehohqHAeGUf-dsILc7qqgpms'

if not 'df_motoristas' in st.session_state:

    with st.spinner('Puxando dados do Google Drive...'):

        puxar_dados_google_drive()

st.title('Análise de Economia')

st.divider()

row0 = st.columns(2)

row1 = st.columns(2)

row2 = st.columns(1)

row3 = st.columns(2)

row4 = st.columns(2)

with row0[0]:

    atualizar_dfs_excel = st.button('Atualizar Dados Google Drive')

if atualizar_dfs_excel:

    with st.spinner('Puxando dados do Google Drive...'):

        puxar_dados_google_drive()

with row1[0]:

    st.subheader('Comparar período de:')

    data_inicial = st.date_input('Data Inicial', value=None, format='DD/MM/YYYY', key='data_inicial')

    data_final = st.date_input('Data Final', value=None, format='DD/MM/YYYY', key='data_final')

with row1[1]:

    st.subheader('Em relação à:')

    data_inicial_base = st.date_input('Data Inicial', value=None, format='DD/MM/YYYY', key='data_inicial_base')

    data_final_base = st.date_input('Data Final', value=None, format='DD/MM/YYYY', key='data_final_base')

if data_inicial and data_final and data_inicial_base and data_final_base:

    with row2[0]:

        st.divider()

    df_abastecimentos = st.session_state.df_abastecimentos.copy()

    df_abastecimentos['Apenas Data'] = df_abastecimentos['Data'].dt.date

    df_base = df_abastecimentos[(df_abastecimentos['Apenas Data']>=data_inicial_base) & (df_abastecimentos['Apenas Data']<=data_final_base)].reset_index(drop=True)
    
    df_filtro_data = df_abastecimentos[(df_abastecimentos['Apenas Data']>=data_inicial) & (df_abastecimentos['Apenas Data']<=data_final)].reset_index(drop=True)

    df_resumo_performance_tipo_veiculo = df_filtro_data.groupby('Grupo de veículo').agg({'Distância de abastecimento': 'sum', 'Quantidade': 'sum', 'Valor total': 'sum'}).reset_index()
    
    df_resumo_performance_tipo_veiculo_base = df_base.groupby('Grupo de veículo').agg({'Distância de abastecimento': 'sum', 'Quantidade': 'sum'}).reset_index()
    
    df_resumo_performance_tipo_veiculo_geral_colunas = criar_df_merge(df_resumo_performance_tipo_veiculo, df_resumo_performance_tipo_veiculo_base, 'Grupo de veículo')

    gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_tipo_veiculo_geral_colunas)
    gb.configure_selection('single')
    gb.configure_grid_options(domLayout='autoHeight')
    gridOptions = gb.build()

    with row3[0]:

        grid_response = AgGrid(df_resumo_performance_tipo_veiculo_geral_colunas, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)

    selected_rows = grid_response['selected_rows']

    if selected_rows is not None and len(selected_rows)>0:

        tipo_veiculo = selected_rows['Grupo de veículo'].iloc[0]

        if tipo_veiculo:

            df_resumo_performance_veiculo = df_filtro_data[df_filtro_data['Grupo de veículo']==tipo_veiculo].groupby('Veículo')\
                .agg({'Distância de abastecimento': 'sum', 'Quantidade': 'sum', 'Valor total': 'sum'}).reset_index()
            
            df_resumo_performance_veiculo_base = df_base[df_base['Grupo de veículo']==tipo_veiculo].groupby('Veículo').agg({'Distância de abastecimento': 'sum', 'Quantidade': 'sum'}).reset_index()
            
            df_resumo_performance_veiculo_geral_colunas = criar_df_merge(df_resumo_performance_veiculo, df_resumo_performance_veiculo_base, 'Veículo')
            
            gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_veiculo_geral_colunas)
            gb.configure_selection('single')
            gb.configure_grid_options(domLayout='autoHeight')
            gridOptions = gb.build()

            with row3[1]:

                grid_response = AgGrid(df_resumo_performance_veiculo_geral_colunas, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)
                
            selected_rows_2 = grid_response['selected_rows']

            if selected_rows_2 is not None and len(selected_rows_2)>0:

                veiculo = selected_rows_2['Veículo'].iloc[0]
                
                df_resumo_performance_motorista_veiculo = df_filtro_data[(df_filtro_data['Veículo']==veiculo) & (df_filtro_data['Grupo de veículo']==tipo_veiculo)].groupby('Colaborador')\
                    .agg({'Distância de abastecimento': 'sum', 'Quantidade': 'sum', 'Valor total': 'sum'}).reset_index()
                
                df_resumo_performance_motorista_veiculo_base = df_base[(df_base['Veículo']==veiculo) & (df_base['Grupo de veículo']==tipo_veiculo)].groupby('Colaborador')\
                    .agg({'Distância de abastecimento': 'sum', 'Quantidade': 'sum'}).reset_index()
                
                df_resumo_performance_motorista_veiculo_geral_colunas = criar_df_merge(df_resumo_performance_motorista_veiculo, df_resumo_performance_motorista_veiculo_base, 'Colaborador')

                gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista_veiculo_geral_colunas)
                gb.configure_selection('single')
                gb.configure_grid_options(domLayout='autoHeight')
                gridOptions = gb.build()

                with row3[1]:

                    grid_response = AgGrid(df_resumo_performance_motorista_veiculo_geral_colunas, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)
