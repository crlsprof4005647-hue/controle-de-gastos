import streamlit as st
import pandas as pd
import datetime 
import altair as alt
from streamlit_gsheets import GSheetsConnection

# Função auxiliar para deixar o dinheiro no padrão Brasil (R$ 1.234,56)
def formata_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================================
# 1. CONFIGURAÇÃO INICIAL DA PÁGINA
# ==========================================
st.set_page_config(page_title="Controle Financeiro", layout="wide")

# ==========================================
# 2. CUSTOMIZAÇÃO DE LAYOUT (Fundo e Cores)
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    cor_de_fundo = """
    <style>
        .stApp { background-color: #0F172A; }
        h1, h2, h3, p, label, .stMarkdown { color: #FFFFFF !important; }
        div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            border: none !important;
        }
        div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #1D4ED8 !important;
        }
    </style>
    """
else:
    cor_de_fundo = """
    <style>
        .stApp { background-color: #1E293B; }
        
        /* Textos e Títulos */
        h1, h2, h3, h4, p, label, .stMarkdown, div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] { 
            color: #FFFFFF !important; 
        }
        
        /* Consertando Botões */
        div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            border: none !important;
        }
        div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #1D4ED8 !important;
        }
        
        /* Consertando Inputs e Selectbox */
        div[data-baseweb="select"] > div, input, div[data-baseweb="base-input"] {
            background-color: #334155 !important;
            color: #FFFFFF !important;
            border-color: #475569 !important;
        }
        
        /* Consertando as Abas (Tabs) */
        button[data-baseweb="tab"] {
            background-color: transparent !important;
            color: #94A3B8 !important; 
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #FFFFFF !important; 
            border-bottom-color: #2563EB !important; 
        }
    </style>
    """
st.markdown(cor_de_fundo, unsafe_allow_html=True)


# ==========================================
# 3. O SISTEMA DE LOGIN 
# ==========================================
if not st.session_state["autenticado"]:
    st.title("🔒 Acesso Restrito")
    
    with st.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password") 
        botao_entrar = st.form_submit_button("Entrar")

    if botao_entrar:
        senhas_salvas = st.secrets["senhas"]
        if email in senhas_salvas and senhas_salvas[email] == senha:
            st.session_state["autenticado"] = True 
            st.session_state["aba_usuario"] = st.secrets["ambientes"][email]
            st.rerun() 
        else:
            st.error("E-mail ou senha incorretos!")
    
    st.stop() 


# ==========================================
# 4. ÁREA LOGADA (O APLICATIVO FINANCEIRO)
# ==========================================
st.title("💲 Meu Controle Financeiro")
st.write(f"Bem-vindo(a)! Base de dados ativa: **{st.session_state['aba_usuario']}**")

conn = st.connection("gsheets", type=GSheetsConnection)
dados_atuais = conn.read(worksheet=st.session_state["aba_usuario"], usecols=list(range(10)), ttl=0)

# Garantir que Valores são números para os cálculos
dados_atuais["Valor"] = pd.to_numeric(dados_atuais["Valor"], errors="coerce").fillna(0)

# --- CARTÕES GLOBAIS DE RESUMO ---
total_entradas = dados_atuais[dados_atuais["Tipo"] == "Entrada"]["Valor"].sum()
total_saidas = dados_atuais[dados_atuais["Tipo"] == "Saída"]["Valor"].sum()
saldo_atual = total_entradas - total_saidas

col_card1, col_card2, col_card3 = st.columns(3)
col_card1.metric("⬆️ Entradas", formata_moeda(total_entradas))
col_card2.metric("⬇️ Saídas", formata_moeda(total_saidas))
col_card3.metric("💰 Saldo Atual", formata_moeda(saldo_atual))

st.write("") 
# ==========================================
# 5. CRIANDO AS ABAS DE NAVEGAÇÃO
# ==========================================
aba_lancamentos, aba_relatorios = st.tabs(["📝 Lançamentos", "📊 Gráficos e Relatórios"])


# ------------------------------------------
# ABA 1: LANÇAMENTOS 
# ------------------------------------------
with aba_lancamentos:
    if st.session_state["aba_usuario"] == "Transacao":
        lista_de_contas = ["Cartão de Crédito", "Dinheiro/Débito ou PIX"]
        lista_de_categorias = ["delivery", "Luz", "Água", "Internet", "Financiamento Casa", "Salário", "Uber", "Lazer", "Outros"]
    else:
        lista_de_contas = ["Cartão de Crédito", "Conta Corrente", "Dinheiro/PIX"]
        lista_de_categorias = ["Internet", "Carro", "Aluguel", "Faculdade", "Salário", "Lazer", "Outros"]

    st.subheader("📝 Adicionar Nova Transação")
    
    tipo_input = st.radio("Selecione o Tipo:", ["Saída", "Entrada"], horizontal=True)

    with st.form(key="form_nova_transacao", clear_on_submit=True):
        coluna1, coluna2 = st.columns(2)
        
        with coluna1:
            data_input = st.date_input("Data da Compra", datetime.date.today())
            descricao_input = st.text_input("Descrição", placeholder="Ex: Compra no Mercado...")
            valor_input = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
            
        with coluna2:
            categoria_input = st.selectbox("Categoria", lista_de_categorias)
            conta_input = st.selectbox("Conta (Origem/Destino)", lista_de_contas)
            
            num_parcelas = 1
            data_vencimento = data_input

            if tipo_input == "Saída":
                status_input = st.selectbox("Status", ["Pago", "Pendente"])
                recorrencia_input = st.selectbox("Recorrência", ["Único", "Fixo Mensal", "Parcelado"])
                
                if recorrencia_input == "Parcelado":
                    st.markdown("---")
                    st.markdown("**Detalhes do Parcelamento**")
                    col_parc1, col_parc2 = st.columns(2)
                    with col_parc1:
                        num_parcelas = st.number_input("Qtd. de Parcelas", min_value=2, max_value=120, value=2, step=1)
                    with col_parc2:
                        data_vencimento = st.date_input("Vencimento 1ª Parcela", datetime.date.today())
            else:
                st.info("💡 Entradas são registradas automaticamente como 'Pago' e 'Único'.")
                status_input = "Pago"
                recorrencia_input = "Único"

        botao_salvar = st.form_submit_button("Salvar Transação")

    if botao_salvar:
        linhas_novas = []
        
        if tipo_input == "Saída" and recorrencia_input == "Parcelado":
            valor_da_parcela = valor_input / num_parcelas
            
            for i in range(num_parcelas):
                novo_id = len(dados_atuais) + i + 1
                data_parcela = (pd.Timestamp(data_vencimento) + pd.DateOffset(months=i)).date()
                descricao_parcela = f"{descricao_input} ({i+1}/{num_parcelas})"
                
                status_parcela = status_input if i == 0 else "Pendente"
                data_baixa_parcela = datetime.date.today().strftime("%d/%m/%Y") if status_parcela == "Pago" else ""
                
                linhas_novas.append({
                    "ID": novo_id, "Data": data_parcela.strftime("%d/%m/%Y"), "Descricao": descricao_parcela,
                    "Valor": valor_da_parcela, "Tipo": tipo_input, "Categoria": categoria_input,
                    "Conta_Origem": conta_input, "Status": status_parcela, "Recorrencia": recorrencia_input,
                    "Data_Baixa": data_baixa_parcela,
                })
        else:
            novo_id = len(dados_atuais) + 1
            linhas_novas.append({
                "ID": novo_id, "Data": data_input.strftime("%d/%m/%Y"), "Descricao": descricao_input,
                "Valor": valor_input, "Tipo": tipo_input, "Categoria": categoria_input,
                "Conta_Origem": conta_input, "Status": status_input, "Recorrencia": recorrencia_input,
                "Data_Baixa": datetime.date.today().strftime("%d/%m/%Y") if status_input == "Pago" else "",
            })

        df_linhas_novas = pd.DataFrame(linhas_novas)
        dados_atualizados = pd.concat([dados_atuais, df_linhas_novas], ignore_index=True)
        conn.update(worksheet=st.session_state["aba_usuario"], data=dados_atualizados)
        
        st.success(f"Transação '{descricao_input}' salva com sucesso!")
        st.rerun()

    st.divider()

    # --- NOVIDADE: FILTRO INTELIGENTE DE MÊS/ANO ---
    st.markdown("### 🔍 Filtrar Visualização Abaixo")
    
    # Extrai as datas e cria a lista de meses disponíveis (ex: 09/2026, 10/2026)
    datas_convertidas = pd.to_datetime(dados_atuais["Data"], format="%d/%m/%Y", errors="coerce").dropna()
    meses_disponiveis = datas_convertidas.dt.strftime("%m/%Y").unique().tolist()
    meses_disponiveis = sorted(meses_disponiveis, key=lambda x: datetime.datetime.strptime(x, "%m/%Y"))
    
    opcoes_filtro = ["Todos"] + meses_disponiveis
    mes_selecionado = st.selectbox("Selecione o Mês de Vencimento:", opcoes_filtro)

    # Aplica o filtro na tabela temporária que alimenta os painéis abaixo
    if mes_selecionado != "Todos":
        mascara_mes = datas_convertidas.dt.strftime("%m/%Y") == mes_selecionado
        # Pega as linhas que correspondem ao mês (usando o índice para bater certinho)
        dados_filtrados = dados_atuais.loc[mascara_mes.index[mascara_mes]].copy()
    else:
        dados_filtrados = dados_atuais.copy()

    st.divider()

    # --- PAINEL DE DAR BAIXA (Agora respeita o Filtro) ---
    st.subheader("✅ Dar Baixa em Pagamentos Pendentes")
    pendentes = dados_filtrados[dados_filtrados["Status"] == "Pendente"]

    if not pendentes.empty:
        opcoes_pendentes = (
            pendentes["ID"].astype(int).astype(str) 
            + " - " + pendentes["Descricao"] 
            + " | " + pendentes["Conta_Origem"]
            + " (R$ " + pendentes["Valor"].astype(str) + ")"
        )
        col_baixa1, col_baixa2 = st.columns([3, 1]) 
        with col_baixa1:
            transacao_escolhida = st.selectbox("Selecione a transação:", opcoes_pendentes, key="select_pendentes")
        with col_baixa2:
            st.write(""); st.write("") 
            botao_baixa = st.button("Dar Baixa")

        if botao_baixa:
            id_escolhido = int(float(transacao_escolhida.split(" - ")[0]))
            # A baixa altera o dado original para garantir que salva certo no banco
            indice = dados_atuais.index[dados_atuais["ID"] == id_escolhido][0]
            dados_atuais.at[indice, "Status"] = "Pago"
            dados_atuais.at[indice, "Data_Baixa"] = datetime.date.today().strftime("%d/%m/%Y")
            conn.update(worksheet=st.session_state["aba_usuario"], data=dados_atuais)
            st.success("Pagamento baixado com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum pagamento pendente para este filtro! Tudo em dia. 🎉")

    st.divider()

    # --- PAINEL DE DESFAZER PAGAMENTO (Agora respeita o Filtro) ---
    st.subheader("⏪ Desfazer Pagamento (Voltar para Pendente)")
    pagos = dados_filtrados[dados_filtrados["Status"] == "Pago"]

    if not pagos.empty:
        opcoes_pagos = (
            pagos["ID"].astype(int).astype(str) 
            + " - " + pagos["Descricao"] 
            + " | " + pagos["Conta_Origem"]
            + " (R$ " + pagos["Valor"].astype(str) + ")"
        )
        col_desfaz1, col_desfaz2 = st.columns([3, 1]) 
        with col_desfaz1:
            transacao_paga_escolhida = st.selectbox("Selecione o pagamento a desfazer:", opcoes_pagos, key="select_pagos")
        with col_desfaz2:
            st.write(""); st.write("") 
            botao_desfazer = st.button("Desfazer Baixa")

        if botao_desfazer:
            id_escolhido_desfaz = int(float(transacao_paga_escolhida.split(" - ")[0]))
            indice_desfaz = dados_atuais.index[dados_atuais["ID"] == id_escolhido_desfaz][0]
            
            dados_atuais.at[indice_desfaz, "Status"] = "Pendente"
            dados_atuais.at[indice_desfaz, "Data_Baixa"] = ""
            
            conn.update(worksheet=st.session_state["aba_usuario"], data=dados_atuais)
            st.success("Pagamento revertido para pendente com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum pagamento concluído para desfazer neste filtro.")

    st.divider()

    # --- TABELA DE RESUMO POR CATEGORIA (Respeita o Filtro) ---
    st.subheader("📋 Resumo de Gastos por Categoria")
    saidas_df = dados_filtrados[dados_filtrados["Tipo"] == "Saída"].copy()
    
    if not saidas_df.empty:
        resumo_cat = saidas_df.groupby("Categoria")["Valor"].sum().reset_index()
        total_saidas_calc = resumo_cat["Valor"].sum()
        
        resumo_cat = resumo_cat.sort_values(by="Valor", ascending=False)
        resumo_cat["Porcentagem (%)"] = (resumo_cat["Valor"] / total_saidas_calc) * 100
        
        resumo_cat["Valor"] = resumo_cat["Valor"].apply(formata_moeda)
        resumo_cat["Porcentagem (%)"] = resumo_cat["Porcentagem (%)"].apply(lambda x: f"{x:.1f} %")
        
        st.dataframe(resumo_cat, use_container_width=True, hide_index=True)
    else:
        st.write("Nenhum gasto registrado para gerar o resumo neste filtro.")

    # --- TABELA DE EDIÇÃO LIVRE (Respeita o Filtro com Atualização Segura) ---
    st.subheader("📊 Histórico de Transações")
    st.write("💡 Dê um duplo clique em qualquer célula para editar.")
    
    dados_exibicao = dados_filtrados.rename(columns=lambda x: x.replace("_", " "))
    dados_editados = st.data_editor(dados_exibicao, use_container_width=True, hide_index=True, key="editor_tabela")

    if not dados_exibicao.equals(dados_editados):
        st.warning("⚠️ Você fez alterações na tabela. Clique abaixo para confirmar.")
        if st.button("💾 Salvar Alterações no Banco"):
            
            dados_para_salvar = dados_editados.rename(columns=lambda x: x.replace(" ", "_"))
            
            # Lógica de Segurança: Pega a base completa e atualiza APENAS as linhas alteradas (pelo ID)
            dados_base = dados_atuais.copy()
            
            dados_base["ID"] = pd.to_numeric(dados_base["ID"], errors="coerce")
            dados_para_salvar["ID"] = pd.to_numeric(dados_para_salvar["ID"], errors="coerce")
            
            dados_base = dados_base.set_index("ID")
            dados_para_salvar = dados_para_salvar.set_index("ID")
            
            # Atualiza a base principal com os dados modificados no filtro
            dados_base.update(dados_para_salvar)
            
            # Volta o ID para ser uma coluna
            dados_base = dados_base.reset_index()
            
            conn.update(worksheet=st.session_state["aba_usuario"], data=dados_base)
            st.success("Alterações salvas com sucesso!")
            st.rerun() 


# ------------------------------------------
# ABA 2: GRÁFICOS E RELATÓRIOS 
# ------------------------------------------
with aba_relatorios:
    st.subheader("📊 Painel de Inteligência Financeira")
    
    dados_graficos = dados_atuais.copy()
    dados_graficos["Data_Real"] = pd.to_datetime(dados_graficos["Data"], format="%d/%m/%Y", errors="coerce")
    dados_graficos["Mes_Ano"] = dados_graficos["Data_Real"].dt.strftime("%Y-%m")
    
    if not dados_graficos.empty and not dados_graficos["Data_Real"].isnull().all():
        
        # --- GRÁFICO 1: Balanço Mensal ---
        st.markdown("#### ⚖️ Balanço Mensal (Entradas x Saídas x Diferença)")
        
        resumo_mes = dados_graficos.groupby(["Mes_Ano", "Tipo"])["Valor"].sum().unstack(fill_value=0)
        if "Entrada" not in resumo_mes.columns: resumo_mes["Entrada"] = 0
        if "Saída" not in resumo_mes.columns: resumo_mes["Saída"] = 0
        resumo_mes["Diferença"] = resumo_mes["Entrada"] - resumo_mes["Saída"]
        
        resumo_melted = resumo_mes.reset_index().melt(id_vars="Mes_Ano", value_vars=["Entrada", "Saída", "Diferença"], var_name="Tipo", value_name="Valor")
        
        base_balanco = alt.Chart(resumo_melted).encode(
            x=alt.X('Mes_Ano:N', title='Mês', axis=alt.Axis(labelAngle=0, labelColor='white', titleColor='white', grid=False)),
            y=alt.Y('Valor:Q', title='Valor (R$)', axis=alt.Axis(labelColor='white', titleColor='white', grid=False, labels=False)),
            color=alt.Color('Tipo:N', scale=alt.Scale(domain=['Entrada', 'Saída', 'Diferença'], range=['#10B981', '#EF4444', '#3B82F6']), legend=alt.Legend(labelColor='white', titleColor='white')),
            xOffset='Tipo:N',
            tooltip=['Mes_Ano', 'Tipo', 'Valor']
        )
        
        barras_balanco = base_balanco.mark_bar()
        textos_balanco = base_balanco.mark_text(align='center', baseline='bottom', dy=-5, color='white', fontWeight='bold').encode(
            text=alt.Text('Valor:Q', format='.2f')
        )
        
        grafico_balanco = alt.layer(barras_balanco, textos_balanco).configure_view(strokeOpacity=0).configure(background='transparent').properties(height=350)
        st.altair_chart(grafico_balanco, use_container_width=True, theme=None)
        
        st.divider()

        saidas = dados_graficos[dados_graficos["Tipo"] == "Saída"]
        
        if not saidas.empty:
            # --- GRÁFICOS 2 e 3: Roscas ---
            st.markdown("#### 🍩 Distribuição de Despesas")
            col_rosca1, col_rosca2 = st.columns(2)
            
            with col_rosca1:
                st.markdown("**Por Categoria**")
                gastos_cat = saidas.groupby("Categoria")["Valor"].sum().reset_index()
                
                base_cat = alt.Chart(gastos_cat).encode(
                    theta=alt.Theta(field="Valor", type="quantitative"),
                    color=alt.Color(field="Categoria", type="nominal", legend=alt.Legend(labelColor='white', titleColor='white')),
                    tooltip=["Categoria", "Valor"]
                )
                
                rosca_cat = base_cat.mark_arc(innerRadius=50)
                texto_cat = base_cat.mark_text(radius=80, color='white', fontWeight='bold', size=11).encode(
                    text=alt.Text('Valor:Q', format='.2f')
                )
                
                grafico_cat_final = alt.layer(rosca_cat, texto_cat).configure_view(strokeOpacity=0).configure(background='transparent').properties(height=300)
                st.altair_chart(grafico_cat_final, use_container_width=True, theme=None)
                
            with col_rosca2:
                st.markdown("**Por Conta (Origem)**")
                gastos_conta_rosca = saidas.groupby("Conta_Origem")["Valor"].sum().reset_index()
                
                base_conta = alt.Chart(gastos_conta_rosca).encode(
                    theta=alt.Theta(field="Valor", type="quantitative"),
                    color=alt.Color(field="Conta_Origem", type="nominal", legend=alt.Legend(labelColor='white', titleColor='white')),
                    tooltip=["Conta_Origem", "Valor"]
                )
                
                rosca_conta = base_conta.mark_arc(innerRadius=50)
                texto_conta = base_conta.mark_text(radius=80, color='white', fontWeight='bold', size=11).encode(
                    text=alt.Text('Valor:Q', format='.2f')
                )
                
                grafico_conta_final = alt.layer(rosca_conta, texto_conta).configure_view(strokeOpacity=0).configure(background='transparent').properties(height=300)
                st.altair_chart(grafico_conta_final, use_container_width=True, theme=None)
                
            st.divider()
            
            # --- GRÁFICO 4: Formas de Pagamento Mensal ---
            st.markdown("#### 💳 Evolução das Formas de Pagamento")
            
            evolucao_contas = saidas.groupby(["Mes_Ano", "Conta_Origem"])["Valor"].sum().reset_index()
            
            base_contas = alt.Chart(evolucao_contas).encode(
                x=alt.X('Mes_Ano:N', title='Mês', axis=alt.Axis(labelAngle=0, labelColor='white', titleColor='white', grid=False)),
                y=alt.Y('Valor:Q', title='Gasto (R$)', axis=alt.Axis(labelColor='white', titleColor='white', grid=False, labels=False)), 
                color=alt.Color('Conta_Origem:N', legend=alt.Legend(labelColor='white', titleColor='white')),
                xOffset='Conta_Origem:N',
                tooltip=['Mes_Ano', 'Conta_Origem', 'Valor']
            )
            
            barras_contas = base_contas.mark_bar()
            textos_contas = base_contas.mark_text(align='center', baseline='bottom', dy=-5, color='white', fontWeight='bold').encode(
                text=alt.Text('Valor:Q', format='.2f')
            )
            
            grafico_contas_final = alt.layer(barras_contas, textos_contas).configure_view(strokeOpacity=0).configure(background='transparent').properties(height=350)
            
            st.altair_chart(grafico_contas_final, use_container_width=True, theme=None)
            
        else:
            st.info("Nenhuma despesa (Saída) registrada para gerar os relatórios detalhados.")
            
    else:
        st.info("Adicione transações para ver os gráficos!")
