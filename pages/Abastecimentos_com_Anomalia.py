import streamlit as st

st.set_page_config(layout='wide')

st.title('Abastecimentos com Anomalias')

if not 'df_servicos_abastecimentos' in st.session_state:

    st.error('Precisa gerar um relatório na aba Gerar Relatório')

else:

    st.divider()

    row0 = st.columns(1)

    with row0[0]:

        percentual_anomalias = st.number_input('Variação Percentual p/ Anomalia', step=1, value=30)

        percentual_anomalias = percentual_anomalias/100
    
    df_filtro_colunas = st.session_state.df_servicos_abastecimentos.copy()

    df_filtro_colunas['Percentual do Estimado'] = round(df_filtro_colunas['Km/Litro']/df_filtro_colunas['Meta']-1, 2)

    df_filtro_colunas = df_filtro_colunas[['Data', 'Motorista', 'Veiculo', 'Km/Litro', 'Meta', 'Percentual do Estimado']]

    df_filtro_colunas.loc[(df_filtro_colunas['Percentual do Estimado'] > percentual_anomalias) | (df_filtro_colunas['Percentual do Estimado'] < -percentual_anomalias), 'Anomalia']='X'

    df_filtro_colunas = df_filtro_colunas[df_filtro_colunas['Anomalia']=='X'].reset_index(drop=True)

    df_filtro_colunas = df_filtro_colunas.rename(columns={'Km/Litro': 'Média km/l', 'Meta': 'Meta km/l'})

    container_dataframe = st.container()

    container_dataframe.dataframe(df_filtro_colunas[['Data', 'Motorista', 'Veiculo', 'Média km/l', 'Meta km/l']], hide_index=True, use_container_width=True)
