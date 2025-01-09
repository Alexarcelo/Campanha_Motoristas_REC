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

    project_id = "grupoluck"
    secret_id = "cred-luck-aracaju"
    secret_client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = secret_client.access_secret_version(request={"name": secret_name})
    secret_payload = response.payload.data.decode("UTF-8")
    credentials_info = json.loads(secret_payload)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)
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

def criar_coluna_performance(df_resumo_performance):

    df_resumo_performance['Performance'] = round(df_resumo_performance['meta_batida'] / df_resumo_performance['Fornecedor'], 2)

    df_resumo_performance = df_resumo_performance.sort_values(by='Performance', ascending=False)

    df_resumo_performance['Performance'] = df_resumo_performance['Performance'].astype(float) * 100

    df_resumo_performance['Performance'] = df_resumo_performance['Performance'].apply(lambda x: f'{x:.0f}%')

    df_resumo_performance = df_resumo_performance.rename(columns={'meta_batida': 'Metas Batidas', 'Fornecedor': 'Serviços'})

    return df_resumo_performance

def montar_df_analise_mensal(df_ref, coluna_ref, info_filtro):

    df_mensal = df_ref[(df_ref[coluna_ref] == info_filtro)].groupby('ano_mes')\
        .agg({'Consumo estimado': 'count', 'meta_batida': 'sum', 'ano': 'first', 'mes': 'first', 'Colaborador': 'first'}).reset_index()

    df_mensal = df_mensal.rename(columns = {'Consumo estimado': 'serviços', 'Colaborador': 'colaborador'})

    df_mensal['performance'] = round(df_mensal['meta_batida'] / df_mensal['serviços'], 2)

    df_mensal = df_mensal.sort_values(by = ['ano', 'mes']).reset_index(drop = True)

    return df_mensal

def grafico_duas_barras_linha_percentual(referencia, eixo_x, eixo_y1, label1, eixo_y2, label2, eixo_y3, label3, 
                                          titulo):
    fig, ax1 = plt.subplots(figsize=(15, 8))

    bar_width = 0.35
    posicao_barra1 = np.arange(len(referencia[eixo_x]))
    posicao_barra2 = posicao_barra1 + bar_width

    ax1.bar(posicao_barra1, referencia[eixo_y1], width=bar_width, label=label1, edgecolor = 'black', linewidth = 1.5)

    ax1.bar(posicao_barra2, referencia[eixo_y2], width=bar_width, label=label2, edgecolor = 'black', linewidth = 1.5)

    for i in range(len(referencia[eixo_x])):
        texto1 = str(int(referencia[eixo_y1][i]))
        ax1.text(posicao_barra1[i], referencia[eixo_y1][i], texto1, ha='center', va='bottom')

    for i in range(len(referencia[eixo_x])):
        texto2 = str(int(referencia[eixo_y2][i]))
        ax1.text(posicao_barra2[i], referencia[eixo_y2][i], texto2, ha='center', va='bottom')

    ax2 = ax1.twinx()
    ax2.plot(referencia[eixo_x], referencia[eixo_y3], linestyle='-', color='black', label=label3, \
    linewidth = 0.5)

    for i in range(len(referencia[eixo_x])):
        texto = str(int(referencia[eixo_y3][i] * 100)) + "%"
        ax2.text(referencia[eixo_x][i], referencia[eixo_y3][i], texto, ha='center', va='bottom')

    # Configurações dos eixos x e legendas
    ax1.set_xticks(posicao_barra1 + bar_width / 2)
    ax1.set_xticklabels(referencia[eixo_x])
    
    ax1.set_ylim(top=max(referencia[eixo_y1]) * 3)
    ax2.set_ylim(bottom = 0, top=max(referencia[eixo_y3]) + .05)
    
    plt.title(titulo, fontsize=30)

    plt.xlabel('Ano/Mês')
    ax1.legend(loc='upper right', bbox_to_anchor=(1.2, 1))
    ax2.legend(loc='lower right', bbox_to_anchor=(1.2, 1))

    st.pyplot(fig)
    plt.close(fig)

st.set_page_config(layout='wide')

if not 'id_gsheet' in st.session_state:

    st.session_state.id_gsheet = '1SGTth5faSNNtAlU_4a_ehohqHAeGUf-dsILc7qqgpms'

if not 'df_motoristas' in st.session_state:

    with st.spinner('Puxando dados do Google Drive...'):

        puxar_dados_google_drive()

st.title('Performance Mensal Motoristas')

st.divider()

row0 = st.columns(2)

row1 = st.columns(1)

row2 = st.columns(2)

row3 = st.columns(1)

row4 = st.columns(2)

with row0[0]:

    data_atual = date.today()
    ano_atual = data_atual.year
    mes_atual = data_atual.month

    ano_analise = st.number_input('Ano', step=1, value=ano_atual, key='ano_analise')

    mes_analise = st.number_input('Mês', step=1, value=mes_atual, key='mes_analise')

with row0[1]:

    atualizar_dfs_excel = st.button('Atualizar Dados Google Drive')

if atualizar_dfs_excel:

    with st.spinner('Puxando dados do Google Drive...'):

        puxar_dados_google_drive()

if ano_analise and mes_analise:

    df_filtro_data = st.session_state.df_abastecimentos[(st.session_state.df_abastecimentos['ano']==ano_analise) & (st.session_state.df_abastecimentos['mes']==mes_analise)].reset_index(drop=True)

    with row0[0]:
    
        tipo_analise = st.radio('Tipo de Análise', ['Motorista', 'Tipo de Veículo'], index=None)

    with row1[0]:

        st.divider()

    if tipo_analise=='Tipo de Veículo':

        df_resumo_performance_tipo_veiculo = df_filtro_data.groupby('Grupo de veículo').agg({'meta_batida': 'sum', 'Fornecedor': 'count'}).reset_index()

        df_resumo_performance_tipo_veiculo = criar_coluna_performance(df_resumo_performance_tipo_veiculo)

        gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_tipo_veiculo)
        gb.configure_selection('single')
        gb.configure_grid_options(domLayout='autoHeight')
        gridOptions = gb.build()

        with row2[0]:

            grid_response = AgGrid(df_resumo_performance_tipo_veiculo, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)

        selected_rows = grid_response['selected_rows']

        if selected_rows is not None and len(selected_rows)>0:

            tipo_veiculo = selected_rows['Grupo de veículo'].iloc[0]

            df_tipo_veiculo = montar_df_analise_mensal(st.session_state.df_abastecimentos, 'Grupo de veículo', tipo_veiculo)

            with row2[1]:

                grafico_duas_barras_linha_percentual(df_tipo_veiculo, 'ano_mes', 'serviços', 'Serviços', 'meta_batida', 'Metas Batidas', 'performance', 'Performance', tipo_veiculo)
                
            with row3[0]:
                
                st.divider()

            df_resumo_performance_motorista_tipo_veiculo = df_filtro_data[df_filtro_data['Grupo de veículo']==tipo_veiculo].groupby('Veículo').agg({'meta_batida': 'sum', 'Fornecedor': 'count'})\
                .reset_index()

            df_resumo_performance_motorista_tipo_veiculo = criar_coluna_performance(df_resumo_performance_motorista_tipo_veiculo)

            gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista_tipo_veiculo)
            gb.configure_selection('single')
            gb.configure_grid_options(domLayout='autoHeight')
            gridOptions = gb.build()

            with row4[0]:

                grid_response = AgGrid(df_resumo_performance_motorista_tipo_veiculo, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)
                
            selected_rows_2 = grid_response['selected_rows']

            if selected_rows_2 is not None and len(selected_rows_2)>0:

                veiculo = selected_rows_2['Veículo'].iloc[0]

                df_veiculo = montar_df_analise_mensal(st.session_state.df_abastecimentos, 'Veículo', veiculo)

                with row4[1]:
    
                    grafico_duas_barras_linha_percentual(df_veiculo, 'ano_mes', 'serviços', 'Serviços', 'meta_batida', 'Metas Batidas', 'performance', 'Performance', veiculo)

                df_resumo_performance_motorista_veiculo = df_filtro_data[(df_filtro_data['Veículo']==veiculo) & (df_filtro_data['Grupo de veículo']==tipo_veiculo)].groupby(['Colaborador'])\
                    .agg({'meta_batida': 'sum', 'Fornecedor': 'count'}).reset_index()
                
                df_resumo_performance_motorista_veiculo = criar_coluna_performance(df_resumo_performance_motorista_veiculo)

                gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista_veiculo)
                gb.configure_selection('single')
                gb.configure_grid_options(domLayout='autoHeight')
                gridOptions = gb.build()

                with row4[0]:

                    grid_response = AgGrid(df_resumo_performance_motorista_veiculo, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)


    elif tipo_analise=='Motorista':

        df_resumo_performance_motorista = df_filtro_data.groupby('Colaborador').agg({'meta_batida': 'sum', 'Fornecedor': 'count'}).reset_index()

        df_resumo_performance_motorista = criar_coluna_performance(df_resumo_performance_motorista)

        gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista)
        gb.configure_selection('single')
        gridOptions = gb.build()

        with row2[0]:

            grid_response = AgGrid(df_resumo_performance_motorista, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)

        selected_rows = grid_response['selected_rows']

        if selected_rows is not None and len(selected_rows)>0:

            motorista = selected_rows['Colaborador'].iloc[0]

            df_motorista = montar_df_analise_mensal(st.session_state.df_abastecimentos, 'Colaborador', motorista)

            with row2[1]:

                grafico_duas_barras_linha_percentual(df_motorista, 'ano_mes', 'serviços', 'Serviços', 'meta_batida', 'Metas Batidas', 'performance', 'Performance', motorista)
                
            with row3[0]:
                
                st.divider()

            df_resumo_performance_motorista_tipo_veiculo = df_filtro_data[df_filtro_data['Colaborador']==motorista].groupby('Grupo de veículo')\
                .agg({'meta_batida': 'sum', 'Fornecedor': 'count'}).reset_index()

            df_resumo_performance_motorista_tipo_veiculo = criar_coluna_performance(df_resumo_performance_motorista_tipo_veiculo)

            gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista_tipo_veiculo)
            gb.configure_selection('single')
            gb.configure_grid_options(domLayout='autoHeight')
            gridOptions = gb.build()

            with row4[0]:

                grid_response = AgGrid(df_resumo_performance_motorista_tipo_veiculo, gridOptions=gridOptions, 
                                    enable_enterprise_modules=False, fit_columns_on_grid_load=True)
                
            selected_rows_2 = grid_response['selected_rows']

            if selected_rows_2 is not None and len(selected_rows_2)>0:

                tipo_veiculo = selected_rows_2['Grupo de veículo'].iloc[0]

                df_resumo_performance_motorista_veiculo = df_filtro_data[(df_filtro_data['Colaborador']==motorista) & (df_filtro_data['Grupo de veículo']==tipo_veiculo)].groupby(['Veículo'])\
                    .agg({'meta_batida': 'sum', 'Fornecedor': 'count'}).reset_index()
                
                df_resumo_performance_motorista_veiculo = criar_coluna_performance(df_resumo_performance_motorista_veiculo)

                gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista_veiculo)
                gb.configure_selection('single')
                gb.configure_grid_options(domLayout='autoHeight')
                gridOptions = gb.build()

                with row4[1]:

                    grid_response = AgGrid(df_resumo_performance_motorista_veiculo, gridOptions=gridOptions, enable_enterprise_modules=False, 
                                            fit_columns_on_grid_load=True)
    
