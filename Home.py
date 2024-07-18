import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

# Configuração da página
#st.set_page_config(layout="wide", page_title="Dashboard de Vendas")
def obter_diretorios():
    # Obter o diretório do script atual
    diretorio_atual = Path(__file__).resolve()
    # Obter o diretório da pasta 'datasets'
    pasta_datasets = Path(__file__).parents[1] / 'datasets'
    
    return diretorio_atual, pasta_datasets

# Usar a função para obter os diretórios
diretorio_atual, pasta_datasets = obter_diretorios()

# Carregar a base de dados a partir de um arquivo Excel
#df_dnd = pd.read_excel(pasta_datasets / 'BaseVendasMatriz-maio-24.xlsx')

# Exibir o DataFrame no Streamlit
#st.dataframe(df_dnd)

# Carregar a base de dados a partir de um arquivo Excel
df_dnd = pd.read_excel('BaseVendasMatriz-maio-24.xlsx')
df2dnd = df_dnd.copy()

# Funções de processamento
def process_data(df_dnd):
    df_dnd['data'] = pd.to_datetime(df_dnd['data'], format='%d/%m/%Y', errors='coerce')
    df_dnd['dia'] = df_dnd['data'].dt.day
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
             'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    df_dnd['mes_extenso'] = df_dnd['data'].dt.month.apply(lambda x: meses[x-1])
    df_dnd['semana_mes'] = df_dnd['data'].dt.day // 7 + 1
    total_vendas = df_dnd.groupby(['tipo', 'vendedor', 'mes_extenso']).agg(total_receb=('total_receb', 'sum')).reset_index()
    total_vendas = total_vendas.sort_values(by='total_receb', ascending=False)
    df_dnd['quantidade'] = 1
    total_vendas_e_quantidade = df_dnd.groupby(['tipo', 'vendedor', 'dia']).agg(
        total_receb=('total_receb', 'sum'),
        quantidade=('quantidade', 'count')
    ).reset_index()
    total_vendas_e_quantidade['tkm'] = total_vendas_e_quantidade['total_receb'] / total_vendas_e_quantidade['quantidade']
    total_vendas_e_quantidade['performance'] = (total_vendas_e_quantidade['total_receb'] * total_vendas_e_quantidade['tkm']) / 1000
    return total_vendas_e_quantidade

def process_weekly_data(df_dnd):
    df_dia_semana = df_dnd[['data', 'total_receb', 'vendedor', 'tipo']].copy()
    df_dia_semana['data'] = pd.to_datetime(df_dia_semana['data'], format='%d/%m/%Y', errors='coerce')
    df_dia_semana['semana_do_ano'] = df_dia_semana['data'].dt.isocalendar().week
    df_agrupado = df_dia_semana.groupby(['tipo', 'vendedor', 'semana_do_ano'])['total_receb'].sum().reset_index()
    df_agrupado.rename(columns={'total_receb': 'total_semanal', 'semana_do_ano': 'semana'}, inplace=True)
    return df_agrupado

def process_indicators(Df_clientes):
    Df_classificacao = Df_clientes.groupby('classificacao').agg({'total_receb': 'sum'})
    ticket_medio = Df_clientes.groupby('classificacao')['total_receb'].mean()
    vendas_por_vendedor = Df_clientes.groupby('vendedor')['total_receb'].sum()
    freq_class = Df_clientes['classificacao'].value_counts()

    novo_df = pd.DataFrame({
        'Faturado': Df_classificacao['total_receb'],
        'Tick M': ticket_medio,
        'Pedidos': freq_class
    }).reset_index()

    total_geral_faturado = novo_df['Faturado'].sum()
    novo_df['Total %'] = (novo_df['Faturado'] / total_geral_faturado * 100).round(2)

    vendas_por_vendedor_df = vendas_por_vendedor.reset_index(name='Vendido')
    vendas_por_vendedor_df['Perfor'] = vendas_por_vendedor_df['Vendido'] * 1000 / vendas_por_vendedor_df['Vendido'].sum()
    vendas_por_vendedor_df = vendas_por_vendedor_df.sort_values(by='Vendido', ascending=False)

    return novo_df, vendas_por_vendedor_df

def calcular_comissao_ajustada_on(total_semanal):
    if total_semanal < 5000:
        return total_semanal * 0.015
    elif total_semanal < 9780:
        return total_semanal * 0.02
    elif total_semanal < 13930:
        return total_semanal * 0.025
    elif total_semanal >= 17943:
        return total_semanal * 0.03
    return 0

def calcular_comissao_ajustada_pr(total_semanal):
    if total_semanal < 19000:
        return total_semanal * 0.01
    elif total_semanal >= 19100:
        return total_semanal * 0.015
    elif total_semanal >= 23490:
        return total_semanal * 0.02
    elif total_semanal >= 27284:
        return total_semanal * 0.025
    return 0

# Processar os dados
total_vendas_e_quantidade = process_data(df_dnd)
df_agrupado = process_weekly_data(df_dnd)
Df_clientes = df_dnd.copy()
novo_df, vendas_por_vendedor_df = process_indicators(Df_clientes)

# Sidebar para navegação entre páginas
st.sidebar.title("Navegação")
page = st.sidebar.radio("Ir para", ["Análise de Vendas", "Dashboard de Vendas", "Vendas da Semana", "Indicadores", "Descontos por Data"])

# Página 1: Análise de Vendas
if page == "Análise de Vendas":
    st.title("Análise de Vendas")
    
    dias_desejados = st.multiselect("Selecione os dias desejados:", list(range(1, 32)))
    
    if dias_desejados:
        filtered_df = total_vendas_e_quantidade[total_vendas_e_quantidade['dia'].isin(dias_desejados)].sort_values(by='total_receb', ascending=False)
        filtered_df['tipo'] = filtered_df['tipo'].str.strip()

        st.write("### Dados Filtrados")
        #dataframe geral do dia
        #st.dataframe(filtered_df)

        dados_PR = filtered_df[filtered_df['tipo'] == 'PR'][['vendedor', 'total_receb', 'quantidade', 'tkm', 'performance']].round(2)
        dados_ON = filtered_df[filtered_df['tipo'] == 'ON'][['vendedor', 'total_receb', 'quantidade', 'tkm', 'performance']].round(2)

        total_vendas_DIA= filtered_df['total_receb'].sum()
        total_vendas_ON = dados_ON['total_receb'].sum()
        total_vendas_PR = dados_PR['total_receb'].sum()
        qtd_vendas_dia = filtered_df ['total_receb'].count()

        # adicionado kpi 
        col1, col2,col3 = st.columns(3)
        valor_vendas = f"R$ {total_vendas_DIA: ,.2f}"
        #dif_metrica = total_vendas_ON / total_vendas_DIA *100
        col1.metric('Valor de total',
        (valor_vendas))

        dif_metrica3 = f"R$ {qtd_vendas_dia : ,.2f}"
        #dif_metrica = total_vendas_ON / total_vendas_DIA *100
        col1.metric('Valor de total',
        (dif_metrica3))



        valor_vendas2 = f"R$ {total_vendas_PR : ,.2f}"
        dif_metrica2 = f"  {total_vendas_PR  / total_vendas_DIA *100: .2f} % "
        col2.metric('Valor presencial',
        valor_vendas2,
        (dif_metrica2))

        valor_vendas3 = f"R$ {total_vendas_ON : ,.2f}"
        dif_metrica3 = f"{total_vendas_ON / total_vendas_DIA *100: .2f} % "
        
        col3.metric('Valor on line',
        valor_vendas3,           
        (dif_metrica3))

        
        #st.write("### Vendas Presenciais")
        #st.write(f"### Vendas Presenciais: R${total_vendas_PR:,.2f}")
        st.dataframe(dados_PR)

        #st.write(f"### Vendas Online: R${total_vendas_ON:,.2f}")
        st.dataframe(dados_ON)


        #st.write(f"### Total de Vendas do Dia: R${total_vendas_DIA:,.2f}")
        #st.write(f"### Total de Vendas Presenciais: R${total_vendas_PR:.2f}")

# Página 2: Dashboard de Vendas
# Página 2: Dashboard de Vendas
if page == "Dashboard de Vendas":
    st.title("Dashboard de Vendas")

    tipos_selecionados = st.multiselect(
        "Selecione os Tipos de Vendas:",
        options=df_dnd['tipo'].unique(),
        default=df_dnd['tipo'].unique()
    )

    filtered_df = total_vendas_e_quantidade[total_vendas_e_quantidade['tipo'].isin(tipos_selecionados)]
    
    total_vendas_ON = filtered_df[filtered_df['tipo'] == 'ON']['total_receb'].sum()
    total_vendas_PR = filtered_df[filtered_df['tipo'] == 'PR']['total_receb'].sum()
    total_vendas = total_vendas_ON + total_vendas_PR

    total_output = (
        f"Total Vendas ON: R${total_vendas_ON:.2f}\n"
        f"Total Vendas PR: R${total_vendas_PR:.2f}\n"
        f"Total Vendas: R${total_vendas:.2f}"
    )

    st.write("### Totais de Vendas")
    st.write(total_output)

    # Gráfico de Vendas por Vendedor
    fig_vendas = px.bar(filtered_df, x='vendedor', y='total_receb', color='tipo', barmode='group')
    st.write("### Vendas por Vendedor")
    st.plotly_chart(fig_vendas)

    # Gráfico de Performance
    performance_df = filtered_df.groupby('vendedor').agg(
        total_receb=('total_receb', 'sum'),
        quantidade=('total_receb', 'count'),
        tkm=('total_receb', lambda x: x.sum()/x.count())
    ).reset_index()
    performance_df['desempenho'] = performance_df['total_receb'] * performance_df['tkm'] / 1000
    performance_df.sort_values('desempenho', ascending=True, inplace=True)

    fig_performance = go.Figure(data=[
        go.Bar(name='Total Recebido', x=performance_df['vendedor'], y=performance_df['total_receb']),
        go.Bar(name='Quantidade', x=performance_df['vendedor'], y=performance_df['quantidade']),
        go.Scatter(name='TKM', x=performance_df['vendedor'], y=performance_df['tkm'], yaxis='y2')
    ])
    fig_performance.update_layout(yaxis2={'overlaying': 'y', 'side': 'right', 'title': 'TKM'},
                                  yaxis={'title': 'Total / Quantidade'},
                                  xaxis={'categoryorder': 'total descending'})

    st.write("### Performance por Vendedor")
    st.plotly_chart(fig_performance)
    
    # Botão para download dos dados
    @st.cache_data
    def convert_df(df):
        return df.to_csv().encode('utf-8')

    csv = convert_df(filtered_df)

    st.download_button(
        label="Baixar Dados",
        data=csv,
        file_name='dados_filtrados.csv',
        mime='text/csv',
    )

# Página 3: Vendas da Semana
elif page == "Vendas da Semana":
    st.title("Vendas da Semana")
    
    semanas_disponiveis = df_agrupado['semana'].unique()
    semana_selecionada = st.selectbox("Selecione a Semana:", semanas_disponiveis)
    
    if semana_selecionada:
        Metas1_df = df_agrupado[df_agrupado['semana'] == semana_selecionada]
        Metas1_df = Metas1_df.sort_values(by='total_semanal', ascending=False)
        Metas1_df['tipo'] = Metas1_df['tipo'].str.strip()

        st.write(f"### Dados da Semana {semana_selecionada}")

        # Separar os dados por tipo
        dados_PR = Metas1_df[Metas1_df['tipo'] == 'PR'].copy()
        dados_ON = Metas1_df[Metas1_df['tipo'] == 'ON'].copy()

        # Adicionar metas e calcular restante e comissão
        dados_ON['MetaS1'] = 9780
        dados_ON['restante'] = dados_ON['total_semanal'] - dados_ON['MetaS1']
        dados_ON['comissao'] = dados_ON['total_semanal'].apply(calcular_comissao_ajustada_on)

        dados_PR['MetaS1'] = 19560
        dados_PR['restante'] = dados_PR['total_semanal'] - dados_PR['MetaS1']
        dados_PR['comissao'] = dados_PR['total_semanal'].apply(calcular_comissao_ajustada_pr)

        st.write("### Vendas Presenciais da Semana")
        st.dataframe(dados_PR)

        st.write("### Vendas Online da Semana")
        st.dataframe(dados_ON)

        st.write(f"### Total Vendas Presenciais: R${dados_PR['total_semanal'].sum():,.2f}")
        st.write(f"### Total Vendas Online: R${dados_ON['total_semanal'].sum():,.2f}")

        # Gráfico de Vendas Semanais por Vendedor
        fig_vendas_semanal = px.bar(Metas1_df, x='vendedor', y='total_semanal', color='tipo', barmode='group')
        st.write("### Vendas Semanais por Vendedor")
        st.plotly_chart(fig_vendas_semanal)

        # Gráfico de Performance Semanal
        performance_df_semanal = Metas1_df.groupby('vendedor').agg(
            total_semanal=('total_semanal', 'sum'),
            quantidade=('total_semanal', 'count'),
            tkm=('total_semanal', lambda x: x.sum()/x.count())
        ).reset_index()
        performance_df_semanal['desempenho'] = performance_df_semanal['total_semanal'] * performance_df_semanal['tkm'] / 1000
        performance_df_semanal.sort_values('desempenho', ascending=True, inplace=True)

        fig_performance_semanal = go.Figure(data=[
            go.Bar(name='Total Recebido', x=performance_df_semanal['vendedor'], y=performance_df_semanal['total_semanal']),
            go.Bar(name='Quantidade', x=performance_df_semanal['vendedor'], y=performance_df_semanal['quantidade']),
            go.Scatter(name='TKM', x=performance_df_semanal['vendedor'], y=performance_df_semanal['tkm'], yaxis='y2')
        ])
        fig_performance_semanal.update_layout(yaxis2={'overlaying': 'y', 'side': 'right', 'title': 'TKM'},
                                              yaxis={'title': 'Total / Quantidade'},
                                              xaxis={'categoryorder': 'total descending'})

        st.write("### Performance Semanal por Vendedor")
        st.plotly_chart(fig_performance_semanal)

        Df_dnd = df_dnd.replace({"(  )     - ": pd.NA})
        num_linhas_sem_telefone = Df_dnd['N_telefone'].isnull().sum()
        total_linhas = len(Df_dnd)
        percentual_linhas_sem_telefone = (num_linhas_sem_telefone / total_linhas) * 100

        Df_clientes = Df_dnd
        Df_classificacao = Df_clientes.groupby('classificacao').agg({'total_receb': 'sum'})
        ticket_medio = Df_clientes.groupby('classificacao')['total_receb'].mean()
        vendas_por_vendedor = Df_clientes.groupby('vendedor')['total_receb'].sum()
        freq_class = Df_dnd['classificacao'].value_counts()

        qtd_pedidos = df_dnd['Pedido'].count()
        Valor_total_vendido = df_dnd['total_receb'].sum()
        tmk_dia = Valor_total_vendido / qtd_pedidos
        clien_nv = len(df_dnd[df_dnd['tipo_clientes'] == 'novo'])
        clein_sc = len(df_dnd[df_dnd['tipo_clientes'] == 'sem cadastro'])
        clein_at = len(df_dnd[df_dnd['tipo_clientes'] == 'antigo'])
        percentual_sem_cadastro = clein_sc / qtd_pedidos * 100

        meta_venda_1 = 495000  # Defina sua meta de vendas
        percentual_meta_atingida = (Valor_total_vendido / meta_venda_1) * 100


        
         # Verificar se os DataFrames retornados não são None
    if novo_df is not None and vendas_por_vendedor_df is not None:
        # Exibindo os DataFrames no Streamlit
        st.dataframe(novo_df)
        st.dataframe(vendas_por_vendedor_df)
        
        # Adicionando KPIs
        col1, col2, col3 = st.columns(3)
        
        meta_venda_1 = 495000  # Defina sua meta de vendas
        Valor_total_vendido = Df_clientes['total_receb'].sum()
        percentual_meta_atingida = (Valor_total_vendido / meta_venda_1) * 100
        qtd_pedidos = Df_clientes['Pedido'].count()
        tmk_dia = Valor_total_vendido / qtd_pedidos
        clien_nv = len(Df_clientes[Df_clientes['tipo_clientes'] == 'novo'])
        clein_sc = len(Df_clientes[Df_clientes['tipo_clientes'] == 'sem cadastro'])
        clein_at = len(Df_clientes[Df_clientes['tipo_clientes'] == 'antigo'])
        percentual_sem_cadastro = clein_sc / qtd_pedidos * 100

        num_linhas_sem_telefone = Df_clientes['N_telefone'].isnull().sum()
        total_linhas = len(Df_clientes)
        percentual_linhas_sem_telefone = (num_linhas_sem_telefone / total_linhas) * 100

        col1.metric('Meta de Vendas', f"R$ {meta_venda_1:,.0f}")
        col1.metric('Total Vendido', f"R$ {Valor_total_vendido:,.0f}", f"{percentual_meta_atingida:,.2f}% da meta")
        col2.metric('Ticket Médio', f"R$ {tmk_dia:,.2f}")
        col2.metric('Total de Pedidos', qtd_pedidos)
        col3.metric('Clientes Novos', clien_nv)
        col3.metric('Clientes sem Cadastro', clein_sc, f"{percentual_sem_cadastro:,.2f}%")
        col1.metric('Clientes Antigos', clein_at)
        col1.metric('Linhas sem Telefone', num_linhas_sem_telefone, f"{percentual_linhas_sem_telefone:.2f}%")
    else:
        st.error("O DataFrame Df_clientes não foi carregado corretamente.")
        


# Página 4: Indicadores
elif page == "Indicadores":
    st.title("Indicadores de Vendas")

    st.write("### Indicadores por Classificação de Cliente")
    st.dataframe(novo_df.style.set_table_styles([
        {'selector': 'th', 'props': [('font-size', '8pt'), ('background-color', 'lightblue')]},
        {'selector': 'td', 'props': [('font-size', '7pt')]}
    ]).format(precision=2, decimal=","))

    st.write("### Indicadores por Vendedor")
    st.dataframe(vendas_por_vendedor_df.style.set_table_styles([
        {'selector': 'th', 'props': [('font-size', '8pt'), ('background-color', 'lightblue')]},
        {'selector': 'td', 'props': [('font-size', '7pt')]}
    ]).format(precision=2, decimal=","))

    st.write("### Gráfico de Performance dos Vendedores")
    fig_performance_vendedores = px.bar(vendas_por_vendedor_df.head(9), x='vendedor', y='Perfor', title="Top 9 Performance por Vendedor")
    st.plotly_chart(fig_performance_vendedores)

    st.write("### Gráfico de Participação das Top 7 Vendedoras")
    top_vendedoras = vendas_por_vendedor_df.sort_values(by='Vendido', ascending=False).head(7)
    top_vendedoras['Percentual'] = (top_vendedoras['Vendido'] / top_vendedoras['Vendido'].sum()) * 100
    fig_pie = px.pie(top_vendedoras, values='Percentual', names='vendedor', title='Contribuição de Vendas por Vendedora')
    st.plotly_chart(fig_pie)


    Df_dnd = df_dnd.replace({"(  )     - ": pd.NA})
    #st.write("Nomes das colunas no DataFrame Df_dnd:", Df_dnd.columns)
    num_linhas_sem_telefone = Df_dnd['N_telefone'].isnull().sum()
    total_linhas = len(Df_dnd)
    percentual_linhas_sem_telefone = (num_linhas_sem_telefone / total_linhas) * 100

    Df_clientes = Df_dnd
    Df_classificacao = Df_clientes.groupby('classificacao').agg({'total_receb': 'sum'})
    ticket_medio = Df_clientes.groupby('classificacao')['total_receb'].mean()
    vendas_por_vendedor = Df_clientes.groupby('vendedor')['total_receb'].sum()
    freq_class = Df_dnd['classificacao'].value_counts()

    qtd_pedidos = df_dnd['Pedido'].count()
    Valor_total_vendido = df_dnd['total_receb'].sum()
    tmk_dia = Valor_total_vendido / qtd_pedidos
    clien_nv = len(df_dnd[df_dnd['tipo_clientes'] == 'novo'])
    clein_sc = len(df_dnd[df_dnd['tipo_clientes'] == 'sem cadastro'])
    clein_at = len(df_dnd[df_dnd['tipo_clientes'] == 'antigo'])
    percentual_sem_cadastro = clein_sc / qtd_pedidos * 100

    meta_venda_1 = 490000  # Defina sua meta de vendas
    percentual_meta_atingida = (Valor_total_vendido / meta_venda_1) * 100

    html_output = f"""
        <style>
            .resultado-mes {{
                font-family: 'Arial';
                font-size: 15px;
            }}
            .resultado-mes h2 {{
                font-size: 15px;
            }}
            .resultado-mes h3 {{
                color: green;
                font-size: 15px;
            }}
            .resultado-mes p {{
                font-size: 15px;
            }}
        </style>

    <div class="resultado-mes">
        <h2>Resultado do Mês</h2>
        <h2>Alvo de venda: R${meta_venda_1:,.0f}</h2>
        <h2>Total Vendido no Mês: R${Valor_total_vendido:,.0f}</h2>
        <h2>Alcançado: {percentual_meta_atingida:,.2f}% da meta</h2>
        <h3>O Ticket Médio do Mês: R${tmk_dia:,.2f}</h3>
        <br>
        <p>O número total de pedidos: <strong>{qtd_pedidos}</strong></p>
        <p>O número de clientes novos: <strong>{clien_nv}</strong></p>
        <p>O número de clientes sem cadastro é: <strong>{clein_sc}</strong></p>
        <p>O número de clientes da Base é: <strong>{clein_at}</strong></p>
        <p>O percentual de clientes não cadastrados é: <strong>{percentual_sem_cadastro:,.2f}%</strong></p>
        <p>O linhas sem informação N_telefone <strong>{num_linhas_sem_telefone:}</strong></p>
        <p>O Percentual de cadastro sem celular <strong>{percentual_linhas_sem_telefone:.2f}%</strong></p>
        </div>
    """

    st.markdown(html_output, unsafe_allow_html=True)






    
    

# Página 5: Descontos por Data
elif page == "Descontos por Data":
    st.title("Descontos por Data")

    # Seleção de data ou período de tempo
    date_option = st.radio("Escolha uma opção:", ["Data específica", "Período de tempo"])
    
    if date_option == "Data específica":
        selected_date = st.date_input("Selecione a data:", value=pd.to_datetime("today"))
        mask = (df_dnd['data'].dt.date == selected_date)
    else:
        start_date = st.date_input("Data inicial:", value=pd.to_datetime("today"))
        end_date = st.date_input("Data final:", value=pd.to_datetime("today"))
        mask = (df_dnd['data'].dt.date >= start_date) & (df_dnd['data'].dt.date <= end_date)
    
    filtered_data = df2dnd
    #st.write("Nomes das colunas no DataFrame Df_dnd:", filtered_data.columns)
    
    # Verifique se as colunas necessárias estão no DataFrame
    required_columns = ['data', 'id_client', 'cliente', 'vendedor', 'vendido', 'desconto']
    missing_columns = [col for col in required_columns if col not in filtered_data.columns]
    
    if missing_columns:
        st.write(f"As seguintes colunas estão faltando na base de dados: {', '.join(missing_columns)}")
    else:
        # Filtrar os dados para descontos maiores que zero
        filtered_data['desconto'] = pd.to_numeric(filtered_data['desconto'], errors='coerce')
        filtered_data = filtered_data[filtered_data['desconto'] > 0]
        
        if filtered_data.empty:
            st.write("Nenhum desconto encontrado para o período selecionado.")
        else:
            filtered_data['%desconto'] = (filtered_data['desconto'] / filtered_data['vendido']) * 100
            filtered_data['%desconto'].fillna(0, inplace=True)
            filtered_data = filtered_data.sort_values('%desconto', ascending=False)
            
            st.write("### Clientes com Desconto")
            st.dataframe(filtered_data[['data', 'id_client', 'cliente', 'vendedor', 'vendido', 'desconto', '%desconto']])
            
            total_desconto = filtered_data['desconto'].sum()
            st.write(f"### Total de Descontos: R${total_desconto:,.2f}")
            
            aggregated_discounts = filtered_data.groupby('vendedor')['desconto'].sum().reset_index()
            aggregated_discounts = aggregated_discounts.sort_values('desconto', ascending=False)
            
            fig = px.bar(aggregated_discounts, x='vendedor', y='desconto', title="Total de Descontos por Vendedora", labels={'desconto': 'Total de Descontos', 'vendedora': 'Vendedora'}, text='desconto')
            fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
            st.plotly_chart(fig)
