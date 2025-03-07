import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

def gerar_df_grid(df, colunas_rename, colunas_df_grid):

    df['Valor/Litro'] = df['Valor Total'] / df['Litros']

    df['Valor Meta'] = df['Litros Consumidos Meta'] * df['Valor/Litro']

    df['Valor Economia'] = df['Valor Meta'] - df['Valor Total']

    df['Economia'] = df.apply(lambda row: f"Economia de R${round(row['Valor Meta'] - row['Valor Total'], 2)}" if row['Valor Meta']>=row['Valor Total'] else 
                              f"Prejuízo de R${round(row['Valor Total'] - row['Valor Meta'], 2)}", axis=1)
    
    df = df.rename(columns=colunas_rename)

    df = df.sort_values(by='Valor Economia', ascending=False).reset_index(drop=True)

    df_geral_colunas = df[colunas_df_grid]

    return df_geral_colunas

st.set_page_config(layout='wide')

st.title('Ranking - Conta Corrente')

st.divider()

row1 = st.columns(2)

row2 = st.columns(1)

row3 = st.columns(2)

with row1[0]:

    st.subheader('Período:')

    data_inicial = st.date_input('Data Inicial', value=None, format='DD/MM/YYYY', key='data_inicial')

    data_final = st.date_input('Data Final', value=None, format='DD/MM/YYYY', key='data_final')

with row1[1]:

    st.subheader('Tipo de Análise')

    tipo_analise = st.radio('', ['Motorista', 'Tipo de Veículo', 'Modelo'], index=None)

if data_inicial and data_final and tipo_analise:

    with row2[0]:

        st.divider()

    df_abastecimentos = st.session_state.df_servicos_abastecimentos.copy()

    df_abastecimentos['Apenas Data'] = df_abastecimentos['Data'].dt.date
    
    df_filtro_data = df_abastecimentos[(df_abastecimentos['Apenas Data']>=data_inicial) & (df_abastecimentos['Apenas Data']<=data_final) & (df_abastecimentos['Km/Litro']>0)].reset_index(drop=True)

    df_filtro_data['Litros Consumidos Meta'] = df_filtro_data.apply(lambda row: round(row['Km Rodado']/row['Meta'], 2), axis=1)

    if tipo_analise=='Motorista':

        with row1[0]:

            filtrar_grupo = st.multiselect('Grupo', sorted(df_filtro_data['Grupo Motorista'].unique()), default=None)

        if len(filtrar_grupo)>0:

            df_filtro_data = df_filtro_data[df_filtro_data['Grupo Motorista'].isin(filtrar_grupo)].reset_index(drop=True)

            df_resumo_performance_motorista = df_filtro_data.groupby(['Motorista', 'Grupo Motorista']).agg({'Km Rodado': 'sum', 'Litros': 'sum', 'Litros Consumidos Meta': 'sum', 'Valor Total': 'sum'})\
                .reset_index()
            
            df_resumo_performance_motorista_geral_colunas = gerar_df_grid(df_resumo_performance_motorista, {'Litros': 'Litros Consumidos Real'}, 
                                                                        ['Motorista', 'Grupo Motorista', 'Km Rodado', 'Litros Consumidos Real', 'Litros Consumidos Meta', 'Economia'])
            
        else:

            df_resumo_performance_motorista = df_filtro_data.groupby('Motorista').agg({'Km Rodado': 'sum', 'Litros': 'sum', 'Litros Consumidos Meta': 'sum', 'Valor Total': 'sum'}).reset_index()

            df_resumo_performance_motorista_geral_colunas = gerar_df_grid(df_resumo_performance_motorista, {'Litros': 'Litros Consumidos Real'}, 
                                                                        ['Motorista', 'Km Rodado', 'Litros Consumidos Real', 'Litros Consumidos Meta', 'Economia'])
        
        container_dataframe = st.container()

        container_dataframe.dataframe(df_resumo_performance_motorista_geral_colunas, hide_index=True, use_container_width=True)

    elif tipo_analise=='Tipo de Veículo':

        df_resumo_performance_tp_veiculo = df_filtro_data.groupby(['Tipo de Veículo']).agg({'Km Rodado': 'sum', 'Litros': 'sum', 'Litros Consumidos Meta': 'sum', 'Valor Total': 'sum'})\
            .reset_index()
        
        df_resumo_performance_tp_veiculo_geral_colunas = gerar_df_grid(df_resumo_performance_tp_veiculo, {'Litros': 'Litros Consumidos Real'}, 
                                                                       ['Tipo de Veículo', 'Km Rodado', 'Litros Consumidos Real', 'Litros Consumidos Meta', 'Economia'])
        
        container_dataframe = st.container()

        container_dataframe.dataframe(df_resumo_performance_tp_veiculo_geral_colunas, hide_index=True, use_container_width=True)

    elif tipo_analise=='Modelo':

        df_resumo_performance_tp_veiculo = df_filtro_data.groupby(['Modelo']).agg({'Km Rodado': 'sum', 'Litros': 'sum', 'Litros Consumidos Meta': 'sum', 'Valor Total': 'sum'})\
            .reset_index()
        
        df_resumo_performance_tp_veiculo_geral_colunas = gerar_df_grid(df_resumo_performance_tp_veiculo, {'Litros': 'Litros Consumidos Real'}, 
                                                                       ['Modelo', 'Km Rodado', 'Litros Consumidos Real', 'Litros Consumidos Meta', 'Economia'])
        
        container_dataframe = st.container()

        container_dataframe.dataframe(df_resumo_performance_tp_veiculo_geral_colunas, hide_index=True, use_container_width=True)

