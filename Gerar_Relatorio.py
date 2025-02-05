import streamlit as st
import pandas as pd
import gspread 
from google.oauth2 import service_account
from datetime import timedelta
import mysql.connector
import decimal

def gerar_df_phoenix(vw_name, base_luck):
    
    config = {'user': 'user_automation_jpa', 'password': 'luck_jpa_2024', 'host': 'comeia.cixat7j68g0n.us-east-1.rds.amazonaws.com', 'database': base_luck}

    conexao = mysql.connector.connect(**config)

    cursor = conexao.cursor()

    request_name = f'SELECT * FROM {vw_name}'

    cursor.execute(request_name)

    resultado = cursor.fetchall()
    
    cabecalho = [desc[0] for desc in cursor.description]

    cursor.close()

    conexao.close()

    df = pd.DataFrame(resultado, columns=cabecalho)

    df = df.applymap(lambda x: float(x) if isinstance(x, decimal.Decimal) else x)

    return df

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

def ajustar_coluna_data_ano_mes(df):

    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y %H:%M:%S')

    df['ano'] = df['Data'].dt.year

    df['mes'] = df['Data'].dt.month

    df['ano_mes'] = df['mes'].astype(str) + '/' + df['ano'].astype(str).str[-2:]

    return df

def verificar_motoristas_sem_correspondencia(dict_renomear_motoristas):

    lista_motoristas_abastecimentos = st.session_state.df_abastecimentos['Motorista'].unique().tolist()

    lista_motoristas_sem_correspondencia = list(set(lista_motoristas_abastecimentos) - set(dict_renomear_motoristas))

    lista_chaves_valor_vazio = [chave for chave, valor in dict_renomear_motoristas.items() if valor == '']

    lista_motoristas_final = list(set(lista_motoristas_sem_correspondencia + lista_chaves_valor_vazio))

    if len(lista_motoristas_final)>0:

        with row1[0]:

            st.error(f'Os motoristas {", ".join(lista_motoristas_final)} não estão cadastrados na aba Motoristas. Precisa cadastrar e informar quais os seus nomes lá no Phoenix')

            st.stop()

def tratar_colunas_df_abastecimentos(df, lista_colunas_texto, lista_colunas_numericas):

    df = ajustar_coluna_data_ano_mes(df)

    for coluna in lista_colunas_texto:

        df[coluna] = df[coluna].astype(str)

    for coluna in lista_colunas_numericas:

        df = transformar_coluna_em_numerica(df, coluna)

    dict_renomear_motoristas = dict(zip(st.session_state.df_motoristas['Motorista Ticket Log'], st.session_state.df_motoristas['Motorista Phoenix']))

    verificar_motoristas_sem_correspondencia(dict_renomear_motoristas)

    df['Motorista'] = df['Motorista'].replace(dict_renomear_motoristas)

def puxar_dados_google_drive():

    puxar_aba_simples(st.session_state.id_gsheet, 'Motoristas', 'df_motoristas')

    puxar_aba_simples(st.session_state.id_gsheet, 'Abastecimentos Ticket Log', 'df_abastecimentos')

    tratar_colunas_df_abastecimentos(st.session_state.df_abastecimentos, ['Placa', 'Tipo de Veículo', 'Modelo', 'Motorista', 'Tipo de Combustível'], 
                                     ['Número Frota', 'Matrícula', 'Litros', 'Valor/Litro', 'Hodômetro', 'Km Rodado', 'Km/Litro', 'Valor Total'])
    
    puxar_aba_simples(st.session_state.id_gsheet, 'Serviços / Categorias', 'df_servicos_categorias')

    puxar_aba_simples(st.session_state.id_gsheet, 'Metas', 'df_metas')

    st.session_state.df_metas = transformar_coluna_em_numerica(st.session_state.df_metas, 'Meta')

def puxar_dados_phoenix():

    st.session_state.df_escalas = gerar_df_phoenix('vw_campanha_motoristas', st.session_state.base_luck)

    st.session_state.df_escalas['ano'] = pd.to_datetime(st.session_state.df_escalas['Data da Escala']).dt.year

    st.session_state.df_escalas['mes'] = pd.to_datetime(st.session_state.df_escalas['Data da Escala']).dt.month

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

def cruzar_servicos_e_abastecimentos(df_escalas_group):

    df_abastecimentos = st.session_state.df_abastecimentos.sort_values(by=['Data']).reset_index(drop=True)

    df_abastecimentos['Chave'] = df_abastecimentos['Placa'].astype(str) + '_' + df_abastecimentos['Motorista'].astype(str)

    df_escalas_group['Chave'] = df_escalas_group['Placa'].astype(str) + '_' + df_escalas_group['Motorista'].astype(str)

    df_escalas_group['Data | Horario Apresentacao'] = pd.to_datetime(df_escalas_group['Data | Horario Apresentacao'])

    df_escalas_group = df_escalas_group.sort_values(by=['Data | Horario Apresentacao']).reset_index(drop=True)

    df_resultado = pd.merge_asof(df_escalas_group, df_abastecimentos[['Data', 'Chave', 'Km/Litro', 'Tipo de Veículo', 'ano_mes', 'Litros', 'Km Rodado']], by='Chave', 
                                 left_on='Data | Horario Apresentacao', right_on='Data', direction='forward')

    df_resultado['Meta Batida'] = df_resultado.apply(lambda row: 1 if row['Km/Litro']>=row['Meta'] else 0, axis=1)

    return df_resultado

def retirar_servicos_sem_abastecimentos(df_servicos_abastecimentos):

    df_servicos_sem_abastecimentos = df_servicos_abastecimentos[pd.isna(df_servicos_abastecimentos['Data'])]

    with row1[0]:

        if len(df_servicos_sem_abastecimentos)>0:

            st.error('Os serviços abaixo não possuem abastecimento relativo e, portanto, foram retirados da análise')

            st.dataframe(df_servicos_sem_abastecimentos[['Data da Escala', 'Escala', 'Veiculo', 'Placa', 'Motorista', 'Servico']], hide_index=True)

    df_servicos_abastecimentos = df_servicos_abastecimentos[pd.notna(df_servicos_abastecimentos['Data'])].reset_index(drop=True)

    return df_servicos_abastecimentos

st.set_page_config(layout='wide')

st.title('Gerar Relatório')

st.divider()

row0 = st.columns(3)

row1 = st.columns(1)

if not 'base_luck' in st.session_state:

    st.session_state.id_gsheet = '1SGTth5faSNNtAlU_4a_ehohqHAeGUf-dsILc7qqgpms'

    st.session_state.base_luck = 'test_phoenix_recife'

if not 'df_escalas' in st.session_state:

    with st.spinner('Puxando dados do Google Drive...'):

        puxar_dados_google_drive()

    with st.spinner('Puxando dados do Phoenix...'):

        puxar_dados_phoenix()

# Ano e Mês de análise

with row0[0]:

    gerar_analise = st.button('Gerar Análise')

# Atualizar dados do Google Drive

with row0[1]:

    atualizar_dfs_excel = st.button('Atualizar Dados Google Drive')

    if atualizar_dfs_excel:

        with st.spinner('Puxando dados do Google Drive...'):

            puxar_dados_google_drive()

with row0[2]:

    atualizar_dados_phoenix = st.button('Atualizar Dados Phoenix')

    if atualizar_dados_phoenix:

        with st.spinner('Puxando dados do Phoenix...'):

            puxar_dados_phoenix()

if gerar_analise:

    # Definindo período existente nos abastecimentos pra só puxar as escalas dentro do período

    data_inicial = st.session_state.df_abastecimentos['Data'].min()-timedelta(days=1)

    data_final = st.session_state.df_abastecimentos['Data'].max()

    # Pegando escalas do mês de análise

    df_escalas = st.session_state.df_escalas[(st.session_state.df_escalas['Data | Horario Apresentacao']>=data_inicial) & 
                                             (st.session_state.df_escalas['Data | Horario Apresentacao']<=data_final)].reset_index(drop=True)

    # Preenchendo valores None da coluna Data | Horario Apresentacao

    df_escalas['Data | Horario Apresentacao'] = df_escalas.apply(lambda row: pd.to_datetime(f"{row['Data da Escala']} 08:00:00") 
                                                                 if pd.isna(row['Data | Horario Apresentacao']) else row['Data | Horario Apresentacao'], axis=1)
    
    # Renomeando escalas que são apoios

    df_escalas.loc[pd.notna(df_escalas['Escala Principal']), 'Servico'] = 'APOIO'

    # Agrupando escalas

    df_escalas_group = df_escalas.groupby(['ano', 'mes', 'Data da Escala', 'Escala', 'Veiculo', 'Placa', 'Motorista']).agg({'Data | Horario Apresentacao': 'min', 'Servico': 'first'}).reset_index()

    # Inserindo categorias de serviços e verificando se todos os serviços estão com suas categorias cadastradas

    df_escalas_group = pd.merge(df_escalas_group, st.session_state.df_servicos_categorias, on='Servico', how='left')

    verificar_servicos_sem_categoria(df_escalas_group)

    # Filtrando apenas as placas contidas na aba metas

    df_escalas_group = df_escalas_group[df_escalas_group['Placa'].isin(st.session_state.df_metas['Placa'].unique())].reset_index(drop=True)

    # Inserindo categoria das metas e valor de meta pra cada veículo/serviço e verificando se todas as combinações tem meta cadastradas

    df_escalas_group = pd.merge(df_escalas_group, st.session_state.df_metas, on=['Placa', 'Categoria Meta'], how='left')

    verificar_veiculos_sem_meta(df_escalas_group)

    # Gerando dataframe com o cruzamento dos serviços e seus abastecimentos relativos

    df_servicos_abastecimentos = cruzar_servicos_e_abastecimentos(df_escalas_group)

    # Retirando da análise as linhas que o robô não encontrou correspondência e avisando quais são elas

    st.session_state.df_servicos_abastecimentos = retirar_servicos_sem_abastecimentos(df_servicos_abastecimentos)

    st.success('Relatório gerado com sucesso!')
