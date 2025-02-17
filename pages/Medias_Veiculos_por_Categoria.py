import streamlit as st

def mostrar_resultados(titulo, df_servicos_abastecimentos, colunas_group_by, percentual_meta_sugerida):

    st.header(titulo)

    df_agrupado = df_servicos_abastecimentos.groupby(colunas_group_by)[['Litros', 'Km Rodado']].sum().reset_index()

    df_agrupado['Média Km/Litro'] = round(df_agrupado['Km Rodado'] / df_agrupado['Litros'], 2)

    df_agrupado['Meta Sugerida'] = round(df_agrupado['Média Km/Litro']*(1+percentual_meta_sugerida), 2)

    st.dataframe(df_agrupado, hide_index=True, use_container_width=True)

st.set_page_config(layout='wide')

st.title('Análise de Médias - Veículos por Categoria de Meta')

st.divider()

row0 = st.columns(2)

row1 = st.columns(1)

# Ano e Mês de análise

with row0[0]:

    container_datas = st.container(border=True)

    container_datas.subheader('Período')

    data_inicial = container_datas.date_input('Data Inicial', value=None ,format='DD/MM/YYYY', key='data_inicial')

    data_final = container_datas.date_input('Data Final', value=None ,format='DD/MM/YYYY', key='data_final')

with row0[1]:

    container_percentual = st.container(border=True)

    percentual_meta_sugerida = container_percentual.number_input('Percentual p/ Sugestão de Meta', value=10, key='percentual_meta_sugerida')

    percentual_meta_sugerida = percentual_meta_sugerida/100

if 'df_servicos_abastecimentos' in st.session_state:

    df_servicos_abastecimentos = st.session_state.df_servicos_abastecimentos.copy()

    if data_inicial and data_final:

        df_servicos_abastecimentos = df_servicos_abastecimentos[(df_servicos_abastecimentos['Data da Escala']>=data_inicial) & (df_servicos_abastecimentos['Data da Escala']<=data_final)]

        with row0[0]:

            tipo_veiculo = container_datas.multiselect('Tipo de Veículo', sorted(df_servicos_abastecimentos['Tipo de Veículo'].unique()), default=None)

            if len(tipo_veiculo)>0:

                df_servicos_abastecimentos = df_servicos_abastecimentos[df_servicos_abastecimentos['Tipo de Veículo'].isin(tipo_veiculo)]

            modelo_veiculo = container_datas.multiselect('Modelo de Veículo', sorted(df_servicos_abastecimentos['Modelo'].unique()), default=None)

            if len(modelo_veiculo)>0:

                df_servicos_abastecimentos = df_servicos_abastecimentos[df_servicos_abastecimentos['Modelo'].isin(modelo_veiculo)]

            veiculo = container_datas.multiselect('Veículo', sorted(df_servicos_abastecimentos['Veiculo'].unique()), default=None)

            if len(veiculo)>0:

                df_servicos_abastecimentos = df_servicos_abastecimentos[df_servicos_abastecimentos['Veiculo'].isin(veiculo)]

        with row1[0]:

            st.divider()

        mostrar_resultados('Resultados por Modelo de Veículo', df_servicos_abastecimentos, ['Modelo', 'Categoria Meta'], percentual_meta_sugerida)

        mostrar_resultados('Resultados por Tipo de Veículo', df_servicos_abastecimentos, ['Tipo de Veículo', 'Categoria Meta'], percentual_meta_sugerida)

        mostrar_resultados('Resultados por Veículo', df_servicos_abastecimentos, ['Veiculo', 'Tipo de Veículo', 'Categoria Meta'], percentual_meta_sugerida)
    
else:

    st.error('Precisa gerar um relatório na aba Gerar Relatório')
