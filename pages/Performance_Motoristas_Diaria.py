
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from st_aggrid import AgGrid, GridOptionsBuilder

def criar_coluna_performance(df_resumo_performance):

    df_resumo_performance['Performance'] = round(df_resumo_performance['Meta Batida'] / df_resumo_performance['Categoria Meta'], 2)

    df_resumo_performance = df_resumo_performance.sort_values(by='Performance', ascending=False)

    df_resumo_performance['Performance'] = df_resumo_performance['Performance'].astype(float) * 100

    df_resumo_performance['Performance'] = df_resumo_performance['Performance'].apply(lambda x: f'{x:.0f}%')

    df_resumo_performance = df_resumo_performance.rename(columns={'Meta Batida': 'Metas Batidas', 'Categoria Meta': 'Serviços'})

    return df_resumo_performance

def montar_df_analise_mensal(df_ref, coluna_ref, info_filtro):

    df_mensal = df_ref[(df_ref[coluna_ref] == info_filtro)].groupby('Apenas Data')\
        .agg({'Meta': 'count', 'Meta Batida': 'sum', 'ano': 'first', 'mes': 'first'}).reset_index()

    df_mensal = df_mensal.rename(columns = {'Meta': 'Serviços'})

    df_mensal['performance'] = round(df_mensal['Meta Batida'] / df_mensal['Serviços'], 2)

    df_mensal = df_mensal.sort_values(by = ['ano', 'mes']).reset_index(drop = True)

    return df_mensal

def grafico_duas_barras_linha_percentual(referencia, eixo_x, eixo_y1, label1, eixo_y2, label2, eixo_y3, label3, 
                                          titulo):
    fig, ax1 = plt.subplots(figsize=(15, 8))

    referencia[eixo_x] = pd.to_datetime(referencia[eixo_x]).dt.strftime('%d/%m/%Y')

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

def exibir_tabela(df):
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(10)
    the_table.scale(1.2, 1.2)
    for (i, j), cell in the_table.get_celld().items():
        if i == 0:  
            cell.set_facecolor('#D3D3D3')  
            cell.set_text_props(weight='bold')  
    st.pyplot(fig)
    plt.close(fig)

st.set_page_config(layout='wide')

st.title('Performance Diária Motoristas')

st.divider()

row0 = st.columns(2)

row1 = st.columns(1)

row2 = st.columns(2)

row3 = st.columns(1)

row4 = st.columns(2)

with row0[0]:

    data_inicial = st.date_input('Data Inicial', value=None, format='DD/MM/YYYY', key='data_inicial')

    data_final = st.date_input('Data Final', value=None, format='DD/MM/YYYY', key='data_final')

if data_inicial and data_final:

    df_filtro_data = st.session_state.df_servicos_abastecimentos.copy()

    df_filtro_data['Apenas Data'] = df_filtro_data['Data'].dt.date

    df_filtro_data = df_filtro_data[(df_filtro_data['Apenas Data']>=data_inicial) & (df_filtro_data['Apenas Data']<=data_final)].reset_index(drop=True)
    
    with row0[0]:
    
        tipo_analise = st.radio('Tipo de Análise', ['Motorista', 'Tipo de Veículo', 'Metas Batidas'], index=None)

    with row1[0]:

        st.divider()

    if tipo_analise=='Tipo de Veículo':

        df_resumo_performance_tipo_veiculo = df_filtro_data.groupby('Tipo de Veículo').agg({'Meta Batida': 'sum', 'Categoria Meta': 'count'}).reset_index()

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

            df_tipo_veiculo = montar_df_analise_mensal(df_filtro_data, 'Tipo de Veículo', tipo_veiculo)

            with row2[1]:

                grafico_duas_barras_linha_percentual(df_tipo_veiculo, 'Apenas Data', 'Serviços', 'Serviços', 'Meta Batida', 'Metas Batidas', 'performance', 'Performance', tipo_veiculo)
                
            with row3[0]:
                
                st.divider()

            df_resumo_performance_motorista_tipo_veiculo = df_filtro_data[df_filtro_data['Tipo de Veículo']==tipo_veiculo].groupby('Veiculo')\
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

                df_veiculo = montar_df_analise_mensal(df_filtro_data, 'Veiculo', veiculo)

                with row4[1]:
    
                    grafico_duas_barras_linha_percentual(df_veiculo, 'Apenas Data', 'Serviços', 'Serviços', 'Meta Batida', 'Metas Batidas', 'performance', 'Performance', veiculo)

                df_resumo_performance_motorista_veiculo = df_filtro_data[(df_filtro_data['Veiculo']==veiculo) & (df_filtro_data['Tipo de Veículo']==tipo_veiculo)].groupby(['Motorista'])\
                    .agg({'Meta Batida': 'sum', 'Categoria Meta': 'count'}).reset_index()
                
                df_resumo_performance_motorista_veiculo = criar_coluna_performance(df_resumo_performance_motorista_veiculo)

                gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista_veiculo)
                gb.configure_selection('single')
                gb.configure_grid_options(domLayout='autoHeight')
                gridOptions = gb.build()

                with row4[0]:

                    grid_response = AgGrid(df_resumo_performance_motorista_veiculo, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)
                            
    elif tipo_analise=='Motorista':

        df_resumo_performance_motorista = df_filtro_data.groupby('Motorista').agg({'Meta Batida': 'sum', 'Categoria Meta': 'count'}).reset_index()

        df_resumo_performance_motorista = criar_coluna_performance(df_resumo_performance_motorista)

        gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista)
        gb.configure_selection('single')
        gridOptions = gb.build()

        with row2[0]:

            grid_response = AgGrid(df_resumo_performance_motorista, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)

        selected_rows = grid_response['selected_rows']

        if selected_rows is not None and len(selected_rows)>0:

            motorista = selected_rows['Motorista'].iloc[0]

            df_motorista = montar_df_analise_mensal(df_filtro_data, 'Motorista', motorista)

            with row2[1]:

                grafico_duas_barras_linha_percentual(df_motorista, 'Apenas Data', 'Serviços', 'Serviços', 'Meta Batida', 'Metas Batidas', 'performance', 'Performance', motorista)
                
            with row3[0]:
                
                st.divider()

            df_resumo_performance_motorista_tipo_veiculo = df_filtro_data[df_filtro_data['Motorista']==motorista].groupby('Tipo de Veículo')\
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

                tipo_veiculo = selected_rows_2['Tipo de Veículo'].iloc[0]

                df_resumo_performance_motorista_veiculo = df_filtro_data[(df_filtro_data['Motorista']==motorista) & (df_filtro_data['Tipo de Veículo']==tipo_veiculo)].groupby(['Veiculo'])\
                    .agg({'Meta Batida': 'sum', 'Categoria Meta': 'count'}).reset_index()
                
                df_resumo_performance_motorista_veiculo = criar_coluna_performance(df_resumo_performance_motorista_veiculo)

                gb = GridOptionsBuilder.from_dataframe(df_resumo_performance_motorista_veiculo)
                gb.configure_selection('single')
                gb.configure_grid_options(domLayout='autoHeight')
                gridOptions = gb.build()

                with row4[1]:

                    grid_response = AgGrid(df_resumo_performance_motorista_veiculo, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)

    elif tipo_analise=='Metas Batidas':

        df_filtro_colunas = df_filtro_data[['Motorista', 'Veiculo', 'Km/Litro', 'Meta', 'Meta Batida']]

        df_filtro_colunas = df_filtro_colunas.rename(columns={'Km/Litro': 'Média Km/l', 'Meta': 'Meta Km/l', 'Meta Batida': 'Metas Batidas'})

        df_filtro_colunas['Meta Km/l'] = round(df_filtro_colunas['Meta Km/l'], 1)

        df_filtro_metas = df_filtro_colunas[df_filtro_colunas['Metas Batidas']==1][['Motorista', 'Veiculo', 'Média Km/l', 'Meta Km/l']].reset_index(drop=True)

        df_filtro_metas = df_filtro_metas.drop_duplicates()

        exibir_tabela(df_filtro_metas)
