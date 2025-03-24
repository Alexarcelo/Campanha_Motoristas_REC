import streamlit as st
import pandas as pd
import gspread 
from google.oauth2 import service_account
from datetime import timedelta
import mysql.connector
import decimal
from datetime import time 

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

def puxar_dados_google_drive():

    def tratar_colunas_df_abastecimentos(df, lista_colunas_texto, lista_colunas_numericas):

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

        df = ajustar_coluna_data_ano_mes(df)

        for coluna in lista_colunas_texto:

            df[coluna] = df[coluna].astype(str)

        for coluna in lista_colunas_numericas:

            df = transformar_coluna_em_numerica(df, coluna)

        dict_renomear_motoristas = dict(zip(st.session_state.df_motoristas['Motorista Ticket Log'], st.session_state.df_motoristas['Motorista Phoenix']))

        verificar_motoristas_sem_correspondencia(dict_renomear_motoristas)

        df['Motorista'] = df['Motorista'].replace(dict_renomear_motoristas)

        df = pd.merge(df, st.session_state.df_motoristas[['Motorista Phoenix', 'Grupo Motorista']], left_on='Motorista', right_on='Motorista Phoenix', how='left')

        return df

    puxar_aba_simples(
        st.session_state.id_gsheet, 
        'Motoristas', 
        'df_motoristas'
    )

    puxar_aba_simples(
        st.session_state.id_gsheet, 
        'Abastecimentos Ticket Log', 
        'df_abastecimentos'
    )

    st.session_state.df_abastecimentos = tratar_colunas_df_abastecimentos(
        st.session_state.df_abastecimentos, 
        [
            'Placa', 
            'Tipo de Veículo', 
            'Modelo', 
            'Motorista', 
            'Tipo de Combustível'
        ], 
        [
            'Número Frota', 
            'Matrícula', 
            'Litros', 
            'Valor/Litro', 
            'Hodômetro', 
            'Km Rodado', 
            'Km/Litro', 
            'Valor Total'
        ]
    )
    
    puxar_aba_simples(
        st.session_state.id_gsheet, 
        'Serviços / Categorias', 
        'df_servicos_categorias'
    )

    puxar_aba_simples(
        st.session_state.id_gsheet, 
        'Metas', 
        'df_metas'
    )

    st.session_state.df_metas = transformar_coluna_em_numerica(
        st.session_state.df_metas, 
        'Meta'
    )

    st.session_state.df_servicos_abastecimentos = gerar_df_historico()

def puxar_dados_phoenix():

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

    st.session_state.df_escalas = gerar_df_phoenix(
        'vw_campanha_motoristas', 
        st.session_state.base_luck
    )

    st.session_state.df_escalas['ano'] = pd.to_datetime(st.session_state.df_escalas['Data da Escala']).dt.year

    st.session_state.df_escalas['mes'] = pd.to_datetime(st.session_state.df_escalas['Data da Escala']).dt.month

def colher_parametros_datas_horario_incremento_gerar_analise(row0):

    with row0[0]:

        data_inicial = st.date_input(
            'Data Inicial', 
            value=None, 
            format='DD/MM/YYYY'
        )

        data_final = st.date_input(       
            'Data Final', 
            value=None, 
            format='DD/MM/YYYY'
        )

        horario_inicio_madrugada = st.time_input(
            'Horário Inicial Madrugada', 
            time(20)
        )

        horario_final_madrugada = st.time_input(
            'Horário Final Madrugada', 
            time(4)
        )

        incremento_percentual = st.number_input(
            'Incremento Percentual na Meta p/ Madrugadas', 
            value=20
        )

        incremento_percentual = incremento_percentual/100

        gerar_analise = st.button('Gerar Análise')

    return data_inicial, data_final, horario_inicio_madrugada, horario_final_madrugada, incremento_percentual, gerar_analise

def botão_puxar_dados_google_drive(row0):

    with row0[1]:

        atualizar_dfs_excel = st.button('Atualizar Dados Google Drive')

        if atualizar_dfs_excel:

            with st.spinner('Puxando dados do Google Drive...'):

                puxar_dados_google_drive()

def botão_puxar_dados_phoenix(row0):

    with row0[2]:

        atualizar_dados_phoenix = st.button('Atualizar Dados Phoenix')

        if atualizar_dados_phoenix:

            with st.spinner('Puxando dados do Phoenix...'):

                puxar_dados_phoenix()

def gerar_df_escalas(data_inicial, data_final):

    # Definindo período existente nos abastecimentos pra só puxar as escalas dentro do período

    # data_inicial = st.session_state.df_abastecimentos['Data'].min()-timedelta(days=1)

    # data_final = st.session_state.df_abastecimentos['Data'].max()

    # Pegando escalas do mês de análise

    # df_escalas = st.session_state.df_escalas[(st.session_state.df_escalas['Data | Horario Apresentacao']>=data_inicial) & 
    #                                          (st.session_state.df_escalas['Data | Horario Apresentacao']<=data_final)].reset_index(drop=True)
    
    df_escalas = st.session_state.df_escalas[
        (st.session_state.df_escalas['Data da Escala']>=data_inicial) & 
        (st.session_state.df_escalas['Data da Escala']<=data_final)
    ].reset_index(drop=True)

    # Preenchendo valores None da coluna Data | Horario Apresentacao

    df_escalas['Data | Horario Apresentacao'] = df_escalas.apply(
        lambda row: pd.to_datetime(f"{row['Data da Escala']} 08:00:00") 
        if pd.isna(row['Data | Horario Apresentacao']) 
        else row['Data | Horario Apresentacao'], 
        axis=1
    )
    
    # Renomeando escalas que são apoios

    df_escalas.loc[
        pd.notna(df_escalas['Escala Principal']), 
        'Servico'
    ] = 'APOIO'

    return df_escalas

def gerar_df_escalas_group(df_escalas):

    def verificar_servicos_sem_categoria(df_escalas_group):

        df_servicos_sem_categoria_meta = pd.DataFrame(
            data=df_escalas_group[
                (pd.isna(df_escalas_group['Categoria Meta'])) | 
                (df_escalas_group['Categoria Meta']=='')
            ]['Servico'].unique(), 
            columns=['Serviços']
        )

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

    # Agrupando escalas

    df_escalas_group = df_escalas.groupby(
        [
            'ano', 
            'mes', 
            'Data da Escala', 
            'Escala', 
            'Veiculo', 
            'Placa', 
            'Motorista'
        ]
    ).agg(
        {
            'Data | Horario Apresentacao': 'min', 
            'Servico': 'first'
        }
    ).reset_index()

    # Inserindo categorias de serviços e verificando se todos os serviços estão com suas categorias cadastradas

    df_escalas_group = pd.merge(
        df_escalas_group, 
        st.session_state.df_servicos_categorias, 
        on='Servico', 
        how='left'
    )

    verificar_servicos_sem_categoria(df_escalas_group)

    # Filtrando apenas as placas contidas na aba metas

    df_escalas_group = df_escalas_group[df_escalas_group['Placa'].isin(st.session_state.df_metas['Placa'].unique())].reset_index(drop=True)

    # Inserindo categoria das metas e valor de meta pra cada veículo/serviço e verificando se todas as combinações tem meta cadastradas

    df_escalas_group = pd.merge(
        df_escalas_group, 
        st.session_state.df_metas, 
        on=[
            'Placa', 
            'Categoria Meta'
        ], 
        how='left'
    )

    verificar_veiculos_sem_meta(df_escalas_group)

    return df_escalas_group

def cruzar_servicos_e_abastecimentos(df_escalas_group, horario_inicio_madrugada, horario_final_madrugada, incremento_percentual):

    df_abastecimentos = st.session_state.df_abastecimentos.sort_values(by=['Data']).reset_index(drop=True)

    df_abastecimentos['Chave'] = df_abastecimentos['Placa'].astype(str) + '_' + df_abastecimentos['Motorista'].astype(str)

    df_escalas_group['Chave'] = df_escalas_group['Placa'].astype(str) + '_' + df_escalas_group['Motorista'].astype(str)

    df_escalas_group['Data | Horario Apresentacao'] = pd.to_datetime(df_escalas_group['Data | Horario Apresentacao'])

    df_escalas_group = df_escalas_group.sort_values(by=['Data | Horario Apresentacao']).reset_index(drop=True)

    df_resultado = pd.merge_asof(df_escalas_group, df_abastecimentos[['Data', 'Chave', 'Km/Litro', 'Tipo de Veículo', 'Modelo', 'ano_mes', 'Litros', 'Km Rodado', 'Valor Total', 'Grupo Motorista']], 
                                 by='Chave', left_on='Data | Horario Apresentacao', right_on='Data', direction='forward')
    
    df_resultado.loc[(df_resultado['Data'].dt.time>=horario_inicio_madrugada) | (df_resultado['Data'].dt.time<=horario_final_madrugada), 'Meta'] = \
        df_resultado.loc[(df_resultado['Data'].dt.time>=horario_inicio_madrugada) | (df_resultado['Data'].dt.time<=horario_final_madrugada), 'Meta'] * (1+incremento_percentual)

    df_resultado['Meta Batida'] = df_resultado.apply(lambda row: 1 if row['Km/Litro']>=row['Meta'] else 0, axis=1)

    return df_resultado

def verificar_servicos_sem_abastecimentos(df_servicos_abastecimentos):

    df_servicos_sem_abastecimentos = df_servicos_abastecimentos[pd.isna(df_servicos_abastecimentos['Data'])]

    with row1[0]:

        if len(df_servicos_sem_abastecimentos)>0:

            st.error('Os serviços abaixo não possuem abastecimento relativo')

            st.dataframe(
                df_servicos_sem_abastecimentos[
                    [
                        'Data da Escala', 
                        'Escala', 
                        'Veiculo', 
                        'Placa', 
                        'Motorista', 
                        'Servico'
                    ]
                ], 
                hide_index=True
            )

    # df_servicos_abastecimentos = df_servicos_abastecimentos[pd.notna(df_servicos_abastecimentos['Data'])].reset_index(drop=True)

    return df_servicos_abastecimentos

def gerar_df_historico(df_insercao=None):

    puxar_aba_simples(
        st.session_state.id_gsheet, 
        'Serviços x Abastecimentos', 
        'df_historico'
    )

    df_historico = st.session_state.df_historico.copy()

    df_historico['Data da Escala'] = pd.to_datetime(df_historico['Data da Escala'], format='%d/%m/%Y').dt.date

    df_historico['Data | Horario Apresentacao'] = pd.to_datetime(df_historico['Data | Horario Apresentacao'], format='%d/%m/%Y %H:%M:%S')

    df_historico['Data'] = pd.to_datetime(df_historico['Data'], format='%d/%m/%Y %H:%M:%S')

    for coluna in ['ano', 'mes', 'Meta', 'Km/Litro', 'Litros', 'Km Rodado', 'Valor Total', 'Meta Batida']:

        df_historico = transformar_coluna_em_numerica(df_historico, coluna)

    if df_insercao is not None:

        df_historico = df_historico[~df_historico['Data da Escala'].isin(df_insercao['Data da Escala'].unique().tolist())]

    return df_historico

def ajustar_dados_df_insercao(df_insercao):

    df_insercao['Data da Escala'] = pd.to_datetime(df_insercao['Data da Escala']).dt.strftime('%Y-%m-%d')

    df_insercao['Data | Horario Apresentacao'] = df_insercao['Data | Horario Apresentacao'].dt.strftime('%Y-%m-%d %H:%M:%S')

    df_insercao['Data'] = df_insercao['Data'].apply(
        lambda x: str(x) 
        if pd.notna(x)
        else '')

    df_insercao.fillna(
        {
            'Km/Litro': 0,
            'Litros': 0,
            'Km Rodado': 0,
            'Valor Total': 0,
            'Tipo de Veículo': '',
            'Modelo': '',
            'Grupo Motorista': ''
        }, 
        inplace=True
    )

    df_insercao = df_insercao[
        [
            'ano', 
            'mes', 
            'Data da Escala', 
            'Escala',
            'Veiculo',
            'Placa',
            'Motorista',
            'Data | Horario Apresentacao',
            'Servico',
            'Categoria Meta',
            'Meta',
            'Data',
            'Km/Litro',
            'Tipo de Veículo',
            'Modelo',
            'Litros',
            'Km Rodado',
            'Valor Total',
            'Grupo Motorista',
            'Meta Batida'
        ]
    ]

    return df_insercao

def inserir_servicos_com_abastecimentos(df, id_gsheet, nome_aba):

    nome_credencial = st.secrets["CREDENCIAL_SHEETS"]

    credentials = service_account.Credentials.from_service_account_info(nome_credencial)
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = credentials.with_scopes(scope)

    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(id_gsheet)
    sheet = spreadsheet.worksheet(nome_aba)

    # Monta o cabeçalho + dados
    header = [df.columns.tolist()]
    data = df.values.tolist()

    # Junta cabeçalho + dados
    full_data = header + data

    # Atualiza começando da célula A1
    sheet.update('A1', full_data)

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

data_inicial, data_final, horario_inicio_madrugada, horario_final_madrugada, incremento_percentual, gerar_analise = colher_parametros_datas_horario_incremento_gerar_analise(row0)

# Atualizar dados do Google Drive

botão_puxar_dados_google_drive(row0)

botão_puxar_dados_phoenix(row0)

if gerar_analise:

    # Gerando dataframe com as escalas das datas selecionadas

    df_escalas = gerar_df_escalas(data_inicial, data_final)

    # Gerando dataframe com escalas agrupadas, com categorias de serviços e metas apenas dos veículos contigos na aba metas

    df_escalas_group = gerar_df_escalas_group(df_escalas)

    # Gerando dataframe com o cruzamento dos serviços e seus abastecimentos relativos

    df_servicos_abastecimentos = cruzar_servicos_e_abastecimentos(df_escalas_group, horario_inicio_madrugada, horario_final_madrugada, incremento_percentual)

    # Avisando as linhas que o robô não encontrou correspondência e avisando quais são elas

    st.session_state.df_servicos_abastecimentos = verificar_servicos_sem_abastecimentos(df_servicos_abastecimentos)

    st.success('Relatório gerado com sucesso!')

if 'df_servicos_abastecimentos' in st.session_state:

    salvar_dados = st.button('Salvar Serviços / Abastecimentos no Google Drive')

    df_insercao = st.session_state.df_servicos_abastecimentos.copy()

    if salvar_dados:

        with st.spinner('Salvando dados no Google Drive...'):
        
            df_historico = gerar_df_historico(df_insercao)

            df_insercao = pd.concat(
                [
                    df_insercao, 
                    df_historico
                ], 
                ignore_index=True
            )

            st.session_state.df_servicos_abastecimentos = df_insercao

            df_insercao = ajustar_dados_df_insercao(df_insercao)

            inserir_servicos_com_abastecimentos(
                df_insercao, 
                st.session_state.id_gsheet, 
                'Serviços x Abastecimentos'
            )
