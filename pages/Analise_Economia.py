import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

def criar_df_merge(df_resumo_performance_tipo_veiculo, df_resumo_performance_tipo_veiculo_base, coluna_merge):
        
    df_resumo_performance_tipo_veiculo['Km/l | Período Atual'] = round(df_resumo_performance_tipo_veiculo['Km Rodado'] / df_resumo_performance_tipo_veiculo['Litros'], 2)
    
    df_resumo_performance_tipo_veiculo_base['Km/l | Período Base'] = round(df_resumo_performance_tipo_veiculo_base['Km Rodado'] / df_resumo_performance_tipo_veiculo_base['Litros'], 2)
    
    df_resumo_performance_tipo_veiculo_geral = pd.merge(df_resumo_performance_tipo_veiculo, df_resumo_performance_tipo_veiculo_base, on=coluna_merge, how='left')
    
    df_resumo_performance_tipo_veiculo_geral['Economia em Litros'] = round((df_resumo_performance_tipo_veiculo_geral['Km Rodado_x'] / 
                                                                            df_resumo_performance_tipo_veiculo_geral['Km/l | Período Base']) - df_resumo_performance_tipo_veiculo_geral['Litros_x'], 0)
    
    df_resumo_performance_tipo_veiculo_geral['Valor Litro'] = round(df_resumo_performance_tipo_veiculo_geral['Valor Total'] / df_resumo_performance_tipo_veiculo_geral['Litros_x'], 2)
    
    df_resumo_performance_tipo_veiculo_geral['Economia em R$'] = df_resumo_performance_tipo_veiculo_geral['Economia em Litros'] * df_resumo_performance_tipo_veiculo_geral['Valor Litro']
    
    df_resumo_performance_tipo_veiculo_geral_colunas = df_resumo_performance_tipo_veiculo_geral[[coluna_merge, 'Km/l | Período Base', 'Km/l | Período Atual', 'Economia em Litros', 'Valor Litro', 
                                                                                                 'Economia em R$']]
    
    return df_resumo_performance_tipo_veiculo_geral_colunas

st.set_page_config(layout='wide')

st.title('Análise de Economia')

st.divider()

row1 = st.columns(2)

row2 = st.columns(1)

row3 = st.columns(1)

with row1[0]:

    st.subheader('Comparar período de:')

    data_inicial = st.date_input('Data Inicial', value=None, format='DD/MM/YYYY', key='data_inicial')

    data_final = st.date_input('Data Final', value=None, format='DD/MM/YYYY', key='data_final')

    st.subheader('Tipo de Análise')

    tipo_analise = st.radio('', ['Tipo de Veículo', 'Modelo'], index=None)

with row1[1]:

    st.subheader('Em relação à:')

    data_inicial_base = st.date_input('Data Inicial', value=None, format='DD/MM/YYYY', key='data_inicial_base')

    data_final_base = st.date_input('Data Final', value=None, format='DD/MM/YYYY', key='data_final_base')

if data_inicial and data_final and tipo_analise:

    with row2[0]:

        st.divider()

    df_abastecimentos = st.session_state.df_servicos_abastecimentos.copy()

    df_abastecimentos['Apenas Data'] = df_abastecimentos['Data'].dt.date
    
    df_filtro_data = df_abastecimentos[(df_abastecimentos['Apenas Data']>=data_inicial) & (df_abastecimentos['Apenas Data']<=data_final) & (df_abastecimentos['Km/Litro']>0)].reset_index(drop=True)

    df_base = df_abastecimentos[(df_abastecimentos['Apenas Data']>=data_inicial_base) & (df_abastecimentos['Apenas Data']<=data_final_base) & (df_abastecimentos['Km/Litro']>0)].reset_index(drop=True)

    df_resumo_performance_tipo_veiculo = df_filtro_data.groupby(tipo_analise).agg({'Km Rodado': 'sum', 'Litros': 'sum', 'Valor Total': 'sum'}).reset_index()
    
    df_resumo_performance_tipo_veiculo_base = df_base.groupby(tipo_analise).agg({'Km Rodado': 'sum', 'Litros': 'sum'}).reset_index()

    df_resumo_performance_tipo_veiculo_geral_colunas = criar_df_merge(df_resumo_performance_tipo_veiculo, df_resumo_performance_tipo_veiculo_base, tipo_analise)

    gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_tipo_veiculo_geral_colunas)
    gb.configure_selection('single')
    gb.configure_grid_options(domLayout='autoHeight')
    gridOptions = gb.build()

    with row3[0]:

        grid_response = AgGrid(df_resumo_performance_tipo_veiculo_geral_colunas, gridOptions=gridOptions, 
                                enable_enterprise_modules=False, fit_columns_on_grid_load=True)

    selected_rows = grid_response['selected_rows']

    if selected_rows is not None and len(selected_rows)>0:

        tipo_veiculo = selected_rows[tipo_analise].iloc[0]

        if tipo_veiculo:

            df_resumo_performance_veiculo = df_filtro_data[df_filtro_data[tipo_analise]==tipo_veiculo].groupby('Veiculo')\
                .agg({'Km Rodado': 'sum', 'Litros': 'sum', 'Valor Total': 'sum'}).reset_index()
            
            df_resumo_performance_veiculo_base = df_base[df_base[tipo_analise]==tipo_veiculo].groupby('Veiculo')\
                .agg({'Km Rodado': 'sum', 'Litros': 'sum'}).reset_index()
            
            df_resumo_performance_veiculo_geral_colunas = criar_df_merge(df_resumo_performance_veiculo, df_resumo_performance_veiculo_base, 
                                                                        'Veiculo')
            
            gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_veiculo_geral_colunas)
            gb.configure_selection('single')
            gb.configure_grid_options(domLayout='autoHeight')
            gridOptions = gb.build()

            with row3[0]:

                grid_response = AgGrid(df_resumo_performance_veiculo_geral_colunas, gridOptions=gridOptions, 
                                       enable_enterprise_modules=False, fit_columns_on_grid_load=True)
                
            selected_rows_2 = grid_response['selected_rows']

            if selected_rows_2 is not None and len(selected_rows_2)>0:

                veiculo = selected_rows_2['Veiculo'].iloc[0]
                
                df_resumo_performance_motorista_veiculo = df_filtro_data[(df_filtro_data['Veiculo']==veiculo) & 
                                                                         (df_filtro_data[tipo_analise]==tipo_veiculo)].groupby('Colaborador')\
                    .agg({'Km Rodado': 'sum', 'Litros': 'sum', 'Valor Total': 'sum'}).reset_index()
                
                df_resumo_performance_motorista_veiculo_base = df_base[(df_base['Veiculo']==veiculo) & 
                                                                              (df_base[tipo_analise]==tipo_veiculo)].groupby('Colaborador')\
                    .agg({'Km Rodado': 'sum', 'Litros': 'sum'}).reset_index()
                
                df_resumo_performance_motorista_veiculo_geral_colunas = criar_df_merge(df_resumo_performance_motorista_veiculo, 
                                                                                       df_resumo_performance_motorista_veiculo_base, 'Colaborador')

                gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista_veiculo_geral_colunas)
                gb.configure_selection('single')
                gb.configure_grid_options(domLayout='autoHeight')
                gridOptions = gb.build()

                with row3[1]:

                    grid_response = AgGrid(df_resumo_performance_motorista_veiculo_geral_colunas, gridOptions=gridOptions, enable_enterprise_modules=False, 
                                            fit_columns_on_grid_load=True)
