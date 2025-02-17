import streamlit as st

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

if 'df_servicos_abastecimentos' in st.session_state:

    df_servicos_abastecimentos = st.session_state.df_servicos_abastecimentos.copy()

    if data_inicial and data_final:

        df_servicos_abastecimentos = df_servicos_abastecimentos[(df_servicos_abastecimentos['Data da Escala']>=data_inicial) & (df_servicos_abastecimentos['Data da Escala']<=data_final)]

        with row0[0]:

            tipo_veiculo = container_datas.multiselect('Tipo de Veículo', sorted(df_servicos_abastecimentos['Tipo de Veículo'].unique()), default=None)

            if len(tipo_veiculo)>0:

                df_servicos_abastecimentos = df_servicos_abastecimentos[df_servicos_abastecimentos['Tipo de Veículo'].isin(tipo_veiculo)]

            veiculo = container_datas.multiselect('Veículo', sorted(df_servicos_abastecimentos['Veiculo'].unique()), default=None)

            if len(veiculo)>0:

                df_servicos_abastecimentos = df_servicos_abastecimentos[df_servicos_abastecimentos['Veiculo'].isin(veiculo)]

        with row1[0]:

            st.divider()

        st.header('Resultados por Tipo de Veículo')

        df_media_tp_veiculos = df_servicos_abastecimentos.groupby(['Tipo de Veículo', 'Categoria Meta'])[['Litros', 'Km Rodado']].sum().reset_index()

        df_media_tp_veiculos['Média Km/Litro'] = round(df_media_tp_veiculos['Km Rodado'] / df_media_tp_veiculos['Litros'], 2)

        st.dataframe(df_media_tp_veiculos, hide_index=True, use_container_width=True)

        st.header('Resultados por Veículo')

        df_media_veiculos = df_servicos_abastecimentos.groupby(['Veiculo', 'Tipo de Veículo', 'Categoria Meta'])[['Litros', 'Km Rodado']].sum().reset_index()

        df_media_veiculos['Média Km/Litro'] = round(df_media_veiculos['Km Rodado'] / df_media_veiculos['Litros'], 2)

        st.dataframe(df_media_veiculos, hide_index=True, use_container_width=True)
    
else:

    st.error('Precisa gerar um relatório na aba Gerar Relatório')
