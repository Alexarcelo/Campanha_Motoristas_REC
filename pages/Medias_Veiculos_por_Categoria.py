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

    if data_inicial and data_final:

        with row0[0]:

            veiculo = st.multiselect('Veículo', sorted(st.session_state.df_servicos_abastecimentos['Veiculo'].unique()), default=None)

        with row1[0]:

            st.divider()

        if len(veiculo)>0:

            df_veiculos = st.session_state.df_servicos_abastecimentos[(st.session_state.df_servicos_abastecimentos['Veiculo'].isin(veiculo)) & 
                                                                      (st.session_state.df_servicos_abastecimentos['Data da Escala']>=data_inicial) & 
                                                                      (st.session_state.df_servicos_abastecimentos['Data da Escala']<=data_final)]

            df_media_categoria = df_veiculos.groupby(['Veiculo', 'Categoria Meta'])[['Litros', 'Km Rodado']].sum().reset_index()

            df_media_categoria['Média Km/Litro'] = round(df_media_categoria['Km Rodado'] / df_media_categoria['Litros'], 2)

            container_dataframe = st.container()

            container_dataframe.dataframe(df_media_categoria, hide_index=True, use_container_width=True)
    
else:

    st.error('Precisa gerar um relatório na aba Gerar Relatório')
