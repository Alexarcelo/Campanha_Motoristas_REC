import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import date

def criar_coluna_performance(df_resumo_performance):

    df_resumo_performance['Performance'] = round(df_resumo_performance['Meta Batida'] / df_resumo_performance['Categoria Meta'], 2)

    df_resumo_performance = df_resumo_performance.sort_values(by='Performance', ascending=False)

    df_resumo_performance['Performance'] = df_resumo_performance['Performance'].astype(float) * 100

    df_resumo_performance['Performance'] = df_resumo_performance['Performance'].apply(lambda x: f'{x:.0f}%')

    df_resumo_performance = df_resumo_performance.rename(columns={'Meta Batida': 'Metas Batidas', 'Categoria Meta': 'Serviços'})

    return df_resumo_performance

def montar_df_analise_mensal(df_ref, coluna_ref, info_filtro):

    df_mensal = df_ref[(df_ref[coluna_ref] == info_filtro)].groupby('ano_mes')\
        .agg({'Meta': 'count', 'Meta Batida': 'sum', 'ano': 'first', 'mes': 'first'}).reset_index()

    df_mensal = df_mensal.rename(columns = {'Meta': 'Serviços'})

    df_mensal['performance'] = round(df_mensal['Meta Batida'] / df_mensal['Serviços'], 2)

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

def verificar_servicos_sem_categoria(df_escalas_group):

    df_servicos_sem_categoria_meta = pd.DataFrame(data=df_escalas_group[(pd.isna(df_escalas_group['Categoria Meta'])) | (df_escalas_group['Categoria Meta']=='')]['Servico'].unique(), 
                                                  columns=['Serviços'])

    if len(df_servicos_sem_categoria_meta)>0:

        st.error('Os serviços abaixo não possuem categoria de meta cadastrada. Por favor, cadastre e tente novamente')

        st.dataframe(df_servicos_sem_categoria_meta, hide_index=True)

        st.stop()

def verificar_veiculos_sem_meta(df_escalas_group):

    df_veiculos_sem_meta_categoria = df_escalas_group[pd.isna(df_escalas_group['Meta'])][['Placa', 'Categoria Meta']].drop_duplicates()

    if len(df_veiculos_sem_meta_categoria)>0:

        st.error('Os veículos abaixo não tem meta cadastrada para as categorias descritas ao lado. Cadastre e tente novamente')

        st.dataframe(df_veiculos_sem_meta_categoria, hide_index=True)

        st.stop()

st.set_page_config(layout='wide')

st.title('Performance Mensal Motoristas')

st.divider()

row0 = st.columns(2)

row1 = st.columns(1)

row2 = st.columns(2)

row3 = st.columns(1)

row4 = st.columns(2)

# Ano e Mês de análise

with row0[0]:

    data_atual = date.today()
    ano_atual = data_atual.year
    mes_atual = data_atual.month

    ano_analise = st.number_input('Ano', step=1, value=ano_atual, key='ano_analise')

    mes_analise = st.number_input('Mês', step=1, value=mes_atual, key='mes_analise')

if 'df_servicos_abastecimentos' in st.session_state:

    with row0[0]:

        tipo_analise = st.radio('Tipo de Análise', ['Motorista', 'Tipo de Veículo'], index=None)

    with row1[0]:

        st.divider()

    if tipo_analise=='Tipo de Veículo':

        df_resumo_performance_tipo_veiculo = st.session_state.df_servicos_abastecimentos.groupby('Tipo de Veículo').agg({'Meta Batida': 'sum', 'Categoria Meta': 'count'}).reset_index()

        df_resumo_performance_tipo_veiculo = criar_coluna_performance(df_resumo_performance_tipo_veiculo)

        gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_tipo_veiculo)
        gb.configure_selection('single')
        gb.configure_grid_options(domLayout='autoHeight')
        gridOptions = gb.build()

        with row2[0]:

            grid_response = AgGrid(df_resumo_performance_tipo_veiculo, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)

        selected_rows = grid_response['selected_rows']

        if selected_rows is not None and len(selected_rows)>0:

            tipo_veiculo = selected_rows['Tipo de Veículo'].iloc[0]

            df_tipo_veiculo = montar_df_analise_mensal(st.session_state.df_servicos_abastecimentos, 'Tipo de Veículo', tipo_veiculo)

            with row2[1]:

                grafico_duas_barras_linha_percentual(df_tipo_veiculo, 'ano_mes', 'Serviços', 'Serviços', 'Meta Batida', 'Metas Batidas', 'performance', 'Performance', tipo_veiculo)
                
            with row3[0]:
                
                st.divider()

            df_resumo_performance_motorista_tipo_veiculo = st.session_state.df_servicos_abastecimentos[st.session_state.df_servicos_abastecimentos['Tipo de Veículo']==tipo_veiculo].groupby('Veiculo')\
                .agg({'Meta Batida': 'sum', 'Categoria Meta': 'count'}).reset_index()

            df_resumo_performance_motorista_tipo_veiculo = criar_coluna_performance(df_resumo_performance_motorista_tipo_veiculo)

            gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista_tipo_veiculo)
            gb.configure_selection('single')
            gb.configure_grid_options(domLayout='autoHeight')
            gridOptions = gb.build()

            with row4[0]:

                grid_response = AgGrid(df_resumo_performance_motorista_tipo_veiculo, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)
                
            selected_rows_2 = grid_response['selected_rows']

            if selected_rows_2 is not None and len(selected_rows_2)>0:

                veiculo = selected_rows_2['Veiculo'].iloc[0]

                df_veiculo = montar_df_analise_mensal(st.session_state.df_servicos_abastecimentos, 'Veiculo', veiculo)

                with row4[1]:

                    grafico_duas_barras_linha_percentual(df_veiculo, 'ano_mes', 'Serviços', 'Serviços', 'Meta Batida', 'Metas Batidas', 'performance', 'Performance', veiculo)

                df_resumo_performance_motorista_veiculo = st.session_state.df_servicos_abastecimentos[(st.session_state.df_servicos_abastecimentos['Veiculo']==veiculo)]\
                    .groupby(['Motorista']).agg({'Meta Batida': 'sum', 'Categoria Meta': 'count'}).reset_index()
                
                df_resumo_performance_motorista_veiculo = criar_coluna_performance(df_resumo_performance_motorista_veiculo)

                gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista_veiculo)
                gb.configure_selection('single')
                gb.configure_grid_options(domLayout='autoHeight')
                gridOptions = gb.build()

                with row4[1]:

                    grid_response = AgGrid(df_resumo_performance_motorista_veiculo, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)

    elif tipo_analise=='Motorista':

        df_resumo_performance_motorista = st.session_state.df_servicos_abastecimentos.groupby('Motorista').agg({'Meta Batida': 'sum', 'Categoria Meta': 'count'}).reset_index()

        df_resumo_performance_motorista = criar_coluna_performance(df_resumo_performance_motorista)

        gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista)
        gb.configure_selection('single')
        gridOptions = gb.build()

        with row2[0]:

            grid_response = AgGrid(df_resumo_performance_motorista, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)

        selected_rows = grid_response['selected_rows']

        if selected_rows is not None and len(selected_rows)>0:

            motorista = selected_rows['Motorista'].iloc[0]

            df_motorista = montar_df_analise_mensal(st.session_state.df_servicos_abastecimentos, 'Motorista', motorista)

            with row2[1]:

                grafico_duas_barras_linha_percentual(df_motorista, 'ano_mes', 'Serviços', 'Serviços', 'Meta Batida', 'Metas Batidas', 'performance', 'Performance', motorista)
                
            with row3[0]:
                
                st.divider()

            df_resumo_performance_motorista_tipo_veiculo = st.session_state.df_servicos_abastecimentos[st.session_state.df_servicos_abastecimentos['Motorista']==motorista].groupby('Tipo de Veículo')\
                .agg({'Meta Batida': 'sum', 'Categoria Meta': 'count'}).reset_index()

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

                tipo_veiculo = selected_rows_2['Tipo de Veículo'].iloc[0]

                df_resumo_performance_motorista_veiculo = \
                    st.session_state.df_servicos_abastecimentos[(st.session_state.df_servicos_abastecimentos['Motorista']==motorista) & 
                                                                (st.session_state.df_servicos_abastecimentos['Tipo de Veículo']==tipo_veiculo)].groupby(['Veiculo'])\
                                                                    .agg({'Meta Batida': 'sum', 'Categoria Meta': 'count'}).reset_index()
                
                df_resumo_performance_motorista_veiculo = criar_coluna_performance(df_resumo_performance_motorista_veiculo)

                gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista_veiculo)
                gb.configure_selection('single')
                gb.configure_grid_options(domLayout='autoHeight')
                gridOptions = gb.build()

                with row4[1]:

                    grid_response = AgGrid(df_resumo_performance_motorista_veiculo, gridOptions=gridOptions, enable_enterprise_modules=False, 
                                            fit_columns_on_grid_load=True)
    
else:

    st.error('Precisa gerar um relatório na aba Gerar Relatório')
